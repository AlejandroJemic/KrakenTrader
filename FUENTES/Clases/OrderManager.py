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
10:   orden ingresada local, (aun no informada al agente)
11:   orden pausada( orden se considera valida pero por algun motivo se decidio no enviarla al agente, requiere confirmacion para envio)
12:   orden descartada (anulada, nunca se envio al agente)
13:   orden cancelada localmente, se evaluo cancelar la orden(manualmente o por el sistema), aun no fue enviada al ajente

estados 2D, la orden se envio al agente
20:      orden enviada al ajente (aun no confirmada)
21:   orgente reciovio orden ok, pendiente de ejecucion (puede ser limit o market)
22:   ajete  recivio orden OK, e indico que la orden se ejecuto
23:      ajete  recivio orden OK, e indico que la orden se ejecutara al darse las condiciones, ej. stoplost o compra/venta a precio limite o fecha llimite

24:   se envio una consulta de ordenes al agente, para confirmar el estado de alguna orden enviada
25:   ORDEN EJECUTADA CON EXITO Y CONFIRMADA por medio de una consulta adicional al agente

26:   se envio una cancelacion de orden al ajente, pero aun no se a confirmado se se cancelo en el broker
27:   agente  recivio cancelacion de orden  OK, e indico que la orden se ejecuto

28:   se envio una consulta de ordenes al agente, para confirmar el estado de la cancelacion de una orden orden enviada
29:   CONCELACION DE ORDEN EJECUTADA CON EXITO Y CONFIRMADA por medio de una consulta adicional al agente

estados 3D, algun tipo de error
30:      error durante el envio de una orden al agente, se deconose si fue recivida o no,
         se recomienda enviar una consulta para validar el estado de la orden
         implica reenviar si es viable y corresponde
31:      agente reporto error al recivir orden,la orden no se cursara, implica reenviar si es viable o coresponde
32:   agente reporto error al intentar ejecutar la orden, orden no cursada, se desconose si se ejecutara enventuamente,
        se recomienda solicitar una cancelacion de orden, evaluar si es viable y corresponde reenviarla

33:   ERROR DURANTE EL ENVIO DE UNA CANCELACION DE ORDEN , se deconose si fue resivida y cancelada por el agente o no.
            se recomienda envia run aconsulta del estado de la orden inicial , y resolicita rla canselacio si es necesario
34:   AGENTE REPORTO ERROR DURANTE EL PEDIDO DE CANCELACION DE UNA ORDEN.
            se recomienda enviar un aconsulta del estado de la orden inicial , y resolicita rla canselacio si es necesario

39:   error generico en ejecucion de la orden, puede se en cualquier etapa

