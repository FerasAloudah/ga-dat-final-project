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


# This method returns the match history of the player.
def filter_match_history(summoner, starting_patch, ending_patch):
    end_time = ending_patch.end
    if end_time is None:
        end_time = arrow.now()
    match_history = MatchHistory(summoner=summoner, seasons={Season.season_9}, queues={
                                 Queue.ranked_solo_fives}, begin_time=starting_patch.start, end_time=end_time)
    return match_history


# This method returns the average kda of the player on a ceratin champion, 0 if no games were found.
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
            features = ['kda', 'winrate', 'cm_points', 'cm_level', 'runes', 'role',
                        'champion', 'champion_winrate', 'champion_pickrate', 'champion_banrate']

            for i in range(1, 11):
                for feature in features:
                    columns.append(f'{i}_{feature}')

            columns.append('won')

            df = pd.DataFrame(columns=columns)

        champions_data = pd.read_csv(f'champions_data.csv', index_col='id')
        summoner = Summoner(name=self.initial_summoner_name, region=self.region)
        starting_patch = Patch.from_str("9.16", region=self.region)
        ending_patch = Patch.from_str("9.17", region=self.region)
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

                    if df[df['match_id'] == new_match_id].shape[0] == 0:
                        new_match = Match(id=new_match_id, region=self.region)
                        match_result = new_match.blue_team.win
                        match = {'match_id': new_match_id}

                        # Loop through all of the players, and add all of their stats to our data frame.
                        for p in new_match.participants:
                            current_summoner = Summoner(id=p.summoner.id, region=self.region)
                            match[f'{p.id}_kda'], match[f'{p.id}_winrate'] = get_average_kda(current_summoner, starting_patch, new_match.creation.shift(minutes=-1), p.champion.id)

                            cm = cass.get_champion_mastery(champion=p.champion.id, summoner=current_summoner, region=self.region)
                            match[f'{p.id}_cm_points'] = cm.points
                            match[f'{p.id}_cm_level'] = cm.level
                            match[f'{p.id}_runes'] = p.runes.keystone.name
                            match[f'{p.id}_role'] = p.role

                            champion_data = champions_data.loc[p.champion.id]
                            match[f'{p.id}_champion'] = p.champion.name
                            match[f'{p.id}_champion_winrate'] = champion_data.winrate
                            match[f'{p.id}_champion_pickrate'] = champion_data.pickrate
                            match[f'{p.id}_champion_banrate'] = champion_data.banrate

                            if p.summoner.id not in pulled_summoner_ids and p.summoner.id not in unpulled_summoner_ids:
                                unpulled_summoner_ids.add(p.summoner.id)

                        match['won'] = 1 if match_result else 0
                        match_series = pd.Series(match)

                        df = df.append(match_series, ignore_index=True)
                        df.to_csv(self.csv_path, index=None, header=True)

                    unpulled_match_ids.remove(new_match_id)
                    pulled_match_ids.add(new_match_id)
            except:
                pass

        print('*' * 100)
        print(self.region, 'has finished!')
        print('*' * 100)

if __name__ == "__main__":
    # Initial data used for fetching random matches.
    initial_data = [["Airithie", 'EUNE', 'data_eune.csv'], ["Hexage", 'EUW', 'data_euw.csv'], ["ThePadzQC", 'NA', 'data_na.csv'],
        ["ERNIO", 'KR', 'data_kr.csv'], ["SG BIank", 'JP', 'data_jp.csv'], ["Throin Riven", "TR", "data_tr.csv"],
        ["Carpe Diem", "OCE", "data_oce.csv"], ["Denarc", "BR", "data_br.csv"], ["Chookity", "LAN", "data_lan.csv"],
        ["Deku", "RU", "data_ru.csv"], ["M4LD4D", "LAS", "data_las.csv"]]

    # Run a thread for each region, since the API rate limiting is linked to the region you are getting your data from.
    for data in initial_data:
        thread = MatchesThread(initial_summoner_name=data[0], region=data[1], csv_path=data[2])
        thread.start()
