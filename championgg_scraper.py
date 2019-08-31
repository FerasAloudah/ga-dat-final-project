import pandas as pd
import os

from bs4 import BeautifulSoup
import requests

import cassiopeia as cass

champion_mapping = {champion.name: champion.id for champion in cass.get_champions(region="EUW")}

with open("championgg_tierlist.html") as ugg:
    soup = BeautifulSoup(ugg, "html.parser")

champions_tr = soup.find_all('tr', class_='ng-scope')
columns = ['id', 'name', 'winrate', 'pickrate', 'banrate']
df = pd.DataFrame(columns=columns)
champions = dict()

for champion in champions_tr:
    champion_ = [s for s in champion.text.splitlines() if s]

    id = champion_mapping[champion_[1]]

    champion = {
        'id': id,
        'name': champion_[1],
        'winrate': float(champion_[3][:-1]),
        'pickrate': float(champion_[4][:-1]),
        'banrate': float(champion_[5][:-1])
    }

    if id in champions:
        champions[id].append(champion)
    else:
        champions[id] = [champion]

    print(champion_)
    print('-' * 100)

for champion_list in champions.values():
    if len(champion_list) == 1:
        champion = champion_list[0]
    else:
        champion = {
            'id': champion_list[0]['id'],
            'name': champion_list[0]['name'],
            'winrate': 0,
            'pickrate': 0,
            'banrate': champion_list[0]['banrate']
        }

        for champion_dict in champion_list:
            champion['winrate'] += champion_dict['winrate']
            champion['pickrate'] += champion_dict['pickrate']

        champion['winrate'] = round(champion['winrate'] / len(champion_list), 2)
        champion['pickrate'] = round(champion['pickrate'], 2)

    champion_series = pd.Series(champion)
    df = df.append(champion_series, ignore_index=True)

df.to_csv('champions_data.csv', index=None, header=True)
