import krakenex as k
import pandas as pd
import matplotlib.pyplot as plt
import time
import datetime
from pathlib import Path
import sys

#funciones auxiliares

from datetime import datetime, timedelta
# Convert a unix time u to a datetime object d
def unixtoDate(u): 
    return datetime.fromtimestamp(u) + timedelta(hours=1)

def strToNum(s):
    try:
        return int(s)
    except ValueError:
        return float(s)
    
def reverseCumSum(serie):
    serieAcum = serie
    volAcum = float(0.0)
    for i in range(len(serie),0,-1):
        volAcum += float(serie.values[i-1])
        serieAcum.values[i-1]= volAcum
    return serie

def PassTime(d1, d2):
    #d1 = datetime.strptime(d1, "%Y-%m-%d %H:%M:%S")
    #d2 = datetime.strptime(d2, "%Y-%m-%d %H:%M:%S")
    return abs((d2 - d1).seconds)

BalanceTime = 10 
espera = 58 #segundas
Ejecutar = True
i = 0
cantEject = int(3600/espera)*4 # = 3 horas aprox
last = 0
tradesQuery =  {'pair': 'XXBTZUSD'}
my_file = Path('balanceHistory.csv')
tradesHistoryFile = Path('tradesHistory.csv')
TradesColsNames = ['price', 'volume', 'time', 'buy_sell', 'market/limit', 'miscellaneous']

lapTradesCount = 0
totalTradesCount = 0

if tradesHistoryFile.is_file():
    tradesHistory = pd.read_csv('tradesHistory.csv')
    tradesHistory.set_index('price',inplace=True)
else:
    tradesHistory =  pd.DataFrame()

