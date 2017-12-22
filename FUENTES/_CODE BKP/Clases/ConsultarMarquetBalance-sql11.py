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
    return datetime.fromtimestamp(u) # + timedelta(hours=1)

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

#set SQL BBDD
from sqlalchemy import create_engine, MetaData, Table, Column, DateTime, Float, String,Integer

dbInstance = 'sqlite:///krakenTeader.db'
dbBalanceHistoryTable = 'BalanceHistory'
dbTradesHistoryTable = 'TradesHistory'
engine = create_engine(dbInstance)

if not engine.dialect.has_table(engine, dbBalanceHistoryTable):  # If table don't exist, Create.
    metadata = MetaData(engine)
    
    # Create a table with the appropriate Columns
    Table(dbBalanceHistoryTable, metadata,
          Column('Time', DateTime, primary_key=True, nullable=False), 
          Column('close', Float), 
          Column('ask', Float), 
          Column('bid', Float),
          Column('balanceRatio', Float),
          Column('volbuy', Float), 
          Column('volsell', Float),
          Column('unbalance', Float))
    # Implement the creation
    metadata.create_all() 
    
if not engine.dialect.has_table(engine, dbTradesHistoryTable):  # If table don't exist, Create.
    metadata = MetaData(engine)
    
    # Create a table with the appropriate Columns
    Table(dbTradesHistoryTable, metadata,
          Column('price', Float, nullable=False), 
          Column('buy_sell', String,  nullable=False),  
          Column('market_limit', String),
          Column('miscellaneous', String),
          Column('time', DateTime,  nullable=False),
          Column('volume', Float, nullable=False))
    # Implement the creation
    metadata.create_all()    
    
BalanceTime = 10 
espera = 57 #segundas
Ejecutar = True
i = 0
cantEject = int(3600/espera)*4 # = 3 horas aprox
last = 0
tradesQuery =  {'pair': 'XXBTZUSD'}

BalanceColNames = ['Time','close','ask','bid','balanceRatio','volbuy','volsell','unbalance']
TradesColsNames = ['price', 'volume', 'time', 'buy_sell', 'market_limit', 'miscellaneous']

lapTradesCount = 0
totalTradesCount = 0
lastKnowTradeTime = datetime.now()  - timedelta(minutes=1)

if  engine.dialect.has_table(engine, dbTradesHistoryTable):
    tradesHistory = pd.read_sql(dbTradesHistoryTable, con=engine)
    if len(tradesHistory) > 0:
        lastKnowTradeTime = tradesHistory['time'].max()    

if  engine.dialect.has_table(engine, dbBalanceHistoryTable) & engine.dialect.has_table(engine, dbTradesHistoryTable):
    while Ejecutar:
    #for i in range(cantEject):
        try:
            
            BalanceHistory =pd.DataFrame(columns=BalanceColNames)
            
            startTime = datetime.now() 

            #i += 1
            #solicitar datos
            kapi = k.API()
            response = kapi.query_public('Trades',tradesQuery)
            #<price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>
            # check error y extraer datos
            error = response['error']
            if len(error) == 0:
                trades = pd.DataFrame(response['result']['XXBTZUSD'])
                # formatear datos
                trades.columns = TradesColsNames
                trades['price'] = trades['price'].apply(strToNum)
                trades['time'] = trades['time'].apply(unixtoDate)
                trades['volume'] = trades['volume'].apply(strToNum)
                trades.set_index('price',inplace=True)

                # filtrar ultima periodo
                intervalo = trades['time'].max() - timedelta(minutes=BalanceTime)
                trades = trades[trades['time'] >= intervalo]

                #agregar a al historial de trades
                tradesHistory = pd.concat([tradesHistory, trades])

                

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
                BalanceHistory.to_sql(dbBalanceHistoryTable,engine, if_exists='append')

                if len(trades[trades['time'] > lastKnowTradeTime]) > 0:     
                    trades= trades[trades['time'] > lastKnowTradeTime]
                    lastKnowTradeTime = trades['time'].max()   
                    lapTradesCount = len(trades)
                    totalTradesCount = totalTradesCount + lapTradesCount
                    trades.to_sql(dbTradesHistoryTable,engine, if_exists='append')
                    print('{0} new Trades | {1} Total Trades'.format(lapTradesCount, totalTradesCount))
                else:
                    print('no new trades from {0}'.format(lastKnowTradeTime))
            else:
                print(error)
        except:
            print ("Unexpected error: {0}".format(sys.exc_info()[0]))
            continue

        time.sleep(espera)
        lapTime = datetime.now()
        print( 'elapsed {0} sec'.format(PassTime(startTime, lapTime)))
        i = i + 1

# read from bddbb
BalanceHistory = pd.read_sql(dbBalanceHistoryTable, con=engine)
BalanceHistory = BalanceHistory.set_index(pd.DatetimeIndex(BalanceHistory['Time']))
BalanceHistory.drop('Time', axis=1,inplace=True)
BalanceHistory.tail(20)
print ('total balance history {0}'.format(len(BalanceHistory)))

# read from bddbb
tradesHistory = pd.read_sql(dbTradesHistoryTable, con=engine)
tradesHistory.set_index('price',inplace=True)
print ('total trades history {0}'.format(len(tradesHistory)))