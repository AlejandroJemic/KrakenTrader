
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, MetaData, Table, Column, DateTime, Float, String,Integer


class DBAdapter:
    '''
    #setea SQLite BBDD
    Contiene metodos para interactua con la bbdd
    creacion de tablas
    lectura de tablas
    '''
    
    dbInstance = 'sqlite:///../../BBDD/krakenTeader.db'
    dbBalanceHistoryTable = 'BalanceHistory'
    dbTradesHistoryTable = 'TradesHistory'
    dbMyTradesTable = 'MyTrades'
    d.bTradesCondensationTable = 'TradesCondensation'
    
    startSampleTime = None     #desde
    EndSampleTime = None     #hasta
    windowTime = None        #cuanto: tiempo en horas
    
    def __init__(self, dbInstance = None):
        '''
        Crea el engine y setea el nombre de la bbdd, si no es indicado toma el nombre por defecto
        '''
        if dbInstance != None:
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
        self.startSampleTime = self.EndSampleTime + timedelta(hours=self.windowTime*-1)

    def CreateAllTables(self):
        '''
        Crea las tablas de bbddd , si no existen
        '''
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
            
        if not self.engine.dialect.has_table(self.engine, self.dbTradesHistoryTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            # Create a table with the appropriate Columns
            Table(self.dbTradesHistoryTable, metadata,
                  Column('price', Float, nullable=False), 
                  Column('buy_sell', String,  nullable=False),  
                  Column('market/limit', String),
                  Column('miscellaneous', String),
                  Column('time', DateTime,  nullable=False),
                  Column('volume', Float, nullable=False))
            # Implement the creation
            metadata.create_all()

        if not self.engine.dialect.has_table(self.engine, self.dbMyTradesTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            # Create a table with the appropriate Columns
            Table(self.dbMyTradesTable, metadata,
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
            
        if not self.engine.dialect.has_table(self.engine, self.dbTradesCondensationTable):  # If table don't exist, Create.
            metadata = MetaData(self.engine)
            # Create a table with the appropriate Columns
            Table(self.dbTradesCondensationTable, metadata,
                     Column('time', DateTime, nullable=True), 
                     Column('price', Float, nullable=True), 
                     Column('countb', Float, nullable=True), 
                     Column('volb', Float, nullable=True), 
                     Column('counts', Float, nullable=True), 
                     Column('vols', Float, nullable=True))
            # Implement the creation
            metadata.create_all()
    
    
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
        BalanceHistory['balanceRatio'] = (BalanceHistory['balanceRatio'] - 0.5 )*2*100 

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
        if startSampleTime == None:
            startSampleTime = self.startSampleTime
        if EndSampleTime == None:
            EndSampleTime = self.EndSampleTime
        tc = pd.read_sql(self.dbTradesCondensationTable, con=self.engine , index_col='time', parse_dates=True)
        tc = tc[(tc.index >= startSampleTime) & (tc.index <= EndSampleTime)]
        return tc

    def ReadMyTrades(self, startSampleTime=None, EndSampleTime=None):
        '''
        #leer y retornar mis Trades desde la bbdd
        '''
        if startSampleTime == None:
            startSampleTime = self.startSampleTime
        if EndSampleTime == None:
            EndSampleTime = self.EndSampleTime
        mt = pd.read_sql(self.dbMyTradesTable, con=self.engine)
        mt.set_index('id',inplace=True)
        mt.drop('index',inplace=True,axis=1)
        mt = mt[(mt.openTime >= startSampleTime) & (mt.closeTime <= EndSampleTime)]
        return mt 