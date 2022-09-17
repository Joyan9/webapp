import streamlit as st
import pandas as pd
import numpy as np
from statsbombpy import sb
import matplotlib.pyplot as plt
import seaborn as sns
from mplsoccer import Pitch,FontManager,Sbopen, Pitch
robotto_regular = FontManager()

@st.experimental_memo
def get_teams_name():
    # get match teams name
    matches = sb.matches(competition_id = 1238, season_id = 108)
    teams = matches.home_team.unique()
    return teams

def get_match_id(home_team,away_team):
    matches = sb.matches(competition_id = 1238, season_id = 108)
    match_id = matches[(matches.home_team == home_team)&(matches.away_team == away_team)].match_id.values[0]
    return match_id

def get_events(home_team, away_team):
    match_id = get_match_id(home_team, away_team)
    events = sb.events(match_id = match_id)
    return events

def get_player_list(home_team, away_team):
    df = get_events(home_team, away_team)
    home_players = df[df.team == home_team]['player'].dropna().unique()
    away_players = df[df.team == away_team]['player'].dropna().unique()
    return home_players, away_players

def get_xT_grid():
    xT_grid = pd.read_csv('xT_grid.csv')
    return xT_grid
def get_event_data():
    event = pd.read_csv("ISL_2021-22_xT.csv")
    return event                     

def get_player_xT(home_team,away_team,player_name):
    xT = get_xT_grid()
    event = get_event_data()
    df = event[event.match_id == get_match_id(home_team,away_team)]
    df = df.loc[df['player_name'] == player_name]
    xT = np.array(xT)
    xT_rows, xT_cols = xT.shape
    try:
        df['x1_bin'] = pd.cut(df['x'], bins=xT_cols, labels=False)
        df['y1_bin'] = pd.cut(df['y'], bins=xT_rows, labels=False)
        df['x2_bin'] = pd.cut(df['end_x'], bins=xT_cols, labels=False)
        df['y2_bin'] = pd.cut(df['end_y'], bins=xT_rows, labels=False)
        df['start_zone_value'] = df[['x1_bin', 'y1_bin']].apply(lambda x: xT[x[1]][x[0]], axis=1)
        df['end_zone_value'] = df[['x2_bin', 'y2_bin']].apply(lambda x: xT[x[1]][x[0]], axis=1)
        df['xT'] = df['end_zone_value'] - df['start_zone_value']
        player_xT = round(df['xT'].sum(),2)
        return player_xT
    except:
        return None
    
def get_all_players_xT(home_team,away_team):
    players = get_player_list(home_team, away_team)
    players = np.concatenate( players, axis=0 )
    players_xT = pd.DataFrame()
    players_xT['players'] = players
    players_xT['xT'] = np.nan
    players_xT_list = []
    for i in range(len(players_xT)):
        players_xT_list.append(get_player_xT(home_team, away_team,players[i]))
    
    players_xT['xT'] = players_xT_list
    players_xT.sort_values(by='xT', axis=0, ascending=False, inplace=True)
    return players_xT

def plot_top_10_creators(home_team,away_team):
    players_xT = get_all_players_xT(home_team,away_team)[:9]
    fig = plt.figure(figsize=(12,10))
    
    ax = sns.barplot(y=players_xT['players'],x=players_xT['xT'],palette="rocket_r")
    ax.bar_label(ax.containers[0])
    ax.text(1, 8.2, '@BhathenaJoyan',
                                       va='center', ha='right', fontsize=15,
                                       fontproperties=robotto_regular.prop, color='#dee6ea')
    
    ax.text(0.4, -1, f"Top 10 xT | {home_team} vs {away_team}",
                                   color='black', va='center', ha='center',
                                   fontproperties=robotto_regular.prop, fontsize=25)
    return plt.show()
teams = get_teams_name()
#----SIDEBAR----
st.sidebar.header("First Select Home Team and then Select Away team")
teams = st.sidebar.multiselect(
    "Select teams (max 2):",
    options=teams,
    default = ['Goa','Mumbai City']
)
home_team, away_team = teams[0], teams[1] 

#----HOME PAGE----
col = st.columns(1)
if len(teams) == 2:
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot(fig=plot_top_10_creators(home_team,away_team))

st.write("Made by Joyan Bhathena, joyansbhathena@gmail.com")
