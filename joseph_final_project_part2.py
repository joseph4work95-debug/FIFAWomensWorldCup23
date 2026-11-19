import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from mplsoccer import Pitch, VerticalPitch, Sbopen

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG — must be the very first Streamlit command
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FIFA Women's World Cup 2023 — Spain Tactical Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# STYLE — matches mentorship website exactly
# Colors: black background, violet accent, white text
# ─────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    /* ── Global background ── */
    .stApp {
        background-color: #0d0d0d;
        color: #ffffff;
    }

    /* ── Sidebar background ── */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #7C3AED;
    }

    /* ── Sidebar text ── */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* ── Main title ── */
    h1 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* ── Headers ── */
    h2, h3 {
        color: #7C3AED !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }

    /* ── Selectbox, radio, widgets ── */
    .stSelectbox > div > div,
    .stRadio > div {
        background-color: #1a1a1a;
        border: 1px solid #7C3AED;
        border-radius: 8px;
        color: #ffffff;
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background-color: #1a1a1a;
        border: 1px solid #7C3AED;
        border-radius: 12px;
        padding: 16px;
    }

    [data-testid="metric-container"] label {
        color: #a5b4fc !important;
        font-size: 13px;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 24px;
        font-weight: 700;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        line-height: 1.2;
    }

    /* ── Divider ── */
    hr {
        border-color: #7C3AED;
        opacity: 0.3;
    }

    /* ── Dataframe table ── */
    .stDataFrame {
        background-color: #1a1a1a;
        border: 1px solid #7C3AED;
        border-radius: 8px;
    }

    /* ── Caption / small text ── */
    .stCaption {
        color: #a0a0a0 !important;
    }

    /* ── Info / success / warning boxes ── */
    .stAlert {
        background-color: #1a1a1a;
        border-left: 4px solid #7C3AED;
        color: #ffffff;
    }

    /* ── Button ── */
    .stButton > button {
        background-color: #7C3AED;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 8px 20px;
    }

    .stButton > button:hover {
        background-color: #6d28d9;
    }

    /* ── Custom Scoreboard Banner ── */
    .scoreboard-box {
        background: linear-gradient(135deg, #161616 0%, #1f1435 100%);
        border: 1px solid #7C3AED;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 18px;
        text-align: center;
    }
    .scoreboard-stage {
        color: #A78BFA;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
    }
    .scoreboard-teams {
        color: #FFFFFF;
        font-size: 26px;
        font-weight: 800;
        margin-bottom: 6px;
    }
    .scoreboard-score {
        color: #7C3AED;
        background-color: #0d0d0d;
        border: 1px solid #7C3AED;
        border-radius: 8px;
        padding: 2px 14px;
        margin: 0 12px;
    }
    .scoreboard-meta {
        color: #A0A0A0;
        font-size: 13px;
    }

    /* ── Remove top padding ── */
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# STYLE CONSTANTS — use these for all your visualizations
# ─────────────────────────────────────────────────────────────
BG_COLOR     = '#0d0d0d'   # Figure & pitch background
PITCH_COLOR  = '#0d0d0d'   # Pitch surface
LINE_COLOR   = '#FFFFFF'   # Pitch lines
MAIN_COLOR   = '#7C3AED'   # Violet — primary color
ACCENT_COLOR = '#A78BFA'   # Light violet — secondary
TEXT_COLOR   = '#FFFFFF'   # All text on figures
GRAY_COLOR   = '#A0A0A0'   # Secondary text / Incomplete actions

# Custom violet colormap for KDE & heatmaps
VIOLET_CMAP = LinearSegmentedColormap.from_list(
    "violet_100",
    [BG_COLOR, MAIN_COLOR, ACCENT_COLOR, TEXT_COLOR],
    N=100
)

# Apply matplotlib global style
plt.rcParams['figure.facecolor'] = BG_COLOR
plt.rcParams['axes.facecolor']   = BG_COLOR
plt.rcParams['text.color']       = TEXT_COLOR
plt.rcParams['font.sans-serif']  = 'DejaVu Sans'

# ─────────────────────────────────────────────────────────────
# HELPER UTILITIES
# ─────────────────────────────────────────────────────────────
def format_player_name(full_name: str) -> str:
    """Convert long StatsBomb legal names into clean tactical display names."""
    if pd.isna(full_name) or not str(full_name).strip():
        return "Unknown"
    nicknames = {
        "Aitana Bonmatí Conca": "Aitana Bonmatí",
        "Alexia Putellas Segura": "Alexia Putellas",
        "Olga Carmona García": "Olga Carmona",
        "Jennifer Hermoso Fuentes": "Jenni Hermoso",
        "Teresa Abelleira Dueñas": "Teresa Abelleira",
        "Salma Celeste Paralluelo Ayingono": "Salma Paralluelo",
        "Mariona Caldentey Oliver": "Mariona Caldentey",
        "Alba María Redondo Ferrer": "Alba Redondo",
        "Ona Batlle Pascual": "Ona Batlle",
        "Irene Paredes Hernández": "Irene Paredes",
        "Laia Codina Panedas": "Laia Codina",
        "Catalina Thomas Coll Lluch": "Cata Coll",
        "Esther González Rodríguez": "Esther González",
        "Athenea del Castillo Beivide": "Athenea del Castillo",
        "Ivana Andrés Sanz": "Ivana Andrés",
        "Oihane Hernández Zurbano": "Oihane Hernández",
        "María Isabel Rodríguez Rivero": "Misa Rodríguez",
    }
    if full_name in nicknames:
        return nicknames[full_name]
    parts = str(full_name).strip().split()
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1]}"
    return str(full_name)


# ─────────────────────────────────────────────────────────────
# DATA LOADING — cached for performance (100% StatsBomb Open Data)
# ─────────────────────────────────────────────────────────────
parser = Sbopen()

# FIFA Women's World Cup 2023 in StatsBomb Open Data:
# competition_id = 72 ("Women's World Cup"), season_id = 107 ("2023")
WWC_COMPETITION_ID = 72
WWC_SEASON_ID      = 107
ERROR_INDEX_CSV    = "wwc23_team_error_index.csv"


@st.cache_data(show_spinner="Loading 2023 FIFA Women's World Cup matches from StatsBomb...")
def load_matches(competition_id: int = WWC_COMPETITION_ID, season_id: int = WWC_SEASON_ID) -> pd.DataFrame:
    matches = parser.match(competition_id=competition_id, season_id=season_id)
    matches = matches.sort_values('match_date', ascending=False).reset_index(drop=True)
    date_str = pd.to_datetime(matches['match_date']).dt.strftime('%Y-%m-%d')
    stage_col = matches['competition_stage_name'] if 'competition_stage_name' in matches.columns else pd.Series('Match', index=matches.index)
    matches['label'] = (
        matches['home_team_name'].str.replace(" Women's", "", regex=False) + ' ' +
        matches['home_score'].astype(str) + '–' +
        matches['away_score'].astype(str) + ' ' +
        matches['away_team_name'].str.replace(" Women's", "", regex=False) +
        '  [' + stage_col.astype(str) + ' · ' + date_str + ']'
    )
    return matches


