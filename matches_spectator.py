import pandas as pd

import cassiopeia as cass
from cassiopeia import Summoner, FeaturedMatches, Season, Queue, Patch
from cassiopeia.core import Summoner, MatchHistory, Match, ChampionMastery

from matches_collector import get_average_kda


def get_spectator_matches(df, champions_data):
    featured_matches = cass.get_featured_matches(region="EUW")
    starting_patch = Patch.from_str("9.16", region="EUW")

    for new_match in featured_matches:
        if new_match.queue.id == 420 and df[df['match_id'] == new_match.id].shape[0] == 0:
            match = {'match_id': int(new_match.id)}
            participants = new_match.blue_team.participants + new_match.red_team.participants
            for (p, id) in zip(participants, range(1, 11)):
                current_summoner = Summoner(id=p.summoner.id, region="EUW")

                match[f'{id}_kda'], match[f'{id}_winrate'] = get_average_kda(current_summoner, starting_patch, new_match.creation.shift(minutes=-10), p.champion.id)

                cm = cass.get_champion_mastery(champion=p.champion.id, summoner=current_summoner, region="EUW")
                match[f'{id}_cm_points'] = int(cm.points)

                champion_data = champions_data[champions_data['name'] == p.champion.name].winrate
                match[f'{id}_champion_winrate'] = champion_data.iloc[0]

            match_series = pd.Series(match)

            df = df.append(match_series, ignore_index=True)
            df.to_csv('spectator_data.csv', index=None, header=True)


if __name__ == "__main__":
    try:
        matches_df = pd.read_csv('spectator_data.csv')
    except:
        columns = ['match_id']
        features = ['kda', 'winrate', 'cm_points', 'champion_winrate']

        for i in range(1, 11):
            for feature in features:
                columns.append(f'{i}_{feature}')

        matches_df = pd.DataFrame(columns=columns)

    champions_data = pd.read_csv('champions_data.csv')
    get_spectator_matches(matches_df, champions_data)
