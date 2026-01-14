from tkinter import *
from tkinter import ttk, messagebox
import math
import sys
import subprocess
from datetime import datetime, timedelta
import urllib.request
import json
import time
import urllib.request, json
from tkinter import ttk


# Try importing SimpleEval; if missing, attempt to install it into
# the same Python interpreter running this script, then re-import.
try:
  from simpleeval import SimpleEval
except Exception:
  try:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'simpleeval'])
    from simpleeval import SimpleEval
  except Exception:
    # Friendly error explaining how to install the dependency manually
    msg = (
      "The required package 'simpleeval' is not installed and automatic install failed.\n"
      "Please install it for the Python interpreter used by VS Code or your run button.\n\n"
      "Suggested commands:\n"
      "pip install simpleeval\n"
      "or, if using the workspace virtualenv:\n"
      "C:/Users/hp/Documents/Python/InventoryManagment/.venv/Scripts/python.exe -m pip install simpleeval\n\n"
      "After installing, re-run this script."
    )
    try:
      root = Tk()
      root.withdraw()
      messagebox.showerror('Missing dependency', msg)
      root.destroy()
    except Exception:
      print(msg, file=sys.stderr)
    sys.exit(1)

window = Tk()

window.title('CALCULATOR')
window.geometry('1270x668+0+0')
window.resizable(0,0)
window.config(bg = 'white')

# Tracks whether the last action produced a result via '='
just_evaluated = False
# History storage
history_items = []
# Angle mode: 'rad' or 'deg'
angle_mode = 'rad'
# Theme state
theme = 'light'
# Memory register for M+, M-, MR, MC
memory_value = 0.0
memory_display_var = StringVar(value='')

global curr_result_var

curr_result_var = StringVar()

# Loading the currency Codes

def load_currency_list():
    url = "https://api.exchangerate.host/symbols"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if "symbols" in data:
        return list(data["symbols"].keys())
    return ["USD","EUR","INR","GBP","JYP","CNY", "AUD", "CAD", "CHF","NZD","BRL", "RUB", "ZAR","MXN", "SGD", "HKD", "SAR", "SEK", "AED", "QAR", "KWD", "OMR", "BHD", "EGP","JOD", "LBP", "IQD", "SPY", "YER", "IRR", "TRY" ]

# Getting live rates of currency 

def fetch_live_now():
  """Manually attempt a live fetch for the currently selected pair and report status."""
  frm = curr_from_var.get()
  to = curr_to_var.get()
  try:
    url = f"https://api.exchangerate.host/convert?from={urllib.request.quote(frm)}&to={urllib.request.quote(to)}&amount=1"
    with urllib.request.urlopen(url, timeout=6) as resp:
      data = resp.read()
    j = json.loads(data.decode('utf-8'))
    if isinstance(j, dict):
      if 'info' in j and isinstance(j['info'], dict) and 'rate' in j['info']:
        last_fetch_label.set('Live OK')
        return
      if 'result' in j:
        last_fetch_label.set('Live OK')
        return
    last_fetch_label.set('Live: unexpected response')
  except Exception as e:
    last_fetch_label.set(f'Live failed: {str(e)[:60]}')

# Converts the from currency to desired currency

def convert_currency():
  # try to get live rate from exchangerate.host; fall back to static example rates
  static_rates = {'USD':1.0, 'EUR':0.92, 'GBP':0.78, 'INR':82.0}

  # simple in-memory cache for live rates: {(frm,to): (rate, ts)}
  if 'rates_cache' not in globals():
    rates_cache = {}
    rates_cache_ttl = 300
  else:
    rates_cache = globals().get('rates_cache')
    rates_cache_ttl = globals().get('rates_cache_ttl', 300)

  def _fetch_live_rate(frm, to, timeout=5):
    """Return conversion rate (float) for 1 unit of frm -> to, or None on failure."""
    frm = frm.lower()
    to = to.lower()
    url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{frm}.json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read()
        j = json.loads(data.decode('utf-8'))
        if frm in j and to in j[frm]:
            r = float(j[frm][to])
            return r
        else:
            last_fetch_label.set("Live: unexpected JSON structure")
            return None
    except Exception as e:
        last_fetch_label.set(f"Live fetch error: {str(e)[:80]}")
        return None

  try:
    amt_text = curr_amount_var.get().strip()
    # if amount field is empty, use the current calculator input
    if amt_text == '':
      amt_text = calc_input.get().strip()
      # also populate the amount field for user feedback
      curr_amount_var.set(amt_text)
    amt = float(amt_text)
    frm = curr_from_var.get()
    to = curr_to_var.get()

    out = None
    if live_rates_var.get():
      rate = _fetch_live_rate(frm, to)
      if rate is not None:
        out = amt * rate
        last_fetch_label.set('Live OK')
      else:
        # If live rates requested, report failure and do not silently use static rates
        # last_fetch_label will contain an error message set by _fetch_live_rate
        curr_result_var.set('Live fetch failed')
        return
    else:
      # fallback to static rates when live is disabled
      if frm not in static_rates or to not in static_rates:
        curr_result_var.set('Rate error')
        return
      usd = amt / static_rates[frm]
      out = usd * static_rates[to]

    if float(out).is_integer():
      curr_result_var.set(str(int(out)))
    else:
      curr_result_var.set(format(out, '.6g'))
  except Exception:
    curr_result_var.set('Input error')