@st.cache_data(show_spinner="Loading StatsBomb match event stream...")
def load_events(match_id: int) -> pd.DataFrame:
    events_df = parser.event(match_id=match_id)[0]
    events_df['player_short'] = events_df['player_name'].apply(format_player_name)
    if 'pass_recipient_name' in events_df.columns:
        events_df['recipient_short'] = events_df['pass_recipient_name'].apply(format_player_name)
    return events_df


@st.cache_data
def load_tournament_error_index(path: str = ERROR_INDEX_CSV) -> pd.DataFrame:
    return pd.read_csv(path)


# ─────────────────────────────────────────────────────────────
# VISUALIZATION FUNCTIONS
# Dark background (#0d0d0d) · White pitch lines (#FFFFFF) · Violet (#7C3AED)
# ─────────────────────────────────────────────────────────────
def plot_passing_network(team_events: pd.DataFrame, team_name: str, match_title: str, min_passes: int = 4):
    """Plot the team's passing network with average positions and pass volume scaling."""
    passes = team_events[
        (team_events['type_name'] == 'Pass') &
        (team_events['outcome_name'].isna()) &
        (team_events['x'].notna()) &
        (team_events['pass_recipient_name'].notna())
    ].copy()

    # Select top 11 players by pass involvement to represent the core tactical structure
    top_players = passes['player_short'].value_counts().head(11).index.tolist()
    net_passes = passes[
        passes['player_short'].isin(top_players) &
        passes['recipient_short'].isin(top_players)
    ].copy()

    avg_locs = (
        net_passes.groupby('player_short')
        .agg(x=('x', 'mean'), y=('y', 'mean'), count=('id', 'count'))
        .reset_index()
    )
    if len(avg_locs) > 0:
        avg_locs['marker_size'] = (avg_locs['count'] / avg_locs['count'].max()) * 2000 + 350
    else:
        avg_locs['marker_size'] = 500

    net_passes['pair_min'] = net_passes[['player_short', 'recipient_short']].min(axis=1)
    net_passes['pair_max'] = net_passes[['player_short', 'recipient_short']].max(axis=1)
    edges = (
        net_passes.groupby(['pair_min', 'pair_max'])
        .agg(pass_count=('id', 'count'))
        .reset_index()
    )
    edges = edges.merge(avg_locs[['player_short', 'x', 'y']], left_on='pair_min', right_on='player_short')
    edges = edges.merge(avg_locs[['player_short', 'x', 'y']], left_on='pair_max', right_on='player_short', suffixes=('', '_end'))
    edges = edges[edges['pass_count'] >= min_passes].copy()
    if len(edges) > 0:
        edges['width'] = (edges['pass_count'] / edges['pass_count'].max()) * 11.0 + 1.2

    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2)
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor(BG_COLOR)

    for _, row in edges.iterrows():
        alpha_val = 0.35 + 0.60 * (row['pass_count'] / max(1, edges['pass_count'].max()))
        pitch.lines(
            row['x'], row['y'], row['x_end'], row['y_end'],
            lw=row['width'], color=MAIN_COLOR, alpha=alpha_val, zorder=2.5, ax=ax
        )

    if len(avg_locs) > 0:
        pitch.scatter(
            avg_locs['x'], avg_locs['y'], s=avg_locs['marker_size'],
            color=MAIN_COLOR, edgecolors=LINE_COLOR, linewidth=1.8, alpha=0.95, zorder=3.5, ax=ax
        )
        pitch.scatter(
            avg_locs['x'], avg_locs['y'], s=avg_locs['marker_size'] * 0.40,
            color=ACCENT_COLOR, edgecolors=BG_COLOR, linewidth=1.0, alpha=1.0, zorder=4.0, ax=ax
        )
        for _, row in avg_locs.iterrows():
            txt = pitch.annotate(
                row['player_short'], xy=(row['x'], row['y'] - 3.5),
                c=TEXT_COLOR, va='center', ha='center', size=10.5, weight='bold', zorder=5, ax=ax
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=3.0, foreground=BG_COLOR)])

    ax.set_title(
        f"{team_name.upper()} — PASSING NETWORK",
        color=TEXT_COLOR, fontsize=18, fontweight='bold', pad=20
    )
    ax.text(
        60, -2.5,
        f"{match_title} | Min. {min_passes} passes per connection | Node size = completed pass volume",
        color=GRAY_COLOR, fontsize=11, ha='center', va='center'
    )
    plt.tight_layout()
    return fig, avg_locs, edges


def plot_pass_and_progression_map(team_events: pd.DataFrame, team_name: str, match_title: str, mode: str = "Progressive Passes & Carries"):
    """Plot either all passes (Completed vs Incomplete) or Progressive Passes & Carries (≥10 yards forward)."""
    passes = team_events[team_events['type_name'] == 'Pass'].copy()
    passes['x_gain'] = passes['end_x'] - passes['x']
    comp_passes = passes[passes['outcome_name'].isna()].copy()
    incomp_passes = passes[passes['outcome_name'].notna()].copy()
    prog_passes = comp_passes[comp_passes['x_gain'] >= 10.0].copy()

    carries = team_events[team_events['type_name'] == 'Carry'].copy()
    carries['x_gain'] = carries['end_x'] - carries['x']
    prog_carries = carries[carries['x_gain'] >= 10.0].copy()

    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2)
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor(BG_COLOR)

    if mode == "All Passes (Completed vs. Incomplete)":
        pitch.arrows(
            incomp_passes['x'], incomp_passes['y'], incomp_passes['end_x'], incomp_passes['end_y'],
            width=1.5, headwidth=3.5, headlength=3.5, color=GRAY_COLOR, alpha=0.45, zorder=2.2, ax=ax
        )
        pitch.arrows(
            comp_passes['x'], comp_passes['y'], comp_passes['end_x'], comp_passes['end_y'],
            width=2.0, headwidth=4.0, headlength=4.0, color=MAIN_COLOR, alpha=0.78, zorder=3.0, ax=ax
        )
        legend_elements = [
            Line2D([0], [0], color=MAIN_COLOR, lw=3, label=f"Completed ({len(comp_passes)} | {len(comp_passes)/max(1, len(passes))*100:.1f}%)"),
            Line2D([0], [0], color=GRAY_COLOR, lw=2, label=f"Incomplete ({len(incomp_passes)})")
        ]
        title_str = f"{team_name.upper()} — FULL MATCH PASS MAP"
        sub_str = f"{match_title} | Total Passes: {len(passes)} | Accuracy: {len(comp_passes)/max(1, len(passes))*100:.1f}%"
    else:
        pitch.arrows(
            prog_carries['x'], prog_carries['y'], prog_carries['end_x'], prog_carries['end_y'],
            width=2.0, headwidth=3.8, headlength=3.8, color=ACCENT_COLOR, alpha=0.75, zorder=2.6, ax=ax
        )
        pitch.arrows(
            prog_passes['x'], prog_passes['y'], prog_passes['end_x'], prog_passes['end_y'],
            width=2.4, headwidth=4.2, headlength=4.2, color=MAIN_COLOR, alpha=0.92, zorder=3.2, ax=ax
        )
        pitch.scatter(
            prog_passes['end_x'], prog_passes['end_y'],
            s=40, color=MAIN_COLOR, edgecolors=LINE_COLOR, linewidth=0.8, zorder=3.5, ax=ax
        )
        legend_elements = [
            Line2D([0], [0], color=MAIN_COLOR, lw=3, label=f"Progressive Passes ≥10m ({len(prog_passes)})"),
            Line2D([0], [0], color=ACCENT_COLOR, lw=2.5, label=f"Progressive Carries ≥10m ({len(prog_carries)})")
        ]
        title_str = f"{team_name.upper()} — BALL PROGRESSION MAP"
        sub_str = f"{match_title} | Progressive Passes: {len(prog_passes)} | Progressive Carries: {len(prog_carries)}"

    leg = ax.legend(handles=legend_elements, loc='upper left', facecolor=BG_COLOR, edgecolor=MAIN_COLOR, fontsize=10.5)
    for t in leg.get_texts():
        t.set_color(TEXT_COLOR)

    ax.set_title(title_str, color=TEXT_COLOR, fontsize=18, fontweight='bold', pad=20)
    ax.text(60, -2.5, sub_str, color=GRAY_COLOR, fontsize=11, ha='center', va='center')
    plt.tight_layout()
    return fig, prog_passes, prog_carries


