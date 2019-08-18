import pandas as pd
from pandas_converter import convertToDF
import json

import random
from sortedcontainers import SortedList
import arrow

from cassiopeia.core import Summoner, MatchHistory, Match
from cassiopeia.datastores.riotapi.common import APIError
from cassiopeia import Season, Queue, Patch

import threading


def filter_match_history(summoner, patch):
    end_time = patch.end
    if end_time is None:
        end_time = arrow.now()
    match_history = MatchHistory(summoner=summoner, seasons={Season.season_9}, queues={
                                 Queue.ranked_solo_fives}, begin_time=patch.start, end_time=end_time)
    return match_history


def collect_matches(initial_summoner_name, region, csv_path):
    print(initial_summoner_name, region, csv_path)

    try:
        df = pd.read_csv(csv_path)
    except:
        df = pd.DataFrame(columns=['match_id', 'player1_id', 'player1_account_id', 'player1_champion', 'player1_runes',
                               'player2_id', 'player2_account_id', 'player2_champion', 'player2_runes',
                               'player3_id', 'player3_account_id', 'player3_champion', 'player3_runes',
                               'player4_id', 'player4_account_id', 'player4_champion', 'player4_runes',
                               'player5_id', 'player5_account_id', 'player5_champion', 'player5_runes',
                               'player6_id', 'player6_account_id', 'player6_champion', 'player6_runes',
                               'player7_id', 'player7_account_id', 'player7_champion', 'player7_runes',
                               'player8_id', 'player8_account_id', 'player8_champion', 'player8_runes',
                               'player9_id', 'player9_account_id', 'player9_champion', 'player9_runes',
                               'player10_id', 'player10_account_id', 'player10_champion', 'player10_runes', 'won']
                      )

    summoner = Summoner(name=initial_summoner_name, region=region)
    patch = Patch.from_str("9.15", region=region)

    unpulled_summoner_ids = SortedList([summoner.id])
    pulled_summoner_ids = SortedList()

    unpulled_match_ids = SortedList()
    pulled_match_ids = SortedList()

    while unpulled_summoner_ids:
        # Get a random summoner from our list of unpulled summoners and pull their match history
        new_summoner_id = random.choice(unpulled_summoner_ids)
        new_summoner = Summoner(id=new_summoner_id, region=region)
        matches = filter_match_history(new_summoner, patch)
        unpulled_match_ids.update([match.id for match in matches])
        unpulled_summoner_ids.remove(new_summoner_id)
        pulled_summoner_ids.add(new_summoner_id)

        while unpulled_match_ids:
            # Get a random match from our list of matches
            new_match_id = random.choice(unpulled_match_ids)
            new_match = Match(id=new_match_id, region=region)
            match_result = new_match.blue_team.win
            match = {'match_id': new_match_id}
            for p in new_match.participants:
                player = f'player{p.id}'
                match[f'{player}_id'] = p.summoner.id
                match[f'{player}_account_id'] = p.summoner.account_id
                match[f'{player}_champion'] = p.champion.id
                match[f'{player}_runes'] = p.runes.keystone.name
                if p.summoner.id not in pulled_summoner_ids and p.summoner.id not in unpulled_summoner_ids:
                    unpulled_summoner_ids.add(p.summoner.id)

            match['won'] = match_result

            unpulled_match_ids.remove(new_match_id)
            pulled_match_ids.add(new_match_id)
            match_series = pd.Series(match)
            df = df.append(match_series, ignore_index=True)
            df.to_csv(csv_path, index=None, header=True)


