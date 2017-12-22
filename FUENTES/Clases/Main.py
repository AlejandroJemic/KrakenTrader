from TradeEvaluator import TradeEvaluator
from DBAdapter import DBAdapter
from datetime import datetime, timedelta
import time
import sys
from Utils import *
from ConsultarMarquetBalance_sql import ConultarOnline
from  threading import *

def WorkerConsultarMarquet():
	ConultarOnline()

def WorkerTradeEvaluator():
    Lock = threading.Lock()
    espera = 60
    TE = TradeEvaluator()
    DBA = DBAdapter()
    DBA.CreateAllTables()
    while True:
        startTime = datetime.now()
        try:
            BalanceHistory = DBA.ReadBalanceHistory()
            TradesCondensation = DBA.ReadCondensatedTrades()
            LogEvent('')
            LogEvent('Evaluacion Inicio')
            Lock.acquire()
            sAction , iAction = TE.OpenerCloserEvaluatorOnLine (BalanceHistory, TradesCondensation, DBA)
            Lock.release()
            LogEvent(sAction)
            LogEvent('Evaluacion FIN. ')
        except:
            LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]),True)
            time.sleep(5)
            LogEvent('waiting 5s...')
            continue
        
        lapTime = datetime.now()
        LogEvent('waitng  60s...')
        t = espera -PassTime(startTime, lapTime)
        if t > 0:
            time.sleep(espera -PassTime(startTime, lapTime))
        lapTime = datetime.now()
        LogEvent('elapsed {0} sec'.format(PassTime(startTime, lapTime)))


def Main():
    threads = list()
    LogEvent('inicio main')
    tCM = threading.Thread(target=WorkerConsultarMarquet, name='ConsultarMarquetBalance')
    threads.append(tCM)
    tCM.start()
    tTE = threading.Thread(target=WorkerTradeEvaluator, name='TradeEvaluator')
    threads.append(tTE)
    tTE.start()

if __name__ == '__main__':
    Main()
