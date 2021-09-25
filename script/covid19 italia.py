import tkinter as tk
from download import downloadFile
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import gmplot
import os
import bs4
  

def create_info(data):
    html = '<h1 align="center">' + data.get('denominazione_regione', 'Italia') + '</h1>'
    html += '<h2>Attualmente positivi: <span style="color: red">'  + str(int(data['totale_positivi'])) + '</span></h2>'
    html += '<h2>Nuovi positivi: <span style="color: orange">'  + str(int(data['nuovi_positivi'])) + '</span></h2>'
    html += '<h2>Terapie intensive: <span style="color: purple">' + str(int(data['terapia_intensiva'])) + '</span></h2>'
    return html

def moving_average(arr, n=7):
    ma = np.zeros(len(arr))
    for i in range(n, len(arr)):
        ma[i] = sum(arr[(i-n):i])/n
    return ma

def download():
    downloadFile('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province.json', 'province.json')
    downloadFile('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-regioni.json', 'regioni.json')
    downloadFile('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni-latest.csv', 'regioni_latest.csv')
    downloadFile('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale-latest.csv', 'ita_latest.csv')
    downloadFile('https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/anagrafica-vaccini-summary-latest.csv', 'vaccini.csv')
    downloadFile('https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/platea.csv', 'population.csv')

def plot(place, type='province'):
    with open(type + '.json', 'r') as data_file:
        json_data = data_file.read()

    data = json.loads(json_data)

    fig = plt.figure()
    ax1 = plt.subplot(211)
    ax2 = plt.subplot(212)
    fig.suptitle(place.upper() + ' ' + data[-1]['data'].split('T')[0])
    fig.tight_layout(pad=3)

    ax1.xaxis.set_minor_locator(matplotlib.dates.MonthLocator())
    ax1.xaxis.set_minor_formatter(matplotlib.dates.DateFormatter('%m'))
    ax1.xaxis.set_major_locator(matplotlib.dates.YearLocator())
    ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
    ax1.tick_params(axis='x', pad=15)
    ax1.grid()
    ax2.xaxis.set_minor_locator(matplotlib.dates.MonthLocator())
    ax2.xaxis.set_minor_formatter(matplotlib.dates.DateFormatter('%m'))
    ax2.xaxis.set_major_locator(matplotlib.dates.YearLocator())
    ax2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
    ax2.tick_params(axis='x', pad=15)
    ax2.grid()

    if type == 'province':
        search_fields = ['stato', 'denominazione_regione', 'denominazione_provincia', 'sigla_provincia']
        contagi = dict()

        for dato in data:
            for field in search_fields:
                if dato[field] is not None and dato[field].lower() == place.lower():
                    contagi[dato['data']] = contagi.get(dato['data'], 0) + dato['totale_casi']

        x = [ matplotlib.dates.date2num(datetime.strptime(key.split('T')[0], '%Y-%m-%d')) for key in contagi.keys() ]
        y = [ value for value in contagi.values() ]

        ax1.title.set_text('totale positivi')
        ax1.plot(x, y)
        ax2.title.set_text('variazione positivi')
        y = np.diff(y, prepend=0)
        ax2.bar(x, y, width=1)
        y = moving_average(y, n=7)
        ax2.plot(x, y, color='red')

    elif type == 'regioni':
        search_fields = ['stato', 'denominazione_regione']

        totale_positivi = dict()
        nuovi_positivi = dict()
        terapia_intensiva = dict()
        deceduti = dict()

        for dato in data:
            for field in search_fields:
                if dato[field] is not None and dato[field].lower() == place.lower():
                    totale_positivi[dato['data']] = totale_positivi.get(dato['data'], 0) + dato['totale_positivi']
                    nuovi_positivi[dato['data']] = nuovi_positivi.get(dato['data'], 0) + dato['nuovi_positivi']
                    terapia_intensiva[dato['data']] = terapia_intensiva.get(dato['data'], 0) + dato['terapia_intensiva']
                    deceduti[dato['data']] = deceduti.get(dato['data'], 0) + dato['deceduti']

        x = [ matplotlib.dates.date2num(datetime.strptime(key.split('T')[0], '%Y-%m-%d')) for key in totale_positivi.keys() ]
        totale_positivi = [ value for value in totale_positivi.values() ]
        nuovi_positivi = [ value for value in nuovi_positivi.values() ]
        terapia_intensiva = [ value for value in terapia_intensiva.values() ]
        deceduti = [ value for value in deceduti.values() ]

        ax1.title.set_text('valori assoluti')
        ax1.plot(x, totale_positivi, label='attualmente positivi')
        ax1.plot(x, deceduti, label='deceduti')

        ax2.title.set_text('variazioni e nuovi positivi')
        ax2.plot(x, nuovi_positivi, label='nuovi_positivi')
        ax2.plot(x, moving_average(nuovi_positivi), label='nuovi_positivi (MA)', color='red')
        ax2.plot(x, terapia_intensiva, label='terapia_intensiva', color='purple')
        ax2.plot(x, np.diff(deceduti, prepend=0), label='variazione deceduti', color='black')

        ax1.legend()
        ax2.legend()

    plt.show()

