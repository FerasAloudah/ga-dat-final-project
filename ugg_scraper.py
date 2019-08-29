import pandas as pd

from bs4 import BeautifulSoup
import requests

import cassiopeia as cass

champion_mapping = {champion.name: champion.id for champion in cass.get_champions(region="EUW")}

with open("ugg_tierlist.html") as ugg:
    soup = BeautifulSoup(ugg, "html.parser")

names = soup.find_all("div", class_="rt-td champion highlight")
tiers = soup.find_all("div", class_="rt-td tier")
winrates = soup.find_all("div", class_="rt-td winrate")
pickrates = soup.find_all("div", class_="rt-td pickrate")
banrates = soup.find_all("div", class_="rt-td banrate")

for (name, tier, winrate, pickrate, banrate) in zip(names, tiers, winrates, pickrates, banrates):

    print(champion_mapping[name.text], name.text, tier.text, winrate.text, pickrate.text, banrate.text)
