import os
import urllib
import datetime
from bs4 import BeautifulSoup
import time
import pandas as pd
import json
import numpy as np

from typing import Tuple, List
from math import log

currencies = []


def negate_logarithm_convertor(graph):
    ''' log of each rate in graph and negate it'''
    result = []
    for i, row in enumerate(graph):
        result.append([])
        for edge in row:
            try:
                result[i].append(-log(edge))
            except:
                result[i].append(None)
    return result


def arbitrage(currency_tuple, rates_matrix):
    ''' Calculates arbitrage situations and prints out the details of this calculations'''
    global currencies

    trans_graph = negate_logarithm_convertor(rates_matrix)

    # Pick any source vertex -- we can run Bellman-Ford from any vertex and get the right result

    source = 0
    n = len(trans_graph)
    min_dist = [float('inf')] * n

    pre = [-1] * n

    min_dist[source] = source

    # 'Relax edges |V-1| times'
    for _ in range(n-1):
        for source_curr in range(n):
            for dest_curr in range(n):
                try:
                    if min_dist[dest_curr] > min_dist[source_curr] + trans_graph[source_curr][dest_curr]:
                        min_dist[dest_curr] = min_dist[source_curr] + trans_graph[source_curr][dest_curr]
                        pre[dest_curr] = source_curr
                except:
                    pass

    # if we can still relax edges, then we have a negative cycle
    for source_curr in range(n):
        for dest_curr in range(n):
            try:

                if min_dist[dest_curr] > min_dist[source_curr] + trans_graph[source_curr][dest_curr]:
                    # negative cycle exists, and use the predecessor chain to print the cycle
                    print_cycle = [dest_curr, source_curr]
                    # Start from the source and go backwards until you see the source vertex again or any vertex that already exists in print_cycle array
                    while pre[source_curr] not in  print_cycle:
                        print_cycle.append(pre[source_curr])
                        source_curr = pre[source_curr]
                    print_cycle.append(pre[source_curr])
                    print("Arbitrage Opportunity: \n")
                    print(" --> ".join([currencies[p] for p in print_cycle[::-1]]))
            except:
                pass


def soup():
    url = "https://www1.oanda.com/currency/live-exchange-rates/#USD"
    req = urllib.request.Request(
    url,
    data=None,
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
        'Connection': 'keep-alive'    }
           )

    global currencies
    while True:
        html = urllib.request.urlopen(req)
        ok = html.read().decode('utf-8')
        soup = BeautifulSoup(ok, "lxml")
        content = soup.find("div", {"id": "menu_content"})

        trades = []
        currencies = []
        for item in content.find_all(class_=["rate_row"]):
            trade_names = item.find_all(class_='inline title left')
            for name in trade_names:
                nam = name.text.replace('/', '_').replace('\n', '')
                trades.append(nam)
                if nam[:3] not in currencies:
                    currencies.append(nam[:3])

            prices = item.find_all(class_='inline value right')

        len_currencies = len(currencies)

        all_scripts = soup.find_all('script')
        print(all_scripts[13])
        data = json.loads(all_scripts[13].get_text()[152:len(all_scripts[13].get_text()) - 6])

        bid, ask, extras, spread = [], [], [], []
        for trade in trades:
            bid.append(data[trade]['bid'])
            ask.append(data[trade]['ask'])
            extras.append(data[trade]['extras'])
            spread.append(data[trade]['spread'])


        df = pd.DataFrame(list(zip(trades, bid, ask, spread, extras)), columns =['Pair', 'Bid', 'Ask', 'Spread', 'Extras'])
        rates = []
        for i in range(len_currencies):
            rates.append(np.zeros(len_currencies))
        df_c = pd.DataFrame(rates, index = currencies, columns = currencies)

        for i, trade in enumerate(trades):
            df_c[trade[:3]][trade[4:]] = ask[i]
            for j in range(len_currencies):
                if i == j:
                    df_c.iloc[i][j] = 1.0
                try:
                    if df_c.iloc[i][j] == 0.0:

                        df_c.iloc[i][j] = None
                except:
                    pass

        print(df_c)
        new_rates = df_c.values
        arbitrage(currencies, new_rates)

        time.sleep(20)


soup()