# Currency Exchange Panel (basic, static rates)

currency_frame = Frame(window, bd=4, relief=RIDGE, bg='white')
currency_frame.place(x=940, y=2, width=320, height=250)
Button(currency_frame, 
        text='Convert',
        font=('Arial', 10), 
        command=convert_currency).grid(row=6, column=0, pady=5)
Button(currency_frame, 
        text='Fetch Now',
        font=('Arial', 10), 
        command= lambda : fetch_live_now()).grid(row=6, column=2, pady=5)

Label(currency_frame, 
      text='Currency Converter', 
      font=('Arial', 12, 'bold'), 
      bg='white').grid(row=0, column=0,pady=5, columnspan=3, sticky='w')
  # live-rate toggle and status
live_rates_var = BooleanVar(value=True)
last_fetch_label = StringVar(value='')

curr_amount_var = StringVar(value='1')
curr_from_var = StringVar(value='USD')
curr_to_var = StringVar(value='INR')

Label(currency_frame, 
      text='Amount:',
      font=('Arial', 10), 
      bg='white').grid(row=1, column=0,pady=5, sticky='w')
Entry(currency_frame, 
      textvariable=curr_amount_var,
      font=('Arial', 10)).grid(row=1, column=1,pady=5, columnspan=2)
Label(currency_frame, 
      text='From:',
      font=('Arial', 10), 
      bg='white').grid(row=2, column=0,pady=5, sticky='w')

currency_codes = load_currency_list()
from_menu = ttk.Combobox(currency_frame, 
                        values=currency_codes, 
                        textvariable=curr_from_var,
                        font=('Arial', 10), 
                        state='readonly', 
                        width=8)
from_menu.grid(row=2, column=1,pady=5)
Label(currency_frame, 
      text='To:',
      font=('Arial', 10), 
      bg='white').grid(row=3, column=0, pady=5,sticky='w')
to_menu   = ttk.Combobox(currency_frame, 
                          values=currency_codes, 
                          textvariable=curr_to_var, 
                          state='readonly',
                          font=('Arial', 10), 
                          width=8)
to_menu.grid(row=3, column=1,pady=5)

Label(currency_frame, 
      textvariable=curr_result_var,
      font=('Arial', 10), 
      bg='white', 
      fg='blue').grid(row=4, column=0, columnspan=3, pady=5)
Checkbutton(currency_frame, 
            text='Live rates',
            font=('Arial', 10), 
            variable=live_rates_var, 
            bg='white').grid(row=5, column=0,pady=5, sticky='w')
Label(currency_frame, 
      textvariable=last_fetch_label, 
      font=('Arial', 10),
      bg='white', fg='gray').grid(row=5, column=1, columnspan=2, pady=5,sticky='e')

