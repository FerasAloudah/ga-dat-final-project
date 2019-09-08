import pandas as pd
from cassiopeia.core import Match


def get_actual_results(matches_ids):
    df = pd.DataFrame(columns=['match_id', 'won'])

    for match_id in matches_ids:
        match = Match(id=int(match_id), region="EUW")
        match_result = match.blue_team.win

        df = df.append(pd.Series({'match_id': match_id, 'won': 1 if match_result else 0}), ignore_index=True)

    df.to_csv('spectator_results.csv', index=None, header=True)


if __name__ == "__main__":
    matches_df = pd.read_csv('spectator_data.csv')
    get_actual_results(matches_df.match_id.values)
