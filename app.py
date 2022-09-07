import dash
from dash import Dash, dcc, html, Input, Output
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
    dcc.Dropdown(list(PLAYER_DF.index), value=f"{list(PLAYER_DF.index)[1]}", id="send_player"),
    dcc.RadioItems(list(FILTER_DICT.keys()), value="Goals", id="filter-input"),
    # dcc.Dropdown(list(PLAYER_DF.index), value=f"{list(PLAYER_DF.index)[1]}")
    # dcc.Graph()
    dcc.Graph(id="player_data"),
    dcc.Store(id="store-player-stats") #need to convert back to df
])

@app.callback([
    Output(component_id="player_data", component_property="figure"),
    Output(component_id="store-player-stats", component_property="data")],
    [Input(component_id="send_player", component_property='value'),
    Input(component_id="filter-input", component_property='value')]
)
def return_player_stats(player_name, filter_input):
    general_stats_df, teams_played_for = get_general_stats(player_name)
    position = PLAYER_DF.loc[player_name]["position.name"]
    df = general_stats_df.set_index("team.name")

    selected_filter = filter_input
    if selected_filter in DIGIT_FILTERS:
        general_stats_df = general_stats_df.groupby('season').sum()
    fig = px.line(general_stats_df, x=general_stats_df.index, y=f"{FILTER_DICT[selected_filter]}",
                  hover_name="stat.games")
    return fig, df.to_dict()

# def

if __name__ == '__main__':
    app.run_server(debug=True)