import streamlit as st
import pandas as pd
import numpy as np
from mplsoccer.pitch import Pitch
#import seaborn as sns
from matplotlib.colors import to_rgba
import matplotlib.pyplot as plt
from statsbombpy import sb
#import networkx as nx

st.title("Pass Analysis")


@st.experimental_memo
def get_teams_name():
    # get match teams name
    matches = sb.matches(competition_id = 1238, season_id = 108)
    teams = matches.home_team.unique()
    return teams

def get_events(home_team, away_team):
    matches = sb.matches(competition_id = 1238, season_id = 108)
    match_id = matches[(matches.home_team == home_team)&(matches.away_team == away_team)].match_id.values[0]
    events = sb.events(match_id = match_id)
    return events

def get_pass_df(home_team, away_team, team_req):
    events = get_events(home_team, away_team)
    if team_req == 'home':
        team_name = home_team
    else:
        team_name = away_team
    events_pn = events[['minute','second','team','type','location','pass_end_location','pass_outcome','player']]
    team_pass_mask = (events_pn.type == 'Pass') & (events_pn.team == team_name)
    
    tact = events[events['tactics'].isnull()==False][['tactics','team','type']]
    tact = tact[tact['type']=='Starting XI']
    tact_team_name = tact[tact.team==team_name]['tactics']
    try:
        dict_team_name = tact_team_name[0]['lineup']
    except:
        dict_team_name = tact_team_name[1]['lineup']

    lineup_team_name = pd.DataFrame.from_dict(dict_team_name)
    players_team_name = {}
    for i in range(len(lineup_team_name)):
        key = lineup_team_name.player[i]['name']
        val = lineup_team_name.jersey_number[i]
        players_team_name[key] = str(val)
    
    events_team_name = events_pn[team_pass_mask]
    events_team_name['pass_maker'], events_team_name['pass_receiver'] = events_team_name['player'], events_team_name['player'].shift(-1)
    events_team_name = events_team_name[events_team_name['pass_outcome'].isnull()==True].reset_index()
    subs_team_name = events[(events.team==team_name)&(events['type']=='Substitution')]
    subs_team_name_min = np.min(subs_team_name['minute'])
    subs_team_name_min_data = subs_team_name[subs_team_name['minute']==subs_team_name_min]
    events_team_name = events_team_name[events_team_name.minute <= subs_team_name_min]
    loc = events_team_name['location']
    loc = pd.DataFrame(loc.to_list(), columns = ['pass_maker_x','pass_maker_y']) 
    loc_end = events_team_name['pass_end_location']
    loc_end = pd.DataFrame(loc_end.to_list(), columns = ['pass_receiver_x','pass_receiver_y'])

    events_team_name['pass_maker_x'] = loc['pass_maker_x']
    events_team_name['pass_maker_y'] = loc['pass_maker_y']
    events_team_name['pass_receiver_x'] = loc_end['pass_receiver_x']
    events_team_name['pass_receiver_y'] = loc_end['pass_receiver_y']

    return events_team_name