'''
from DTO import *
from DBAdapter import *
from TradeEvaluator import *
from Utils import *
import sys

minDate = datetime(1900, 1, 1, 0, 0, 0)

# ================================================================================================================
# class OrderValues
# representa los valores de una orden que esta siendo gestionada
# ================================================================================================================
class OrderValues:

    idTrade               = 0                             # Integer      # Id del trade al que coresponden
    idOrder               = 0                             # Integer      # Id local de la orden
    OrderTime             = minDate                       # DateTime     # fecha hora de ingreso al sistema
    AgentCode             = 'KRAKEN'                      # String       # agente al que coresponden
    PairCode              = 'XXBTZUSD'                    # String       # cryptomoneda a la que coresponden
    Price                 = 0.0                           # Float        # precio considerado en el envio
    Vol                   = 0.0                           # Float        # volumen en la moneda de la orden
    PriceVolValue         = 0.0                           # Float        # valor  CALCULADO orden(precio crypto/USD * volumen a ejecurar, segun el precio considerado)
    ComisionPersent       = 0.0                           # Float        # % comicion calculado
    ComisionAmount        = 0.0                           # Float        # USD comicion calculada
    idOrderAgent          = ""                            # String       # Id asignado por el agente
    OrderTimeAgent        = minDate                       # DateTime     # fecha hora de confirmacion
    PriceAgent            = 0.0                           # Float        # precio confirmado por el agente al cual se ejecuto
    VolAgent              = 0.0                           # Float        # volumen ejecutado por el agente
    PriceVolValueAgent    = 0.0                           # Float        # valor  EJECUTADO orden(precio crypto/USD ejc * volumen a ejecutado, segun el precio informado por el egente)
    ComisionPersent       = 0.0                           # Float        # % comicion  informado
    ComisionAmountAgent   = 0.0                           # Float        # USD comicion informado
    SpreadComisionPersent = 0.0                           # Float        # spread % comicion
    SpreadComisionAmount  = 0.0                           # Float        # spread USD ajecucion
    SpreadPriceVolValue   = 0.0                           # Float        # spread valor calculado - Valor Ejcuctado
    DelayTime             = 0                             # DateTime     # deley ejecucion (en segundos)
    IsConditional         = 0                             # Integer      # flag es inmediata o condicional
    OrderType             = 0                             # Integer      # tipo de orden: 1 compra market, 2 compra limit , 3 venta market, 4 venta limit , 5 stoplost, 6 totallost
    OrderState            = 0                             # Integer      # estado de la orden
    PrevState             = 0                             # Integer      # estado anterior
    OrderStateTime        = minDate                       # DateTime     # fecha ultimo estado
    PrevStateTime         = minDate                       # DateTime     # fecha estado anterior
    CancelationTime       = minDate                       # DateTime     # fecha hora de cancelacion de la orden
    CancelationDesc       = minDate                       # DateTime     # motivo de cancelacion descriptivo

# ================================================================================================================
# class OrderHistoryValues
# representa los valores de la hystoria de una orden
# para la historia completa se requere una lista
# ================================================================================================================
class OrderHistoryValues:
    idTrade           = 0                             # Integer  # Id del trade al que coresponde
    idOrder           = 0                             # Integer  # Id local de la orden
    idOrderAgent      = ''                            # String   # id asignado por el agente ( si existe)
    AgentCode         = 'KRAKEN'                      # String   # Broker corespondiente
    PairCode          = 'XXBTZUSD'                    # String   # Cryptomoneda
    OrderState        = 0                             # Integer  # id estado
    OrderStateTime    = minDate                       # DateTime # fecha hora del ultimo estado
    PrevState         = 0                             # Integer  # id estado anterior
    PrevStateTime     = minDate                       # DateTime # fecha ora estado anterior
    StateChangeMotive = ''                            # String   # motivo del cambio de estado
    SentJson          = 0.0                           # Float    # json enviado
    ResivedJson       = 0.0                           # Float    # json recivido

# ================================================================================================================
# class OrderManager
# ================================================================================================================



class OrderManager:
    SendOrdersEnabled = True # hablita o deshabilita el envio general de ordenes
    AgentOrderManager = None # instancia del ordersManager corespondiente al agente

    lastOrden = 0

    def __init__(self, pAgentCode='KRAKEN'):
        if pAgentCode == 'KRAKEN':
            self.SendOrdersEnabled = True
            self.AgentOrderManager = KRAKENOrderManager(self.SendOrdersEnabled) # TO-DO: SE DEBE HACER DINAICO CUANDO SE INCORPOREN NUEVOS AGENTES
            self.AgentCode         = self.AgentOrderManager.AgentCode


    def HabilitarEnvioOrdenes(pHabilitar=True):
        # considerar flag de interrumpion envio de ordenes al gente, ( no enviar mas compras, no enviar mas ventas independientes)
        self.SendOrdersEnabled = pHabilitar


    def ReadLastTrade(self, DBA):
        # leer el ultimo trade generado
        # DBA = DBAdapter()
        oTrade = None
        try:
            oTrade = DBA.MyTradesReadLast() # returns type Mytrades
        except:
            LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]), True)
        return oTrade


    def OrdersReadForTrade(self, idTRade, DBA):
        # leer las ordenes asociadas a un trade (debuelve una lista de ordenes)
        # DBA = DBAdapter()|
        oOrder = None
        try:
            oOrder = DBA.OrdersReadForTrade(idTRade) # returns type DTO.Orders list (many rows in bbdd)
        except:
            LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]), True)
        return oOrder


    def OrdersReadLastForTrade(self, idTRade, DBA):
        # leer la ultima orden asociadas a un trade (debuelve la ultima orden creada para el trade)
        # DBA = DBAdapter()
        oOrder = None
        try:
            oOrder = DBA.OrdersReadLastForTrade(idTRade) # returns type DTO.Orders  (1 row in bbdd)
        except:
            LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]), True)
        return oOrder


# ======================================================================================================================================

    def OrdersInsertOne(self, oMytrade, DBA, pEstadoOrden, pTipoOrden):
        # Inserta UnaOrden en bbdd en el estado inicial del flujo

        # DBA = DBAdapter()
        oOrderValues = OrderValues()
        oOrderValues.idTrade               = oMytrade.id
        oOrderValues.idOrder               = self.lastOrden + 1
        oOrderValues.OrderTime             = oMytrade.OrderTime
        # default oOrderValues.AgentCode   = oMytrade.AgentCode
        # default oOrderValues.PairCode    = oMytrade.PairCode
        oOrderValues.Price                 = oMytrade.openingP
        oOrderValues.Vol                   = oMytrade.Vol
        oOrderValues.PriceVolValue         = oMytrade.PriceVolValue
        oOrderValues.ComisionPersent       = TradeEvaluator.TradeEvaluator.comCompra + TradeEvaluator.TradeEvaluator.spreadEntrada
        oOrderValues.ComisionAmount        = oOrderValues.Price * oOrderValues.ComisionPersent

        oOrderValues.PriceAgent            = 0
        oOrderValues.VolAgent              = 0
        oOrderValues.PriceVolValueAgent    = 0
        oOrderValues.ComisionPersent       = 0
        oOrderValues.ComisionAmountAgent   = 0
        oOrderValues.SpreadComisionPersent = 0
        oOrderValues.SpreadComisionAmount  = 0
        oOrderValues.SpreadPriceVolValue   = 0
        oOrderValues.DelayTime             = 0
        oOrderValues.IsConditional         = False

        oOrderValues.OrderType             = pTipoOrden # tipo de orden: 1 compra market, 2 compra limit , 3 venta market, 4 venta limit , 5 stoplost, 6 totallost
        oOrderValues.OrderState            = pEstadoOrden
        oOrderValues.PrevState             = None
        oOrderValues.OrderStateTime        = datetime.now()
        oOrderValues.PrevStateTime         = None

        oOrder = Orders(oOrderValues)
        try:
            DBA.OrdersInsertOne(oOrder) # returns type DTO.Orders  (1 row in bbdd)
            LogEvent('Orden Grabada en BBDD')
        except:
            LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]), True)
        return

# ========================================================================================================================================

    def EnviarOrden(self, OrderType):
        # envia una orden generica al agente instanciado
        if self.SendOrdersEnabled is True:
            self.AgentOrderManager.EnviarOrden(OrderType)
            raise NotImplementedError("To be implemented")
        return False

# enviar orden de compra (market, limit, date limit)
# enviar orden de stoplost (market) (cancelar orden de totallost)
# enviar orden de totallost (market)
# enviar orden de venta (market, limit, date limit)
# enviar cancelacion de orden
# cancelacionde emergencia de una o todas las ordenes ( por agente y criptomoneda, general)
# consultar estado de ordenes al agente
# si una orden es cancelada , se debe actualizar el estado del trade corespondiente segun coresponde
# cuando la operacion entre en BASE, deve:
#     enviar y confirmar la cancelacion de la orden de TOTALLOST
#     enviar y confirmar la aplicacion de una nueva orden de STOPLOST
# segurir estado de ordenes enviadas y validar si fueron aplicasas por el agente
# Llebar un historial del estado y flujo de una orden, debe contener, el texto envioado al aajente y la respuesta del mismo.
# reportar estado de ordenes enviadas, pendientes, ejecutadas, canceladas, por medio de mails
# entergar links de acciones alternatibas de ordenes segun el estado y sus alternativas


    def GestionarOrdenes(self, DBA):
        # EVALUAR, reevaluar si coresponde enviar, reenviar, anular localmente, o solicitar la cancelacion una orden  al agente
        # gestiona el workFlow de las ordenes para los trades en curso
        try:
            oMytrade = self.ReadLastTrade(DBA)
            if oMytrade is None:
                LogEvent('Sin trades para gestionar ordenes. FIN')
                return
            else:
                LogEvent('Find last trade: ' + str(oMytrade.id))
                oOrders = self.OrdersReadForTrade(oMytrade.id, DBA)
                if oMytrade.closeTime == minDate: # trade abierto
                    if len(oOrders) == 0:
                        LogEvent('Sin Ordenes')
                        # insert Orden
                        OrdersInsertOne(oMytrade, DBA, pEstadoOrden=10, pTipoOrden=1)
                    else:
                        LogEvent('Existen Ordenes')
                        for Orden in oOrders:
                            if Orden.OrderType in [1, 2]: # tipo de orden: 1 compra market, 2 compra limit , 3 venta market, 4 venta limit , 5 stoplost, 6 totallost
                                LogEvent('Encontrada Orden de compra nro: {0}'.format(Orden.idOrder))
                                Estdo = EvaluarFlujoOrden(DBA, Orden)
                                if Orden.OrderState == 25:
                                    LogEvent('confirmada Orden de Compra')
                                    # si orden confirmada
                                    # revisar existe orden stoplost
                                    # si no esxiste insertar
                            elif Orden.OrderType in [5, 6]: # tipo de orden: 1 compra market, 2 compra limit , 3 venta market, 4 venta limit , 5 stoplost, 6 totallost
                                LogEvent('Encontrada Orden de stoplost nro: {0}'.format(Orden.idOrder))
                                Estdo = EvaluarFlujoOrden(DBA, Orden)
                                if Orden.OrderState == 25:
                                    LogEvent('confirmada Orden de stoplost')
                else: # EL TRADE ESTA CERRADO
                    a = 1
        except:
            LogEvent("Unexpected error: {0}".format(sys.exc_info()[0]), True)


    def EvaluarFlujoOrden(self, DBA, Orden):
        while Orden.OrderState not in [25, 29]:
            if Orden.OrderState    == 10: # orden ingresada local, (aun no informada al agente)
                a = 1
                # enviar orden
                # actualizar orden si ese tiene los datos
                # agregar historia orden si envio ok
            if Orden.OrderState in [11, 12]: # orden pausada, orden descartada
                a = 1
                # no hacer nada, dejar pasar
            if Orden.OrderState    == 13: #   orden cancelada localmente
                a = 1
                # solicitar cancelacion orden
                # actualizar estado orden
                # agregar historia orden si envio ok
            if Orden.OrderState    == 20: #   orden enviada al ajente (aun no confirmada)
                a = 1
                # conultar estado orden, si orden confirmada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
            if Orden.OrderState    == 21: #   orgente reciovio orden ok, pendiente de ejecucion (puede ser limit o market)
                a = 1
                # conultar estado orden, si orden confirmada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # si orden ejecutada fin
            if Orden.OrderState    == 22: #   ajete  recivio orden OK, e indico que la orden se ejecuto
                a = 1
                # conultar estado orden, si orden confirmada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # si orden ejecutada fin
            if Orden.OrderState    == 23: #   ajete  recivio orden OK, e indico que la orden se ejecutara al darse las condiciones, ej. stoplost o compra/venta a precio limite o fecha llimite
                a = 1
                # conultar estado orden, si orden confirmada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # si orden ejecutada fin
            if Orden.OrderState    == 24: #   se envio una consulta de ordenes al agente, para confirmar el estado de alguna orden enviada
                a = 1
                # conultar estado orden, si orden confirmada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # si orden ejecutada fin
            if Orden.OrderState    == 25: #   ORDEN EJECUTADA CON EXITO Y CONFIRMADA por medio de una consulta adicional al agente
                a = 1
                # no hacer nada. Fin
            if Orden.OrderState    == 26: #   se envio una cancelacion de orden al ajente, pero aun no se a confirmado si se cancelo en el broker
                a = 1
                # conultar estado orden, si orden cancelada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
            if Orden.OrderState    == 27: #   agente  recivio cancelacion de orden  OK, e indico que la orden se cancelo
                a = 1
                # conultar estado orden, si orden cancelada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
            if Orden.OrderState    == 28: #   se envio una consulta de ordenes al agente, para confirmar el estado de la cancelacion de una orden orden enviada
                a = 1
                # conultar estado orden, si orden cancelada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
            if Orden.OrderState    == 29: #   CONCELACION DE ORDEN EJECUTADA CON EXITO Y CONFIRMADA por medio de una consulta adicional al agente
                a = 1
                # no hacer nada. Fin
            if Orden.OrderState    == 30: #   error durante el envio de una orden al agente, se deconose si fue recivida o no, 
                a = 1
                # conultar estado orden, si orden confirmada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # SI orden no recivida enviar orden
                # actualizar orden si ese tiene los datos
                # agregar historia orden si envio ok
            if Orden.OrderState    == 31: #   agente reporto error al recivir orden,la orden no se cursara, implica reenviar si es viable o coresponde
                a = 1
                # enviar orden
                # actualizar orden si ese tiene los datos
                # agregar historia orden si envio ok
            if Orden.OrderState    == 32: #   agente reporto error al intentar ejecutar la orden, orden no cursada, se desconose si se ejecutara enventuamente,
                a = 1
                # solicitar cancelacion orden
                # actualizar estado orden
                # agregar historia orden si envio ok
                # RE enviar orden
                # actualizar orden si ese tiene los datos
                # agregar historia orden si envio ok
            if Orden.OrderState    == 33: #   ERROR DURANTE EL ENVIO DE UNA CANCELACION DE ORDEN , se deconose si fue resivida y cancelada por el agente o no.
                a = 1
                # conultar estado orden, si orden cancelada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # si orden no fue cancelda , RE solicitar cancelacion orden
                # actualizar estado orden
                # agregar historia orden si envio ok
            if Orden.OrderState    == 34: #   AGENTE REPORTO ERROR DURANTE EL PEDIDO DE CANCELACION DE UNA ORDEN.
                a = 1
                # conultar estado orden, si orden cancelada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # si orden no fue cancelda , RE solicitar cancelacion orden
                # actualizar estado orden
                # agregar historia orden si envio ok
            if Orden.OrderState    == 39: #   error generico en ejecucion de la orden, puede se en cualquier e
                a = 1
                # conultar estado orden, si orden confirmada fin
                # actualizar estado orden
                # agregar historia orden si envio ok
                # SI orden no recivida enviar orden
                # actualizar orden si ese tiene los datos
                # agregar historia orden si envio ok
        # end while
        return Orden.OrderState


'''
work flow ordenes
 > 1° leer ultimo trade
        > si no hay trades FIN
        > else si hay trade
        >   leer ordenes asociadas al trade
        >   si trade esta abierto
        >         si existe orden asociada de compra
        >           evaluar estado orden
        >               si orden pausada o descartada FIN
                         si orden registrada: enviar
                         si roden eenviada si respuesta: consulta ordenes y confirmar estado
                             si orden fue resivida actualizar: estado
                             si orden no fue recivida: reenviar
                         so orden enviada con respuesta error: reenviar
                         si orden enviada con respuesta ok: actualizar estado
                             consultar ordenes y confirmar estado
        >       else no existe orden
        >           crear orden
                    enviar roden
                    espera rdespuesta orden
                        sin respueta: consulta ordenes y confirmar estado
                             si orden fue resivida actualizar: estado
                             si orden no fue recivida: reenviar
                    so orden enviada con respuesta error: reenviar
                         si orden enviada con respuesta ok: actualizar estado
                             consultar ordenes y confirmar estado
                 si orden de compra confirmada
                     si  existe orden stop lost
                         si orden pausada o descartada FIN 
                         si roden eenviada si respuesta: consulta ordenes y confirmar estado
                                 si orden fue resivida actualizar: estado
                                 si orden no fue recivida: reenviar
                             so orden enviada con respuesta error: reenviar
                             si orden enviada con respuesta ok: actualizar estado
                                 consultar ordenes y confirmar estado
                     else no existe orden stop lost
                        crear orden
                        enviar roden
                        espera rdespuesta orden
                            sin respueta: consulta ordenes y confirmar estado
                                 si orden fue resivida actualizar: estado
                                 si orden no fue recivida: reenviar
                        so orden enviada con respuesta error: reenviar
                             si orden enviada con respuesta ok: actualizar estado
                                 consultar ordenes y confirmar estado
        >    else si trade esta cerrado
                 si existe orden asociada de venta
                     evaluar estado orden
                         si orden de venta confirmada FIN
                         si orden pausada o descartada FIN
                         si orden registrada: enviar
                         si roden eenviada si respuesta: consulta ordenes y confirmar estado
                             si orden fue resivida actualizar: estado
                             si orden no fue recivida: reenviar
                         so orden enviada con respuesta error: reenviar 
                         si orden enviada con respuesta ok: actualizar estado
                             consultar ordenes y confirmar estado
                else no existe orden de venta
                    crear orden
                    enviar roden
                    espera rdespuesta orden
                        sin respueta: consulta ordenes y confirmar estado
                             si orden fue resivida actualizar: estado
                             si orden no fue recivida: reenviar
                        so orden enviada con respuesta error: reenviar
                             si orden enviada con respuesta ok: actualizar estado
                                 consultar ordenes y confirmar estado
                 

'''

