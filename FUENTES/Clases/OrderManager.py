'''
OrderManager_1.0.py
aun no funcional

v 1.0

este modulo se ocupa de registrar ordenes en la bbdd local
aguardar o solicitar confirmacion de estado de una orden
seguir el estado de una orden

============================================================
funcionalidades:
============================================================
considerar flag de interrumpion envio de ordenes al gente, ( no enviar mas compras, no enviar mas ventas independientes)
enviar orden de compra (market, limit, date limit)
enviar orden de stoplost (market)
enviar orden de totallost (market)
enviar orden de venta (market, limit, date limit)
enviar cancelacion de orden

cancelacionde emergencia de una o todas las ordenes ( por agente y criptomoneda, general)

consultar estado de ordenes al agente

si una orden es cancelada , se debe actualizar el estado del trade corespondiente segun coresponde

cuando la operacion entre en BASE, deve:
	enviar y confirmar la cancelacion de la orden de TOTALLOST
	enviar y confirmar la aplicacion de una nueva orden de STOPLOST

segurir estado de ordenes enviadas y validar si fueron aplicasas por el agente

Llebar un historial del estado y flujo de una orden, debe contener, el texto envioado al aajente y la respuesta del mismo.

reportar estado de ordenes enviadas, pendientes, ejecutadas, canceladas, por medio de mails
entergar links de acciones alternatibas de ordenes segun el estado y sus alternativas

reevaluar si coresponde enviar, reenviar, anular localmente, o solicita rla cancelacion una orden  al agente


============================================================
las ordenes pueden tener los siguintes estados
============================================================
IdEstadoOrden: 
estados 1D, la orden permanece local
10:   orden ingresada local, (aun no informada al ajente)
11:   orden pausada( orden se considera valida pero por algun motivo se decidio no enviarla al agente, requiere confirmacion para envio)
12:   orden descartada (anulada, nunca se envio al agente)
13:   orden cancelada localmente, se evaluo cancelar la orden(manualmente o por el sistema), aun no fue enviada al ajente

estados 2D, la orden se envio al agente
20:	  orden enviada al ajente (aun no confirmada)
21:   orgente reciovio orden ok, pendiente de ejecucion (puede ser limit o market)
22:   ajete  recivio orden OK, e indico que la orden se ejecuto
23:	  ajete  recivio orden OK, e indico que la orden se ejecutara al darse las condiciones, ej. stoplost o compra/venta a precio limite o fecha llimite

24:   se envio una consulta de ordenes al agente, para confirmar el estado de alguna orden enviada
25:   ORDEN EJECUTADA CON EXITO Y CONFIRMADA por medio de una consulta adicional al agente

26:   se envio una cancelacion de orden al ajente, pero aun no se a confirmado se se cancelo en el broker
27:   agente  recivio cancelacion de orden  OK, e indico que la orden se ejecuto

28:   se envio una consulta de ordenes al agente, para confirmar el estado de la cancelacion de una orden orden enviada
29:   CONCELACION DE ORDEN EJECUTADA CON EXITO Y CONFIRMADA por medio de una consulta adicional al agente

estados 3D, algun tipo de error
30:	  error durante el envio de una orden al agente, se deconose si fue recivida o no, 
         se recomienda enviar una consulta para validar el estado de la orden
         implica reenviar si es viable y corresponde
31:	  agente reporto error al recivir orden,la orden no se cursara, implica reenviar si es viable o coresponde
32:   agente reporto error al intentar ejecutar la orden, orden no cursada, se desconose si se ejecutara enventuamente,
        se recomienda solicitar una cancelacion de orden, evaluar si es viable y corresponde reenviarla

33:   ERROR DURANTE EL ENVIO DE UNA CANCELACION DE ORDEN , se deconose si fue resivida y cancelada por el agente o no.
			se recomienda envia run aconsulta del estado de la orden inicial , y resolicita rla canselacio si es necesario
34:   AGENTE REPORTO ERROR DURANTE EL PEDIDO DE CANCELACION DE UNA ORDEN. 
			se recomienda enviar un aconsulta del estado de la orden inicial , y resolicita rla canselacio si es necesario

39:   error generico en ejecucion de la orden, puede se en cualquier etapa

'''