def pass_network(home_team, away_team, team_req):
    events_team_name = get_pass_df(home_team, away_team, team_req)
    
    av_loc_team_name = events_team_name.groupby('pass_maker').agg({'pass_maker_x':['mean'],'pass_maker_y':['mean','count']})
    av_loc_team_name.columns = ['pass_maker_x','pass_maker_y','count']
    
    pass_team_name = events_team_name.groupby(['pass_maker','pass_receiver']).index.count().reset_index()
    pass_team_name.rename(columns={'index':'number_of_passes'},inplace=True)
    
    pass_team_name = pass_team_name.merge(av_loc_team_name, left_on = 'pass_maker', right_index = True)
    pass_team_name = pass_team_name.merge(av_loc_team_name, left_on = 'pass_receiver', right_index = True, suffixes=['','_receipt'])
    pass_team_name.rename(columns = {'pass_maker_x_receipt':'pass_receiver_x',
                                 'pass_maker_y_receipt':'pass_receiver_y',
                                 'count_receipt':'number_of_passes_received'
                                 }, inplace = True)
    pass_team_name = pass_team_name[(pass_team_name.pass_maker != pass_team_name.pass_receiver)&(pass_team_name['count']>2)].reset_index()
    
    pass_team_name_new = pass_team_name.replace({'pass_maker':players_team_name,'pass_receiver':players_team_name})
    
    av_loc_team_name.dropna(inplace=True)
    
    MAX_LINE_WIDTH = 8
    pass_team_name_new['width'] = (pass_team_name_new['count'] / pass_team_name_new['count'].max() * MAX_LINE_WIDTH)
    
    MIN_TRANSPARENCY = 0.3
    color = np.array(to_rgba('white'))
    color = np.tile(color, (len(pass_team_name_new), 1))
    c_transparency = pass_team_name_new['count'] / pass_team_name_new['count'].max()
    c_transparency = (c_transparency * (1 - MIN_TRANSPARENCY)) + MIN_TRANSPARENCY
    color[:, 3] = c_transparency

    
    pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='#c7d5cc')

    fig, ax = pitch.draw(figsize=(16,10), constrained_layout=True, tight_layout=True)

    plt.title(f"{home_team} Vs {away_team} -  {team_name} Pass Map", fontsize=30)
    arrows = pitch.lines(pass_team_name.pass_maker_x,pass_team_name.pass_maker_y,
                     pass_team_name.pass_receiver_x,pass_team_name.pass_receiver_y,ax=ax,
                     lw=pass_team_name_new.width,color=color, zorder=1, alpha=0.5)

    for index,row in av_loc_team_name.iterrows():
        pitch.annotate(row.name.split(' ')[0], xy=(row.pass_maker_x, row.pass_maker_y), c='black', va='center',
                       ha='center', size=8, weight='bold', ax=ax)
        
    return fig

def pass_flow(home_team,away_team, team_req):
    pass_df = get_pass_df(home_team,away_team,team_req)
    events= get_events(home_team, away_team)
    if team_req == 'home':
        team_name = home_team
    else:
        team_name = away_team
    pitch = Pitch(pitch_color='grass', line_color='white', line_zorder=2)
    fig, ax = pitch.draw(figsize=(16,10))
    # plot the heatmap (darker color means more passes from that square)
    bins = (6, 3)  # divide pitch to 6 columns and 3 rows
    bins_heatmap = pitch.bin_statistic(pass_df.pass_maker_x, pass_df.pass_maker_y, statistic='count', bins=bins)
    pitch.heatmap(bins_heatmap, ax=ax, cmap='Reds')
    # plot the arrows pass flow
    pitch.flow(
        xstart=pass_df.pass_maker_x, ystart=pass_df.pass_maker_y, xend=pass_df.pass_receiver_x, yend=pass_df.pass_receiver_y,
        ax=ax, color='black', arrow_type='same', arrow_length=9, bins=bins
    )
    ax.set_title(f'{team_name} Pass Flow Map', fontsize=30)
    
    return fig



teams = get_teams_name()
#----SIDEBAR----
st.sidebar.header("First Select Home Team and then Select Away team")
teams = st.sidebar.multiselect(
    "Select teams (max 2):",
    options=teams,
    default = ['Goa','Mumbai City']
)
home_team, away_team = teams[0], teams[1]
st.sidebar.write("Home Team --> ",home_team)
st.sidebar.write("Away Team --> ",away_team)   
team_req = st.radio("Home or Away", options = ['home','away']) 
tab1, tab2 = st.tabs(["Pass Network", "Pass Flow"])

with tab1:
    st.header("Pass Network")
    st.write("Pass networks help visualise the common pass routes in the given team. The player locations is the average player location during the match. For the sake of simplicity, the pass network only shows the starting XI players and not the substitutes. The shade of the line shows the number of passes between those players.")
    try:
        st.pyplot(fig=pass_network(home_team, away_team, team_req))
    except:
        pass

with tab2:
    st.header("Pass Flow")
    st.write("Pass flow maps are basically heatmaps with directions, they help to understand which areas of the pitch had most passes and which direction as well.")
    try:
        st.pyplot(fig=pass_flow(home_team, away_team,team_req))
    except:
        pass

st.write("Made by Joyan Bhathena, joyansbhathena@gmail.com")
