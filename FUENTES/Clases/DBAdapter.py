
# DBAdapter v1.1 17-12-2017
# incorpora MyTradesInsertOne y MyTradesUpdateOne por medio de sqlalquemy con DTOs
# incorpra MyTradesReadLast

import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, MetaData, Table, Column, DateTime, Float, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from DTO import MyTrades
from TradeEvaluator import TradeValues
import os
from Utils import *


path = os.getcwd()
ROOT_path = os.sep.join(path.split(os.sep)[:-2])


class DBAdapter:
    '''
    #setea SQLite BBDD
    Contiene metodos para interactua con la bbdd
    creacion de tablas
    lectura de tablas
    '''
    dbInstance = 'sqlite:///'+ ROOT_path +'\BBDD\krakenTrader.db'
    dbBalanceHistoryTable = 'BalanceHistory'
    dbTradesHistoryTable = 'TradesHistory'
    dbMyTradesTable = 'MyTrades'
    dbTradesCondensationTable = 'TradesCondensation'
    dbOrdersTable = 'Orders'
    dbOrdersHistoryTable = 'OrdersHistory'

    startSampleTime = None     # desde
    EndSampleTime = None     # hasta
    windowTime = None        # cuanto: tiempo en horas

    def __init__(self, dbInstance=None):
        '''
        Crea el engine y setea el nombre de la bbdd, si no es indicado toma el nombre por defecto
        '''
        if dbInstance is not None:
            self.dbInstance = dbInstance
        self.engine = create_engine(self.dbInstance)
        self.SetStartEndTimeAuto()

    def SetStartEndTimeAuto(self):
        '''
        Establese automaticamente los parametros de ventana de datos  a partir de la tabla BalanceHistory, completa
        '''
        bh = pd.read_sql(self.dbBalanceHistoryTable, con=self.engine, index_col='Time', parse_dates=True)
        self.startSampleTime = bh.index[0] #desde
        self.EndSampleTime   = bh.index[len(bh)-1]  #hasta
        self.windowTime = (self.EndSampleTime - self.startSampleTime).total_seconds()/3600 #cuanto: tiempo en horas
    
    def SetStartEndTime(self, windowTime, EndSampleTime=datetime.now()):
        '''
        Determina manualmente la ventana de datos
        windowTime: tiempo en horas
        EndSampleTime: fecha hasta, si no se indica toma el datetime.now

        ejemplo: periodo de interes en duro
        EndSampleTime = datetime(2017,12,11,13,0,0) #hasta
        windowTime = (24 * 60) + 13 #cuanto tiempo en horas
        startSampleTime = EndSampleTime + timedelta(hours=windowTime*-1) #desde : tiempo en horas
        '''
        self.EndSampleTime = EndSampleTime
        self.windowTime = windowTime
        self.startSampleTime = self.EndSampleTime + timedelta(hours=self.windowTime*-1)

    def CreateAllTables(self):
        '''
        Crea las tablas de bbddd , si no existen
        '''
        print(self.dbInstance)
        if not self.engine.dialect.has_table(self.engine, self.dbBalanceHistoryTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            # Create a table with the appropriate Columns
            Table(self.dbBalanceHistoryTable, metadata,
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
            print('creada la table' + self.dbBalanceHistoryTable)
            
        if not self.engine.dialect.has_table(self.engine, self.dbTradesHistoryTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            # Create a table with the appropriate Columns
            Table(self.dbTradesHistoryTable, metadata,
                  Column('price', Float, nullable=False),
                  Column('buy_sell', String, nullable=False),
                  Column('market_limit', String),
                  Column('miscellaneous', String),
                  Column('time', DateTime, nullable=False),
                  Column('volume', Float, nullable=False))
            # Implement the creation
            metadata.create_all()
            print('creada la table' + self.dbTradesHistoryTable)

        if not self.engine.dialect.has_table(self.engine, self.dbMyTradesTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            # Create a table with the appropriate Columns
            Table(self.dbMyTradesTable, metadata,
                     Column('index', Integer, nullable=True),
                     Column('id', Integer, nullable=True),
                     Column('openTime', DateTime, nullable=True),
                     Column('closeTime', DateTime, nullable=True),
                     Column('tradeDescription', String, nullable=True),
                     Column('OpeningTypeID', Integer, nullable=True),
                     Column('ClosingTypeID', Integer, nullable=True),
                     Column('openingCH', Float, nullable=True),
                     Column('baseCH', Float, nullable=True),
                     Column('targetCH', Float, nullable=True),
                     Column('stopLoseCH', Float, nullable=True),
                     Column('TotalLoseCH', Float, nullable=True),
                     Column('closingCH', Float, nullable=True),
                     Column('deltaCH', Float, nullable=True), 
                     Column('openingP', Float, nullable=True), 
                     Column('baseP', Float, nullable=True), 
                     Column('targetP', Float, nullable=True), 
                     Column('stopLoseP', Float, nullable=True), 
                     Column('TotalLoseP', Float, nullable=True), 
                     Column('closingP', Float, nullable=True), 
                     Column('deltaP', Float, nullable=True), 
                     Column('Profit', Float, nullable=True),
                     Column('Profit_Gastos', Float, nullable=True))
            # Implement the creation
            metadata.create_all()
            print('creada la table' + self.dbMyTradesTable)

        if not self.engine.dialect.has_table(self.engine, self.dbTradesCondensationTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            # Create a table with the appropriate Columns
            Table(self.dbTradesCondensationTable, metadata,
                     Column('time', DateTime, nullable=True),
                     Column('price', Float, nullable=True),
                     Column('countb', Float, nullable=True),
                     Column('volb', Float, nullable=True),
                     Column('counts', Float, nullable=True), # 
                     Column('vols', Float, nullable=True))
            # Implement the creation
            metadata.create_all()
            print('creada la tabla' + self.dbTradesCondensationTable)

        if not self.engine.dialect.has_table(self.engine, self.dbOrdersTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            Table(self.dbOrdersTable, metadata,
                Column('idTrade', Integer, nullable=False),     # Id del trade al que coresponden
                Column('idOrder', Integer, nullable=False),      # Id local de la orden 
                Column('OrderTime', DateTime, nullable=False),   # fecha hora de ingreso al sistema
                Column('AgentCode', String, nullable=True),      # agente al que coresponden
                Column('CoinCode', String, nullable=True),       # cryptomoneda a la que coresponden
                Column('ClosingPrice', Float, nullable=True),    # precio considerado en el envio
                Column('Vol', Float, nullable=True),             # volumen en la moneda de la orden
                Column('PriceVolValue', Float, nullable=True),   # valor  CALCULADO orden(precio crypto/USD * volumen a ejecurar, segun el precio considerado)
                Column('ComisionPersent', Float, nullable=True), # % comicion calculado
                Column('ComisionAmount', Float, nullable=True),  # USD comicion calculada
                Column('idOrderAgent', String, nullable=True),      # Id asignado por el agente 
                Column('OrderTimeAgent', DateTime, nullable=True),  # fecha hora de confirmacion
                Column('ClosingPriceAgent', Float, nullable=True),  # precio confirmado por el agente al cual se ejecuto
                Column('VolAgent', Float, nullable=True),           # volumen ejecutado por el agente
                Column('PriceVolValueAgent', Float, nullable=True), # valor  EJECUTADO orden(precio crypto/USD ejc * volumen a ejecutado, segun el precio informado por el egente)
                Column('ComisionPersent', Float, nullable=True),    # % comicion  informado
                Column('ComisionAmountAgent', Float, nullable=True),# USD comicion informado
                Column('SpreadComisionPersent', Float, nullable=True),  # spread % comicion
                Column('SpreadComisionAmount', Float, nullable=True),   # spread USD ajecucion
                Column('SpreadPriceVolValue', Float, nullable=True),    # spread valor calculado - Valor Ejcuctado
                Column('DelayTime', DateTime, nullable=True),           # deley ejecucion (en segundos) 
                Column('IsConditional', Integer, nullable=True),     # flag es inmediata o condicional
                Column('OrderType', Integer, nullable=True),         # tipo de orden: compra market, compra limit/datelimit , venta, market, venta limit/datelimit , stoplost, totallost, salvarganancia, 
                Column('OrderState', Integer, nullable=True),        # estado de la orden
                Column('PrevState', Integer, nullable=True),         # estado anterior
                Column('OrderStateTime', DateTime, nullable=True),   # fecha ultimo estado
                Column('PrevStateTime', DateTime, nullable=True),    # fecha estado anterior
                Column('CancelationTime', DateTime, nullable=True),  # fecha hora de cancelacion de la orden
                Column('CancelationDesc', DateTime, nullable=True))  # motivo de cancelacion descriptivo
            # Implement the creation
            metadata.create_all()
            print('creada la tabla' + self.dbOrdersTable)

        if not self.engine.dialect.has_table(self.engine, self.dbOrdersHistoryTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            Table(self.dbOrdersHistoryTable, metadata,
                Column('idTrade', Integer, nullable=True),     # Id del trade al que coresponde
                Column('idOrder', Integer, nullable=True),     # Id local de la orden 
                Column('idOrderAgent', String, nullable=True), # id asignado por el agente ( si existe)
                Column('AgentCode', String, nullable=True),    # Broker corespondiente
                Column('CoinCode', String, nullable=True),     # Cryptomoneda
                Column('OrderState', Integer, nullable=True),      # id estado
                Column('OrderStateTime', DateTime, nullable=True), # fecha hora del ultimo estado
                Column('PrevState', Integer, nullable=True),       # id estado anterior
                Column('PrevStateTime', DateTime, nullable=True),  # fecha ora estado anterior
                Column('StateChangeMotive', String, nullable=True), # motivo del cambio de estado
                Column('SentJson', Float, nullable=True),           # json enviado
                Column('ResivedJson', Float, nullable=True))        # json recivido
            # Implement the creation
            metadata.create_all()
            print('creada la tabla' + self.dbOrdersHistoryTable)

    def ReadBalanceHistory(self, startSampleTime=None, EndSampleTime=None):
        '''
        leer y retornar el balance y precio desde la bbdd, el % cambio se calcula on demand
        '''
        if startSampleTime == None:
            startSampleTime = self.startSampleTime
        if EndSampleTime == None:
            EndSampleTime = self.EndSampleTime
        BalanceHistory = pd.read_sql(self.dbBalanceHistoryTable, con=self.engine, index_col='Time', parse_dates=True)
        
        BalanceHistory = BalanceHistory[(BalanceHistory.index >= startSampleTime) & (BalanceHistory.index <= EndSampleTime)]
        #combertir el balance a un porcentaje entre -100% y 100%
        BalanceHistory['balanceRatio'] = (BalanceHistory['balanceRatio'] - 0.5)* 2 * 100 # lo trasnformo a un valor poercentual entre -100 y +100

        BalanceHistory['volbuy'] = BalanceHistory['volbuy'] / BalanceHistory['close']
        BalanceHistory['volsell'] = BalanceHistory['volsell'] / BalanceHistory['close']
        BalanceHistory['unbalance'] = BalanceHistory['unbalance'] / BalanceHistory['close']

        #calcular %CH, %CH Acum , SMA %CH Acum
        BalanceHistory['change'] = BalanceHistory['close'].pct_change(periods=1)*100
        #BalanceHistory['cahnge2'] = BalanceHistory['close'] / BalanceHistory['close'].shift(1) -1 #equibalente 
        BalanceHistory['cum_change'] = BalanceHistory['change'].cumsum()
        BalanceHistory['SMA03_cum_change'] = BalanceHistory['cum_change'].rolling(5).mean()
        BalanceHistory['SMA12_cum_change'] = BalanceHistory['cum_change'].rolling(12).mean()

        #calcular sma de 3 periodos (suavisar el grafico)
        BalanceHistory['EWM_unbalance'] =  BalanceHistory["unbalance"].ewm(span=3).mean()

        #calcular la porsiocn negativa (para mostrar en rojo en el grafico)
        BalanceHistory['EWM_unbalance_N'] = BalanceHistory['EWM_unbalance']
        neg = BalanceHistory['EWM_unbalance_N']
        neg[neg >= 0] = np.nan
        BalanceHistory['EWM_unbalance_N'] = neg
        return BalanceHistory

    def ReadCondensatedTrades(self, startSampleTime=None, EndSampleTime=None):
        '''
        #leer y retornar los datos de trades condensados desde la bbdd: 
        '''
        if startSampleTime is None:
            startSampleTime = self.startSampleTime
        if EndSampleTime is None:
            EndSampleTime = self.EndSampleTime
        tc = pd.read_sql(self.dbTradesCondensationTable, con=self.engine , index_col='time', parse_dates=True)
        tc = tc[(tc.index >= startSampleTime) & (tc.index <= EndSampleTime)]
        return tc

    def ReadMyTrades(self, startSampleTime=None, EndSampleTime=None):
        '''
        #leer y retornar mis Trades desde la bbdd
        '''
        if startSampleTime is None:
            startSampleTime = self.startSampleTime
        if EndSampleTime is None:
            EndSampleTime = self.EndSampleTime
        mt = pd.read_sql(self.dbMyTradesTable, con=self.engine, parse_dates = True)
        mt.set_index('id', inplace=True)
        mt.drop('index', inplace=True, axis=1)
        mt = mt[(mt.openTime >= startSampleTime) & (mt.closeTime <= EndSampleTime)]
        return mt
    
    def MytradesDeleteAll(self):
        '''
        borrar la tabla Mytrades, para reprocesar
        '''
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            q = 'delete from ' + self.dbMyTradesTable
            session.execute(q)
            session.commit()
        except SQLAlchemyError as e:
            print(e)
        finally:
            session.close()

    def MytradesInsertOne(self, oTradeValues, tableName):
        '''
        inserta una fila en la tabla MyTrades a partir d eun objeto TradeValues por medio de SQLalchemy
        '''
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            newTrade = MyTrades(oTradeValues, tableName)
            session.add(newTrade)
            session.commit()
        except SQLAlchemyError as e:
            print(e)
        finally:
            session.close()

    def MytradesUpdateOne(self, oTradeValues):
        '''
        inserta una fila en la tabla MyTrades a partir d eun objeto TradeValues por medio de SQLalchemy
        '''
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            oTrade = session.query(MyTrades).filter(MyTrades.id == oTradeValues.idTrade).first()
            oTrade.openTime = oTradeValues.openTime
            oTrade.closeTime = oTradeValues.closeTime
            oTrade.tradeDescription = oTradeValues.sDesc
            oTrade.OpeningTypeID = oTradeValues.OpeningTypeID
            oTrade.ClosingTypeID = oTradeValues.ClosingTypeID
            oTrade.openingCH = oTradeValues.openingCH
            oTrade.baseCH = oTradeValues.baseCH
            oTrade.targetCH = oTradeValues.targetCH
            oTrade.stopLoseCH = oTradeValues.stopLoseCH
            oTrade.TotalLoseCH = oTradeValues.TotalLoseCH
            oTrade.closingCH = oTradeValues.closingCH
            oTrade.deltaCH = oTradeValues.deltaCH 
            oTrade.openingP = oTradeValues.openingP
            oTrade.baseP = oTradeValues.baseP
            oTrade.targetP = oTradeValues.targetP
            oTrade.stopLoseP = oTradeValues.stopLoseP
            oTrade.TotalLoseP = oTradeValues.TotalLoseP
            oTrade.closingP = oTradeValues.closingP
            oTrade.deltaP = oTradeValues.deltaP
            oTrade.Profit = oTradeValues.Profit
            oTrade.Profit_Gastos = oTradeValues.Profit_Gastos
            session.commit()
        except SQLAlchemyError as e:
            print(e)
        finally:
            session.close()

    def MyTradesReadLast(self):
        '''
        devuelve el ultimo trade creado , 
        como registro de la tabla MyTrades
        '''
        Session = sessionmaker(bind=self.engine)
        session = Session()
        oTradeValues = TradeValues()
        oTrade = MyTrades(oTradeValues, self.dbMyTradesTable)
        try:
            cant = session.query(MyTrades).count()
            if cant > 0 :
                oTrade = session.query(MyTrades).order_by(MyTrades.id.desc()).first()
                session.expunge(oTrade)
            else:
                oTrade = None
            session.commit()
        except SQLAlchemyError as e:
            print(e)
        finally:
            session.close()
        return oTrade