def plot_shot_map(team_events: pd.DataFrame, team_name: str, match_title: str):
    """Plot half-pitch xG Shot Map and Key Passes."""
    shots = team_events[team_events['type_name'] == 'Shot'].copy()
    shots['xg'] = shots['shot_statsbomb_xg'].fillna(0.0) if 'shot_statsbomb_xg' in shots.columns else 0.05
    goals = shots[shots['outcome_name'] == 'Goal'].copy()
    misses = shots[shots['outcome_name'] != 'Goal'].copy()

    pitch = VerticalPitch(pitch_type='statsbomb', half=True, pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2)
    fig, ax = pitch.draw(figsize=(10, 8))
    fig.set_facecolor(BG_COLOR)

    if len(misses) > 0:
        pitch.scatter(
            misses['x'], misses['y'],
            s=misses['xg'] * 550 + 75,
            color=GRAY_COLOR, edgecolors=LINE_COLOR, linewidth=1.2, alpha=0.75, zorder=3.0, ax=ax
        )
    if len(goals) > 0:
        pitch.scatter(
            goals['x'], goals['y'],
            s=goals['xg'] * 550 + 130,
            color=MAIN_COLOR, edgecolors=LINE_COLOR, linewidth=2.2, alpha=1.0, zorder=4.5, ax=ax
        )
        for _, row in goals.iterrows():
            txt = pitch.annotate(
                f"{row['player_short']} ({int(row['minute'])}')\nxG: {row['xg']:.2f}",
                xy=(row['x'] + 2.0, row['y']),
                c=TEXT_COLOR, va='center', ha='center', size=10, weight='bold', zorder=5, ax=ax
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=2.8, foreground=BG_COLOR)])

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=f"Goal ({len(goals)})", markerfacecolor=MAIN_COLOR, markersize=11),
        Line2D([0], [0], marker='o', color='w', label=f"No Goal ({len(misses)})", markerfacecolor=GRAY_COLOR, markersize=9)
    ]
    leg = ax.legend(handles=legend_elements, loc='lower left', facecolor=BG_COLOR, edgecolor=MAIN_COLOR, fontsize=10.5)
    for t in leg.get_texts():
        t.set_color(TEXT_COLOR)

    total_xg = shots['xg'].sum()
    ax.set_title(
        f"{team_name.upper()} — SHOT MAP (xG SCALED)",
        color=TEXT_COLOR, fontsize=18, fontweight='bold', pad=24
    )
    ax.text(
        40, 123.2,
        f"{match_title} | Shots: {len(shots)} | Goals: {len(goals)} | Total xG: {total_xg:.2f}",
        color=GRAY_COLOR, fontsize=11, ha='center', va='center'
    )
    plt.tight_layout()
    return fig, shots


def plot_pressure_heatmap(team_events: pd.DataFrame, team_name: str, match_title: str):
    """Plot KDE Pressure Heatmap with Defensive Action overlays and average pressure line."""
    pressures = team_events[
        (team_events['type_name'] == 'Pressure') &
        (team_events['x'].notna()) &
        (team_events['y'].notna())
    ].copy()
    recoveries = team_events[
        (team_events['type_name'] == 'Ball Recovery') &
        (team_events['x'].notna())
    ].copy()

    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2)
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor(BG_COLOR)

    if len(pressures) >= 5:
        pitch.kdeplot(
            pressures['x'], pressures['y'],
            ax=ax, cmap=VIOLET_CMAP, fill=True, levels=100, thresh=0.05, alpha=0.82
        )
    if len(pressures) > 0:
        pitch.scatter(
            pressures['x'], pressures['y'],
            s=28, color=TEXT_COLOR, edgecolors=BG_COLOR, alpha=0.45, zorder=3.0, ax=ax
        )
        avg_px = pressures['x'].mean()
        ax.plot([avg_px, avg_px], [0, 80], color=ACCENT_COLOR, linestyle='--', linewidth=2.2, zorder=3.8)
        ax.text(
            avg_px + 1.5, 5.0,
            f"Avg. Pressure Height\n(x = {avg_px:.1f})",
            color=TEXT_COLOR, fontsize=10.5, fontweight='bold', ha='left', va='top', zorder=4.5
        )
    if len(recoveries) > 0:
        pitch.scatter(
            recoveries['x'], recoveries['y'],
            s=85, color=MAIN_COLOR, edgecolors=LINE_COLOR, linewidth=1.2, alpha=0.92, zorder=3.6, ax=ax
        )

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=f"Pressures ({len(pressures)})", markerfacecolor=TEXT_COLOR, markersize=7),
        Line2D([0], [0], marker='o', color='w', label=f"Ball Recoveries ({len(recoveries)})", markerfacecolor=MAIN_COLOR, markersize=9)
    ]
    leg = ax.legend(handles=legend_elements, loc='upper left', facecolor=BG_COLOR, edgecolor=MAIN_COLOR, fontsize=10.5)
    for t in leg.get_texts():
        t.set_color(TEXT_COLOR)

    ax.set_title(
        f"{team_name.upper()} — PRESSURE DENSITY & RECOVERIES",
        color=TEXT_COLOR, fontsize=18, fontweight='bold', pad=20
    )
    ax.text(
        60, -2.5,
        f"{match_title} | Pressures: {len(pressures)} | Ball Recoveries: {len(recoveries)} | Direction: Left → Right",
        color=GRAY_COLOR, fontsize=11, ha='center', va='center'
    )
    plt.tight_layout()
    return fig, pressures, recoveries


