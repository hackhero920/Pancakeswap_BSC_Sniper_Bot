
from txns import Txn_bot
from time import sleep
import argparse, math, sys, json
from honeypotChecker import HoneyPotChecker
from halo import Halo
from threading import Thread
from style import style



spinneroptions = {'interval': 250,
                    'frames': ['🚀 ', '🌙 ', '🚀 ', '🌕 ', '💸 '],
                    }

parser = argparse.ArgumentParser(description='Set your Token and Amount example: "sniper.py -t 0x34faa80fec0233e045ed4737cc152a71e490e2e3 -a 0.2 -s 15"')
parser.add_argument('-t', '--token', help='str, Token for snipe e.g. "-t 0x34faa80fec0233e045ed4737cc152a71e490e2e3"')
parser.add_argument('-a', '--amount', help='float, Amount in Bnb to snipe e.g. "-a 0.1"')
parser.add_argument('-tx', '--txamount', default=1, nargs="?", const=1, type=int, help='int, how mutch tx you want to send? It Split your BNB Amount in e.g. "-tx 5"')
parser.add_argument('-hp', '--honeypot', help='bool, check if your token to buy is a Honeypot, e.g. "-hp True"')
parser.add_argument('-tp', '--takeprofit', default=0, nargs="?", const=True, type=int, help='int, Percentage TakeProfit from your input BNB amount, if 0 then not used. e.g. "-tp 50" ')
parser.add_argument('-wb', '--awaitBlocks', default=0, nargs="?", const=True, type=int, help='int, Await Blocks bevore sending BUY Transaction, if 0 then not used. e.g. "-ab 50" ')
parser.add_argument('-g', '--gas', default=6, nargs="?", const=True, type=int, help='int, set Gas in GWEI default 6" ')
args = parser.parse_args()


TXN = int(args.txamount)
SNIPEquantity = (float(args.amount) / TXN)

token = args.token
checkHoney = str(args.honeypot)
takeprofit = int(args.takeprofit)
waitingBlocks = int(args.awaitBlocks)
gas_price = int(args.gas) * (10**9)
Timer = float(0.1)

def calcProfitExit():
    a = ((SNIPEquantity * TXN) * takeprofit) / 100
    b = a + (SNIPEquantity * TXN)
    return b 
    

profit = "not activated"
if takeprofit != 0: 
    profit = calcProfitExit() 
else:
    profit = 0


print("")
print(style().GREEN +"Start Sniper with following arguments"+ style().RESET)
print(style().GREEN +"""Attention, they pay 1% fees on each transaction."""+ style().RESET)
print(style().BLUE + "---------------------------------------------------"+ style().RESET)
print(style().YELLOW + "Amount for Buy:",style().GREEN + str(args.amount) + " BNB"+ style().RESET)
print(style().YELLOW + "Token to Snipe :",style().GREEN + str(args.token) + style().RESET)
print(style().YELLOW + "Transaction to send:",style().GREEN + str(args.txamount)+ style().RESET)
print(style().YELLOW + "Amount per transaction :",style().GREEN + str(SNIPEquantity)+ style().RESET)
print(style().YELLOW + "Await Blocks before buy :",style().GREEN + str(waitingBlocks)+ style().RESET)
print(style().YELLOW + "Take Profit Percent :",style().GREEN + str(takeprofit)+ style().RESET)
print(style().YELLOW + "Min Output from Take Profit:",style().GREEN +str(profit)+ style().RESET)
print(style().BLUE + "---------------------------------------------------"+ style().RESET)


def checkIsHoneypot():
    isHoney = HoneyPotChecker(token).Is_Honeypot()
    return isHoney

def CheckingTAX():
    with open("Settings.json", "r") as S:
        settings = json.load(S)
    MaxSellTax = settings["MaxSellTax"]
    MaxBuyTax = settings["MaxBuyTax"]
    SellTax, BuyTax = HoneyPotChecker(token).getTAX()
    if float(MaxSellTax) >= float(SellTax):
        if float(MaxBuyTax) >= float(BuyTax):
            return True
        else:
            return False
    else:
        return False
 