class MatchesThread(threading.Thread):
    def __init__(self, initial_summoner_name, region, csv_path):
      threading.Thread.__init__(self)
      self.initial_summoner_name = initial_summoner_name
      self.region = region
      self.csv_path = csv_path

    def run(self):
        print(self.initial_summoner_name, self.region, self.csv_path)

        try:
            df = pd.read_csv(self.csv_path)
        except:
            df = pd.DataFrame(columns=['match_id', 'player1_id', 'player1_account_id', 'player1_champion', 'player1_runes',
                                   'player2_id', 'player2_account_id', 'player2_champion', 'player2_runes',
                                   'player3_id', 'player3_account_id', 'player3_champion', 'player3_runes',
                                   'player4_id', 'player4_account_id', 'player4_champion', 'player4_runes',
                                   'player5_id', 'player5_account_id', 'player5_champion', 'player5_runes',
                                   'player6_id', 'player6_account_id', 'player6_champion', 'player6_runes',
                                   'player7_id', 'player7_account_id', 'player7_champion', 'player7_runes',
                                   'player8_id', 'player8_account_id', 'player8_champion', 'player8_runes',
                                   'player9_id', 'player9_account_id', 'player9_champion', 'player9_runes',
                                   'player10_id', 'player10_account_id', 'player10_champion', 'player10_runes', 'won']
                          )

        summoner = Summoner(name=self.initial_summoner_name, region=self.region)
        patch = Patch.from_str("9.15", region=self.region)

        unpulled_summoner_ids = SortedList([summoner.id])
        pulled_summoner_ids = SortedList()

        unpulled_match_ids = SortedList()
        pulled_match_ids = SortedList()

        while unpulled_summoner_ids:
            try:
                # Get a random summoner from our list of unpulled summoners and pull their match history
                new_summoner_id = random.choice(unpulled_summoner_ids)
                new_summoner = Summoner(id=new_summoner_id, region=self.region)
                matches = filter_match_history(new_summoner, patch)
                unpulled_match_ids.update([match.id for match in matches])
                unpulled_summoner_ids.remove(new_summoner_id)
                pulled_summoner_ids.add(new_summoner_id)

                while unpulled_match_ids:
                    # Get a random match from our list of matches
                    new_match_id = random.choice(unpulled_match_ids)
                    new_match = Match(id=new_match_id, region=self.region)
                    match_result = new_match.blue_team.win
                    match = {'match_id': new_match_id}
                    for p in new_match.participants:
                        player = f'player{p.id}'
                        match[f'{player}_id'] = p.summoner.id
                        match[f'{player}_account_id'] = p.summoner.account_id
                        match[f'{player}_champion'] = p.champion.id
                        match[f'{player}_runes'] = p.runes.keystone.name
                        if p.summoner.id not in pulled_summoner_ids and p.summoner.id not in unpulled_summoner_ids:
                            unpulled_summoner_ids.add(p.summoner.id)

                    match['won'] = match_result

                    unpulled_match_ids.remove(new_match_id)
                    pulled_match_ids.add(new_match_id)
                    match_series = pd.Series(match)

                    df = df.append(match_series, ignore_index=True)
                    df.to_csv(self.csv_path, index=None, header=True)
            except APIError:
                pass

if __name__ == "__main__":
    # Initial data used for fetching random matches.
    initial_data = [["Azooz0633", 'EUNE', 'data_eune.csv'], ["Azooz0633", 'EUW', 'data_euw.csv'], ["FatRainCloud", 'NA', 'data_na.csv'],
        ["Baki", 'KR', 'data_kr.csv'], ["kuailefengnan111", 'JP', 'data_jp.csv'], ["Phasey", "TR", "data_tr.csv"],
        ["Alfredo Linguini", "OCE", "data_oce.csv"], ["GlorfindeI", "BR", "data_br.csv"], ["Leonidas lV", "LAN", "data_lan.csv"],
        ["Мason", "RU", "data_ru.csv"], ["SliMeBluE1", "LAS", "data_las.csv"]]

    initial_data = [["Krissυ", 'EUNE', 'data_eune.csv'], ["Kawales", 'EUW', 'data_euw.csv'], ["BlackCacao", 'KR', 'data_kr.csv'],
        ["SkaMX", "LAN", "data_lan.csv"], ["Yaaasuo", "RU", "data_ru.csv"], ["Letheria", "TR", "data_tr.csv"]]

    for data in initial_data:
        thread = MatchesThread(initial_summoner_name=data[0], region=data[1], csv_path=data[2])
        thread.start()
