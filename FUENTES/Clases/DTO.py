# DTO v1.0 17-12-217
# incluyo clases DTOs para sqlalquemy

from sqlalchemy import (create_engine, Column, Date, DateTime, Float, Integer, ForeignKey, String, Table, BigInteger, Text)
from sqlalchemy.ext.declarative import declarative_base

dbInstance = 'sqlite:///../../BBDD/krakenTeader.db'
engine = create_engine(dbInstance, echo=True, connect_args={'timeout': 20})
Base = declarative_base()

class BalanceHistory(Base):
    __tablename__ = 'BalanceHistory'
    Time          = Column(DateTime, primary_key=True)
    close         = Column(Float)
    ask           = Column(Float)
    bid           = Column(Float)
    balanceRatio  = Column(Float)
    volbuy        = Column(Float)
    volsell       = Column(Float)
    unbalance     = Column(Float)


class TradesCondensation(Base):
    __tablename__ = 'TradesCondensation'
    time          = Column(DateTime, primary_key=True)
    price         = Column(Float)
    countb        = Column(Float)
    volb          = Column(Float)
    counts        = Column(Float)
    vols          = Column(Float)


class TradesHistory(Base):
    __tablename__ = 'TradesHistory'
    price         = Column(Float, nullable=False)
    buy_sell      = Column(String, nullable=False)
    market_limit  = Column(String)
    miscellaneous = Column(String)
    time          = Column(DateTime,  primary_key=True)
    volume        = Column(Float, nullable=False)


class MyTrades(Base):
    __tablename__    = 'MyTrades'
    index            = Column(Integer, primary_key=True)
    id               = Column(BigInteger)
    openTime         = Column(DateTime)
    closeTime        = Column(DateTime)
    tradeDescription = Column(Text)
    OpeningTypeID    = Column(BigInteger)
    ClosingTypeID    = Column(BigInteger)
    openingCH        = Column(Float)
    baseCH           = Column(Float)
    targetCH         = Column(Float)
    stopLoseCH       = Column(Float)
    TotalLoseCH      = Column(Float)
    closingCH        = Column(Float)
    deltaCH          = Column(Float)
    openingP         = Column(Float)
    baseP            = Column(Float)
    targetP          = Column(Float)
    stopLoseP        = Column(Float)
    TotalLoseP       = Column(Float)
    closingP         = Column(Float)
    deltaP           = Column(Float)
    Profit           = Column(Float)
    Profit_Gastos    = Column(Float)

    def __init__(self, oTradeValues, TableName):
        self.index            = oTradeValues.idTrade
        self.id               = oTradeValues.idTrade
        self.openTime         = oTradeValues.openTime
        self.closeTime        = oTradeValues.closeTime
        self.tradeDescription = oTradeValues.sDesc
        self.OpeningTypeID    = oTradeValues.OpeningTypeID
        self.ClosingTypeID    = oTradeValues.ClosingTypeID
        self.openingCH        = oTradeValues.openingCH
        self.baseCH           = oTradeValues.baseCH
        self.targetCH         = oTradeValues.targetCH
        self.stopLoseCH       = oTradeValues.stopLoseCH
        self.TotalLoseCH      = oTradeValues.TotalLoseCH
        self.closingCH        = oTradeValues.closingCH
        self.deltaCH          = oTradeValues.deltaCH 
        self.openingP         = oTradeValues.openingP
        self.baseP            = oTradeValues.baseP
        self.targetP          = oTradeValues.targetP
        self.stopLoseP        = oTradeValues.stopLoseP
        self.TotalLoseP       = oTradeValues.TotalLoseP
        self.closingP         = oTradeValues.closingP
        self.deltaP           = oTradeValues.deltaP
        self.Profit           = oTradeValues.Profit
        self.Profit_Gastos    = oTradeValues.Profit_Gastos


