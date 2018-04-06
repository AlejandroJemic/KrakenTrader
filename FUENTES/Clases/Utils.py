
import logging
import traceback
import threading
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

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


def SendMail(SUBJECT, msg, BODY):
    """envio mails con el smpt gratuito de gmail por tls"""

    # Credentials (if needed) for sending the mail
    TO = 'a.jemic@gmail.com'
    FROM ='a.jemic@gmail.com'
    password = "cuarzo-777"
    # Create message container - the correct MIME type is multipart/alternative here!
    MESSAGE = MIMEMultipart('alternative')
    MESSAGE['subject'] = SUBJECT
    MESSAGE['To'] = TO
    MESSAGE['From'] = FROM
    MESSAGE.preamble = """mail enviado por Kraken_Trader_bot"""
    # Record the MIME type text/html.
    text_body = MIMEText(msg, 'text')
    HTML_BODY = MIMEText(BODY, 'html')
    
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    MESSAGE.attach(text_body)
    MESSAGE.attach(HTML_BODY)
    # The actual sending of the e-mail
    server = smtplib.SMTP('smtp.gmail.com:587')
    # Print debugging output when testing
    if __name__ == "__main__":
        server.set_debuglevel(1)
    server.starttls()
    server.login(FROM,password)
    server.sendmail(FROM, [TO], MESSAGE.as_string())
    server.quit()


def SendOrderMail(obj, subject='KRAKEN BOT', h3='ORDEN EJECUTADA', P='SE HA EJECUTADO LA SUIGUIENTE ORDEN'):
    try:
        BODY = GetHTMLMail(obj, h3, P)
        SendMail(subject, h3, BODY)
    except:
         LogEvent("Email error: {0}".format(sys.exc_info()[0]),True)

def GetHTMLMail(obj, h3='', P=''):
    '''lee plantilla mail y retorna el html con formatpo y contenido del obj en una tabla'''
    f = open("../Templates/mail_template.html","r")
    html = f.read()
    html = html.replace('<<MENSAGE>>',h3)
    html = html.replace('<<P>>',P)
    html = html.replace('<<HREF>>','https://www.tradingview.com/chart/W9VPDAJI/') #TO-DO: LINK DEBE HACERSE DINAMICO CUANDO SE INCORPOREN OTRAS MONEDAS
    html = html.replace('<<TABLA>>',HTMLObjectValues(obj))
    return html

def HTMLObjectValues(obj):  
    '''genera el contenido html de la tabla a partir de un obj'''   
    lineas = list()
    nl = '\n'
    for attr, value in obj.__dict__.items():
        if not attr.startswith('_'):
            lineas.append('<tr>' + nl)
            lineas.append('<td>{0}</td><td>{1}</td>'.format(str(attr), str(value)) + nl)
            lineas.append('<tr>'+ nl)
    return ''.join(lineas)

def LogObjectValues(obj, h3=''):
    '''registra en el log el contenido de un objeto y un mensaje descrptivo'''
    LogEvent(h3)
    for attr, value in obj.__dict__.items():
        if not attr.startswith('_'):
            LogEvent( '{0}: {1}'.format(str(attr), str(value)))

def SetupLogsFolder(folder):
    '''establese arl directorio de logs por defecto'''
    if not os.path.exists(folder):
        os.makedirs(folder)
    