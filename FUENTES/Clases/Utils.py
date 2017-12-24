
import logging
import traceback
import threading
import sys

logging.basicConfig(filename="../../LOGs/LogEventos.log", level=logging.DEBUG)

def LogEvent(msg,isError = False):
    msg = '[' + threading.currentThread().getName() + ']: ' + msg 
    if isError == True:
        logging.error(msg, exc_info=True)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        print(''.join(line for line in lines))
    else:
        print(msg)
        logging.info(msg)


def PassTime(d1, d2):
    #d1 = datetime.strptime(d1, "%Y-%m-%d %H:%M:%S")
    #d2 = datetime.strptime(d2, "%Y-%m-%d %H:%M:%S")
    return abs((d2 - d1).seconds)


def LogObjectValues(obj, msg=''):
    for attr, value in obj.__dict__.iteritems():
        LogEvent(msg)
        LogEvent( '{a}:    {v}'.format(str(sattr), str(value)))