# ================================================================================================================
# class OrderValues
# ================================================================================================================
class OrderValues:
	
	idTrade               = 0                             # Integer      # Id del trade al que coresponden
	idOrder               = 0                             # Integer      # Id local de la orden 
	OrderTime             = datetime(1900, 1, 1, 0, 0, 0) # DateTime     # fecha hora de ingreso al sistema
	AgentCode             = 'KRAKEN'                      # String       # agente al que coresponden
	CoinCode              = 'XBT'                         # String       # cryptomoneda a la que coresponden
	ClosingPrice          = 0.0                           # Float        # precio considerado en el envio
	Vol                   =  0.0                          # Float        # volumen en la moneda de la orden
	PriceVolValue         = 0.0                           # Float        # valor  CALCULADO orden(precio crypto/USD * volumen a ejecurar, segun el precio considerado)
	ComisionPersent       = 0.0                           # Float        # % comicion calculado
	ComisionAmount        = 0.0                           # Float        # USD comicion calculada
	idOrderAgent          = ""                            # String       # Id asignado por el agente 
	OrderTimeAgent        = datetime(1900, 1, 1, 0, 0, 0) # DateTime     # fecha hora de confirmacion
	ClosingPriceAgent     = 0.0                           # Float        # precio confirmado por el agente al cual se ejecuto
	VolAgent              = 0.0                           # Float        # volumen ejecutado por el agente
	PriceVolValueAgent    = 0.0                           # Float        # valor  EJECUTADO orden(precio crypto/USD ejc * volumen a ejecutado, segun el precio informado por el egente)
	ComisionPersent       = 0.0                           # Float        # % comicion  informado
	ComisionAmountAgent   = 0.0                           # Float        # USD comicion informado
	SpreadComisionPersent = 0.0                           # Float        # spread % comicion
	SpreadComisionAmount  = 0.0                           # Float        # spread USD ajecucion
	SpreadPriceVolValue   = 0.0                           # Float        # spread valor calculado - Valor Ejcuctado
	DelayTime             = datetime(1900, 1, 1, 0, 0, 0) # DateTime     # deley ejecucion (en segundos) 
	IsConditional         = 0                             # Integer      # flag es inmediata o condicional
	OrderType             = 0                             # Integer      # tipo de orden: compra market, compra limit/datelimit , venta, market, venta limit/datelimit , stoplost, totallost, salvarganancia, 
	OrderState            = 0                             # Integer      # estado de la orden
	PrevState             = 0                             # Integer      # estado anterior
	OrderStateTime        = datetime(1900, 1, 1, 0, 0, 0) # DateTime     # fecha ultimo estado
	PrevStateTime         = datetime(1900, 1, 1, 0, 0, 0) # DateTime     # fecha estado anterior
	CancelationTime       = datetime(1900, 1, 1, 0, 0, 0) # DateTime     # fecha hora de cancelacion de la orden
	CancelationDesc       = datetime(1900, 1, 1, 0, 0, 0) # DateTime     # motivo de cancelacion descriptivo

# ================================================================================================================
# class OrderHistoryValues
# ================================================================================================================
class OrderHistoryValues:
	idTrade           = 0                             # Integer  # Id del trade al que coresponde
	idOrder           = 0                             # Integer  # Id local de la orden 
	idOrderAgent      = ''                            # String   # id asignado por el agente ( si existe)
	AgentCode         = 'KRAKEN'                      # String   # Broker corespondiente
	CoinCode          = 'XBT'                         # String   # Cryptomoneda
	OrderState        = 0                             # Integer  # id estado
	OrderStateTime    = datetime(1900, 1, 1, 0, 0, 0) # DateTime # fecha hora del ultimo estado
	PrevState         = 0                             # Integer  # id estado anterior
	PrevStateTime     = datetime(1900, 1, 1, 0, 0, 0) # DateTime # fecha ora estado anterior
	StateChangeMotive = ''                            # String   # motivo del cambio de estado
	SentJson          = 0.0                           # Float    # json enviado
	ResivedJson       = 0.0                           # Float    # json recivido

# ================================================================================================================
# class OrderManager
# ================================================================================================================

from AgentManagers import *
from Utils import *


 class OrderManager:
 	SendOrdersEnabled = True # hablita o deshabilita el envio general de ordenes
 	AgentOrderManager = None # instancia del ordersManager corespondiente al agente

def __init__(self, pAgentCode):
	if pAgentCode == 'KRAKEN':
		self.SendOrdersEnabled = True
		self.AgentOrderManager = KRAKENOrderManager(self.SendOrdersEnabled) # TO-DO: SE DEBE HACER DINAICO CUANDO SE INCORPOREN NUEVOS AGENTES
		self.AgentCode         = self.AgentOrderManager.AgentCode

# considerar flag de interrumpion envio de ordenes al gente, ( no enviar mas compras, no enviar mas ventas independientes)
def HabilitarEnvioOrdenes(pHabilitar = True):
	self.SendOrdersEnabled = pHabilitar

def EnviarOrden(self, OrderType):
	if self.SendOrdersEnabled == True:
		self.AgentOrderManager.EnviarOrden(OrderType)
    	raise NotImplementedError("To be implemented")
    return True


# enviar orden de compra (market, limit, date limit)
# enviar orden de stoplost (market)
# enviar orden de totallost (market)
# enviar orden de venta (market, limit, date limit)
# enviar cancelacion de orden
# cancelacionde emergencia de una o todas las ordenes ( por agente y criptomoneda, general)
# consultar estado de ordenes al agente
# si una orden es cancelada , se debe actualizar el estado del trade corespondiente segun coresponde
# cuando la operacion entre en BASE, deve:
# 	enviar y confirmar la cancelacion de la orden de TOTALLOST
# 	enviar y confirmar la aplicacion de una nueva orden de STOPLOST
# segurir estado de ordenes enviadas y validar si fueron aplicasas por el agente
# Llebar un historial del estado y flujo de una orden, debe contener, el texto envioado al aajente y la respuesta del mismo.
# reportar estado de ordenes enviadas, pendientes, ejecutadas, canceladas, por medio de mails
# entergar links de acciones alternatibas de ordenes segun el estado y sus alternativas
# reevaluar si coresponde enviar, reenviar, anular localmente, o solicita rla cancelacion una orden  al agente