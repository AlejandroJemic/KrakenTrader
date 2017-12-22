# DTO v1.0 17-12-217
# incluyo clases DTOs para sqlalquemy

from sqlalchemy import (create_engine, Column, Date, DateTime, Float, Integer, ForeignKey, String, Table, BigInteger, Text)
from sqlalchemy.ext.declarative import declarative_base

dbInstance = 'sqlite:///../../BBDD/krakenTeader.db'
engine = create_engine(dbInstance, echo=True)
Base = declarative_base()

class BalanceHistory(Base):

    __tablename__ = 'BalanceHistory'
    Time = Column(DateTime, primary_key=True)
    close = Column(Float)
    ask = Column(Float)
    bid = Column(Float)
    balanceRatio = Column(Float)
    volbuy = Column(Float)
    volsell = Column(Float)
    unbalance = Column(Float)


class TradesCondensation(Base):

    __tablename__ = 'TradesCondensation'
    time = Column(DateTime, primary_key=True)
    price = Column(Float)
    countb = Column(Float)
    volb = Column(Float)
    counts = Column(Float)
    vols = Column(Float)


class TradesHistory(Base):

    __tablename__ = 'TradesHistory'
    price = Column(Float, nullable=False)
    buy_sell = Column(String, nullable=False)
    market_limit  = Column(String)
    miscellaneous = Column(String)
    time = Column(DateTime,  primary_key=True)
    volume = Column(Float, nullable=False)


class MyTrades(Base):
    __tablename__ = 'MyTrades'
    index = Column(Integer, primary_key=True)
    id = Column(BigInteger)
    openTime = Column(DateTime)
    closeTime = Column(DateTime)
    tradeDescription = Column(Text)
    OpeningTypeID = Column(BigInteger)
    ClosingTypeID = Column(BigInteger)
    openingCH = Column(Float)
    baseCH = Column(Float)
    targetCH = Column(Float)
    stopLoseCH = Column(Float)
    TotalLoseCH = Column(Float)
    closingCH = Column(Float)
    deltaCH = Column(Float)
    openingP = Column(Float)
    baseP = Column(Float)
    targetP = Column(Float)
    stopLoseP = Column(Float)
    TotalLoseP = Column(Float)
    closingP = Column(Float)
    deltaP = Column(Float)
    Profit = Column(Float)
    Profit_Gastos = Column(Float)

    def __init__(self, oTradeValues, TableName):
        self.__tablename__ = TableName
        self.index = oTradeValues.idTrade
        self.id = oTradeValues.idTrade
        self.openTime = oTradeValues.openTime
        self.closeTime = oTradeValues.closeTime
        self.tradeDescription = oTradeValues.sDesc
        self.OpeningTypeID = oTradeValues.OpeningTypeID
        self.ClosingTypeID = oTradeValues.ClosingTypeID
        self.openingCH = oTradeValues.openingCH
        self.baseCH = oTradeValues.baseCH
        self.targetCH = oTradeValues.targetCH
        self.stopLoseCH = oTradeValues.stopLoseCH
        self.TotalLoseCH = oTradeValues.TotalLoseCH
        self.closingCH = oTradeValues.closingCH
        self.deltaCH = oTradeValues.deltaCH 
        self.openingP = oTradeValues.openingP
        self.baseP = oTradeValues.baseP
        self.targetP = oTradeValues.targetP
        self.stopLoseP = oTradeValues.stopLoseP
        self.TotalLoseP = oTradeValues.TotalLoseP
        self.closingP = oTradeValues.closingP
        self.deltaP = oTradeValues.deltaP
        self.Profit = oTradeValues.Profit
        self.Profit_Gastos = oTradeValues.Profit_Gastos
