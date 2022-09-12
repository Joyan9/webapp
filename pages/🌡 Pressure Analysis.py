import streamlit as st
from statsbombpy import sb
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
from mplsoccer import Pitch,FontManager

robotto_regular = FontManager()

# path effects
path_eff = [path_effects.Stroke(linewidth=1.5, foreground='black'),
            path_effects.Normal()]

# see the custom colormaps example for more ideas on setting colormaps
pearl_earring_cmap = LinearSegmentedColormap.from_list("Pearl Earring - 10 colors",
                                                       ['#15242e', '#4393c4'], N=10)

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

def get_pressure_df(home_team, away_team, team_req):
    event_df = get_events(home_team, away_team)
    if team_req == 'home':
        team_name = home_team
    else:
        team_name = away_team
    team_pressure_mask = (event_df.type == 'Pressure') & (event_df.team == team_name)
    # create a dataframe of the pressure only
    pressure_df = event_df[team_pressure_mask]
    pressure_df['location'].iloc[0][0]
    x_coordinates,y_coordinates = [],[]
    for i in range(len(pressure_df)):
        x_coordinates.append(pressure_df['location'].iloc[i][0])
        y_coordinates.append(pressure_df['location'].iloc[i][1])


    pressure_df['x'], pressure_df['y'] = x_coordinates, y_coordinates
    return pressure_df

def pressure_map(home_team,away_team,team_req):
    df_pressure = get_pressure_df(home_team,away_team,team_req)

    if team_req == 'home':
        team_name = home_team
    else:
        team_name = away_team

    pitch = VerticalPitch(pitch_type='statsbomb', line_zorder=2, pitch_color='#1e4259')
    fig, axs = pitch.grid(figheight = 15,endnote_height=0.03, endnote_space=0,
                          title_height=0.08, title_space=0,
                          axis=False,
                          grid_height=0.84)
    fig.set_facecolor('#1e4259')

    bin_x = np.linspace(pitch.dim.left, pitch.dim.right, num=7)
    bin_y = np.sort(np.array([pitch.dim.bottom, pitch.dim.six_yard_bottom,
                              pitch.dim.six_yard_top, pitch.dim.top]))
    bin_statistic = pitch.bin_statistic(df_pressure.x, df_pressure.y, statistic='count',
                                        bins=(bin_x, bin_y), normalize=True)
    pitch.heatmap(bin_statistic, ax=axs['pitch'], cmap='Oranges_r', edgecolor='#f9f9f9')
    labels3 = pitch.label_heatmap(bin_statistic, color='#dee6ea', fontsize=18,
                                  ax=axs['pitch'], ha='center', va='center',
                                  str_format='{:.0%}', path_effects=path_eff)

    # endnote and title
    endnote_text = axs['endnote'].text(1, 0.5, '@BhathenaJoyan',
                                       va='center', ha='right', fontsize=15,
                                       fontproperties=robotto_regular.prop, color='#dee6ea')
    title_text = axs['title'].text(0.5, 0.5, f"Pressure applied by\n {team_name}",
                                   color='#dee6ea', va='center', ha='center', path_effects=path_eff,
                                   fontproperties=robotto_regular.prop, fontsize=30)
    

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

#----HOME PAGE----
team_req = st.radio("Home or Away", options = ['home','away'])
col = st.columns(1)
st.write("Pressure map helps visualise the locations on the pitch where pressure was applied by the selected team. Bright regions signify high pressure and darker regions shows less pressure was applied in that region.")
if len(teams) == 2:
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot(fig=pressure_map(home_team, away_team, team_req))

st.write("Made by Joyan Bhathena, joyansbhathena@gmail.com")
