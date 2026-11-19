import pandas as pd
from mplsoccer import Sbopen

parser = Sbopen()
matches = parser.match(competition_id=72, season_id=107)
WINDOW_SEC = 15

records = []

for i, m in matches.iterrows():
    mid = int(m['match_id'])
    df = parser.event(match_id=mid)[0]
    df['abs_sec'] = df['minute'].fillna(0).astype(int) * 60 + df['second'].fillna(0).astype(int)

    for team in [m['home_team_name'], m['away_team_name']]:
        t_df = df[df['team_name'] == team]
        opp_shots = df[(df['team_name'] != team) & (df['type_name'] == 'Shot')]

        # Same 4 turnover types as your analyze_turnover_punishment()
        is_turnover = (
            ((t_df['type_name'] == 'Pass') & (t_df['outcome_name'].isin(['Incomplete', 'Out', 'Pass Offside']))) |
            (t_df['type_name'].isin(['Dispossessed', 'Miscontrol'])) |
            ((t_df['type_name'] == 'Dribble') & (t_df['outcome_name'] == 'Incomplete'))
        )
        turnovers = t_df[is_turnover & t_df['x'].notna()].copy()
        own_half_losses = int((turnovers['x'] < 60).sum())

        led_to_shot = 0
        led_to_goal = 0
        opp_xg = 0.0

        for _, row in turnovers.iterrows():
            shots_in_win = opp_shots[
                (opp_shots['period'] == row['period']) &
                (opp_shots['abs_sec'] >= row['abs_sec']) &
                ((opp_shots['abs_sec'] - row['abs_sec']) <= WINDOW_SEC)
            ]
            if len(shots_in_win) > 0:
                led_to_shot += 1
                goals = shots_in_win[shots_in_win['outcome_name'] == 'Goal']
                chosen = goals.iloc[0] if len(goals) > 0 else shots_in_win.iloc[0]
                if chosen['outcome_name'] == 'Goal':
                    led_to_goal += 1
                xg = chosen.get('shot_statsbomb_xg', 0.0)
                opp_xg += float(xg) if pd.notna(xg) else 0.0

        records.append({
            'team_name': team,
            'match_id': mid,
            'total_turnovers': len(turnovers),
            'own_half_losses': own_half_losses,
            'led_to_shot': led_to_shot,
            'led_to_goal': led_to_goal,
            'opp_xg': opp_xg
        })

    print(f"Processed {i + 1}/{len(matches)} matches...")

match_df = pd.DataFrame(records)

summary = (
    match_df.groupby('team_name')
    .agg(
        matches_played=('match_id', 'nunique'),
        total_turnovers=('total_turnovers', 'sum'),
        own_half_losses=('own_half_losses', 'sum'),
        led_to_shot=('led_to_shot', 'sum'),
        led_to_goal=('led_to_goal', 'sum'),
        opp_xg=('opp_xg', 'sum')
    )
    .reset_index()
)

summary['team_clean'] = summary['team_name'].str.replace(" Women's", "", regex=False)
summary['own_half_per_match'] = summary['own_half_losses'] / summary['matches_played']
summary['punished_per_match'] = summary['led_to_shot'] / summary['matches_played']
summary['opp_xg_per_match'] = summary['opp_xg'] / summary['matches_played']
summary['punishment_rate_pct'] = (summary['led_to_shot'] / summary['total_turnovers'].clip(lower=1)) * 100

# Overall Error-Proneness Index (per match)
summary['error_index'] = (
    (summary['own_half_losses'] * 1) +
    (summary['led_to_shot'] * 3) +
    (summary['led_to_goal'] * 5)
) / summary['matches_played']

summary = summary.sort_values('error_index', ascending=False).reset_index(drop=True)
summary['rank'] = summary.index + 1

summary.to_csv("wwc23_team_error_index.csv", index=False)
print("Saved wwc23_team_error_index.csv!")