def checkProfit():
    spinner = Halo(text='Checking Profit', spinner=spinneroptions)
    spinner.start()
    pbot = Txn_bot(
                    token_address=token,
                    quantity=SNIPEquantity,
                    gas_price=gas_price)
    txn = pbot.approve()
    print(txn[1])
    sleep(3)
    cbot = Txn_bot(
                    token_address=token,
                    quantity=0,
                    gas_price=gas_price)
    spinner.stop()
    sleep(3)
    while True:
        try:
            sleep(Timer)
            currentProfit = (cbot.getOutputfromTokentoBNB() / (10**18))
            print(style().YELLOW +"Current Output from your Tokens",style().GREEN + str(round(currentProfit,7)), end="\r" + style().RESET)
            if currentProfit >= profit:
                sbot = Txn_bot(
                    token_address=token,
                    quantity=0,
                    gas_price=gas_price)
                tx = sbot.sell_tokens()
                print(tx[1])
                if tx[0] == False:
                    sys.exit()
                break
        except Exception as e:
            print(e)
            break
  
def waitBlocks():
    spinner = Halo(text='Waiting Blocks', spinner=spinneroptions)
    spinner.start()
    blocksbot = Txn_bot(token_address=token, quantity=0, gas_price=gas_price)
    waitForHigh = int(blocksbot.getBlockHigh()) + waitingBlocks
    while True:
        try:
            sleep(0.8)
            currentBlock = blocksbot.getBlockHigh()
            if waitForHigh <= currentBlock:
                if CheckingTAX() == True:
                    if "TRUE" in checkHoney.upper():
                        T = checkIsHoneypot()
                    else:
                        T = False
                    if T == False:
                        print(style().GREEN +"\n[OK], your Token is not a honeypot!"+ style().RESET)
                        spinner.stop()
                        buy()
                        break
                    else:
                        print(style().RED +"\n[FAIL]",token, "is current a Honeypot Token!"+ style().RESET)
                        break
                else:
                    print(style().RED +"\n[FAIL] Taxes exceed, Buy/Sell Tax higher then Settings.json"+ style().RESET)
                    break
        except Exception as e:
            print(e)
            break

def buy():
    spinner = Halo(text='BUY Tokens', spinner=spinneroptions)
    spinner.start()
    try:
        print(style().GREEN + "\n[OK] BUY with " + str(TXN)+ " Transactions, Good luck"+ style().RESET )
        for i in range(TXN):
            try:
                bot = Txn_bot(token_address=token, quantity=SNIPEquantity, gas_price=gas_price)
                tx = bot.buy_token()
                print(tx[1])
                if tx[0] == False:
                    sys.exit()
            except Exception as e:
                print(e)
        spinner.stop()
        if tx[0] == True:
            if profit != 0:
                checkProfit()
    except Exception as e:
        print(e)
   
def Snip():
    spinner = Halo(text='Waiting for Liquidity', spinner=spinneroptions)
    spinner.start()
    sbot = Txn_bot(token_address=token, quantity=SNIPEquantity, gas_price=gas_price)
    while True:
        sleep(Timer)
        try:
            print(
                style().YELLOW + f"\nMin Output from {str(round(SNIPEquantity,5))}BNB "
                + style.GREEN+ str(round(float(sbot.getOutputfromBNBtoToken() / (10 ** sbot.get_token_decimals())),5)) + style().RESET)
            try:
                spinner.stop()
                waitBlocks()
                break
            except Exception as e:
                print(e)
                break
        except Exception as e:
           #print(e)
            pass    

Snip()
print(style().GREEN + "[DONE] TradingTigers Sniper Bot finish!" + style().RESET)
