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


============================================================
las ordenes deben tener los sguientes datos:
============================================================

Id del trade al que coresponden
Id local de la orden 
fecha hora de ingreso al sistema

agente al que coresponden
cryptomoneda a la que coresponden
precio considerado en el envio
volumen en la moneda de la orden
valor  CALCULADO orden(precio crypto/USD * volumen a ejecurar, segun el precio considerado)
% comicion calculado
USD comicion calculada
Id asignado por el agente 

fecha hora de confirmacion
precio confirmado por el agente al cual se ejecuto
volumen ejecutado por el agente
valor  EJECUTADO orden(precio crypto/USD ejc * volumen a ejecutado, segun el precio informado por el egente)
% comicion  informado
USD comicion informado

spread % comicion
spread USD ajecucion
sdread valor calculado - Valor Ejcuctado
deley ejecucion (en segundos) 

flag es inmediata o condicional
tipo de orden: compra market, compra limit/datelimit , venta, market, venta limit/datelimit , stoplost, totallost, salvarganancia, 
estado de la orden
estado anterior
fecha ultimo estado
fecha estado anterior

fecha hora de cancelacion de la orden
motivo de cancelacion descriptivo


============================================================
los historiales de ordenes deben tener los sguientes datos:
============================================================

Id del trade al que coresponde
Id local de la orden 
id asignado por el agente ( si existe)
Broker corespondiente
Cryptomoneda

id estado
fecha hora del ultimo estado
id estado anterior
fecha ora estado anterior

motivo del cambio de estado

json enviado
json recivido

'''