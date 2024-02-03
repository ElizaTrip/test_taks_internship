import pygsheets
import pandas as pd

# Linking service account
gc = pygsheets.authorize(service_account_file="")

# Opening spreadsheet.
sh_pyg = gc.open("work_table")

#  We are getting worksheet using gspread and saving as pandas dataframe
wks_users = sh_pyg[0]
users = wks_users.get_as_df()

# We need to get score table via gspread and save as pandas dataframe
wks_scores = sh_pyg[1]
scores = wks_scores.get_as_df()

# --- PROBLEM 1: TEAM LEADERBOARD ---
# For more comfortable usage, merge together dataframe with statements and dataframe with names of teams.
users_and_scores = pd.merge(users, scores)

# Creating dataframe with all names of teams and empty fields for reasons ond
team_leaderboard = pd.DataFrame()
team_leaderboard["Thinking Teams Leaderboard"] = users_and_scores["Team Name"].unique()
team_leaderboard["Average Statements"] = 0
team_leaderboard["Average Reasons"] = 0

# Looping over rows to automatically fill average reasons/statements in cells
for index_t, team in team_leaderboard.iterrows():
    name = team["Thinking Teams Leaderboard"]
    av_reason = 0
    av_statements = 0
    count = 0
    for index, score in users_and_scores.iterrows():
        if score["Team Name"] == name:
            av_statements += score["total_statements"]
            av_reason += score["total_reasons"]
            count += 1
    team_leaderboard.at[index_t, "Average Statements"] = round(av_statements / count, 2)
    team_leaderboard.at[index_t, "Average Reasons"] = round(av_reason/count, 2)

# Creating temporary column for easier sorting
# Dataframe is sorted by total amount of average statements and reasons
team_leaderboard["total"] = team_leaderboard[["Average Statements", "Average Reasons"]].sum(axis=1)
team_leaderboard = team_leaderboard.sort_values(by="total", ascending=False)

# Deleting temporary column
del team_leaderboard["total"]

# Add autogenerated ranking value
team_leaderboard.insert(0, "Team Rank", range(1, 1+len(team_leaderboard)))

# Send dataframe to google sheets.
lead_team = sh_pyg[2]
lead_team.set_dataframe(team_leaderboard, (1, 1))

# ----- PROBLEM 2: INDIVIDUAL LEADERBOARD. -----
# For correct output we need to sort table
# Sorting by total number of reasons and statements. Creating new column with sum of two.
scores["total"] = scores[["total_statements", "total_reasons"]].sum(axis=1)

# For sorting in alphabet order we need to get all characters in same case.
# Using upper case because it's more convenient for us.
scores["name_lowercase"] = scores["name"].str.upper()
scores = scores.sort_values(by=["total", "name_lowercase"], ascending=[False, True])

# Deleting helping rows after sorting + deleting number since we won't need old order
del scores["name_lowercase"]
del scores["total"]
del scores["S No"]

# Before writing in file we need to rename columns.
scores = scores.rename(columns={"name": "Name", "uid": "UID", "total_statements": "No. of Statements",
                                "total_reasons": "No. of Reasons"})

# Adding new column with autogenerated rank
scores.insert(0, "Rank", range(1, 1+len(scores)))

leaderboard_person = sh_pyg[3]
leaderboard_person.set_dataframe(scores, (1, 1))