def plot_player_heatmap(team_events: pd.DataFrame, player_short: str, team_name: str, match_title: str, show_passes: bool = True):
    """Plot an individual player's KDE Heatmap, Touch Map, and Progressive/Key Passes."""
    p_events = team_events[
        (team_events['player_short'] == player_short) &
        (team_events['x'].notna()) &
        (team_events['y'].notna())
    ].copy()
    p_passes = p_events[p_events['type_name'] == 'Pass'].copy()
    p_comp_passes = p_passes[p_passes['outcome_name'].isna()].copy()

    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2)
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor(BG_COLOR)

    if len(p_events) >= 5:
        pitch.kdeplot(
            p_events['x'], p_events['y'],
            ax=ax, cmap=VIOLET_CMAP, fill=True, levels=100, thresh=0.05, alpha=0.80
        )

    if show_passes and len(p_comp_passes) > 0:
        pitch.arrows(
            p_comp_passes['x'], p_comp_passes['y'],
            p_comp_passes['end_x'], p_comp_passes['end_y'],
            width=1.8, headwidth=3.8, headlength=3.8, color=ACCENT_COLOR, alpha=0.75, zorder=3.2, ax=ax
        )

    if len(p_events) > 0:
        pitch.scatter(
            p_events['x'], p_events['y'],
            s=45, color=MAIN_COLOR, edgecolors=LINE_COLOR, linewidth=0.9, alpha=0.88, zorder=3.5, ax=ax
        )
        avg_x, avg_y = p_events['x'].mean(), p_events['y'].mean()
        pitch.scatter(
            [avg_x], [avg_y],
            s=260, color=ACCENT_COLOR, edgecolors=LINE_COLOR, linewidth=2.0, zorder=4.5, ax=ax
        )
        txt = pitch.annotate(
            f"{player_short}\nAvg ({avg_x:.1f}, {avg_y:.1f})",
            xy=(avg_x, avg_y - 4.0),
            c=TEXT_COLOR, va='center', ha='center', size=10.5, weight='bold', zorder=5, ax=ax
        )
        txt.set_path_effects([path_effects.withStroke(linewidth=2.8, foreground=BG_COLOR)])

    ax.set_title(
        f"{player_short.upper()} — INDIVIDUAL HEATMAP & TOUCH PROFILE",
        color=TEXT_COLOR, fontsize=18, fontweight='bold', pad=20
    )
    ax.text(
        60, -2.5,
        f"{team_name} | {match_title} | On-Ball Actions: {len(p_events)} | Completed Passes: {len(p_comp_passes)}/{len(p_passes)}",
        color=GRAY_COLOR, fontsize=11, ha='center', va='center'
    )
    plt.tight_layout()
    return fig, p_events