def map():
    df = pd.read_csv('regioni_latest.csv')

    gmap = gmplot.GoogleMapPlotter(41.17, 12.34, 5)

    for index, regione in df.iterrows():
        gmap.marker(regione['lat'], regione['long'], label=regione['denominazione_regione'][0],
                    title=regione['denominazione_regione'], info_window=create_info(regione))
        gmap.circle(regione['lat'], regione['long'], regione['nuovi_positivi']*10**2, color='orange')

    gmap.draw('map.html')

    df = pd.read_csv('ita_latest.csv')

    with open("map.html") as f:
        txt = f.read()
    soup = bs4.BeautifulSoup(txt, 'html.parser')

    title = bs4.BeautifulSoup(create_info(df), 'html.parser')
    title.h1.append(title.new_tag('br'))
    title.h1.append(df['data'][0].split('T')[0])

    soup.head.append(title)

    with open("map.html", "w") as f:
        f.write(str(soup))

    os.system('map.html')

def summary():
    contagi = pd.read_csv('regioni_latest.csv')

    date = contagi['data'][0].split('T')[0]

    #order columns
    df = contagi[['denominazione_regione', 'totale_positivi', 'nuovi_positivi', 'terapia_intensiva']]
    df = df.sort_values(by=['nuovi_positivi'], ascending=False)

    # plot grouped bar chart
    ax = df.plot(x='denominazione_regione',
                kind='bar',
                stacked=False,
                title='Italy ' + date)


    plt.tight_layout()

    plt.show()

def vaccine():
    df = pd.read_csv('vaccini.csv')
    df.set_index('fascia_anagrafica', inplace=True)
    sum_ = df.loc[['80-89', '90+']].sum()
    sum_.name = '80+'
    df = df.drop(['80-89', '90+'])
    df = df.append(sum_)

    df = df.reset_index()

    date = df['ultimo_aggiornamento'][0]

    df = df[['fascia_anagrafica', 'prima_dose', 'seconda_dose', 'pregressa_infezione']]

    #creo un Dataframe che indica la percentuale dei vaccinati per fascia di popolazione
    population = pd.read_csv('population.csv')
    population.set_index('fascia_anagrafica', inplace=True)
    abitanti = list()
    for age in df['fascia_anagrafica']:
        abitanti.append( sum(population.loc[age]['totale_popolazione']) )
    df['totale_popolazione'] = abitanti
    df['prima_dose_per'] = df['prima_dose'] / df['totale_popolazione'] * 100
    df['seconda_dose_per'] = df['seconda_dose'] / df['totale_popolazione'] * 100
    df['pregressa_infezione_per'] = df['pregressa_infezione'] / df['totale_popolazione'] * 100


    #traccio i grafici
    fig, axes = plt.subplots(nrows=2, ncols=1)
    axes[1].set_ylim(top=100, bottom=0)

    df.plot(x='fascia_anagrafica',
            y=['prima_dose', 'seconda_dose', 'pregressa_infezione'],
            kind='bar',
            stacked=False,
            title='totale: ' + str(sum(df['totale_popolazione'])) + '\n' +
                  'prima dose: ' + str(sum(df['prima_dose'])) + '\n' +
                  'seconda dose: ' + str(sum(df['seconda_dose'])) + '\n' +
                  'pregressa infezione:' + str(sum(df['pregressa_infezione'])),
            ax=axes[0],
            legend=False)


    df.plot(x='fascia_anagrafica',
            kind='bar',
            y=['prima_dose_per', 'seconda_dose_per', 'pregressa_infezione_per'],
            stacked=False,
            title='prima dose: ' + str(int(sum(df['prima_dose'])/sum(df['totale_popolazione'])*100)) + '%\n' +
                  'seconda dose: ' + str(int(sum(df['seconda_dose'])/sum(df['totale_popolazione'])*100)) + '%\n' +
                  'pregressa infezione: ' + str(int(sum(df['pregressa_infezione'])/sum(df['totale_popolazione'])*100)) + '%',
            ax=axes[1],
            legend=False)

    fig.suptitle('VACCINAZIONI ' + date)
    fig.legend(['prima dose', 'seconda dose', 'pregressa_infezione'])
    fig.tight_layout()
    axes[0].grid()
    axes[1].grid()
    plt.show()

root = tk.Tk()

input = tk.Entry()
input.grid(row=0, column=0)

province_button = tk.Button(text="PROVINCE", command=lambda : plot(input.get(), 'province'))
province_button.grid(row=0, column=1)

regioni_button = tk.Button(text="REGIONI", command=lambda : plot(input.get(), 'regioni'))
regioni_button.grid(row=0, column=2)

download_button = tk.Button(text="DOWNLOAD", command=download)
download_button.grid(row=0, column=3)

map_button = tk.Button(text="MAP", command=map)
map_button.grid(row=1, column=0, columnspan=2, sticky='ew')

summary_button = tk.Button(text="SUMMARY", command=summary)
summary_button.grid(row=1, column=2, columnspan=2, sticky='ew')

vaccini_button = tk.Button(text="VACCINI", command=vaccine)
vaccini_button.grid(row=2, column=0, columnspan=4, sticky='ew')

root.mainloop()
