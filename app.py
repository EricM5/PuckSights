import json

import dash
from dash import Dash, dcc, html, Input, Output, ctx
import requests
import pandas as pd
import plotly.express as px


BASE_URL = "https://statsapi.web.nhl.com"


response = requests.get("https://statsapi.web.nhl.com/api/v1/teams?expand=team.roster")
df = pd.json_normalize(response.json())

c = pd.json_normalize(response.json(), record_path=["teams"])[["roster.roster"]].apply(pd.Series)

PLAYER_DF = pd.DataFrame()

df = c.reset_index()  # make sure indexes pair with number of rows

for index, row in df.iterrows():
    PLAYER_DF = pd.concat([PLAYER_DF, pd.json_normalize(c.loc[index][0]).set_index("person.fullName")])

FILTER_DICT = {"Goals":"stat.goals",
               "Assists":"stat.assists",
               "Points":"stat.points",
               "Games Played":"stat.games",
               "Penalty Minutes":"stat.pim",
               "PlusMinus": "stat.plusMinus"
              }
DIGIT_FILTERS = ["Goals", "Assists", "Points",
                 "Games Played", "Penalty Minutes", "PlusMinus"]



def get_player_id(name):
    player_id = PLAYER_DF.loc[name]["person.id"]
    return player_id

def get_general_stats(player_name):
    player_id = get_player_id(player_name)
    '''
    returns df of previous stats, year to year
    and list of teams played for
    '''
    response = requests.get(BASE_URL + f"/api/v1/people/{player_id}/stats?stats=yearByYear")
    response_json = response.json()["stats"][0]["splits"]
    df = pd.json_normalize(response_json)
    teams_list = [f"{df.iloc[i]['team.name']} ({df.iloc[i]['league.name']})" for i in range(len(list(df['team.name'])) - 1, -1, -1)]
    seen = set()
    teams_played_for = [x for x in teams_list if not (x in seen or seen.add(x))]
    return df, teams_played_for

app = Dash(__name__)

app.layout = html.Div([
    dcc.Store(id="player_data_store"),
    dcc.Dropdown(list(PLAYER_DF.index), value=f"{list(PLAYER_DF.index)[1]}", id="player_list"),
    dcc.Dropdown(id="team_list", value="All Teams", placeholder="All Teams"),
    dcc.Store(id="store_player_name"),
    dcc.RadioItems(list(FILTER_DICT.keys()), id="filter_input"),
    # dcc.Dropdown(list(PLAYER_DF.index), value=f"{list(PLAYER_DF.index)[1]}")
    # dcc.Graph()
    html.Div(id="sendhere"),
    dcc.Graph(id="player_data") #need to convert back to df
    # dcc.Store(id="team_list")
])

@app.callback([
    Output(component_id="team_list", component_property="options"),
    Output(component_id="team_list", component_property="value"),
    Output(component_id="store_player_name", component_property="data"),
    Output(component_id="player_data_store", component_property="data")
],
    Input(component_id="player_list", component_property="value")
)
def update_dropdown(player_name):
    general_stats_df, teams_played_for = get_general_stats(player_name)
    temp_list = ["All Teams"]
    temp_list.extend(teams_played_for)
    json_general_stats_df = general_stats_df.to_json()
    return temp_list, "All Teams", player_name, json_general_stats_df

@app.callback(
    # Output(component_id="player_data", component_property="figure"),
    Output(component_id="filter_input", component_property="options"),
    Input(component_id="team_list", component_property="value"),
    Input(component_id="store_player_name", component_property="data")
)
def update_stat_options(team, player_name):
    position = PLAYER_DF.loc[player_name]["position.name"]
    if position == "Goalie":
        # stat_options = ["stat.shutouts", "stat.ties",
        #                 "stat.wins", "stat.losses",
        #                 "stat.goalAgainstAverage",
        #                 "stat.games", "stat.goalsAgainst"]
        stat_options = ["GAA", "Shutouts", "Wins", "Losses", "Ties", "Games"]
    else:
        stat_options = ["Goals", "Assists", "Points", "Games", "Penalty Minutes", "Plus/Minus"]
    return stat_options

# @app.callback(
#     [
#         Output(component_id="player_data", component_property="figure")],
#     [
#         Input(component_id="filter_input", component_property="value"),
#         Input(component_id="store-player-stats", component_property="value")]
# )
# def return_player_graph(selected_filter, general_stats_df):
#     general_stats_df = pd.DataFrame(general_stats_df)
#     if selected_filter in DIGIT_FILTERS:
#         general_stats_df = general_stats_df.groupby('season').sum()
#     fig = px.line(general_stats_df, x=general_stats_df.index, y=f"{FILTER_DICT[selected_filter]}",
#                   hover_name="stat.games")
# @app.callback([
#     Output(component_id="player_data", component_property="figure"),
#     Output(component_id="store-player-stats", component_property="data"),
#     Output(component_id="team_list", component_property="options")],
#     [Input(component_id="send_player", component_property='value'),
#      Input(component_id="team_list", component_property="value"),
#      Input(component_id="filter_input", component_property="value")
#     ]
# )
# def return_player_stats(player_name, team_name, filter_input):
#     trigger_id = ctx.triggered_id
#     general_stats_df, teams_played_for = get_general_stats(player_name)
#     # df = general_stats_df.set_index("team.name")
#
#     # if trigger_id == "send_player":
#     #
#     # elif trigger_id == "send_team":
#     #     general_stats_df = pd.DataFrame(player_data)
#
#     position = PLAYER_DF.loc[player_name]["position.name"]
#     selected_filter = filter_input
#
#     fig = px.line(general_stats_df, x=general_stats_df.index, y=f"{FILTER_DICT[selected_filter]}")
#
#
#     if trigger_id == "send_player":
#         if selected_filter in DIGIT_FILTERS:
#             general_stats_df = general_stats_df.groupby('season').sum()
#         fig = px.line(general_stats_df, x=general_stats_df.index, y=f"stat.goals")
#     elif trigger_id == "filter_input":
#         general_stats_df = general_stats_df.loc[general_stats_df["team.name"] == team_name]
#         # if selected_filter in DIGIT_FILTERS:
#         #     general_stats_df = general_stats_df.groupby('season').sum()
#         fig = px.line(general_stats_df, x="season", y=f"{FILTER_DICT[selected_filter]}")
#     elif trigger_id == "team_list":
#         # copy_df = general_stats_df.copy()
#         # general_stats_df = general_stats_df.set_index('team.name')
#         # general_stats_df = general_stats_df.loc[team_name.split(" (", 1)[0]]
#         team_specific_df = general_stats_df.loc[general_stats_df["team.name"]==team_name]
#         fig = px.line(team_specific_df, x="season", y=f"stat.goals")
#
#         if selected_filter in DIGIT_FILTERS:
#             general_stats_df = general_stats_df.groupby('season').sum()
#         fig = px.line(general_stats_df, x=general_stats_df.index, y=f"{FILTER_DICT[selected_filter]}")
#     else:
#         fig = px.line(general_stats_df.set_index("season"), x=general_stats_df.index, y=f"stat.goals")
#
#     return fig, df.to_dict(), teams_played_for

# def

if __name__ == '__main__':
    app.run_server(debug=True)