def plot_error_proneness_ranking(error_df: pd.DataFrame):
    """Horizontal bar chart ranking all 32 teams from Most to Least Error-Prone."""
    plot_df = error_df.sort_values('error_index', ascending=True).reset_index(drop=True)

    colors = []
    for _, r in plot_df.iterrows():
        if "Spain" in str(r['team_clean']):
            colors.append(MAIN_COLOR)      # Violet highlight for Spain
        elif r['rank'] <= 3:
            colors.append('#F87171')       # Soft red for Top 3 Most Error-Prone
        elif r['rank'] > len(plot_df) - 3:
            colors.append('#10B981')       # Emerald for Top 3 Least Error-Prone
        else:
            colors.append('#3F3F46')       # Neutral dark gray

    fig, ax = plt.subplots(figsize=(11, 10))
    fig.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.barh(plot_df['team_clean'], plot_df['error_index'], color=colors, edgecolor='none', height=0.72)

    for bar, val in zip(bars, plot_df['error_index']):
        ax.text(
            val + 0.6, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va='center', ha='left', color=TEXT_COLOR, fontsize=8.5, fontweight='bold'
        )

    ax.set_xlabel("Error Score per Match  [(Own-Half Losses×1 + →Shot×3 + →Goal×5) / Matches]  ·  Lower = Safer", color=GRAY_COLOR, fontsize=10)
    ax.set_title("2023 WOMEN'S WORLD CUP — MOST vs. LEAST ERROR-PRONE TEAMS", color=TEXT_COLOR, fontsize=15, fontweight='bold', pad=16)
    ax.tick_params(axis='both', colors=TEXT_COLOR, labelsize=9)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(GRAY_COLOR)

    legend_elements = [
        Line2D([0], [0], color='#F87171', lw=6, label='Most Error-Prone (Top 3)'),
        Line2D([0], [0], color=MAIN_COLOR, lw=6, label='Spain (Champions)'),
        Line2D([0], [0], color='#10B981', lw=6, label='Least Error-Prone (Bottom 3)'),
    ]
    leg = ax.legend(handles=legend_elements, loc='lower right', facecolor=BG_COLOR, edgecolor=MAIN_COLOR, fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(TEXT_COLOR)

    plt.tight_layout()
    return fig


def analyze_turnover_punishment(events_df: pd.DataFrame, team_name: str, window_sec: int = 15) -> pd.DataFrame:
    """
    Identify all possession losses (Wrong/Incomplete Passes, Dispossessed, Miscontrol, Failed Dribbles)
    for `team_name` and check whether the opponent took a Shot or scored a Goal within `window_sec` seconds.
    """
    df = events_df.copy()
    sort_cols = [c for c in ['period', 'minute', 'second', 'index'] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)

    df['abs_sec'] = df['minute'].fillna(0).astype(int) * 60 + df['second'].fillna(0).astype(int)

    team_df = df[df['team_name'] == team_name].copy()
    opp_shots = df[(df['team_name'] != team_name) & (df['type_name'] == 'Shot')].copy()

    # Classify turnovers
    wrong_passes = team_df[
        (team_df['type_name'] == 'Pass') &
        (team_df['outcome_name'].isin(['Incomplete', 'Out', 'Pass Offside']))
    ].copy()
    wrong_passes['turnover_type'] = 'Wrong Pass (' + wrong_passes['outcome_name'].astype(str) + ')'

    dispossessed = team_df[team_df['type_name'] == 'Dispossessed'].copy()
    dispossessed['turnover_type'] = 'Dispossessed'

    miscontrols = team_df[team_df['type_name'] == 'Miscontrol'].copy()
    miscontrols['turnover_type'] = 'Miscontrol'

    failed_dribbles = team_df[
        (team_df['type_name'] == 'Dribble') &
        (team_df['outcome_name'] == 'Incomplete')
    ].copy()
    failed_dribbles['turnover_type'] = 'Failed Dribble'

    turnovers = pd.concat([wrong_passes, dispossessed, miscontrols, failed_dribbles], ignore_index=True)
    turnovers = turnovers[turnovers['x'].notna() & turnovers['y'].notna()].copy()
    if len(turnovers) == 0:
        return pd.DataFrame()

    turnovers = turnovers.sort_values(['period', 'abs_sec']).reset_index(drop=True)

    led_to_shot = []
    led_to_goal = []
    shot_time_list = []
    sec_to_shot_list = []
    opp_shooter_list = []
    opp_xg_list = []
    opp_outcome_list = []
    opp_shot_x_list = []
    opp_shot_y_list = []

    for _, row in turnovers.iterrows():
        t_per = row['period']
        t_sec = row['abs_sec']
        matches_shot = opp_shots[
            (opp_shots['period'] == t_per) &
            (opp_shots['abs_sec'] >= t_sec) &
            ((opp_shots['abs_sec'] - t_sec) <= window_sec)
        ]
        if len(matches_shot) > 0:
            # Prioritize Goal if one occurred in the window, otherwise take the first shot
            goals_in_win = matches_shot[matches_shot['outcome_name'] == 'Goal']
            chosen = goals_in_win.iloc[0] if len(goals_in_win) > 0 else matches_shot.iloc[0]
            led_to_shot.append(True)
            led_to_goal.append(bool(chosen['outcome_name'] == 'Goal'))
            shot_time_list.append(f"{int(chosen['minute']):02d}:{int(chosen['second']):02d}")
            sec_to_shot_list.append(int(chosen['abs_sec'] - t_sec))
            opp_shooter_list.append(chosen.get('player_short', chosen.get('player_name', 'Opponent')))
            xg_val = chosen.get('shot_statsbomb_xg', 0.0)
            opp_xg_list.append(float(xg_val) if pd.notna(xg_val) else 0.0)
            opp_outcome_list.append(str(chosen.get('outcome_name', 'Shot')))
            # Flip opponent shot coordinates onto selected_team's pitch orientation (0=own goal, 120=opp goal)
            opp_shot_x_list.append(120.0 - float(chosen['x']) if pd.notna(chosen['x']) else np.nan)
            opp_shot_y_list.append(80.0 - float(chosen['y']) if pd.notna(chosen['y']) else np.nan)
        else:
            led_to_shot.append(False)
            led_to_goal.append(False)
            shot_time_list.append("—")
            sec_to_shot_list.append(np.nan)
            opp_shooter_list.append("—")
            opp_xg_list.append(0.0)
            opp_outcome_list.append("No Shot")
            opp_shot_x_list.append(np.nan)
            opp_shot_y_list.append(np.nan)

    turnovers['time_str'] = turnovers.apply(lambda r: f"{int(r['minute']):02d}:{int(r['second']):02d}", axis=1)
    turnovers['led_to_shot'] = led_to_shot
    turnovers['led_to_goal'] = led_to_goal
    turnovers['shot_time_str'] = shot_time_list
    turnovers['sec_to_shot'] = sec_to_shot_list
    turnovers['opp_shooter'] = opp_shooter_list
    turnovers['opp_xg'] = opp_xg_list
    turnovers['opp_outcome'] = opp_outcome_list
    turnovers['opp_shot_x'] = opp_shot_x_list
    turnovers['opp_shot_y'] = opp_shot_y_list
    return turnovers


def plot_turnover_punishment(
    turnovers_df: pd.DataFrame,
    team_name: str,
    match_title: str,
    player_filter: str = "All Players (Whole Team)",
    window_sec: int = 15,
    punished_only: bool = False
):
    """Plot turnovers on the pitch colored by whether they led to an opponent Goal, Shot, or no shot."""
    df = turnovers_df.copy()
    if player_filter != "All Players (Whole Team)":
        df = df[df['player_short'] == player_filter].copy()

    unpunished = df[~df['led_to_shot']].copy()
    shot_only = df[df['led_to_shot'] & (~df['led_to_goal'])].copy()
    goal_punished = df[df['led_to_goal']].copy()

    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.5, line_zorder=2)
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor(BG_COLOR)

    if not punished_only and len(unpunished) > 0:
        pitch.scatter(
            unpunished['x'], unpunished['y'],
            s=55, color=GRAY_COLOR, edgecolors=BG_COLOR, alpha=0.40, zorder=2.5, ax=ax
        )

    if len(shot_only) > 0:
        pitch.scatter(
            shot_only['x'], shot_only['y'],
            s=130, color=ACCENT_COLOR, edgecolors=LINE_COLOR, linewidth=1.2, alpha=0.90, zorder=3.5, ax=ax
        )
        for _, row in shot_only.iterrows():
            if pd.notna(row['opp_shot_x']) and pd.notna(row['opp_shot_y']):
                pitch.lines(
                    row['x'], row['y'], row['opp_shot_x'], row['opp_shot_y'],
                    lw=1.6, color=ACCENT_COLOR, alpha=0.55, zorder=3.0, ax=ax
                )
            txt = pitch.annotate(
                f"{row['time_str']} {row['player_short']}",
                xy=(row['x'], row['y'] - 3.0),
                c=ACCENT_COLOR, va='center', ha='center', size=8.5, weight='bold', zorder=4.2, ax=ax
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=2.2, foreground=BG_COLOR)])

    if len(goal_punished) > 0:
        pitch.scatter(
            goal_punished['x'], goal_punished['y'],
            s=230, color=MAIN_COLOR, edgecolors=LINE_COLOR, linewidth=2.2, alpha=1.0, zorder=4.5, ax=ax
        )
        for _, row in goal_punished.iterrows():
            if pd.notna(row['opp_shot_x']) and pd.notna(row['opp_shot_y']):
                pitch.arrows(
                    row['x'], row['y'], row['opp_shot_x'], row['opp_shot_y'],
                    width=2.5, headwidth=4.5, headlength=4.5, color=MAIN_COLOR, alpha=0.95, zorder=4.0, ax=ax
                )
                pitch.scatter(
                    [row['opp_shot_x']], [row['opp_shot_y']],
                    s=140, color=TEXT_COLOR, edgecolors=MAIN_COLOR, marker='*', linewidth=1.5, zorder=4.8, ax=ax
                )
            txt = pitch.annotate(
                f"GOAL {row['shot_time_str']}!\n({row['time_str']} {row['player_short']})",
                xy=(row['x'], row['y'] - 4.2),
                c=TEXT_COLOR, va='center', ha='center', size=9.5, weight='bold', zorder=5.0, ax=ax
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=2.8, foreground=BG_COLOR)])

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=f"Led to Goal ({len(goal_punished)})", markerfacecolor=MAIN_COLOR, markersize=11),
        Line2D([0], [0], marker='o', color='w', label=f"Led to Shot ({len(shot_only)})", markerfacecolor=ACCENT_COLOR, markersize=9),
    ]
    if not punished_only:
        legend_elements.append(
            Line2D([0], [0], marker='o', color='w', label=f"No Shot in {window_sec}s ({len(unpunished)})", markerfacecolor=GRAY_COLOR, markersize=7)
        )
    leg = ax.legend(handles=legend_elements, loc='upper right', facecolor=BG_COLOR, edgecolor=MAIN_COLOR, fontsize=10.5)
    for t in leg.get_texts():
        t.set_color(TEXT_COLOR)

    scope_label = team_name.upper() if player_filter == "All Players (Whole Team)" else f"{player_filter.upper()} ({team_name})"
    ax.set_title(
        f"{scope_label} — TURNOVER PUNISHMENT MAP ({window_sec}s WINDOW)",
        color=TEXT_COLOR, fontsize=17.5, fontweight='bold', pad=20
    )
    ax.text(
        60, -2.5,
        f"{match_title} | Turnovers: {len(df)} | Led to Shot: {len(shot_only) + len(goal_punished)} | Led to Goal: {len(goal_punished)} (Attacking Left → Right)",
        color=GRAY_COLOR, fontsize=10.5, ha='center', va='center'
    )
    plt.tight_layout()
    return fig, df


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏆 Filters")
    st.caption("2023 FIFA Women's World Cup · StatsBomb Open Data")
    st.divider()

    # Load 2023 FIFA Women's World Cup matches (competition_id=72, season_id=107)
    all_matches = load_matches(competition_id=WWC_COMPETITION_ID, season_id=WWC_SEASON_ID)

    spain_only = st.checkbox("🇪🇸 Show Only Spain's Matches (Champions)", value=True)
    if spain_only:
        matches = all_matches[
            (all_matches['home_team_name'].str.contains('Spain', case=False, na=False)) |
            (all_matches['away_team_name'].str.contains('Spain', case=False, na=False))
        ].reset_index(drop=True)
        if len(matches) == 0:
            matches = all_matches
    else:
        matches = all_matches

    match_label = st.selectbox("Select a Match", matches['label'], index=0)
    match_row = matches[matches['label'] == match_label].iloc[0]
    match_id = int(match_row['match_id'])

    events = load_events(match_id)
    teams = sorted(events['team_name'].dropna().unique())

    # Default to Spain Women's whenever Spain is one of the competing teams
    default_team_idx = 0
    for idx, t_name in enumerate(teams):
        if "Spain" in t_name:
            default_team_idx = idx
            break

    selected_team = st.selectbox("Select a Team", teams, index=default_team_idx)

    plot_type = st.radio("Visualization", [
        "Passing Network",
        "Pass & Progression Map",
        "Shot Map",
        "Pressure Heatmap",
        "Player Heatmap",
        "Turnover Punishment (Loss → Goal/Shot)",
        "Tournament Error-Proneness Ranking"
    ])

    # Context-sensitive controls for the chosen visualization (safe defaults)
    min_pass_links = 4
    pass_map_mode = "Progressive Passes & Carries"
    selected_player = None
    overlay_player_passes = True
    turnover_player_filter = "All Players (Whole Team)"
    punishment_window_sec = 15
    show_punished_only = False

    if plot_type == "Passing Network":
        st.divider()
        min_pass_links = st.slider("Min. Passes per Connection", min_value=2, max_value=12, value=4, step=1)
    elif plot_type == "Pass & Progression Map":
        st.divider()
        pass_map_mode = st.selectbox(
            "Pass View Mode",
            ["Progressive Passes & Carries", "All Passes (Completed vs. Incomplete)"]
        )
    elif plot_type == "Player Heatmap":
        st.divider()
        team_player_counts = (
            events[(events['team_name'] == selected_team) & (events['x'].notna())]['player_short']
            .value_counts()
        )
        available_players = team_player_counts.index.tolist()
        selected_player = st.selectbox("Select a Player", available_players, index=0)
        overlay_player_passes = st.checkbox("Overlay Completed Passes", value=True)
    elif plot_type == "Turnover Punishment (Loss → Goal/Shot)":
        st.divider()
        team_player_counts = (
            events[(events['team_name'] == selected_team) & (events['x'].notna())]['player_short']
            .value_counts()
        )
        available_players = team_player_counts.index.tolist()
        turnover_player_filter = st.selectbox(
            "Player Scope",
            ["All Players (Whole Team)"] + available_players,
            index=0
        )
        punishment_window_sec = st.slider(
            "Punishment Window (seconds)",
            min_value=5,
            max_value=30,
            value=15,
            step=1,
            help="Time window after losing possession to check for an opponent shot or goal."
        )
        show_punished_only = st.checkbox("Show Only Turnovers Leading to Shot / Goal", value=False)

    st.divider()
    st.caption("Football Data Analysis Mentorship")
    st.caption("Cohort 2 — Sara Bentelli")