# Getting teh input of oprators and numbers
def get_input(num, calc_input):
  global just_evaluated
  num = str(num)
  current = calc_input.get()
  # operators to guard against duplicates
  ops = '+-*/'
  # If the last action was evaluation and the user types a digit or '.',
  # start a new entry (clear previous result). If they type an operator, keep it.
  if just_evaluated and (num.isdigit() or num == '.'):
    current = ''

  # sqrt handling: if current is a single number, wrap it; otherwise insert token
  # function handling: wrap current numeric value when user presses a function
  if num.startswith("sqrt") or num.startswith("math.sqrt") or num.endswith('('):
    token = 'sqrt(' if num.startswith('math.sqrt') else num
    if current == "":
      # insert function token
      xnum = current + token
    else:
      # if current is a plain number (no operators), wrap it: func(current)
      ops_present = any(op in current for op in ops)
      if not ops_present:
        try:
          float(current)
        except Exception:
          xnum = current + token
        else:
          # wrap the existing number with the function and close the paren
          if token.endswith('('):
            func_name = token[:-1]
            xnum = f"{func_name}({current})"
          else:
            xnum = f"{token}({current})"
      else:
        xnum = current + token
  # square handling: prefer replacing current number with (<n>)**2
  elif num == "**":
    if current == "":
      xnum = current + num
    else:
      try:
        float(current)
      except Exception:
        xnum = current + num
      else:
        xnum = f"({current})**2"
  # operator handling: avoid double operators like '++' or '+*'
  elif num in ops:
    if current == "":
      # allow unary minus at start
      if num == '-':
        xnum = num
      else:
        return
    else:
      if current[-1] in ops:
        # allow forming exponent '**' only if not already present
        if current[-1] == '*' and num == '*' and not current.endswith('**'):
          xnum = current + num
        else:
          # replace the trailing operator with the new one
          xnum = current[:-1] + num
      else:
        xnum = current + num
  # decimal point: prevent multiple dots in the current numeric segment
  elif num == '.':
    last_op = -1
    for o in ops:
      pos = current.rfind(o)
      if pos > last_op:
        last_op = pos
    segment = current[last_op+1:]
    if '.' in segment:
      return
    else:
      xnum = current + num
  else:
    xnum = current + num

  # any normal input clears the evaluated state
  just_evaluated = False
  calc_input.set(xnum)

# clear the screen of Calculator
def clear_calc(calc_input):
  global just_evaluated
  just_evaluated = False
  return calc_input.set('')

# use of backspace in key board for removing last Number
def backspace(calc_input):
  """Remove the last character from the current expression."""
  global just_evaluated
  current = calc_input.get()
  if current:
    # remove last character
    calc_input.set(current[:-1])
  just_evaluated = False

# Adding the history
def add_history(expr, result):
  """Add an entry to the history listbox and internal list."""
  global history_items, history_listbox
  entry = f"{expr} = {result}"
  history_items.append(entry)
  try:
    history_listbox.insert(END, entry)
  except Exception:
    pass

# Clear the History
def clear_history():
  """Clear history entries."""
  global history_items, history_listbox
  history_items.clear()
  try:
    history_listbox.delete(0, END)
  except Exception:
    pass

# Load the history
def load_history(event=None):
  """Load selected history expression into the input for editing."""
  try:
    sel = history_listbox.curselection()
    if not sel:
      return
    text = history_listbox.get(sel[0])
    # format is 'expr = result'
    expr = text.split(' = ')[0]
    calc_input.set(expr)
  except Exception:
    pass

# taking the degree as rad
def toggle_angle():
  global angle_mode
  angle_mode = 'deg' if angle_mode == 'rad' else 'rad'
  angle_btn.config(text=angle_mode.upper())

# using the key board keys
def on_key(event):
  """Keyboard input handler for digits, operators, Enter, Backspace, Esc."""
  k = event.keysym
  # digits
  if k.isdigit() or event.char in '.+-*/()':
    get_input(event.char, calc_input)
  elif k in ('Return', 'KP_Enter'):
    perform_calc(calc_input)
  elif k in ('BackSpace',):
    backspace(calc_input)
  elif k in ('Escape',):
    clear_calc(calc_input)

# Parforming scientific calculator
def perform_calc(calc_input):
  expr = calc_input.get()
  # Auto-close any unmatched opening parentheses to avoid common user errors
  opens = expr.count('(') - expr.count(')')
  if opens > 0:
    expr = expr + (')' * opens)

  global just_evaluated
  # Build a safe evaluator with math functions and angle-mode-aware trig wrappers
  def sin_wr(x):
    return math.sin(math.radians(x) if angle_mode == 'deg' else x)
  def cos_wr(x):
    return math.cos(math.radians(x) if angle_mode == 'deg' else x)
  def tan_wr(x):
    return math.tan(math.radians(x) if angle_mode == 'deg' else x)

  # Split symbols (names) from callable functions for SimpleEval
  functions = {
    'sin': sin_wr,
    'cos': cos_wr,
    'tan': tan_wr,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'sqrt': math.sqrt,
    'factorial': math.factorial,
    'fact': math.factorial,
    'log': math.log10,
    'ln': math.log,
    'exp': math.exp,
    'pow': pow,
    'abs': abs,
    'round': round,
  }

  names = {
    'pi': math.pi,
    'e': math.e,
  }

  s = SimpleEval(names=names, functions=functions)
  try:
    value = s.eval(expr)
  except Exception:
    calc_input.set('Error')
    just_evaluated = True
  else:
    # Format numeric results: show integers without .0 and cap precision for floats
    if isinstance(value, float):
      if value.is_integer():
        result_str = str(int(value))
      else:
        result_str = format(value, '.12g')
    else:
      result_str = str(value)

    calc_input.set(result_str)
    just_evaluated = True
    add_history(expr, result_str)