class Orders(Base):
    __tablename__ = 'Orders'
    idTrade =               Column(Integer, nullable=False)    # Id del trade al que coresponden
    idOrder =               Column(Integer, primary_key=True, nullable=False)      # Id local de la orden 
    OrderTime =             Column(DateTime, nullable=False)   # fecha hora de ingreso al sistema
    AgentCode =             Column(String, nullable=True)      # agente al que coresponden
    PairCode =              Column(String, nullable=True)      # par de monedas   que coresponden a la orden
    Price =                 Column(Float, nullable=True)       # precio considerado en el envio
    Vol =                   Column(Float, nullable=True)       # volumen en la moneda de la orden
    PriceVolValue =         Column(Float, nullable=True)       # valor  CALCULADO orden(precio crypto/USD * volumen a ejecurar, segun el precio considerado)
    ComisionPersent =       Column(Float, nullable=True)       # % comicion calculado
    ComisionAmount =        Column(Float, nullable=True)       # USD comicion calculada
    idOrderAgent =          Column(String, nullable=True)      # Id asignado por el agente 
    OrderTimeAgent =        Column(DateTime, nullable=True)    # fecha hora de confirmacion
    PriceAgent =            Column(Float, nullable=True)       # precio confirmado por el agente al cual se ejecuto
    VolAgent =              Column(Float, nullable=True)       # volumen ejecutado por el agente
    PriceVolValueAgent =    Column(Float, nullable=True)       # valor  EJECUTADO orden(precio crypto/USD ejc * volumen a ejecutado, segun el precio informado por el egente)
    ComisionPersentAgent =  Column(Float, nullable=True)       # % comicion  informado
    ComisionAmountAgent =   Column(Float, nullable=True)       # USD comicion informado
    SpreadComisionPersent = Column(Float, nullable=True)       # spread % comicion
    SpreadComisionAmount =  Column(Float, nullable=True)       # spread USD ajecucion
    SpreadPriceVolValue =   Column(Float, nullable=True)       # spread valor calculado - Valor Ejcuctado
    DelayTime =             Column(DateTime, nullable=True)    # deley ejecucion (en segundos) 
    IsConditional =         Column(Integer, nullable=True)     # flag es inmediata o condicional
    OrderType =             Column(Integer, nullable=True)     # tipo de orden: 1 compra market, 2 compra limit , 3 venta market, 4 venta limit , 5 stoplost, 6 totallost
    OrderState =            Column(Integer, nullable=True)     # estado de la orden
    PrevState =             Column(Integer, nullable=True)     # estado anterior
    OrderStateTime =        Column(DateTime, nullable=True)    # fecha ultimo estado
    PrevStateTime =         Column(DateTime, nullable=True)    # fecha estado anterior
    CancelationTime =       Column(DateTime, nullable=True)    # fecha hora de cancelacion de la orden
    CancelationDesc =       Column(DateTime, nullable=True)    # motivo de cancelacion descriptivo

    def __init__(self, oOrder): # oOrder is of type OrderValues
        self.idTrade               = oOrder.idTrade 
        self.idOrder               = oOrder.idOrder
        self.OrderTime             = oOrder.OrderTime
        self.AgentCode             = oOrder.AgentCode
        self.PairCode              = oOrder.PairCode
        self.Price                 = oOrder.Price
        self.Vol                   = oOrder.Vol
        self.PriceVolValue         = oOrder.PriceVolValue
        self.ComisionPersent       = oOrder.ComisionPersent
        self.ComisionAmount        = oOrder.ComisionAmount
        self.idOrderAgent          = oOrder.idOrderAgent
        self.OrderTimeAgent        = oOrder.OrderTimeAgent
        self.PriceAgent            = oOrder.PriceAgent
        self.VolAgent              = oOrder.VolAgent
        self.PriceVolValueAgent    = oOrder.PriceVolValueAgent
        self.ComisionPersentAgent  = oOrder.ComisionPersentAgent
        self.ComisionAmountAgent   = oOrder.ComisionAmountAgent
        self.SpreadComisionPersent = oOrder.SpreadComisionPersent
        self.SpreadComisionAmount  = oOrder.SpreadComisionAmount
        self.SpreadPriceVolValue   = oOrder.SpreadPriceVolValue
        self.DelayTime             = oOrder.DelayTime
        self.IsConditional         = oOrder.IsConditional
        self.OrderType             = oOrder.OrderType
        self.OrderState            = oOrder.OrderState
        self.PrevState             = oOrder.PrevState
        self.OrderStateTime        = oOrder.OrderStateTime
        self.PrevStateTime         = oOrder.PrevStateTime
        self.CancelationTime       = oOrder.CancelationTime
        self.CancelationDesc       = oOrder.CancelationDesc

class OrdersHistory(Base):
    __tablename__ = 'OrdersHistory'
    idTrade =           Column(Integer, nullable=True)  # Id del trade al que coresponde
    idOrder =           Column(Integer, primary_key=True, nullable=True)  # Id local de la orden 
    idOrderAgent =      Column(String, nullable=True)   # id asignado por el agente ( si existe)
    AgentCode =         Column(String, nullable=True)   # Broker corespondiente
    CoinCode =          Column(String, nullable=True)   # Cryptomoneda
    OrderState =        Column(Integer, nullable=True)  # id estado
    OrderStateTime =    Column(DateTime, primary_key=True, nullable=True) # fecha hora del ultimo estado
    PrevState =         Column(Integer, nullable=True)  # id estado anterior
    PrevStateTime =     Column(DateTime, nullable=True) # fecha ora estado anterior
    StateChangeMotive = Column(String, nullable=True)   # motivo del cambio de estado
    SentJson =          Column(String, nullable=True)    # json enviado
    ResivedJson =       Column(String, nullable=True)    # json recivido

    def __init__(self, oOrderHistory):  # oOrderHistory is of type OrderHistoryValues
        self.idTrade           = oOrderHistory.idTrade          
        self.idOrder           = oOrderHistory.idOrder          
        self.idOrderAgent      = oOrderHistory.idOrderAgent
        self.AgentCode         = oOrderHistory.AgentCode        
        self.CoinCode          = oOrderHistory.CoinCode   
        self.OrderState        = oOrderHistory.OrderState       
        self.OrderStateTime    = oOrderHistory.OrderStateTime
        self.PrevState         = oOrderHistory.PrevState         
        self.PrevStateTime     = oOrderHistory.PrevStateTime
        self.StateChangeMotive = oOrderHistory.StateChangeMotive
        self.SentJson          = oOrderHistory.SentJson         
        self.ResivedJson       = oOrderHistory.ResivedJson      