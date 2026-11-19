# 2023 FIFA Women's World Cup — Tactical Match Dashboard

An interactive football analytics dashboard built with **Python**, **Streamlit**, and **mplsoccer** using 100% **StatsBomb Open Data** (`competition_id=72`, `season_id=107`). Created as Final Project Part 2 for the **Football Data Analysis Mentorship (FDAM) — Cohort 2**, mentored by **Sara Bentelli**.

**Live App:** (https://fifawomensworldcup23.streamlit.app/))

## What This Dashboard Covers

Built around Spain's historic 2023 World Cup title run—with full support for all **64 matches** and **32 teams**—the app bridges tournament-wide team benchmarking down to timestamped match events for video review:

| View | What It Shows |
| :--- | :--- |
| **Passing Network** | Core 11 average positions, pass volume scaling, and top passing combinations with an adjustable minimum-link filter. |
| **Pass & Progression Map** | Toggle between all completed/incomplete passes and progressive passes & carries advancing ≥10 yards toward goal. |
| **Shot Map** | Half-pitch StatsBomb xG-scaled shot map, goal annotations, match shot log, and key-pass creators. |
| **Pressure Heatmap** | Team KDE pressing density, average pressure height line, ball recoveries, and pressing leaders. |
| **Player Heatmap** | Individual player spatial KDE heatmap, zonal touch split (defensive/middle/final third), and completed pass overlay. |
| **Turnover Punishment (`Loss → Goal/Shot`)** | Maps possession losses (wrong passes, dispossessed, miscontrols, failed dribbles) that led to an opponent shot or goal within a configurable 5–30s window, paired with an `MM:SS` cross-reference log. |
| **Tournament Error-Proneness Ranking** | Compares all 32 teams using a per-match **Error Score** (`(Own-Half Losses × 1 + Led to Shot × 3 + Led to Goal × 5) / Matches Played`), highlighting the most error-prone teams, least error-prone teams, and Spain's rank. |

## Tech Stack & Data

- **Data Source:** [StatsBomb Open Data](https://github.com/statsbomb/open-data) — 2023 FIFA Women's World Cup
- **Libraries:** `streamlit`, `mplsoccer`, `pandas`, `numpy`, `matplotlib`, `seaborn`

## Author

**Joseph The Football Analyst.**  
Football Data Analysis Mentorship (FDAM) — Cohort 2 (Mentor: Sara Bentelli)
