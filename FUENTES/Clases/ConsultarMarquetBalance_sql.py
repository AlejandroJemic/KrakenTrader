'''
# ConsultarMarquetBalance_sql v1.4  last at 20-12-2017

v1.4 
incorpora funcionalidad para ser llamado como thread

v1.3
# ejecuta las consultas al broker, actualmente solo soporta XTBUSD sobre Kraken.compras
# calcula el indicador balanceratio y lo guerad en bbdd
# calcula el tradesCondensation y lo guarda en bbdd
'''

import krakenex as k
import pandas as pd
import matplotlib.pyplot as plt
import time
import datetime
from pathlib import Path
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, MetaData, Table, Column, DateTime, Float, String,Integer
import os
from Utils import *


from  threading import *

path = os.getcwd()
ROOT_path = os.sep.join(path.split(os.sep)[:-2])

dbInstance = 'sqlite:///'+ ROOT_path +'\BBDD\krakenTrader.db'
engine = create_engine(dbInstance, connect_args={'timeout': 20})
dbBalanceHistoryTable = 'BalanceHistory'
dbTradesHistoryTable = 'TradesHistory'
dbTradesCondensationTable = 'TradesCondensation'

# funciones auxiliares
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

   
#set SQL BBDD, crear tablas
def setBBDD():
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

    if not engine.dialect.has_table(engine, dbTradesCondensationTable):  # If table don't exist, Create.
        metadata = MetaData(engine)
        
        # Create a table with the appropriate Columns
        Table(dbTradesCondensationTable, metadata,
                 Column('time', DateTime, nullable=True), 
                 Column('price', Float, nullable=True), 
                 Column('countb', Float, nullable=True), 
                 Column('volb', Float, nullable=True), 
                 Column('counts', Float, nullable=True), 
                 Column('vols', Float, nullable=True))
        # Implement the creation
        metadata.create_all()    

# funcion que condensa los trades del broker minuto a minuto para obtenre el volumen b y s por periodo
def CondensatetradesOnline(DBA, lastKnowTradeTime, currentTime):
    # leer trades history
    # startTime = datetime.now()
    tradesHistoryToCondens = pd.read_sql(dbTradesHistoryTable, con=engine)
    tradesHistoryToCondens.set_index(pd.DatetimeIndex(tradesHistoryToCondens['time']),inplace=True)
    tradesHistoryToCondens.drop('time', axis=1,inplace=True)

    # LogEvent('lectura t1 {0} sec'.format(PassTime(startTime, datetime.now()))) 

    # filtrar trades mayor a la ultima fecha conosida
    tradesHistoryToCondens = tradesHistoryToCondens[tradesHistoryToCondens.index > lastKnowTradeTime]
    tradesHistoryToCondens = tradesHistoryToCondens.sort_index()
    # LogEvent('lectura t2 {0} sec'.format(PassTime(startTime, datetime.now())))
    #crear tataframe para condensar trades
    tradesCondensation =  pd.DataFrame(columns=['time','price','countb','volb','counts','vols'])
    #condensa, si existen datos para condensar 
    if (len(tradesHistoryToCondens) > 0):
        t0 = tradesHistoryToCondens.index.max()
        trades0 = tradesHistoryToCondens[lastKnowTradeTime:t0]
        trades0b = trades0[trades0['buy_sell'] =='b']
        trades0s = trades0[trades0['buy_sell'] =='s']
        tradesCountb = len(trades0b)
        tradesCounts = len(trades0s)*-1
        price = trades0.price.mean()
        if price == 0:
            price = tradesHistoryToCondens.index[i-1]
        volb = trades0b.volume.sum()
        vols = trades0s.volume.sum()*-1
        new = [currentTime,price,tradesCountb,volb,tradesCounts,vols]
        tradesCondensation.loc[len(tradesCondensation)] = new
    else:
        new = [currentTime,0.0,0,0.0,0,0.0]
        tradesCondensation.loc[len(tradesCondensation)] = new
    #si exisnten datos
    # LogEvent('calculo t3 {0} sec'.format(PassTime(startTime, datetime.now())))
    if (len(tradesCondensation) > 0):
        tradesCondensation.fillna(0,inplace=True)
        tradesCondensation.set_index(pd.DatetimeIndex(tradesCondensation['time']),inplace=True)
        tradesCondensation.drop('time',inplace=True,axis=1)
    #guardar en bbdd, si existen datos condensados de fecha mayor a al ultima condensacion conosida
    if len(tradesCondensation[tradesCondensation.index >= currentTime]) > 0:
        tradesCondensation.to_sql(dbTradesCondensationTable,engine, if_exists='append')
    # LogEvent('escritura t4 {0} sec'.format(PassTime(startTime, datetime.now())))

    DBA.TradesHistoryDeleteAll()

    LogEvent('Condensated {0} Trades'.format(len(tradesHistoryToCondens)))
    return True   

