'''
TradeEvaluator v1.2 19-12-2017

v 1.2
metodo OpenerCloserEvaluator incorpora soporte para evaluacion online por medio del flag  pIsBackTest = False y 
se agrega parametro startEvalpos para indicar si se itera desde el inicio de la serie o solo el ultimpo indice
se agrega metodo ReadLastTrade returns of type TradeValues
se incorpora mejora en el metodo EvaluateTrend para deterctar el minimo y evaluar desde dicho punto

v1.1
metodo SaveAllTrades en desuso, ahora se empla DBA.MytradesInsertOne(oTradeValues)
cuando se se abre y cierra  cada trade 
desde  AddClosedTread(self, oTradeValues, oDBAdapter)
    y  UpdateClosedTread(self, oTradeValues, oDBAdapter)
'''
# imports
import numpy as np
import pandas as pd
import time
from pathlib import Path
import sys
from datetime import datetime, timedelta
from DTO import MyTrades

##################################################################################################################3
#    class TradeValues:                                                                         ##################3
##################################################################################################################3

class TradeValues:
    '''
    representa los valores de una operacion mientras esta siendo evaluada
    '''
    #valores de cada operacion 
    openPos = 0        # indice del tiempo de apertura
    ClosePos = 0       # inidce del tiempo de cierre
    isOpen = False     # flag operacion abierta/cerrada
    inBase = False     # flag operacion sobre gastos operacionales
        
    sOpenCond = ""                    # descripcion tipo de apertura
    sCloseCond = 'IN PROGRESS'   # descripcion tipo de cierre
    sDesc = ""                        # descripcion e apertura y cierre
        
    openingCH = 0.0        # % de cambio acumulado desde el inicio de la cerie hasta la apertura de la operacion
    baseCH = 0.0           # % openingCH  + gasttos operacionales por compra venta
    targetCH = 0.0         # % openingCH + objetivo libre de gastos
    stopLoseCH = 0.0       # % openingCH + gasttos operacionales - corte de perdidas
    TotalLoseCH = 0.0      # % openingCH - corte de perdidas (perdida total sin cubrir los gastos operacionales)
    closingCH = 0.0        # % de cambio acumulado desde el inicio de la serie hasta el cierre d ela operacion 
    deltaCH = 0.0          # % openingCH +- closingCH
    
    idTrade = 0                    # id operaciones
    openTime = datetime(1900, 1, 1, 0, 0, 0)    # tiempo apertura operacion
    closeTime = datetime(1900, 1, 1, 0, 0, 0)   # tiempo cierre operacion
    maximo = 0.0                   # % cambio acumulado maximo, desde la apertura de la operacion
    maximoTolerado = 0.0           # % cambio acumulado tolerado para cierre, desde la apertura, se calcula con una funcion
    
    OpeningTypeID = 0    # id tipo apertura
    ClosingTypeID = 0    # id tipo cierre
        
    openingP = 0.0         # precio al opentime
    baseP = 0.0            # precio de gasttos operacionales por compra venta
    targetP = 0.0          # precio objetivo libre de gastos
    stopLoseP = 0.0        # openingP + gasttos operacionales - corte de perdidas
    TotalLoseP = 0.0       # openingP - corte de perdidas (perdida total sin cubrir los gastos)
    closingP = 0.0         # precion al closeTime
    deltaP = 0.0           # openingP +- ClosingP
    Profit = 0.0           # ganacia acumulada de todas las operaciones
    Profit_Gastos = 0.0    # ganacia acumulada de todas las operaciones - los gastos operacionales

##################################################################################################################3
#    class OpenCloseValues:                                                                     ##################3
##################################################################################################################3
    