# ─────────────────────────────────────────────────────────────
# MAIN HEADER & MATCH SCOREBOARD
# ─────────────────────────────────────────────────────────────
st.title("🇪🇸 2023 FIFA Women's World Cup — Tactical Match Dashboard")
st.caption("Exploring Spain's Historic First World Cup Title · Powered by 100% StatsBomb Open Data (`competition_id=72`, `season_id=107`)")

home_team = match_row['home_team_name']
away_team = match_row['away_team_name']
home_score = int(match_row['home_score'])
away_score = int(match_row['away_score'])
stage_name = match_row.get('competition_stage_name', 'Tournament Match')
stadium_name = match_row.get('stadium_name', 'Australia / New Zealand')
match_date_str = str(match_row['match_date'])[:10]

st.markdown(f"""
<div class="scoreboard-box">
    <div class="scoreboard-stage">FIFA Women's World Cup 2023 · {stage_name}</div>
    <div class="scoreboard-teams">
        {home_team} <span class="scoreboard-score">{home_score} – {away_score}</span> {away_team}
    </div>
    <div class="scoreboard-meta">📅 {match_date_str} &nbsp;|&nbsp; 🏟️ {stadium_name} &nbsp;|&nbsp; StatsBomb Match ID: {match_id}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# METRICS ROW
# ─────────────────────────────────────────────────────────────
team_events = events[events['team_name'] == selected_team].copy()
opp_team = away_team if selected_team == home_team else home_team
opp_events = events[events['team_name'] == opp_team].copy()

team_passes_df = team_events[team_events['type_name'] == 'Pass']
team_comp_passes_df = team_passes_df[team_passes_df['outcome_name'].isna()]
team_shots_df = team_events[team_events['type_name'] == 'Shot']
team_pressures_df = team_events[team_events['type_name'] == 'Pressure']
team_carries_df = team_events[team_events['type_name'] == 'Carry']
team_recoveries_df = team_events[team_events['type_name'] == 'Ball Recovery']

team_xg = team_shots_df['shot_statsbomb_xg'].fillna(0).sum() if 'shot_statsbomb_xg' in team_shots_df.columns else 0.0
opp_shots_df = opp_events[opp_events['type_name'] == 'Shot']
opp_xg = opp_shots_df['shot_statsbomb_xg'].fillna(0).sum() if 'shot_statsbomb_xg' in opp_shots_df.columns else 0.0
pass_acc = len(team_comp_passes_df) / max(1, len(team_passes_df)) * 100.0
prog_pass_count = len(team_comp_passes_df[(team_comp_passes_df['end_x'] - team_comp_passes_df['x']) >= 10.0])

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Total Passes",
    f"{len(team_passes_df)}",
    f"{pass_acc:.1f}% completion ({len(team_comp_passes_df)} comp.)"
)
col2.metric(
    "Total Shots",
    f"{len(team_shots_df)}",
    f"{team_xg:.2f} xG (vs. {opp_xg:.2f} opp. xG)"
)
col3.metric(
    "Pressures",
    f"{len(team_pressures_df)}",
    f"{len(team_recoveries_df)} Ball Recoveries"
)
col4.metric(
    "Carries",
    f"{len(team_carries_df)}",
    f"{prog_pass_count} Progressive Passes (≥10m)"
)

st.divider()

# ─────────────────────────────────────────────────────────────
# RENDER SELECTED VISUALIZATION & TACTICAL BREAKDOWN
# ─────────────────────────────────────────────────────────────
clean_home = home_team.replace(" Women's", "")
clean_away = away_team.replace(" Women's", "")
match_short_title = f"{clean_home} {home_score}–{away_score} {clean_away} ({stage_name})"

if plot_type == "Tournament Error-Proneness Ranking":
    if not os.path.exists(ERROR_INDEX_CSV):
        st.warning(
            f"Pre-computed file `{ERROR_INDEX_CSV}` not found. "
            "Run `python build_error_index.py` locally and push the generated CSV to your repository."
        )
    else:
        error_df = load_tournament_error_index(ERROR_INDEX_CSV)
        most_err = error_df.iloc[0]
        least_err = error_df.iloc[-1]
        spain_matches = error_df[error_df['team_clean'].str.contains('Spain', case=False, na=False)]

        st.subheader("🏆 Tournament Error-Proneness Ranking (All 32 Teams)")
        k1, k2, k3 = st.columns(3)
        k1.metric(
            "Most Error-Prone Team",
            str(most_err['team_clean']),
            f"Error Score: {most_err['error_index']:.1f} / match",
            delta_color="off"
        )
        k2.metric(
            "Least Error-Prone Team",
            str(least_err['team_clean']),
            f"Error Score: {least_err['error_index']:.1f} / match",
            delta_color="off"
        )
        if len(spain_matches) > 0:
            spain_row = spain_matches.iloc[0]
            k3.metric(
                "Spain (Champions)",
                f"#{int(spain_row['rank'])} of {len(error_df)}",
                f"Error Score: {spain_row['error_index']:.1f} / match",
                delta_color="off"
            )

        st.info(
            "**How to read Error Score (per match):** Weighted penalty score combining own-half ball losses "
            "(**+1 pt** each), turnovers leading to an opponent shot within 15s (**+3 pts**), and turnovers "
            "leading to a goal (**+5 pts**), divided by matches played. **Lower score = safer, more composed team.**"
        )

        viz_col, table_col = st.columns([1.65, 1.0], gap="large")
        with viz_col:
            fig = plot_error_proneness_ranking(error_df)
            st.pyplot(fig, use_container_width=True)

        with table_col:
            st.subheader("📋 Full 32-Team Leaderboard")
            display_df = error_df[[
                'rank', 'team_clean', 'matches_played', 'own_half_per_match',
                'punished_per_match', 'led_to_goal', 'opp_xg_per_match', 'error_index'
            ]].rename(columns={
                'rank': '#',
                'team_clean': 'Team',
                'matches_played': 'MP',
                'own_half_per_match': 'Own-Half/M',
                'punished_per_match': '→Shot/M',
                'led_to_goal': '→Goal',
                'opp_xg_per_match': 'Opp xG/M',
                'error_index': 'Error Score'
            }).round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=720)

else:
    viz_col, table_col = st.columns([1.65, 1.0], gap="large")

if plot_type == "Passing Network":
    fig, avg_locs, edges = plot_passing_network(team_events, selected_team, match_short_title, min_passes=min_pass_links)
    with viz_col:
        st.subheader("🕸️ Team Passing Network & Spatial Structure")
        st.pyplot(fig, use_container_width=True)
    with table_col:
        st.subheader("📊 Top Passing Combinations")
        if len(edges) > 0:
            top_edges = (
                edges[['pair_min', 'pair_max', 'pass_count']]
                .sort_values('pass_count', ascending=False)
                .rename(columns={'pair_min': 'Player A', 'pair_max': 'Player B', 'pass_count': 'Passes Exchanged'})
                .reset_index(drop=True)
            )
            st.dataframe(top_edges.head(10), use_container_width=True, hide_index=True)
        st.subheader("🎯 Hub Involvement (Core 11)")
        if len(avg_locs) > 0:
            hub_table = (
                avg_locs[['player_short', 'count', 'x', 'y']]
                .sort_values('count', ascending=False)
                .rename(columns={'player_short': 'Player', 'count': 'Completed Passes', 'x': 'Avg X', 'y': 'Avg Y'})
                .round(1)
            )
            st.dataframe(hub_table, use_container_width=True, hide_index=True)

elif plot_type == "Pass & Progression Map":
    fig, prog_passes, prog_carries = plot_pass_and_progression_map(team_events, selected_team, match_short_title, mode=pass_map_mode)
    with viz_col:
        st.subheader(f"🚀 {pass_map_mode}")
        st.pyplot(fig, use_container_width=True)
    with table_col:
        st.subheader("⚡ Top Ball Progressors")
        prog_pass_counts = prog_passes['player_short'].value_counts().rename("Prog. Passes")
        prog_carry_counts = prog_carries['player_short'].value_counts().rename("Prog. Carries")
        prog_summary = pd.concat([prog_pass_counts, prog_carry_counts], axis=1).fillna(0).astype(int)
        prog_summary['Total Progressions'] = prog_summary['Prog. Passes'] + prog_summary['Prog. Carries']
        prog_summary = prog_summary.sort_values('Total Progressions', ascending=False).reset_index().rename(columns={'index': 'Player', 'player_short': 'Player'})
        st.dataframe(prog_summary.head(12), use_container_width=True, hide_index=True)
        st.info(
            f"**Tactical Progression Insight:** {selected_team} completed **{len(prog_passes)} progressive passes** "
            f"and **{len(prog_carries)} progressive carries** (advancing the ball ≥10 yards toward the opponent's goal)."
        )

elif plot_type == "Shot Map":
    fig, shots_df = plot_shot_map(team_events, selected_team, match_short_title)
    with viz_col:
        st.subheader("🎯 Shot Map (Scaled by StatsBomb xG)")
        st.pyplot(fig, use_container_width=True)
    with table_col:
        st.subheader("📋 Match Shot Log")
        if len(shots_df) > 0:
            shot_table = (
                shots_df[['minute', 'player_short', 'xg', 'outcome_name', 'body_part_name']]
                .sort_values(['xg', 'minute'], ascending=[False, True])
                .rename(columns={
                    'minute': 'Min',
                    'player_short': 'Player',
                    'xg': 'xG',
                    'outcome_name': 'Outcome',
                    'body_part_name': 'Body Part'
                })
                .round({'xG': 3})
            )
            st.dataframe(shot_table, use_container_width=True, hide_index=True)
        else:
            st.warning("No shots recorded for this selection.")

        key_passes_df = team_passes_df[
            team_passes_df['pass_goal_assist'].notna() |
            team_passes_df['pass_shot_assist'].notna()
        ]
        st.subheader("🔑 Top Chance Creators (Key Passes)")
        if len(key_passes_df) > 0:
            kp_table = (
                key_passes_df.groupby('player_short')
                .agg(
                    Key_Passes=('id', 'count'),
                    Goal_Assists=('pass_goal_assist', lambda s: int(s.notna().sum()))
                )
                .sort_values(['Goal_Assists', 'Key_Passes'], ascending=False)
                .reset_index()
                .rename(columns={'player_short': 'Player', 'Key_Passes': 'Key Passes', 'Goal_Assists': 'Goal Assists'})
            )
            st.dataframe(kp_table, use_container_width=True, hide_index=True)

elif plot_type == "Pressure Heatmap":
    fig, pressures_df, recoveries_df = plot_pressure_heatmap(team_events, selected_team, match_short_title)
    with viz_col:
        st.subheader("🛡️ Defensive Pressure KDE & Ball Recoveries")
        st.pyplot(fig, use_container_width=True)
    with table_col:
        st.subheader("🔥 Pressing & Recovery Leaders")
        press_counts = pressures_df['player_short'].value_counts().rename("Pressures")
        rec_counts = recoveries_df['player_short'].value_counts().rename("Recoveries")
        def_summary = pd.concat([press_counts, rec_counts], axis=1).fillna(0).astype(int)
        def_summary['Total Def. Actions'] = def_summary['Pressures'] + def_summary['Recoveries']
        def_summary = def_summary.sort_values('Total Def. Actions', ascending=False).reset_index().rename(columns={'index': 'Player', 'player_short': 'Player'})
        st.dataframe(def_summary.head(12), use_container_width=True, hide_index=True)

        avg_px = pressures_df['x'].mean() if len(pressures_df) > 0 else 0.0
        high_press_pct = (pressures_df['x'] >= 60.0).mean() * 100.0 if len(pressures_df) > 0 else 0.0
        st.info(
            f"**Defensive Line Profile:** {selected_team} maintained an average pressure height of **x = {avg_px:.1f}**, "
            f"with **{high_press_pct:.1f}%** of pressures applied in the opponent's half (`x ≥ 60`)."
        )

elif plot_type == "Player Heatmap":
    fig, p_events = plot_player_heatmap(
        team_events, selected_player, selected_team, match_short_title, show_passes=overlay_player_passes
    )
    with viz_col:
        st.subheader(f"👟 {selected_player} — Spatial Heatmap & Pass Profile")
        st.pyplot(fig, use_container_width=True)
    with table_col:
        st.subheader(f"📈 {selected_player} — Action Breakdown")
        action_counts = (
            p_events['type_name']
            .value_counts()
            .reset_index()
        )
        action_counts.columns = ['Event Type', 'Count']
        st.dataframe(action_counts, use_container_width=True, hide_index=True)

        def_pct = (p_events['x'] < 40).mean() * 100.0 if len(p_events) > 0 else 0.0
        mid_pct = (p_events['x'].between(40, 80)).mean() * 100.0 if len(p_events) > 0 else 0.0
        att_pct = (p_events['x'] > 80).mean() * 100.0 if len(p_events) > 0 else 0.0
        st.info(
            f"**Zonal Touch Split for {selected_player}:**\n"
            f"- **Defensive Third:** {def_pct:.1f}%\n"
            f"- **Middle Third:** {mid_pct:.1f}%\n"
            f"- **Final Third:** {att_pct:.1f}%"
        )

elif plot_type == "Turnover Punishment (Loss → Goal/Shot)":
    turnovers_all = analyze_turnover_punishment(events, selected_team, window_sec=punishment_window_sec)
    if len(turnovers_all) > 0:
        fig, filtered_turnovers = plot_turnover_punishment(
            turnovers_all,
            selected_team,
            match_short_title,
            player_filter=turnover_player_filter,
            window_sec=punishment_window_sec,
            punished_only=show_punished_only
        )
        with viz_col:
            st.subheader(f"⚠️ Possession Losses → Opponent Shots & Goals ({punishment_window_sec}s Window)")
            st.pyplot(fig, use_container_width=True)
        with table_col:
            punished_df = filtered_turnovers[filtered_turnovers['led_to_shot']].copy()
            st.subheader("🕒 Punished Turnovers (Cross-Reference Log)")
            if len(punished_df) > 0:
                log_cols = ['time_str', 'period', 'player_short', 'turnover_type', 'sec_to_shot', 'opp_outcome', 'opp_shooter', 'opp_xg']
                log_table = (
                    punished_df[log_cols]
                    .sort_values(['opp_outcome', 'period', 'time_str'], ascending=[True, True, True])
                    .rename(columns={
                        'time_str': 'Loss Time',
                        'period': 'Half',
                        'player_short': 'Player',
                        'turnover_type': 'Loss Type',
                        'sec_to_shot': 'Sec → Shot',
                        'opp_outcome': 'Result',
                        'opp_shooter': 'Opp. Shooter',
                        'opp_xg': 'Opp. xG'
                    })
                    .round({'Opp. xG': 2})
                )
                st.dataframe(log_table, use_container_width=True, hide_index=True)
            else:
                st.info(f"No turnovers led to an opponent shot within {punishment_window_sec} seconds for this selection.")

            st.subheader("📊 Team Turnover Punishment Breakdown")
            summary_tbl = (
                filtered_turnovers.groupby('player_short')
                .agg(
                    Total_Losses=('id', 'count'),
                    Wrong_Passes=('turnover_type', lambda s: int(s.str.startswith('Wrong Pass').sum())),
                    Dispossessed=('turnover_type', lambda s: int((s == 'Dispossessed').sum())),
                    Led_to_Shot=('led_to_shot', lambda s: int(s.sum())),
                    Led_to_Goal=('led_to_goal', lambda s: int(s.sum())),
                    Opp_xG_Conceded=('opp_xg', 'sum')
                )
                .sort_values(['Led_to_Goal', 'Led_to_Shot', 'Total_Losses'], ascending=[False, False, False])
                .reset_index()
                .rename(columns={
                    'player_short': 'Player',
                    'Total_Losses': 'Losses',
                    'Wrong_Passes': 'Wrong Pass',
                    'Dispossessed': 'Disposs.',
                    'Led_to_Shot': '→ Shot',
                    'Led_to_Goal': '→ Goal',
                    'Opp_xG_Conceded': 'Opp. xG'
                })
                .round({'Opp. xG': 2})
            )
            st.dataframe(summary_tbl, use_container_width=True, hide_index=True)
    else:
        st.warning("No turnover events found for this team selection.")


# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.divider()
st.caption("Football Data Analysis Mentorship — Cohort 2  ·  Sara Bentelli  ·  2026  ·  Data: StatsBomb Open Data (FIFA Women's World Cup 2023)")