# Main frame 
calcframe = Frame(window,bd=4, relief=RIDGE, bg='white')
calcframe.place(x=2, y=2,width=268, height=460)

calc_input = StringVar()
    
cal_input =Entry(calcframe, 
                  textvariable=calc_input,
                  font=('Arial', 15, 'bold'),
                  width=21,bd=10, 
                  relief=GROOVE, 
                  state='normal',
                  justify=RIGHT)
cal_input.grid(row=0,columnspan=4)

# Memory M+
def memory_add(calc_input):
  """Add the current numeric value to memory (M+)."""
  global memory_value
  # prefer currency result, then calculator input, then currency amount
  candidates = []
  try:
    if 'curr_result_var' in globals() and curr_result_var.get().strip() != '':
      candidates.append(curr_result_var.get())
  except Exception:
    pass
  candidates.append(calc_input.get())
  try:
    if 'curr_amount_var' in globals() and curr_amount_var.get().strip() != '':
      candidates.append(curr_amount_var.get())
  except Exception:
    pass
  for txt in candidates:
    try:
      v = float(txt)
    except Exception:
      continue
    memory_value += v
    break
  _update_memory_display()

# Mamory M-
def memory_sub(calc_input):
  """Subtract the current numeric value from memory (M-)."""
  global memory_value
  # prefer currency result, then calculator input, then currency amount
  candidates = []
  try:
    if 'curr_result_var' in globals() and curr_result_var.get().strip() != '':
      candidates.append(curr_result_var.get())
  except Exception:
    pass
  candidates.append(calc_input.get())
  try:
    if 'curr_amount_var' in globals() and curr_amount_var.get().strip() != '':
      candidates.append(curr_amount_var.get())
  except Exception:
    pass
  for txt in candidates:
    try:
      v = float(txt)
    except Exception:
      continue
    memory_value -= v
    break
  _update_memory_display()
curr_amount_var

# Memory MR
def memory_recall(calc_input):
  """Recall memory into the input (MR)."""
  global memory_value
  # format similarly to perform_calc result formatting
  if float(memory_value).is_integer():
    calc_input.set(str(int(memory_value)))
  else:
    calc_input.set(format(memory_value, '.12g'))
  # also populate currency amount field if it exists
  try:
    if 'curr_amount_var' in globals():
      curr_amount_var.set(calc_input.get())
  except Exception:
    pass

# Memory MC
def memory_clear():
  """Clear memory (MC)."""
  global memory_value
  memory_value = 0.0
  _update_memory_display()

# updating the value display in Memory
def _update_memory_display():
  try:
    if float(memory_value) == 0.0:
      memory_display_var.set('')
    else:
      # show short formatted memory value
      if float(memory_value).is_integer():
        memory_display_var.set(f'M: {int(memory_value)}')
      else:
        memory_display_var.set(f'M: {format(memory_value, ".12g")}')
  except Exception:
    memory_display_var.set('')

  # Memory buttons (M+, M-, MR, MC)
btnMplus = Button(calcframe, 
                  text='M+', 
                  font=('Arial', 10, 'bold'), 
                  command=lambda: memory_add(calc_input), 
                  bd=5, 
                  width=4, 
                  pady=6, 
                  cursor='hand2')
btnMplus.grid(row=7, column=0)
btnMminus = Button(calcframe, 
                    text='M-', 
                    font=('Arial', 10, 'bold'), 
                    command=lambda: memory_sub(calc_input), 
                    bd=5, 
                    width=4, 
                    pady=6, 
                    cursor='hand2')
btnMminus.grid(row=7, column=1)
btnMR = Button(calcframe, 
                text='MR', 
                font=('Arial', 10, 'bold'), 
                command=lambda: memory_recall(calc_input), 
                bd=5, 
                width=4, 
                pady=6, 
                cursor='hand2')
btnMR.grid(row=7, column=2)
btnMC = Button(calcframe, 
               text='MC', 
               font=('Arial', 10, 'bold'), 
               command=lambda: memory_clear(), 
               bd=5, 
               width=4, 
               pady=6, 
               cursor='hand2')
btnMC.grid(row=7, column=3)
  # memory display label
Label(calcframe, 
      textvariable=memory_display_var, 
      bg='white', 
      fg='green', 
      font=('Arial',10,'bold')).grid(row=8, column=0, columnspan=4, sticky='w', padx=4)

