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
    while True:
        while not Lock.acquire():
            LogEvent('[TradeEvaluator]: No se puede bloquear. Waitng  1s...') 
            time.sleep(1)
        LogEvent('[TradeEvaluator]: Bloqueando')
        startTime = datetime.now()
        try:
            LogEvent('Evaluacion Inicio at ' + str(startTime))
            DBA.EndSampleTime = startTime
            Balance = DBA.ReadBalanceHistory()
            Condensation = DBA.ReadCondensatedTrades()
            sAction , iAction = TE.OpenerCloserEvaluatorOnLine (Balance, Condensation, DBA)
            LogEvent(sAction)
            LogEvent('Evaluacion FIN. ')
            Lock.release()
        except:
            LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]),True)
            LogEvent('waiting 5s...')
            Lock.release()
            time.sleep(5)
            continue
        lapTime = datetime.now()
        LogEvent('waitng  60s...')
        t = espera -PassTime(startTime, lapTime)
        if t > 0:
            time.sleep(espera -PassTime(startTime, lapTime))
        lapTime = datetime.now()
        LogEvent('')
        LogEvent('elapsed {0} sec'.format(PassTime(startTime, lapTime)))

def Main():
    try:
        DBA = DBAdapter()
        DBA.CreateAllTables()
        threads = list()
        LogEvent('Inicio Main')
        tCM = threading.Thread(target=WorkerConsultarMarquet, name='ConsultarMarketBalance')
        threads.append(tCM)
        tCM.start()
        tTE = threading.Thread(target=WorkerTradeEvaluator, name='TradeEvaluator')
        threads.append(tTE)
        tTE.start()
    except:
        LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]),True)
        raise

if __name__ == '__main__':
    Main()
