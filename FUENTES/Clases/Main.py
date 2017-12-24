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
        startTime = datetime.now()
        try:
            Lock.acquire()
            LogEvent('')
            LogEvent('Evaluacion Inicio at ' + str(startTime))
            DBA.EndSampleTime = datetime.now()
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
        LogEvent('elapsed {0} sec'.format(PassTime(startTime, lapTime)))

def Main():
    try:
        DBA = DBAdapter()
        DBA.CreateAllTables()
        threads = list()
        LogEvent('inicio main')
        tCM = threading.Thread(target=WorkerConsultarMarquet, name='ConsultarMarquetBalance')
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