# The main frame and Starting the buttons of Calculator
btn7 = Button(calcframe, 
              text=7,
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(7,
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn7.grid(row=1,column=0)

btn8 = Button(calcframe, 
              text=8, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(8, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn8.grid(row=1,column=1)

btn9 = Button(calcframe, 
              text=9, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(9, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn9.grid(row=1,column=2)

btnSum = Button(calcframe, 
                text='+', 
                font=('Arial', 15, 'bold'),
                command=lambda : get_input('+', 
                                           calc_input), 
                bd=5, 
                width=4, 
                pady=6,
                cursor='hand2')
btnSum.grid(row=1,column=3)
    
btn4 = Button(calcframe, 
              text=4, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(4, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn4.grid(row=2,column=0)

btn5 = Button(calcframe, 
              text=5, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(5, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn5.grid(row=2,column=1)

btn6 = Button(calcframe, 
              text=6, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(6, 
                                          calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn6.grid(row=2,column=2)

btnMinus = Button(calcframe, 
                  text='-', 
                  font=('Arial', 15, 'bold'),
                  command=lambda : get_input('-', 
                                             calc_input), 
                  bd=5, 
                  width=4, 
                  pady=6,
                  cursor='hand2')
btnMinus.grid(row=2,column=3)

btn1 = Button(calcframe, 
              text=1, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(1, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn1.grid(row=3,column=0)

btn2 = Button(calcframe, 
              text=2, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(2, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn2.grid(row=3,column=1)

btn3 = Button(calcframe, 
              text=3, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(3, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn3.grid(row=3,column=2)

btnEqual = Button(calcframe, 
                  text='=', 
                  font=('Arial', 15, 'bold'),
                  command=lambda : perform_calc(calc_input), 
                  bd=5, 
                  width=4, 
                  pady=6,
                  cursor='hand2')
btnEqual.grid(row=3,column=3)

btn0 = Button(calcframe, 
              text=0, 
              font=('Arial', 15, 'bold'),
              command=lambda : get_input(0, 
                                         calc_input), 
              bd=5, 
              width=4, 
              pady=6,
              cursor='hand2')
btn0.grid(row=4,column=0)

btnPoint = Button(calcframe, 
                  text='.', 
                  font=('Arial', 15, 'bold'),
                  command=lambda : get_input('.', 
                                             calc_input), 
                  bd=5, 
                  width=4, 
                  pady=6,
                  cursor='hand2')
btnPoint.grid(row=4,column=1)

btnMulti = Button(calcframe, 
                  text='*', 
                  font=('Arial', 15, 'bold'),
                  command=lambda : get_input('*', 
                                             calc_input), 
                  bd=5, 
                  width=4, 
                  pady=6,
                  cursor='hand2')
btnMulti.grid(row=4,column=2)

btnDevide = Button(calcframe, 
                   text='/', 
                   font=('Arial', 15, 'bold'),
                   command=lambda : get_input('/', 
                                               calc_input), 
                    bd=5, 
                    width=4, 
                    pady=6,
                    cursor='hand2')
btnDevide.grid(row=4,column=3)

btnSq = Button(calcframe, 
               text='sq', 
               font=('Arial', 15, 'bold'),
               command=lambda :get_input("**",
                                        calc_input), 
               bd=5, 
               width=4, 
               pady=6,
               cursor='hand2')
btnSq.grid(row=5,column=0)

btnStRt = Button(calcframe, 
                 text='√', 
                 font=('Arial', 15, 'bold'),
                 command=lambda :get_input("sqrt(", 
                                           calc_input), 
                  bd=5, 
                  width=4, 
                  pady=6,
                  cursor='hand2')
btnStRt.grid(row=5,column=1)

# Percentage Calculation
def percent_action(calc_input):
  """If the current entry is a single number, convert it to its percent (divide by 100).
  Otherwise append '/100' so expressions like '50+10%' become '50+10/100'.
  """
  cur = calc_input.get()
  ops = '+-*/'
  # if there's no operator in the current text, try to interpret as a single number
  if cur != "" and not any(o in cur for o in ops):
    try:
      v = float(cur)
    except Exception:
      # fallback to appending token
      calc_input.set(cur + '/100')
    else:
      # replace with computed percent, formatted nicely
      if v.is_integer():
        calc_input.set(str(int(v/100)))
      else:
        calc_input.set(format(v/100, '.12g'))
  else:
    calc_input.set(cur + '/100')

# Button %
btnPerc = Button(calcframe, 
                 text='%', 
                 font=('Arial', 15, 'bold'),
                 command=lambda : percent_action(calc_input), 
                 bd=5, 
                 width=4, 
                 pady=6,
                 cursor='hand2')
btnPerc.grid(row=5,column=2)

# Button Clear
btnClear = Button(calcframe, 
                  text='C', 
                  font=('Arial', 15, 'bold'),
                  command=lambda :clear_calc(calc_input), 
                  bd=5, 
                  width=4, 
                  pady=6,
                  cursor='hand2')
btnClear.grid(row=5,column=3)

# Backspace / delete button
btnDel = Button(calcframe, 
                text='DEL', 
                font=('Arial', 12, 'bold'), 
                command=lambda: backspace(calc_input), 
                bd=5, 
                width=4, 
                pady=6, 
                cursor='hand2')
btnDel.grid(row=6, column=0)

# Angle mode button
angle_btn = Button(calcframe, 
                   text=angle_mode.upper(), 
                   font=('Arial', 12, 'bold'), 
                   command=toggle_angle, 
                   bd=5, 
                   width=4, 
                   pady=6, 
                   cursor='hand2')
angle_btn.grid(row=6, column=1)

# Copy current input/result to clipboard
def copy_to_clipboard():
  try:
    txt = calc_input.get()
    window.clipboard_clear()
    window.clipboard_append(txt)
  except Exception:
    pass

btnCopy = Button(calcframe, 
                 text='Copy', 
                 font=('Arial', 10, 'bold'), 
                 command=copy_to_clipboard, 
                 bd=5, 
                 width=4, 
                 pady=6, 
                 cursor='hand2')
btnCopy.grid(row=6, column=2)

# Scientific panel below the main calculator All Buttons
sci_frame = Frame(window, bd=4, relief=RIDGE, bg='white')
sci_frame.place(x=2, y=465, width=370, height=200)

Label(sci_frame, 
      text='Scientific', 
      font=('Arial', 12, 'bold'), 
      bg='white').grid(row=0, column=0, columnspan=4, sticky='w')

btn_sin = Button(sci_frame, 
                 text='sin', 
                 font=('Arial', 12), 
                 command=lambda: get_input('sin(', 
                                           calc_input), 
                  width=8)
btn_sin.grid(row=1, column=0, padx=4, pady=4)

btn_cos = Button(sci_frame, 
                 text='cos', 
                 font=('Arial', 12), 
                 command=lambda: get_input('cos(', 
                                           calc_input), 
                  width=8)
btn_cos.grid(row=1, column=1, padx=4, pady=4)

btn_tan = Button(sci_frame, 
                 text='tan', 
                 font=('Arial', 12), 
                 command=lambda: get_input('tan(', 
                                           calc_input), 
                  width=8)
btn_tan.grid(row=1, column=2, padx=4, pady=4)

btn_pow = Button(sci_frame, 
                 text='pow', 
                 font=('Arial', 12), 
                 command=lambda: get_input('pow(', 
                                           calc_input), 
                  width=8)
btn_pow.grid(row=1, column=3, padx=4, pady=4)

btn_asin = Button(sci_frame, 
                  text='asin', 
                  font=('Arial', 12), 
                  command=lambda: get_input('asin(', 
                                            calc_input), 
                  width=8)
btn_asin.grid(row=2, column=0, padx=4, pady=4)

btn_acos = Button(sci_frame, 
                  text='acos', 
                  font=('Arial', 12), 
                  command =lambda: get_input('acos(', 
                                             calc_input), 
                  width=8)
btn_acos.grid(row=2, column=1, padx=4, pady=4)

btn_atan = Button(sci_frame, 
                  text='atan', 
                  font=('Arial', 12), 
                  command=lambda: get_input('atan(', 
                                            calc_input), 
                  width=8)
btn_atan.grid(row=2, column=2, padx=4, pady=4)

btn_exp = Button(sci_frame, 
                 text='exp', 
                 font=('Arial', 12), 
                 command=lambda: get_input('exp(', 
                                           calc_input), 
                width=8)
btn_exp.grid(row=2, column=3, padx=4, pady=4)

btn_ln = Button(sci_frame, 
                text='ln', 
                font=('Arial', 12), 
                command=lambda: get_input('ln(', 
                                          calc_input), 
                width=8)
btn_ln.grid(row=3, column=0, padx=4, pady=4)

btn_log = Button(sci_frame, 
                 text='log', 
                 font=('Arial', 12), 
                 command=lambda: get_input('log(', 
                                           calc_input), 
                 width=8)
btn_log.grid(row=3, column=1, padx=4, pady=4)

btn_sqrt = Button(sci_frame, 
                  text='sqrt', 
                  font=('Arial', 12), 
                  command=lambda: get_input('sqrt(', 
                                            calc_input), 
                  width=8)
btn_sqrt.grid(row=3, column=2, padx=4, pady=4)

btn_pi = Button(sci_frame, 
                text='π', 
                font=('Arial', 12), 
                command=lambda: get_input(str(math.pi), 
                                          calc_input), 
                width=8)
btn_pi.grid(row=3, column=3, padx=4, pady=4)

btn_e = Button(sci_frame, 
               text='e', 
               font=('Arial', 12), 
               command=lambda: get_input('e', 
                                         calc_input), 
              width=8)
btn_e.grid(row=4, column=0, padx=4, pady=4)

btn_lpar = Button(sci_frame, 
                  text='(', 
                  font=('Arial', 12), 
                  command=lambda: get_input('(', 
                                            calc_input), 
                  width=8)
btn_lpar.grid(row=4, column=1, padx=4, pady=4)

btn_rpar = Button(sci_frame, 
                  text=')', 
                  font=('Arial', 12), 
                  command=lambda: get_input(')', 
                                            calc_input), 
                  width=8)
btn_rpar.grid(row=4, column=2, padx=4, pady=4)

btn_fact = Button(sci_frame, 
                  text='fact', 
                  font=('Arial', 12), 
                  command=lambda: get_input('factorial(', 
                                            calc_input), 
                  width=8)
btn_fact.grid(row=4, column=3, padx=4, pady=4)

# History panel to the right of calculator
history_frame = Frame(window, bd=4, relief=RIDGE, bg='white')
history_frame.place(x=272, y=2, width=300, height=460)

history_label = Label(history_frame, 
                      text='History', 
                      font=('Arial', 12, 'bold'), 
                      bg='white')
history_label.pack(anchor='nw')

btnClearHist = Button(history_frame, 
                      text='Clear History', 
                      font=('Arial', 10),
                      command=clear_history)
btnClearHist.pack(anchor ='ne')

history_sb = Scrollbar(history_frame)
history_sb.pack(side=RIGHT, fill=Y)

history_listbox = Listbox(history_frame, 
                          yscrollcommand=history_sb.set, 
                          width=40, 
                          height=15)
history_listbox.pack(side=LEFT, fill=BOTH, expand=True)
history_sb.config(command=history_listbox.yview)

# bind selection to load into input
history_listbox.bind('<<ListboxSelect>>', load_history)
# Also allow double-click to load selected history expression
history_listbox.bind('<Double-Button-1>', lambda e: load_history())

# Basic financial panel
finance_frame = Frame(window, bd=4, relief=RIDGE, bg='white')
finance_frame.place(x=578, y=2, width=360, height=248)

Label(finance_frame, 
      text='Financial Tools', 
      font=('Arial', 12, 'bold'), 
      bg='white').pack(anchor='nw')

f_inner = Frame(finance_frame, bg='white')
f_inner.pack(fill=BOTH, expand=True, padx=6, pady=6)

Label(f_inner, 
      text='Principal:',
      font=('Arial', 10), 
      bg='white').grid(row=0, column=0, sticky='w', padx=6, pady=6)

principal_var = StringVar()
Entry(f_inner, 
      textvariable=principal_var).grid(row=0, column=1, padx=6, pady=6)

Label(f_inner, 
      text='Rate (%):',
      font=('Arial', 10), 
      bg='white').grid(row=1, column=0, sticky='w', padx=6, pady=6)
rate_var = StringVar()
Entry(f_inner, 
      textvariable=rate_var).grid(row=1, column=1, padx=6, pady=6)

Label(f_inner, 
      text='Years:',
      font=('Arial', 10), 
      bg='white').grid(row=2, column=0, sticky='w', padx=6, pady=6)
years_var = StringVar()
Entry(f_inner,
       textvariable=years_var).grid(row=2, column=1, padx=6, pady=6)

Label(f_inner, 
      text='Compounds/yr:',
      font=('Arial', 10), 
      bg='white').grid(row=3, column=0, sticky='w', padx=6, pady=6)
comp_var = StringVar(value='1')
Entry(f_inner, 
      textvariable=comp_var).grid(row=3, column=1, padx=6, pady=6)

fin_result_var = StringVar()
Label(f_inner, 
      textvariable=fin_result_var, 
      bg='lightyellow', 
      fg='blue').grid(row=4, column=0, columnspan=2, padx=10, pady=6)

# Simple Intrest
def compute_simple_interest():
  try:
    P = float(principal_var.get())
    r = float(rate_var.get()) / 100.0
    t = float(years_var.get())
    A = P * (1 + r * t)
    fin_result_var.set(f"Simple: {A:.2f}")
  except Exception:
    fin_result_var.set('Input error')

# Compoud Intrest
def compute_compound_interest():
  try:
    P = float(principal_var.get())
    r = float(rate_var.get()) / 100.0
    t = float(years_var.get())
    n = float(comp_var.get())
    A = P * (1 + r/n) ** (n * t)
    fin_result_var.set(f"Compound: {A:.2f}")
  except Exception:
    fin_result_var.set('Input error')

#  Montholy Instalment
def compute_loan_payment():
  try:
    P = float(principal_var.get())
    r = float(rate_var.get()) / 100.0 / 12.0
    n = int(float(years_var.get()) * 12)
    if r == 0:
      m = P / n
    else:
      m = P * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    fin_result_var.set(f"Monthly: {m:.2f}")
  except Exception:
    fin_result_var.set('Input error')

# Main Buttons 
Button(f_inner, 
       text='Simple',
       font=('Arial', 10), 
       command=compute_simple_interest).grid(row=5, column=0, pady=6)

Button(f_inner, 
       text='Compound',
       font=('Arial', 10), 
       command=compute_compound_interest).grid(row=5, column=1, padx=6, pady=6)

Button(f_inner, 
       text='Instalment',
       font=('Arial', 10), 
       command=compute_loan_payment).grid(row=5, column=2, pady=6)

# Date/Time Calculations Panel
date_frame = Frame(window, bd=4, relief=RIDGE, bg='white')
date_frame.place(x=578, y=252, width=320, height=210)

Label(date_frame, 
      text='Date/Time Tools', 
      font=('Arial', 12, 'bold'), 
      bg='white').grid(row=0, column=0, columnspan=2, sticky='w')

Label(date_frame, 
      text='Date (YYYY-MM-DD):',
      font=('Arial', 10), 
      bg='white').grid(row=1, column=0, pady=6,sticky='w')
date1_var = StringVar()
date2_var = StringVar()
Entry(date_frame, 
      textvariable=date1_var,
      font=('Arial', 10)).grid(row=1, column=1, pady=6)

Label(date_frame, 
      text='Other Date:',
      font=('Arial', 10), 
      bg='white').grid(row=2, column=0, pady=6, sticky='w')
Entry(date_frame, 
      textvariable=date2_var,
      font=('Arial', 10)).grid(row=2, column=1,pady=6)

diff_var = StringVar()
Label(date_frame, 
      textvariable=diff_var,
      font=('Arial', 10), 
      bg='white', 
      fg='blue').grid(row=3, column=0, pady=6, columnspan=2)

# Diffrence in dates 
def compute_date_diff():
  try:
    d1 = datetime.fromisoformat(date1_var.get())
    d2 = datetime.fromisoformat(date2_var.get())
    delta = d2 - d1 if d2 >= d1 else d1 - d2
    diff_var.set(f"{delta.days} days, {delta.seconds//3600} hrs")
  except Exception:
    diff_var.set('Parse error')

Label(date_frame, 
      text='Add days to date:', 
      bg='white').grid(row=4, column=0, sticky='w')

add_days_var = StringVar()
Entry(date_frame, 
      textvariable=add_days_var).grid(row=4, column=1)
add_result_var = StringVar()

Label(date_frame, 
      textvariable=add_result_var, 
      bg='white', 
      fg='blue').grid(row=5, column=0, columnspan=2)

# Adding the days to date
def add_days_to_date():
  try:
    base = datetime.fromisoformat(date1_var.get())
    n = int(add_days_var.get())
    out = base + timedelta(days=n)
    add_result_var.set(out.date().isoformat())
  except Exception:
    add_result_var.set('Input error')

Button(date_frame, 
       text='Diff', 
       command=compute_date_diff).grid(row=6, column=0)
Button(date_frame, 
       text='Add', 
       command=add_days_to_date).grid(row=6, column=1)

# keyboard bindings
window.bind('<Key>', on_key)
# scientific keyboard shortcuts (Ctrl+letter)
window.bind('<Control-s>', lambda e: get_input('sin(', calc_input))
window.bind('<Control-c>', lambda e: get_input('cos(', calc_input))
window.bind('<Control-t>', lambda e: get_input('tan(', calc_input))
window.bind('<Control-f>', lambda e: get_input('factorial(', calc_input))
window.bind('<Control-l>', lambda e: get_input('ln(', calc_input))
window.bind('<Control-g>', lambda e: get_input('log(', calc_input))
window.bind('<Control-p>', lambda e: get_input(str(math.pi), calc_input))
window.bind('<Control-e>', lambda e: get_input('e', calc_input))
window.bind('<Control-r>', lambda e: get_input('sqrt(', calc_input))

if __name__ == '__main__':
  window.mainloop()