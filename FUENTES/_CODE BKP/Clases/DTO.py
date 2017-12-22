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

class TradesHistory:
    __tablename__ = 'TradesHistory'
    price         = Column(Float, nullable=False)
    buy_sell      = Column(String, nullable=False)
    market_limit  = Column(String)
    miscellaneous = Column(String)
    time          = Column(DateTime, nullable=False)
    volume        = Column( Float, nullable=False)
	
class MyTrades:
	__tablename__ = 'MyTrades'
    index         = Column(DateTime, primary_key=True)
	id            = Column(BigInteger)
    openTime      = Column(DateTime)
    closeTime     = Column(DateTime)
    tradeDescription = Column(Text)
    OpeningTypeID = Column(BigInteger)
    ClosingTypeID = Column(BigInteger)
    openingCH     = Column(Float)
    baseCH        = Column(Float)
    targetCH      = Column(Float)
    stopLoseCH    = Column(Float)
    TotalLoseCH   = Column(Float)
    closingCH     = Column(Float)
    deltaCH       = Column(Float)
    openingP      = Column(Float)
    baseP         = Column(Float)
    targetP	      = Column(Float)
    stopLoseP     = Column(Float)
    TotalLoseP    = Column(Float)
    closingP      = Column(Float)
    deltaP        = Column(Float)
    Profit        = Column(Float)
    Profit_Gastos = Column(Float)