def CondensateEmptytradesOnline(lastKnowTradeTime, currentTime):
    tradesCondensation =  pd.DataFrame(columns=['time','price','countb','volb','counts','vols'])
    new = [currentTime,0.0,0,0.0,0,0.0]
    tradesCondensation.loc[len(tradesCondensation)] = new
    tradesCondensation.set_index(pd.DatetimeIndex(tradesCondensation['time']),inplace=True)
    tradesCondensation.drop('time',inplace=True,axis=1)
    tradesCondensation.to_sql(dbTradesCondensationTable,engine, if_exists='append')
    LogEvent('condensated EMPTY Trades')
    return True    
 
#funcion principal que consulta los datos online 
def ConultarOnline(DBA):
    BalanceTime = 10 
    espera = 60 #segundas
    Ejecutar = True
    i = 0
    # cantEject = int(3600 / espera) * 4 # = 3 horas aprox
    # last = 0
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
    Lock = threading.Lock()
    if  engine.dialect.has_table(engine, dbBalanceHistoryTable) & engine.dialect.has_table(engine, dbTradesHistoryTable):
        while Ejecutar:
            
            try:
                BalanceHistory =pd.DataFrame(columns=BalanceColNames)
                startTime = datetime.now() 
                #solicitar datos
                kapi = k.API()
                response = kapi.query_public('Trades',tradesQuery)
                tikerResponce = kapi.query_public('Ticker', tradesQuery)
                #<price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>
                # check error y extraer datos
                error = response['error']
                errorTiker = tikerResponce['error']
                LogEvent('consulta {0} sec'.format(PassTime(startTime, datetime.now())))

                if (len(error) == 0) & (len(errorTiker) == 0):
                    while not Lock.acquire():
                        LogEvent( 'No se puede bloquear. Waitng  1s...') 
                        time.sleep(1)
                    LogEvent('Bloqueando')
                    LogEvent('lap {0} -  at {1}'.format(i, startTime))
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

                    # balance
                    volbuy = mb['buy'].sum()
                    volsell = mb['sell'].sum()
                    unbalance = mb['delta'].sum()
                    balanceRatio = volbuy / (volbuy - volsell) # es un valor porcentual entre 0 y 1

                   
                    LogEvent('balanceRatio: {0}'.format(balanceRatio))
                    LogEvent('volbuy:       {b}-BTCUSD | volsell: {s}-BTCUSD'.format(b=volbuy,s=volsell))
                    LogEvent('-> Unbalance: {u}-BTCUSD'.format(u=unbalance))
                    
                    #obtener precio actual
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
                        LogEvent('close: {0}'.format(close))
                        #guardar historia balance
                        newBalance = [currentTime,strToNum(close),strToNum(ask),strToNum(bid),balanceRatio,volbuy,volsell,unbalance]
                        BalanceHistory.loc[len(BalanceHistory)] = newBalance
                    else:
                        LogEvent(errorTiker,True)
                    
                    # LogEvent('calculo {0} sec'.format(PassTime(startTime, datetime.now())))  

                    BalanceHistory = BalanceHistory.set_index(pd.DatetimeIndex(BalanceHistory['Time']))
                    BalanceHistory.drop('Time', axis=1,inplace=True)
                    BalanceHistory.to_sql(dbBalanceHistoryTable,engine, if_exists='append')
                    
                    # LogEvent('escritura {0} sec'.format(PassTime(startTime, datetime.now()))) 

                    if len(trades[trades['time'] > lastKnowTradeTime]) > 0:     
                        trades= trades[trades['time'] > lastKnowTradeTime]
                        lapTradesCount = len(trades)
                        totalTradesCount = totalTradesCount + lapTradesCount
                        trades.to_sql(dbTradesHistoryTable,engine, if_exists='append')
                        CondensatetradesOnline(DBA, lastKnowTradeTime, currentTime)
                        
                        # LogEvent('condensado {0} sec'.format(PassTime(startTime, datetime.now()))) 

                        lastKnowTradeTime = trades['time'].max()
                        LogEvent('{0} new Trades | {1} Total Trades'.format(lapTradesCount, totalTradesCount))
                    else:
                        CondensateEmptytradesOnline(lastKnowTradeTime, currentTime)
                        LogEvent('no new trades from {0}'.format(lastKnowTradeTime))
                    Lock.release()
                else:
                    LogEvent(error + errorTiker, True)
                    LogEvent('waiting 5s...')
                    time.sleep(5)
            except:
                LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]),True)
                LogEvent('waiting 5s...')
                time.sleep(5)
                continue
            LogEvent('Total {0} sec'.format(PassTime(startTime, datetime.now()))) 
            lapTime = datetime.now()
            LogEvent('waitng  60s...')
            t = espera -PassTime(startTime, lapTime)
            if t > 0:
                time.sleep(espera -PassTime(startTime, lapTime))
            lapTime = datetime.now()
            LogEvent("")
            LogEvent('elapsed {0} sec'.format(PassTime(startTime, lapTime)))
            i = i + 1

            
##########################################################################################################
# MAIN
##########################################################################################################

def Main():
    setBBDD()
    ConultarOnline()

if __name__ == '__main__':
    Main()