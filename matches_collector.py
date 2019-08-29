import pandas as pd
import json

import random
from sortedcontainers import SortedList
import arrow

from cassiopeia.core import Summoner, MatchHistory, Match, ChampionMastery
from cassiopeia.datastores.riotapi.common import APIError
from cassiopeia import Season, Queue, Patch
import cassiopeia as cass

import threading


def filter_match_history(summoner, starting_patch, ending_patch):
    end_time = ending_patch.end
    if end_time is None:
        end_time = arrow.now()
    match_history = MatchHistory(summoner=summoner, seasons={Season.season_9}, queues={
                                 Queue.ranked_solo_fives}, begin_time=starting_patch.start, end_time=end_time)
    return match_history


def get_average_kda(summoner, starting_patch, end_time, champion):
    match_history = MatchHistory(summoner=summoner, seasons={Season.season_9}, champions={champion}, queues={
                                 Queue.ranked_solo_fives}, begin_time=starting_patch.start, end_time=end_time)

    kda = []
    wins = 0

    for match in match_history:
        p = match.participants[summoner.name]
        kda.append(p.stats.kda)
        wins += 1 if p.stats.win else 0

    average = 0 if len(kda) == 0 else sum(kda) / len(kda)
    winrate = 0 if len(kda) == 0 else wins / len(kda)

    return round(average, 2), round(winrate, 2)



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
            columns = ['match_id']
            features = ['kda', 'winrate', 'cm_points', 'cm_level', 'runes', 'role']

            for i in range(1, 11):
                player = f'player{i}'
                for feature in features:
                    columns.append(f'{player}_{feature}')

            columns.append('won')

            df = pd.DataFrame(columns=columns)

        summoner = Summoner(name=self.initial_summoner_name, region=self.region)
        starting_patch = Patch.from_str("9.15", region=self.region)
        ending_patch = Patch.from_str("9.16", region=self.region)
        first_patch = Patch.from_str("9.1", region=self.region)

        unpulled_summoner_ids = SortedList([summoner.id])
        pulled_summoner_ids = SortedList()

        unpulled_match_ids = SortedList()
        pulled_match_ids = SortedList()

        while unpulled_summoner_ids:
            try:
                # Get a random summoner from our list of unpulled summoners and pull their match history
                new_summoner_id = random.choice(unpulled_summoner_ids)
                new_summoner = Summoner(id=new_summoner_id, region=self.region)
                matches = filter_match_history(new_summoner, starting_patch, ending_patch)
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
                        # match[f'{player}_id'] = p.summoner.id
                        # match[f'{player}_account_id'] = p.summoner.account_id
                        # match[f'{player}_champion'] = p.champion.id

                        current_summoner = Summoner(id=p.summoner.id, region=self.region)
                        match[f'{player}_kda'], match[f'{player}_winrate'] = get_average_kda(current_summoner, starting_patch, new_match.creation.shift(minutes=-1), p.champion.id)

                        cm = cass.get_champion_mastery(champion=p.champion.id, summoner=current_summoner, region=self.region)
                        match[f'{player}_cm_points'] = cm.points
                        match[f'{player}_cm_level'] = cm.level
                        match[f'{player}_runes'] = p.runes.keystone.name
                        match[f'{player}_role'] = p.role

                        if p.summoner.id not in pulled_summoner_ids and p.summoner.id not in unpulled_summoner_ids:
                            unpulled_summoner_ids.add(p.summoner.id)

                    match['won'] = 1 if match_result else 0

                    unpulled_match_ids.remove(new_match_id)
                    pulled_match_ids.add(new_match_id)
                    match_series = pd.Series(match)

                    df = df.append(match_series, ignore_index=True)
                    df.to_csv(self.csv_path, index=None, header=True)
            except:
                pass

if __name__ == "__main__":
    # Initial data used for fetching random matches.
    initial_data = [["Azooz0633", 'EUNE', 'data_eune.csv'], ["Azooz0633", 'EUW', 'data_euw.csv'], ["FatRainCloud", 'NA', 'data_na.csv'],
        ["Baki", 'KR', 'data_kr.csv'], ["kuailefengnan111", 'JP', 'data_jp.csv'], ["Phasey", "TR", "data_tr.csv"],
        ["Alfredo Linguini", "OCE", "data_oce.csv"], ["GlorfindeI", "BR", "data_br.csv"], ["Leonidas lV", "LAN", "data_lan.csv"],
        ["Мason", "RU", "data_ru.csv"], ["SliMeBluE1", "LAS", "data_las.csv"]]

    initial_data = [["Azooz0633", 'EUNE', 'data_eune.csv']]

    for data in initial_data:
        thread = MatchesThread(initial_summoner_name=data[0], region=data[1], csv_path=data[2])
        thread.start()
