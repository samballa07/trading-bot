import requests
import time
from webull import paper_webull
from prettyprinter import pprint

f = open("secrets.txt", "r")
secrets = []
for line in f:
   secrets.append(line.strip("\n"))
email = secrets[0]
password = secrets[1]
trade_token = secrets[2]
api_key = secrets[3]
print(email, password, trade_token, api_key)
wb = paper_webull()
auth_token = int(input("Enter the token sent to your email: "))
wb.login(email, password, "Seth", auth_token)

f = open("stocks.txt", "r")
temp = []
for line in f:
   temp.append(line.strip("\n"))
stocks = {}
for stock in temp:
   r = requests.get(f"https://finnhub.io/api/v1/quote?symbol={stock}&token={api_key}").json()
   stocks[stock] = r["c"]

def check_api_limit(response):
   if "error" in response:
      return True
   return False

def check_position_exists(stock):
   positions = wb.get_positions()
   for position in positions:
      if stock == position["ticker"]["symbol"]:
         return True
   return False

def resistance_check(stc):
   x = requests.get(f'https://finnhub.io/api/v1/scan/support-resistance?symbol={stc}&resolution=15&token={api_key}').json()
   quote = requests.get(f'https://finnhub.io/api/v1/quote?symbol={stc}&token={api_key}').json()
   if x == {} or check_api_limit(x) or check_api_limit(quote):
      return False
   price = quote["c"]
   levels = x["levels"]
   if levels == []:
      return False
   resistance = levels[-1]
   #print("Resistance: ", stc, price, resistance)
   if price >= resistance + .05: 
      return True
   return False

def support_check(stc):
   x = requests.get(f'https://finnhub.io/api/v1/scan/support-resistance?symbol={stc}&resolution=15&token={api_key}').json()
   quote = requests.get(f'https://finnhub.io/api/v1/quote?symbol={stc}&token={api_key}').json()
   if x == {} or check_api_limit(x) or check_api_limit(quote):
      return False
   price = quote["c"]
   levels = x["levels"]
   if levels == []:
      return False

   support = levels[0]
   #print("Support: ", stc, price, support)
   if price > support and price < levels[1]:
      return True
   return False

def execute_limit_buy(stc, prc, qty):
   if(check_position_exists(stc)):
      return
   wb.get_trade_token(trade_token)
   wb.place_order(stock=stc, price=prc, quant=qty, orderType="LMT")
   print(f"Bought: {qty} shares of {stc}")

def execute_limit_sell(stc, prc, qty):
   wb.get_trade_token(trade_token)
   wb.place_order(stock=stc, price=prc, quant=qty, action="SELL", orderType="LMT")
   print(f"Sold: {qty} shares of {stc}")


def buy_signal(stc):
   r = requests.get(f'https://finnhub.io/api/v1/scan/technical-indicator?symbol={stc}&resolution=30&token={api_key}').json()
   if r == {} or check_api_limit(r):
      return False
   buy = r["technicalAnalysis"]["count"]["buy"]
   sell = r["technicalAnalysis"]["count"]["sell"]
   signal = r["technicalAnalysis"]["signal"]
   adx = r["trend"]["adx"]
   trend = r["trend"]["trending"]
   print(stock, buy, sell, signal, adx, trend)
   if trend and adx > 25 and (signal == "buy" or signal =="strong buy") and buy >(3 + sell):
      return True
   return False


def checkProfitLoss():
   positions = wb.get_positions()
   for position in positions:
      profitLoss = float(position["unrealizedProfitLossRate"]) * 100.0
      last_price = float(position["lastPrice"])
      symbol = position["ticker"]["symbol"]
      quant = int(position["position"])
      if profitLoss < -2:
         execute_limit_sell(symbol, last_price, quant)
         print("Lost more than 2% on " + symbol+ ". SELL")
      elif profitLoss > 4:
         execute_limit_sell(symbol, last_price, quant)
         print("Gained more than 4%:", symbol)

while (True):
   print("Running..")

   for stock in stocks:
      quote = wb.get_quote(stock=stock)
      curr_price = float(quote["close"])

      if buy_signal(stock):
         execute_limit_buy(stock, curr_price, 2)
      if resistance_check(stock) or support_check(stock):      
         execute_limit_buy(stock, curr_price, 2)

   checkProfitLoss()
   time.sleep(20)
