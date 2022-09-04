import requests
import pandas as pd
pd.set_option("display.max_rows", None)

response = requests.get("https://statsapi.web.nhl.com/api/v1/teams?expand=team.roster")

df = pd.json_normalize(response.json())

response.json()

c = pd.json_normalize(response.json(), record_path=["teams"])[["roster.roster"]].apply(pd.Series)

# pd.DataFrame(c.loc[0][0])
# pd.json_normalize(c.loc[25][0])

playerdf = pd.json_normalize(c.loc[25][0]).set_index("person.fullName")

personidseries = playerdf["person.id"]

# personseries.to_dict()
# player_id_df = pd.json_normalize(c.loc[0][0]).set_index("person.fullName")
player_id_df = pd.DataFrame()
df = c.reset_index()  # make sure indexes pair with number of rows

for index, row in df.iterrows():
    player_id_df = pd.concat([player_id_df, pd.json_normalize(c.loc[index][0]).set_index("person.fullName")])
#player_id_df is a df with index person.fullName 

player_id_df
