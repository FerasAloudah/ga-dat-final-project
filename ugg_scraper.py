import pandas as pd

from bs4 import BeautifulSoup
import requests

import cassiopeia as cass

champion_mapping = {champion.name: champion.id for champion in cass.get_champions(region="EUW")}
tiers_dict = {'S+': 5, 'S': 4, 'A': 3, 'B': 2, 'C': 1, 'D': 0}

with open("ugg_tierlist.html") as ugg:
    soup = BeautifulSoup(ugg, "html.parser")

names = soup.find_all("div", class_="rt-td champion highlight")
tiers = soup.find_all("div", class_="rt-td tier")
winrates = soup.find_all("div", class_="rt-td winrate")
pickrates = soup.find_all("div", class_="rt-td pickrate")
banrates = soup.find_all("div", class_="rt-td banrate")

columns = ['id', 'name', 'tier', 'winrate', 'pickrate', 'banrate']
df = pd.DataFrame(columns=columns)

champions = dict()

for (name, tier, winrate, pickrate, banrate) in zip(names, tiers, winrates, pickrates, banrates):
    id = champion_mapping[name.text]

    champion = {
        'id': id,
        'name': name.text,
        'tier': tier.text,
        'winrate': float(winrate.text[:-1]),
        'pickrate': float(pickrate.text[:-1]),
        'banrate': float(banrate.text[:-1])
    }

    if id in champions:
        champions[id].append(champion)
    else:
        champions[id] = [champion]


    print(champion)

for champion_list in champions.values():
    if len(champion_list) == 1:
        champion = champion_list[0]
    else:
        champion = {
            'id': champion_list[0]['id'],
            'name': champion_list[0]['name'],
            'tier': 'D',
            'winrate': 0,
            'pickrate': 0,
            'banrate': champion_list[0]['banrate']
        }

        for champion_dict in champion_list:
            if tiers_dict[champion_dict['tier']] > tiers_dict[champion['tier']]:
                champion['tier'] = champion_dict['tier']

            champion['winrate'] += champion_dict['winrate']
            champion['pickrate'] += champion_dict['pickrate']

        champion['winrate'] = round(champion['winrate'] / len(champion_list), 2)
        champion['pickrate'] = round(champion['pickrate'], 2)

    champion_series = pd.Series(champion)
    df = df.append(champion_series, ignore_index=True)

df.to_csv('champions_data.csv', index=None, header=True)
