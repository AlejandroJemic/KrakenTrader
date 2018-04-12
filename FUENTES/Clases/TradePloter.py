"""
branch desde VerMarquetBalnce-sql-2.6.ipynb
    
    no es continuacion
    esta vercion no tiene el metodo OpenerCloserEvaluator
    
	implementea la clase TradePloter completamante funcional y encapsulada para todos los graficos
    este codigo es capas de leer completamentede desde bbdd y presentar los graficos
    sin realizar ningun calculo de apertura/cierre de posiciones
    
    prendiente:
        encasular los metodos de bbdd en una clase independiente
        encapsular calculo de entrada salida en una clase independiente que corra periodicamante online
        crear script mail con multitread que ejecute lectura de dados y calculo de operaciones online 
"""
# imports
import pandas as pd
import matplotlib.pyplot as plt
#%matplotlib inline
import time
from datetime import datetime, timedelta
from matplotlib import dates 
import IPython.core.debugger
dbg = IPython.core.debugger.Pdb()
#dbg.set_trace() #colocar dondo punto interrupcion
import matplotlib.dates as mdates
import matplotlib.ticker as mticker


class TradePloter:
    deltaBaseCH = 0.0
    plotmin = True
    HoursInterval = 1
    
    def __init__(self,deltaBaseCH, windowTime):
        self.deltaBaseCH = deltaBaseCH
        if windowTime > 6: self.plotmin = False

        if windowTime > 12:      self.HoursInterval = 2
        if windowTime > 24:      self.HoursInterval = 4
        if windowTime > 24 * 2:  self.HoursInterval = 8
        if windowTime > 24 * 5:  self.HoursInterval = 12
        if windowTime > 24 * 10: self.HoursInterval = 24
        if windowTime > 24 * 15: self.HoursInterval = 48
        if windowTime > 24 * 30: self.HoursInterval = 96

    # genera el grafico de prfit y Profit_Gastos
    def plotProfit(self,myTrades):
        print('Total Trades: {0}'.format(len(myTrades)))
        if len(myTrades) > 0:
            totalCom = len(myTrades) * self.deltaBaseCH
            totalWin = myTrades.deltaCH.sum()
            finalBalance = totalWin - totalCom
            print('total win: {0}, total commiciones: {1}, Balance Final {2}'.format( round(totalWin,1),round(totalCom,1),round(finalBalance)))    
            if len(myTrades) > 1:
                myTrades['Profit'].plot()   
                myTrades['Profit_Gastos'].plot()

    #genera el grafico dodne se ve toda la histporia y los momentos de apertura y cierra
    def plotHistory(self,BalanceHistory,myTrades,tradesCondensation , plotVolume=False, plotTrades=False):
        fig,ax = plt.subplots( sharex=True, figsize=(16,14), nrows=4, ncols=1)

        #plot price
        ax[0].plot_date(BalanceHistory.index, BalanceHistory['close'],'orange',marker='o', markersize=1)
        ax[0].yaxis.grid(True) 
        ax[0].xaxis.grid(True) 
        ax[0].xaxis.set_major_locator(dates.HourLocator(interval=self.HoursInterval)) 
        ax[0].xaxis.set_major_formatter(dates.DateFormatter('\n %d-%m %H'))
        if self.plotmin ==True:
            ax[0].xaxis.set_minor_locator(dates.MinuteLocator(interval=5))
            ax[0].xaxis.set_minor_formatter(dates.DateFormatter('%M'))
            ax[0].xaxis.grid(b=True, which='minor', color='grey', linestyle='--')

        ax[0].set_title('CLOSE')
        ax[0].legend(loc='best')

        #plot %CH short SMA Large SMA
        ax[1].plot_date(BalanceHistory.index, BalanceHistory['change'],'ro-', markersize=1)
        ax[1].plot_date(BalanceHistory.index, BalanceHistory['cum_change'],'b-')
        ax[1].plot_date(BalanceHistory.index, BalanceHistory['SMA03_cum_change'],'go-', markersize=1,alpha=0.6) #ligthBlue
        ax[1].yaxis.grid(True) 
        ax[1].xaxis.grid(True) 
        ax[1].xaxis.set_major_locator(dates.HourLocator(interval=self.HoursInterval)) 
        ax[1].xaxis.set_major_formatter(dates.DateFormatter('\n %d-%m %H'))
        if self.plotmin ==True:
            ax[1].xaxis.set_minor_locator(dates.MinuteLocator(interval=5))
            ax[1].xaxis.set_minor_formatter(dates.DateFormatter('%M'))
            ax[1].xaxis.grid(b=True, which='minor', color='grey', linestyle='--')

        ax[1].set_title('% CHANGE - CUMULATIVE CHANGE')
        ax[1].legend(loc='best')
        ax[1].axhline(0,color='g',ls='-')

        #plot  MarquetBalance
        ax[2].plot_date(BalanceHistory.index, BalanceHistory['volbuy'],'g--',alpha=0.5)
        ax[2].plot_date(BalanceHistory.index, BalanceHistory['volsell'],'r--',alpha=0.5) 
        #ax[2].plot_date(BalanceHistory.index, BalanceHistory['unbalance'],'bo-', markersize=3)
        ax[2].plot_date(BalanceHistory.index, BalanceHistory['EWM_unbalance'],'bo-', markersize=1)
        ax[2].plot_date(BalanceHistory.index, BalanceHistory['EWM_unbalance_N'],'ro-', markersize=1)

        ax[2].yaxis.grid(True) 
        ax[2].xaxis.grid(True) 
        ax[2].xaxis.set_major_locator(dates.HourLocator(interval=self.HoursInterval)) 
        ax[2].xaxis.set_major_formatter(dates.DateFormatter('\n %d-%m %H'))
        if self.plotmin ==True:
            ax[2].xaxis.set_minor_locator(dates.MinuteLocator(interval=5))
            ax[2].xaxis.set_minor_formatter(dates.DateFormatter('%M'))
            ax[2].xaxis.grid(b=True, which='minor', color='grey', linestyle='--')

        ax[2].set_title('volbuy - volsell- unbalance')
        ax[2].legend(loc='best')
        #ax[2].axhline(0,color='g',ls='-')

        # plot volumen
        if plotVolume == True:
            ax[3].plot_date(tradesCondensation.index, tradesCondensation['volb'],'g',marker='o', markersize=3)
            ax[3].plot_date(tradesCondensation.index, tradesCondensation['vols'],'r',marker='o', markersize=3)
            ax[3].yaxis.grid(True) 
            ax[3].xaxis.grid(True) 
            ax[3].xaxis.set_major_locator(dates.HourLocator(interval=self.HoursInterval)) 
            ax[3].xaxis.set_major_formatter(dates.DateFormatter('\n %d-%m %H'))
            if self.plotmin ==True:
                ax[3].xaxis.set_minor_locator(dates.MinuteLocator(interval=5))
                ax[3].xaxis.set_minor_formatter(dates.DateFormatter('%M'))
                ax[3].xaxis.grid(b=True, which='minor', color='grey', linestyle='--')

            ax[3].set_title('VOLUMEN POR PERIODO')
            ax[3].legend(loc='best')
            ax[3].axhline(0,color='g',ls='-')

        if plotTrades == True:
            cont = 1
            for d in  myTrades.openTime:        
                ax[1].annotate(cont , xy=(d,1))
                ax[0].axvline(d,ymin=-1.2,ymax=1,c="#05652F",linewidth=2,zorder=0, clip_on=False)
                ax[1].axvline(d,ymin=-1.2,ymax=1,c="#05652F",linewidth=2,zorder=0, clip_on=False)
                ax[2].axvline(d,ymin=-1.2,ymax=1,c="#05652F",linewidth=2,zorder=0, clip_on=False)
                ax[3].axvline(d,ymin=0,ymax=1,c="#05652F",linewidth=2,zorder=0, clip_on=False)
                cont += 1

            for d in myTrades.closeTime:
                ax[0].axvline(d,ymin=-1.2,ymax=1,c="#ffaa80",linewidth=2,zorder=0, clip_on=False)
                ax[1].axvline(d,ymin=-1.2,ymax=1,c="#ffaa80",linewidth=2,zorder=0, clip_on=False)
                ax[2].axvline(d,ymin=-1.2,ymax=1,c="#ffaa80",linewidth=2,zorder=0, clip_on=False)
                ax[3].axvline(d,ymin=0,ymax=1,c="#ffaa80",linewidth=2,zorder=0, clip_on=False)

    #genera el grafico de detalle de todas las operaciones            
    def plotAllTrades(self,BalanceHistory, myTrades):
        tradesCount = len(myTrades)
        if tradesCount > 0:
            fig, axes = plt.subplots(tradesCount, 2, figsize=(16,tradesCount*5), squeeze=False)
            for i in range(tradesCount):
                n = i+1
                row = axes[i]
                dOpen = myTrades.openTime[n]
                iniPos = BalanceHistory.index.get_loc(dOpen)-25
                iniMoment = BalanceHistory.index[iniPos] 

                sDesc = myTrades.tradeDescription[n]

                dClose = myTrades.closeTime[n]
                endPos = BalanceHistory.index.get_loc(dClose)+25
                maxPos  = len(BalanceHistory)
                if endPos >= maxPos:
                    endPos = maxPos-1

                endMoment = BalanceHistory.index[endPos] 

                df =  BalanceHistory[(BalanceHistory.index >= iniMoment) & (BalanceHistory.index <= endMoment)]

                #calcular %CH, %CH Acum , SMA %CH Acum
                #df['change'] = df['close'].pct_change(periods=1)*100
                #df['cum_change'] = df['change'].cumsum()
                #df['SMA03_cum_change'] = df['cum_change'].rolling(3).mean()
                #df['SMA12_cum_change'] = df['cum_change'].rolling(12).mean()
                self.plotTrade(row, df,dOpen, dClose, sDesc,myTrades.openingCH[n],myTrades.closingCH[n])
            fig.autofmt_xdate() 
            plt.legend() 
            plt.tight_layout() 
            plt.show()
        else:
            print('No trades for plot')

    #Genera el grafico de una operacion
    def plotTrade(self,ax, df, dOpen, dClose, sDesc, openCH,closeCH):
        intervalo = int(self.HoursInterval/4)
        if intervalo == 0: intervalo = 1
        locator = mdates.HourLocator(interval=intervalo)
        locator.MAXTICKS = 10000

        ax[0].plot_date(df.index, df['volbuy'],'g--',alpha=0.5)
        ax[0].plot_date(df.index, df['volsell'],'r--',alpha=0.5)
        ax[0].plot_date(df.index, df['unbalance'],'bo-', markersize=3)
        #ax[0].plot_date(df.index, df['EWM_unbalance'],'bo-', markersize=3)
        #ax[0].plot_date(df.index, df['EWM_unbalance_N'],'ro-', markersize=3)
        ax[0].axvline(dOpen,ymin=-0,ymax=1,c="#05652F",linewidth=2,zorder=0)
        ax[0].axvline(dClose,ymin=-0,ymax=1,c="#F44C04",linewidth=2,zorder=0)
        ax[0].yaxis.grid(True) 
        ax[0].xaxis.grid(True) 
        ax[0].xaxis.set_major_locator(locator)
        ax[0].xaxis.set_major_formatter(dates.DateFormatter('%d %H'))
        ax[0].yaxis.set_major_locator(mticker.AutoLocator())
        ax[0].xaxis.grid(b=True, which='mayor', color='grey', linestyle='--')
        ax[0].legend(loc='best')
        ax[0].axhline(0,color='g',ls='-')
        ax[0].set_title(sDesc)

        ax[1].plot_date(df.index, df['cum_change']- openCH,'b-')
        ax[1].plot_date(df.index, df['SMA03_cum_change']- openCH,'go-', markersize=2,alpha=0.8)
        ax[1].plot_date(df.index, df['SMA12_cum_change'] - openCH,'o-',color='#3366ff', markersize=2,alpha=0.8) #ligthBlue
        ax[1].axvline(dOpen,ymin=-0,ymax=1,c="#05652F",linewidth=2,zorder=0)
        ax[1].axvline(dClose,ymin=-0,ymax=1,c="#F44C04",linewidth=2,zorder=0)

        ax[1].axhline(openCH - openCH,xmin=-0,xmax=1,c="#05652F",linewidth=2,zorder=0)
        ax[1].axhline(closeCH - openCH,xmin=-0,xmax=1,c="#F44C04",linewidth=2,zorder=0)

        ax[1].yaxis.grid(True) 
        ax[1].xaxis.grid(True) 
        ax[1].xaxis.set_major_locator(locator)
        ax[1].xaxis.set_major_formatter(dates.DateFormatter('%d %H'))
        ax[1].yaxis.set_major_locator(mticker.AutoLocator())
        ax[1].xaxis.grid(b=True, which='mayor', color='grey', linestyle='--')
        ax[1].legend(loc='best')
        ax[1].axhline(0,color='b',ls='-')