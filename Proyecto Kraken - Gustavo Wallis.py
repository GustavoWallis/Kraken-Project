#!/usr/bin/env python
# coding: utf-8

# Se importan las librerias que vamos a usar y se define 'kraken' dada la recomendación de la documentación de krakenex
import pandas as pd
import krakenex
import matplotlib.pyplot as plt

kraken = krakenex.API()

# Se crea un diccionario con 5 posibles pares de monedas que se pueden tomar de Kraken. 
opciones = {
    "1": "XBTUSDT",
    "2": "ETHUSDT",
    "3": "XRPUSDT",
    "4": "XDGUSDT",
    "5": "LTCUSDT"
}


# Se define una función que permite elegir, dentro de 5 opciones, el par de monedas que se desea visualizar. 
# El while loop se usa para presentar las 5 opciones posibles hasta que el usuario elija correctamente un par válido
def escogencia():
    opcion = ""
    while opcion not in opciones:
        print("Elija el par que desea visualizar:") 
        print("1: XBT/USDT (Bitcoin)")
        print("2: ETH/USDT (Ethereum)")
        print("3: XRP/USD (Ripple)")
        print("4: DOGE/USDT (Dogecoin)")
        print("5: LTC/USDT (Litecoin)")
        opcion = input()
        
# Para el manejo de errores, se usa try y except. Esto para el caso de que el usuario elija una opción no disponible.
        try:
            pares = opciones[opcion]

        except KeyError:
            print(f'ERROR: La opción {opcion} es inválida, escoja un número válido\n')
            
    return pares
        
    
# El par elegido se guarda en esta variable, que será usada más adelante.         
par_escogido = escogencia()
    
print(f"\nEligió el par {par_escogido}")


# Se realiza el query de "Recent Trades", que permite obtener las últimas 1.000 transacciones de la moneda seleccionada
resp = kraken.query_public("Trades", data={'pair': par_escogido})


# Se crea un DataFrame con la información traída desde Kraken. Los nombres de las columnas fueron tomados de la
# documentación de la API. 
df = pd.DataFrame(resp["result"][par_escogido])
df.columns = ['Price', 'Volume', 'Time', 'Buy/Sell', 'Market/Limit', 'Miscellaneous']


# Price" y "Volume" vienen en formato "str", por lo que se procede a transformarlas en 'floats'
cols = ['Price', 'Volume']
df[cols] = df[cols].apply(pd.to_numeric, errors='coerce', axis=1)

# La columna Date, que viene como un "Float", se transforma en un Timestamp
df["Date"] = pd.to_datetime(df['Time'], unit='s')


# Se indica que el huso horario de "Date" es UTC±00:00
df.Date = df.Date.dt.tz_localize('UTC')


# Pasamos las fechas y horas de Date al huso horario de Madrid.
df.Date = df.Date.dt.tz_convert('Europe/Madrid') 


# Se crea la columna "Hora", que toma los valores de "Date" y los agrupa por cada hora del día
df['Hora'] = df["Date"].dt.strftime("%Y/%m/%d %H:00")
                               

# Se crea una columna multiplicando el precio por el volumen de cada transacción realizada.
df['PricexVolume'] = df['Price']*df['Volume']  


# Se calcula la sumatoria, en intervalos de una hora, de PricexVolume y de Volume.
PxV_acu = df.groupby(df['Hora'])['PricexVolume'].sum()

V_acu = df.groupby(df['Hora'])['Volume'].sum()

# Se calcula el VWAP ((ΣPrecio x Volumen) / ΣVol))
VWAP = PxV_acu / V_acu

                                          
# Se crea un nuevo DataFrame con el VWAP por hora
tabla = pd.DataFrame(VWAP)

tabla.rename(columns={0: "VWAP"}, inplace=True)


# Al nuevo DataFrame ("tabla"), se le agregan dos columnas: el último precio, y el volumen total de cada hora.
tabla['Precio'] = df.groupby('Hora').Price.last()
tabla['Volumen'] = df.groupby(df['Hora'])['Volume'].sum()


# Se crea la figura
fig, ax = plt.subplots(figsize=(10, 10))


# Se crea el gráfico de arriba (que muestra el precio), y se eliminan los "labels" del eje X.
top_plt = plt.subplot2grid((8, 4), (0, 0), rowspan=4, colspan=4)
top_plt.set_xticklabels([])


# Título del gráfico de arriba
plt.title(f"Cotización por hora {par_escogido} (últimas 1.000 transacciones)")


# Se incluye una línea que representa el Precio y otra el VWAP.
top_plt.plot(tabla.index, tabla["Precio"], linestyle='-', color='b', marker='o', label='Precio (en USD)')
top_plt.plot(tabla.index, tabla["VWAP"], linestyle=':', color='r', label='VWAP')

# Se incluye una leyenda y se modifican los "labels" del eje Y.
top_plt.legend(loc='best')
plt.gca().yaxis.set_major_formatter('${x:1.2f}')

# Se crea el gráfico de abajo (que muestra el volumen) y se rotan los "labels" del eje x
bottom_plt = plt.subplot2grid((5, 4), (3, 0), rowspan=1, colspan=4)
plt.xticks(rotation=90)
bottom_plt.bar(tabla.index, tabla['Volumen'], color='k')

# Título del gráfico de abajo
plt.title('Volumen', y=1.0)

# Se le agrega un tipo de estilo al gráfico.
plt.style.use('seaborn-deep')

# Se ajusta el tamaño del gráfico
plt.gcf().set_size_inches(15, 8)

plt.show()