class OpenCloseValues:
    '''
    establese parametros para abrir y cerrar operaciones
    '''
    volPriceOpen  = 50000          # monto en moneda que debe mover moverse para abir una operacion
    chOpen = 0.4                   # % de cambio para abrir una operacion
    mbOpen = 1.05                   # indicador BalanceHistory.unbalance para abrir una operacion
    deltaCHObjetivo = 20            # % cambio objetibo, lo se que espera ganar
    chClose = 1                    # % cambio para corte de perdidas si se alcanso la base
    deltaTotalLoseCH = 0.5         # % cambio para corde de perdidas si no se alcanso la base
    waitPeriods = 60               # cuando la operacion esta abierta y se alcanso la base, se espera periodos=waitPeriods * waitFactor
    waitFactor = 48
    waitPeriodsOutBase = 60        # cuando la operacion esta abierta fuera de base, se espera periodos=waitPeriodsOutBase * waitFactorOutBase
    waitFactorOutBase = 3
    cumCHIncrement = 2.6           # % de cambio acumuladoa para apertura de operacion si existe tendencia positiva lenta
    
##################################################################################################################3
#    class TradeEvaluator:                                                                      ##################3
##################################################################################################################3

class TradeEvaluator:
    '''
    contiene metodos para determinar posisiones de apertura y cierre de operaciones segun las acciones del mercado
    '''
    comCompra = 0.29      # % comision de compra
    comVenta = 0.19       # % comision de salido
    spreadEntrada = 0.2   # % spread tentiatiovo precio de compra
    spreadSalida = 0.2    # % spread tentativo precio de venta
    deltabaseCH = 0.0     # % total de gastos operativos por operacion, es usado com obase para salida sin ganancias ni perdidas
    
    lastIdTrade = 0          # ultimo id trade creado
    lastOpenPos = 0          # ultimo posision incide para apertura operacion
    lastClosePos = 0         # ultima posision indice para cierre operacion 
    
    cols = ['id', 'openTime', 'closeTime', 'tradeDescription', 'OpeningTypeID', 'ClosingTypeID', 'openingCH', 'baseCH', 'targetCH', 'stopLoseCH', 'TotalLoseCH', 'closingCH', 'deltaCH', 'openingP', 'baseP', 'targetP', 'stopLoseP', 'TotalLoseP', 'closingP', 'deltaP', 'Profit', 'Profit_Gastos']     
    myTrades = pd.DataFrame(columns=cols)
    
    def __init__(self,comCompra = None, comVenta = None, spreadEntrada = None, spreadSalida = None):
        if comCompra != None:      
            self.comCompra = comCompra # % comision de compra
        if comVenta != None:      
            self.comVenta = comVenta        # % comision de salido
        if spreadSalida != None:      
            self.spreadEntrada = spreadEntrada  # % spread tentiatiovo precio de compra
        if spreadSalida != None:      
            self.spreadSalida = spreadSalida    # % spread tentativo precio de venta
        self.deltabaseCH = self.comCompra + self.comVenta + self.spreadEntrada + self.spreadSalida     # % total de gastos poerativos por Operacion, es usado com obase para salida sin ganancias ni perdidas
    
    def obtenerMaximo(Self, m,n):
        '''
        debuelve el mayor de dos numeros
        '''
        if m >= n: 
            return m
        else:
            return n 
        
    def  acumular(self, serie,cant,pos):
        '''
        debuelve la suma acumulada de una serie , a partir de una posision indicada(final) y la cantidad de posisiones
        '''
        su = 0.0
        for i in range(pos,pos - cant - 1,-1):
            su = su + serie[i]
        return su

    def restarGastos (self,s):
        '''
        a partir d euna serie profit, devuelve una nueba serie profit-menos gastos acumulados
        '''
        l = []
        for i in range(len(s)):
            l.append((s[i] - (self.deltabaseCH*(i+1))))
        return l

    def EvaluateTrend(self, bh, OCV):
        try:
            pini = 0 
            pfin = len(bh)-1
            isUpTrend = False
            if ((pfin - pini) >= 60):
                bh['change'] = bh['close'].pct_change(periods=1)*100
                ch = bh['change']
                bh['cum_change'] = bh['change'].cumsum()

                # busco la posision del minimo de la serie y , recalculo el porcentaje de cambio acumulado 
                pmin = bh.index.get_loc(bh['cum_change'].argmin())
                bh2 = bh[pmin:pfin].copy(deep=True)
                pfin = len(bh2) -1
                if pfin > 0:
                    bh2['cum_change'] = bh2['change'].cumsum()
                    cumch = bh2['cum_change']
                    if (cumch[pfin] >= OCV.cumCHIncrement):
                        isUpTrend = True
        except:
            dbg.set_trace()
            raise
        return isUpTrend
    
    ##################################################################################################################
        
    def OpenerCloserEvaluator (self,bh, tc, DBA, pOpenCloseValues = None, pIsBackTest = True):
        '''
        funcion principal de la clase que
        Evalua cuando abrir o cerrar una operacion segun las condiciones del mercado
        dentro de una ventana de tiempo dada (implisitida en el largo de los dataframes bh y tc)
        
        parametros:
        bh                 BalanceHistory Table
        tc                 TradeCondensation table 
        DBA                of type DBAdapter
        pOpenCloseValues   of type  OpenCloseValues, parametros de evaluacion para abrir y cerrar
        pIsBackTest        si True:  se ejecuta en modo backtest, es decir lee datos historicos y recalcula todos los trades 
                                        usa la tabla "MyTradesBackTest"
                           si False: lee de bbdd el ultimo trade, y solo el ultimo periodo de la serie, y evalua apertura cierre 
                                        usa la tabla "MyTrades"
        '''
        OCV = OpenCloseValues()
        
        if pOpenCloseValues != None:
            OCV = pOpenCloseValues
        
        # valores generales
        deltabaseCH = self.deltabaseCH                       # % para cubrir gastos operacionales por compra venta
        deltaTargetCH = deltabaseCH + OCV.deltaCHObjetivo    # % para alcanzar el objetivo libre de gastos
        deltaStopLose = deltabaseCH - OCV.chClose            # % corte de perdidas

        s = bh['unbalance']                                # serie que indica el indice de desvalance entre compra venta
        sma03 = bh['SMA03_cum_change']                     # media movil corta del % de cambio acumulado
        sma12 = bh['SMA12_cum_change']                     # media movio larga del % de cambio acumulado
        ch = bh['change']                                  # % de cambio del ultimo periodo
        cumch = bh['cum_change']                           # % de cambio acumulado desde el inicio de la serie
        
        volb = tc['volb']                                  # % volumen de compras en el ultimo periodo(del broker)
        
        T = TradeValues()

       

        #  pIsBackTest = True:
        DBA.dbMyTradesTable = 'MyTradesBackTest'
        DBA.CreateAllTables()
        DBA.MytradesDeleteAll()     # borra la tabla para reprocesar
        T = TradeValues()
            
        for i in range(len(s)):
            if i > 12:
                if (T.isOpen == False):
                    if i < len(tc):
                        T = self.EvaluateOpening(T, OCV, s,sma03, sma12, volb, bh, tc, i)
                        
                    if T.isOpen == True:
                        T = self.SetOpening(OCV, T, tc, s, cumch, deltaTargetCH, deltaStopLose, i, self.lastIdTrade)
                        
                        self.InsertOpenedTread(T, DBA)
                        
                if (T.isOpen == True):
                    T = self.EvaluateClosing(T, OCV, s, deltaStopLose, bh,  cumch, i)
                    
                    if (T.isOpen == False) or ((i == len(s)-1) & (T.isOpen == True)): #si cerro operacion o es el ultimo periodo y alguna operacion sigue abierta
                        T = self.SetClosing( T, s, bh, tc, i)
                            
                        self.UpdateClosedTread(T, DBA) 
                        
                        self.lastIdTrade = T.idTrade
                        self.lastOpenPos = T.openPos
                        self.lastClosePos = T.ClosePos
                        T = TradeValues()
                        T.openPos = self.lastOpenPos
                        T.ClosePos = self.lastClosePos
        #end For
        
        #self.SaveAllTrades(DBA) # es desuso desde v1.1
        
        #leer y retornar mis Trades desde la bbdd
        mt = DBA.ReadMyTrades()
        print('Total Trades: {0}'.format(len(mt)))
        return mt


    ##################################################################################################################3

    def OpenerCloserEvaluatorOnLine (self,bh, tc, DBA, pOpenCloseValues = None, pIsBackTest = False):
        '''
        funcion principal de la clase que
        Evalua ONLINE cuando abrir o cerrar una operacion segun las condiciones del mercado
        tomando el ultimo indice de las series recividas
        
        parametros:
        bh                 BalanceHistory Table
        tc                 TradeCondensation table 
        DBA                of type DBAdapter
        pOpenCloseValues   of type  OpenCloseValues, parametros de evaluacion para abrir y cerrar
        pIsBackTest        si True:  se ejecuta en modo backtest, es decir lee datos historicos y recalcula todos los trades 
                                        usa la tabla "MyTradesBackTest"
                           si False: lee de bbdd el ultimo trade, y solo el ultimo periodo de la serie, y evalua apertura cierre 
                                        usa la tabla "MyTrades"
        '''
        OCV = OpenCloseValues()
        
        if pOpenCloseValues != None:
            OCV = pOpenCloseValues
        
        # valores generales
        deltabaseCH = self.deltabaseCH                       # % para cubrir gastos operacionales por compra venta
        deltaTargetCH = deltabaseCH + OCV.deltaCHObjetivo    # % para alcanzar el objetivo libre de gastos
        deltaStopLose = deltabaseCH - OCV.chClose            # % corte de perdidas

        s = bh['unbalance']                                # serie que indica el indice de desvalance entre compra venta
        sma03 = bh['SMA03_cum_change']                     # media movil corta del % de cambio acumulado
        sma12 = bh['SMA12_cum_change']                     # media movio larga del % de cambio acumulado
        ch = bh['change']                                  # % de cambio del ultimo periodo
        cumch = bh['cum_change']                           # % de cambio acumulado desde el inicio de la serie
        
        volb = tc['volb']                                  # % volumen de compras en el ultimo periodo(del broker)
        
        T = TradeValues()
        sAction  = 'No action'
        iAction = 0
        # pIsBackTest = False:
        DBA.dbMyTradesTable = 'MyTrades'
        Evalpos = len(s) -1    # inicia en el ultipo periodo para evaluar solo el momento actual(presupone corriendo online), 
        T = self.ReadLastTrade(s, DBA) # lee ultimo trade creado
        sAction  ='Find last trade: ' + str(T.idTrade)
        if T.idTrade == 0:
            T = TradeValues() 
            sAction  = 'No trades in DDBB'
        if Evalpos > 12:
            if (T.isOpen == False):
                if Evalpos < len(tc):
                    sAction  = sAction + '. Evaluating opening'
                    iAction = 1
                    T = self.EvaluateOpening(T, OCV, s,sma03, sma12, volb, bh, tc, Evalpos)
                if T.isOpen == True:
                    
                    T = self.SetOpening(OCV, T, tc, s, cumch, deltaTargetCH, deltaStopLose, Evalpos, self.lastIdTrade)
                    sAction = sAction + '. Trade Opened'
                    iAction = 2
                    self.InsertOpenedTread(T, DBA)
                    sAction = sAction + '. Trade saved in DDBB'
                    iAction = 3
                    
            if (T.isOpen == True):
                sAction = sAction + '. Evaluating Closing'
                iAction = 4
                T = self.EvaluateClosing(T, OCV, s, deltaStopLose, bh,  cumch, Evalpos)
                
                if (T.isOpen == False): #si cerro operacion
                    T = self.SetClosing( T, s, bh, tc, Evalpos)
                    sAction = sAction + '. Trade Closed'
                    iAction = 5
                        
                    self.UpdateClosedTread(T, DBA) 
                    sAction = sAction + '. Trade Updated in DDBB'
                    iAction = 6
                    
                    self.lastIdTrade = T.idTrade
                    self.lastOpenPos = T.openPos
                    self.lastClosePos = T.ClosePos
                    T = TradeValues()
                    T.openPos = self.lastOpenPos
                    T.ClosePos = self.lastClosePos
        return sAction , iAction

    ##################################################################################################################3
    
    def EvaluateOpening(self, T, OCV, s,sma03, sma12, volb, bh, tc, i):
        '''
        evalua cuando abrir una operacion segun las condiciones del mercado
        '''
        pini = self.obtenerMaximo(T.openPos,T.ClosePos)
        pfin = i
        b = bh[pini:pfin].copy(deep=True)
        IsUpTrend = self.EvaluateTrend(b,OCV)
        if(volb[i] * tc['price'][i] >= OCV.volPriceOpen):
            '''
            if (s[i] > 0) & (s[i-1] < 0):
                if (sma03[i] > sma03[i-1]+ OCV.chOpen):
                    T.isOpen = True
                    T.sOpenCond = "MB UP 1"
                    T.OpeningTypeID = 1
            elif (s[i] < 0) & (s[i-1] > s[i-2] + OCV.mbOpen):
                T.isOpen = True
                T.sOpenCond = "MB UP 3"
                T.OpeningTypeID = 3
            elif (ch[i] > ch[i-1] + OCV.chOpen): 
                if (sma03[i] > sma03[i-1]+ OCV.chOpen):
                    T.isOpen = True
                    T.sOpenCond = "CH UP"
                    T.OpeningTypeID = 5
            '''
            if (s[i] > 0) & (s[i] > OCV.mbOpen):
                T.isOpen = True
                T.sOpenCond = "MB UP 2"
                T.OpeningTypeID = 2
            elif ((sma03[i-1] < sma12[i-1]) & (sma03[i] > sma12[i])): 
                if (sma03[i] > sma03[i-1]+ OCV.chOpen*1):
                    T.isOpen = True
                    T.sOpenCond = "SMA03 UP"
                    T.OpeningTypeID = 4
            elif (IsUpTrend == True):
                T.isOpen = True
                T.sOpenCond = "TREND UP"
                T.OpeningTypeID = 6
        return T
    
    def SetOpening(self, OCV, T, tc, s, cumch, deltaTargetCH, deltaStopLose, i, lastIdTrade):
        '''
        establese los valores en la  apertura de una operacion
        '''
        T.openPos = i
        T.idTrade = lastIdTrade + 1
        T.sDesc = '({0}) {1}'.format(T.idTrade, T.sOpenCond)
        T.inBase = False
        T.openTime = s.index[i].to_pydatetime()
        T.openingCH = cumch[i]
        T.baseCH = T.openingCH + self.deltabaseCH
        T.targetCH = T.openingCH + deltaTargetCH
        T.stopLoseCH = T.openingCH + deltaStopLose
        T.TotalLoseCH = T.openingCH - OCV.deltaTotalLoseCH
        
        T.openingP =  tc['price'][i]
        T.baseP = T.openingP * ((100+self.deltabaseCH)/100)
        T.targetP = T.openingP * ((100+deltaTargetCH)/100)
        T.stopLoseP = T.openingP * ((100+deltaStopLose)/100)
        T.TotalLoseP = T.openingP * ((100+OCV.deltaTotalLoseCH)/100)
        
        return T
        
    def EvaluateClosing(self, T, OCV, s, deltaStopLose, bh,  cumch, i):
        '''
        evalua cuando cerrar una operacion
        '''
        if bh.cum_change[i] >= T.baseCH: #nivel de perdidas operacionales superado
            T.inBase = True
        if T.inBase == True: 
            currentCumCH = cumch[i] -  T.openingCH
            T.maximo = self.obtenerMaximo(T.maximo,currentCumCH)
            
            T.maximoTolerado = self.CalcularMaximoTolerado(T,OCV, deltaStopLose)

            if (currentCumCH <= T.maximoTolerado):
                T.isOpen = False
                T.sCloseCond = "Maximo AT {0} %CH, Tolerado AT {1} %CH".format(round(T.maximo,2), round(T.maximoTolerado,2))
                T.ClosingTypeID = 1
            
            if cumch[i] <= (T.stopLoseCH): #cierre por stop lose
                T.isOpen = False
                T.sCloseCond = "STOP LOSE AT {0} %CH".format(round(deltaStopLose,2))
                T.ClosingTypeID = 2
            elif (i >= (T.openPos + OCV.waitPeriods*OCV.waitFactor)): #cierre por tiempo trascurrido sin logar objetivos
                T.isOpen = False
                T.sCloseCond = "elapsed {0} times without goals | IN BASE".format(OCV.waitPeriods*OCV.waitFactor)
                T.ClosingTypeID = 3
        
        else: #nivel de perdidas operacionales no se logro 
            if (s[i] <= 0) &(cumch[i] < T.TotalLoseCH): #cierre por perdida total
                T.isOpen = False
                T.sCloseCond = "TOTAL LOSE"
                T.ClosingTypeID = 4
            elif (i >= (T.openPos + OCV.waitPeriodsOutBase*OCV.waitFactorOutBase)): #cierre por tiempo trascurrido sin logar objetivos
                T.isOpen = False
                T.sCloseCond = "elapsed {0} times without goals | OUT BASE".format(OCV.waitPeriodsOutBase*OCV.waitFactorOutBase)
                T.ClosingTypeID = 5
        
        return T
    
    def SetClosing(self, T, s, bh, tc, i):
        '''
        establese los valores de cierre de una operacion
        '''
        T.sDesc = T.sDesc + ' | {0}'.format(T.sCloseCond)
        T.inBase = False
        T.closeTime = s.index[i].to_pydatetime()
        T.closingCH = bh.cum_change[i]
        T.closingP = tc['price'][i]
        T.ClosePos = i
        
        if T.openingCH >= T.closingCH:
            T.deltaCH = T.closingCH - T.openingCH
            T.deltaP = T.closingP - T.openingP
        else:
            T.deltaCH = T.closingCH - T.openingCH
            T.deltaP = T.closingP - T.openingP
        return T
        
    def CalcularMaximoTolerado(self, T, OCV, deltaStopLose):
        '''
        calcula la tolerancia para cierre en caso de caida desde el maximo alcansado desde la apertura de la operacion
        '''
        if (T.maximo < OCV.deltaCHObjetivo):
            if (T.maximo >= deltaStopLose) & (T.maximo < OCV.deltaCHObjetivo *0.25):  T.maximoTolerado = deltaStopLose    
            elif (T.maximo >= OCV.deltaCHObjetivo *0.25) & (T.maximo < OCV.deltaCHObjetivo *0.5): T.maximoTolerado = deltaStopLose + 1.2
            elif (T.maximo >= OCV.deltaCHObjetivo *0.5) & (T.maximo < OCV.deltaCHObjetivo *0.75): T.maximoTolerado = deltaStopLose + 4.5
            elif (T.maximo >= OCV.deltaCHObjetivo *0.75) & (T.maximo < OCV.deltaCHObjetivo): T.maximoTolerado = deltaStopLose + 6.5                    

        else:
            if (T.maximo >= OCV.deltaCHObjetivo) & (T.maximo < OCV.deltaCHObjetivo *1.25):        T.maximoTolerado = OCV.deltaCHObjetivo * 0.9
            elif (T.maximo >= OCV.deltaCHObjetivo *1.25) & (T.maximo < OCV.deltaCHObjetivo *1.5):  T.maximoTolerado = OCV.deltaCHObjetivo * 1.1
            elif (T.maximo >= OCV.deltaCHObjetivo *1.5)  & (T.maximo < OCV.deltaCHObjetivo *1.75): T.maximoTolerado = OCV.deltaCHObjetivo * 1.4      
            elif (T.maximo >= OCV.deltaCHObjetivo *1.75) & (T.maximo < OCV.deltaCHObjetivo *2):    T.maximoTolerado = OCV.deltaCHObjetivo * 1.6
            elif (T.maximo >= OCV.deltaCHObjetivo *2)    & (T.maximo < OCV.deltaCHObjetivo *2.5):  T.maximoTolerado = OCV.deltaCHObjetivo *1.8
            elif (T.maximo >= OCV.deltaCHObjetivo *2.5): T.maximoTolerado = OCV.deltaCHObjetivo *2.1
        return T.maximoTolerado
    
    def InsertOpenedTread(self, T, DBA):
        '''
        agrega una operacion cerrada a la lista de operacioens calculadas
        '''
        DBA.MytradesInsertOne(T)
        
    def UpdateClosedTread(self, T, DBA):
        '''
        actualiza una operacion cerrada a la lista de operacioens calculadas
        '''
        newTrade = [T.idTrade,T.openTime,T.closeTime,T.sDesc,T.OpeningTypeID,T.ClosingTypeID,T.openingCH,T.baseCH,T.targetCH,T.stopLoseCH, T.TotalLoseCH,T.closingCH,T.deltaCH, T.openingP,T.baseP,T.targetP,T.stopLoseP,T.TotalLoseP,T.closingP,T.deltaP, T.Profit, T.Profit_Gastos]              
        self.myTrades.loc[len(self.myTrades)] = newTrade
        self.myTrades['Profit'] = self.myTrades['deltaCH'].cumsum()
        self.myTrades['Profit_Gastos'] = self.restarGastos(self.myTrades['Profit'])

        T.Profit = self.myTrades['Profit'][len(self.myTrades)-1]
        T.Profit_Gastos = self.myTrades['Profit_Gastos'][len(self.myTrades)-1]

        DBA.MytradesUpdateOne(T)
    
    def SaveAllTrades(self, DBA):
        '''
        Persiste  todas las operaciones cerradas en la bbdd
        '''
        if (len(self.myTrades) > 0):
            self.myTrades['Profit'] = self.myTrades['deltaCH'].cumsum()
            self.myTrades['Profit_Gastos'] = self.restarGastos(self.myTrades['Profit'])
            self.myTrades.fillna(0,inplace=True)
            self.myTrades.to_sql(DBA.dbMyTradesTable,DBA.engine, if_exists='replace')

    def ReadLastTrade (self, s, DBA):
        '''
        devuelve el ultimo trade creado , 
        como objeto del tipo TradeValues
        '''
        oTrade = DBA.MyTradesReadLast() # returns type Mytrades
        
        T = TradeValues()
        if oTrade is not None:
            T.idTrade = oTrade.index 
            T.idTrade = oTrade.id 
            T.openTime = oTrade.openTime
            T.closeTime = oTrade.closeTime 
            T.sDesc = oTrade.tradeDescription
            T.OpeningTypeID = oTrade.OpeningTypeID
            T.ClosingTypeID = oTrade.ClosingTypeID 
            T.openingCH = oTrade.openingCH 
            T.baseCH = oTrade.baseCH 
            T.targetCH = oTrade.targetCH 
            T.stopLoseCH = oTrade.stopLoseCH
            T.TotalLoseCH = oTrade.TotalLoseCH 
            T.closingCH = oTrade.closingCH 
            T.deltaCH  = oTrade.deltaCH 
            T.openingP = oTrade.openingP 
            T.baseP = oTrade.baseP 
            T.targetP = oTrade.targetP 
            T.stopLoseP = oTrade.stopLoseP 
            T.TotalLoseP = oTrade.TotalLoseP 
            T.closingP = oTrade.closingP 
            T.deltaP = oTrade.deltaP 
            T.Profit = oTrade.Profit 
            T.Profit_Gastos = oTrade.Profit_Gastos 
            T.openPos = s.index.get_loc(str(T.openTime))        # indice del tiempo de apertura
            T.inBase = False                                    # flag operacion sobre gastos operacionales, el metodo EvaluateClosing lo valida y lo setea despues
            if T.closeTime <= T.openTime:                       # significa que no tiene fecha de cierre, y tomo el default 1900-01-01
                T.isOpen = True                                 # flag operacion abierta/cerrada
            else:
                T.isOpen = False 
                T.ClosePos = s.index.get_loc(str(T.closeTime))  # inidce del tiempo de cierre
        return T