if my_file.is_file():
    while Ejecutar:
    #for i in range(cantEject):
        try:
            BalanceHistory = pd.read_csv('balanceHistory.csv')
            
            startTime = datetime.now()

            #i += 1
            #solicitar datos
            if last != 0:
                tradesQuery =  {'pair': 'XXBTZUSD', 'since': last}
            kapi = k.API()
            response = kapi.query_public('Trades',tradesQuery)
            #<price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>

            # check error y extraer datos
            error = response['error']
            if len(error) == 0:
                last = response['result']['last'] #ultimo id, utilizar ara proxima xonsulta como parametro since (desde)   
                trades = pd.DataFrame(response['result']['XXBTZUSD'])
                
                if len(trades) > 0:
                    #formatear datos
                    trades.columns = TradesColsNames
                    #trades.drop('miscellaneous',axis=1, inplace=True)
                    trades['price'] = trades['price'].apply(strToNum)
                    trades['time'] = trades['time'].apply(unixtoDate)
                    trades['volume'] = trades['volume'].apply(strToNum)

                    trades.set_index('price',inplace=True)
                    #agregar a al historial de trades
                    lapTradesCount = len(trades)
                    tradesHistory = pd.concat([tradesHistory, trades])
                    totalTradesCount = len(tradesHistory)

                    # filtrar ultima periodo
                    
                    intervalo = trades['time'].max() - timedelta(minutes=BalanceTime)
                    trades = trades[trades['time'] >= intervalo]

                    #separar compras y ventas
                    buys = trades[trades['buy_sell'] == 'b']
                    sells = trades[trades['buy_sell'] == 's']
                    buys = buys.sort_index()
                    sells = sells.sort_index(ascending=False)

                    #agrupar y sumar volumen por precio para compras y ventas
                    sbuy = buys['volume']
                    sbuy = sbuy.groupby('price').sum()
                    ssell = sells['volume']
                    ssell = sells.groupby('price').sum()
                    ssell = ssell * -1

                    #acumular y obtener delta
                    mb =pd.concat([sbuy,ssell],axis=1)
                    mb.columns = ['buy','sell']
                    mb.fillna(0, inplace=True)
                    mb['buy'] = mb['buy'].cumsum()
                    mb['sell'] = reverseCumSum(mb['sell'])
                    mb['delta'] = mb['buy'] + mb['sell']
                    mb['c'] = mb['buy']*0

                    #graficar Balance
                    #mb.plot(figsize=(15,5), kind='area', stacked=False);

                    # balance
                    volbuy = mb['buy'].sum()
                    volsell = mb['sell'].sum()
                    unbalance = mb['delta'].sum()
                    balanceRatio = volbuy / (volbuy - volsell)
                    print()
                    print('lap {0} - at {1}:'.format(i , startTime))
                    print('balanceRatio: {0}'.format(balanceRatio))
                    print('volbuy: {b}-BTCUSD | volsell: {s}-BTCUSD'.format(b=volbuy,s=volsell))
                    print('-> Unbalance: {u}-BTCUSD'.format(u=unbalance))
                    
                    #obtener precio actual
                    kapi = k.API()
                    tikerResponce = kapi.query_public('Ticker', {'pair': 'XXBTZUSD'})
                    #<pair_name> = pair name
                    #    a = ask array(<price>, <whole lot volume>, <lot volume>),
                    #    b = bid array(<price>, <whole lot volume>, <lot volume>),
                    #    c = last trade closed array(<price>, <lot volume>),
                    #    v = volume array(<today>, <last 24 hours>),
                    #    p = volume weighted average price array(<today>, <last 24 hours>),
                    #    t = number of trades array(<today>, <last 24 hours>),
                    #    l = low array(<today>, <last 24 hours>),
                    #    h = high array(<today>, <last 24 hours>),
                    #    o = today's opening price
                    currentTime = datetime.now()
                    errorTiker = tikerResponce['error']
                    if len(errorTiker) == 0:
                        close = pd.DataFrame(tikerResponce['result']['XXBTZUSD']['c'])[0][0]
                        ask = pd.DataFrame(tikerResponce['result']['XXBTZUSD']['a'])[0][0]
                        bid = pd.DataFrame(tikerResponce['result']['XXBTZUSD']['b'])[0][0]
                        print('close: {0}'.format(close))
                        #guardar historia balance
                        newBalance = [currentTime,strToNum(close),strToNum(ask),strToNum(bid),balanceRatio,volbuy,volsell,unbalance]
                        BalanceHistory.loc[len(BalanceHistory)] = newBalance
                    else:
                        print(errorTiker)
                    BalanceHistory = BalanceHistory.set_index(pd.DatetimeIndex(BalanceHistory['Time']))
                    BalanceHistory.drop('Time', axis=1,inplace=True)
                    BalanceHistory.to_csv('balanceHistory.csv')
                    tradesHistory.to_csv('tradesHistory.csv')
                    print('{0} new Trades | {1} Total Trades'.format(lapTradesCount, totalTradesCount))

                else:
                    print('no new trades')
            else:
                print(error)
        except:
            print ("Unexpected error: {0}".format(sys.exc_info()[0]))
            continue

        time.sleep(espera)
        lapTime = datetime.now()
        print( 'elapsed {0} sec'.format(PassTime(startTime, lapTime)))
        i = i + 1

#guardar y preparar datos para plotear
#BalanceHistory = pd.read_csv('balanceHistory.csv')
#BalanceHistory = BalanceHistory.set_index(pd.DatetimeIndex(BalanceHistory['Time']))
#BalanceHistory.drop('Time', axis=1,inplace=True)
#BalanceHistory.to_csv('balanceHistory.csv')
  
#graficar Balance
mb.plot(figsize=(15,5),kind='area', stacked =False);

#BalanceHistory.drop(BalanceHistory.index[0], inplace=True) #elimina 1 fila
#BalanceHistory = pd.read_csv('balanceHistory.csv')

#BalanceHistory = BalanceHistory.set_index(pd.DatetimeIndex(BalanceHistory['Time']))
#BalanceHistory.drop('Time', axis=1,inplace=True) #elimina 1 columna


#<pair_name> = pair name
            #    a = ask array(<price>, <whole lot volume>, <lot volume>),
            #    b = bid array(<price>, <whole lot volume>, <lot volume>),
            #    c = last trade closed array(<price>, <lot volume>),
            #    v = volume array(<today>, <last 24 hours>),
            #    p = volume weighted average price array(<today>, <last 24 hours>),
            #    t = number of trades array(<today>, <last 24 hours>),
            #    l = low array(<today>, <last 24 hours>),
            #    h = high array(<today>, <last 24 hours>),
            #    o = today's opening price
            
#tikerResponce['result']['XXBTZUSD']

