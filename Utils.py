import pandas as pd

NO_TEAM = "Independent"  # drivers without teams are in the "Independent" team


# Read series drivers info
def read_drivers_table(series_directory):
    drivers_table_file = "{}/drivers_table.csv".format(series_directory)
    table = pd.read_csv(drivers_table_file, dtype=object)
    table = table.set_index("ign")
    return table


# Read series points scoring info
def read_scoring_table(series_directory):
    points_table_file = "{}/points_table.csv".format(series_directory)
    table = pd.read_csv(points_table_file, dtype=object)
    table = table.astype(int)
    table = table.set_index("pos")
    return table


# Read series track info (used only for championship table)
def read_tracks_table(series_directory):
    tracks_table_file = "{}/tracks_table.csv".format(series_directory)
    table = pd.read_csv(tracks_table_file, dtype=object)
    table["csv_manual_adjustment"] = table["csv_manual_adjustment"].astype(int)
    table = table.set_index("directory")
    return table
