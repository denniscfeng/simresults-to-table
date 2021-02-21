import os
import re

import numpy as np
import pandas as pd

import Utils


class RaceReport:

    # Constructor, optionally pass in already-parsed drivers and points table info
    def __init__(self, table_names, series_directory, race_directory, drivers_table=None, points_table=None,
                 csv_manual_adjustment=0):

        self.table_names = table_names
        # TODO logging instead of printing
        print("Creating race report:", series_directory, race_directory)

        self.drivers_table = drivers_table if drivers_table is not None else Utils.read_drivers_table(
            series_directory)
        self.points_table = points_table if points_table is not None else Utils.read_points_table(series_directory)

        self.race_directory_path = "{}/{}".format(series_directory, race_directory)
        assert os.path.isdir(self.race_directory_path), "Race directory path does not exist: {}".format(
            self.race_directory_path)

        csv_files = [file for file in os.listdir(self.race_directory_path) if file.endswith(".csv")]
        if len(csv_files) < 1:
            raise FileNotFoundError()
        simresults_file_name = [file for file in os.listdir(self.race_directory_path) if file.endswith(".csv")][0]
        simresults_code = os.path.splitext(simresults_file_name)[0]
        self.results_file = "{}/{}.csv".format(self.race_directory_path, simresults_code)
        self.simresults_url = "https://simresults.net/{}".format(simresults_code)

        self.csv_manual_adjustment = csv_manual_adjustment
        self.tables = self.__read_results_tables()
        self.__clean_results_tables()

    # Return race result pandas dataframes in dict keyed by table_names
    def __read_results_tables(self):

        rows = {name: [0, 0] for name in self.table_names}
        with open(self.results_file) as fp:
            current_table = ""
            for i, row in enumerate(fp):
                if current_table:
                    if row == "\n":
                        rows[current_table][1] = i
                        print("ending line {}".format(rows[current_table][1]))
                        current_table = ""
                    else:
                        print(row, end="")
                else:
                    for name in self.table_names:
                        if row.startswith(name):
                            current_table = name
                            rows[current_table][0] = i + 2
                            print("found table '{}' starting line {} ".format(current_table, rows[current_table][0]))

        tables = {}
        for name in self.table_names:
            table_skiprows = rows[name][0] + self.csv_manual_adjustment
            table_nrows = rows[name][1] - table_skiprows - 1 + self.csv_manual_adjustment
            table_df = pd.read_csv(self.results_file, skiprows=table_skiprows, nrows=table_nrows, index_col=False,
                                   skipinitialspace=True, quotechar='"', dtype=object)
            print("read to dataframe:", name)
            tables[name] = table_df

        return tables

    # Clean race result dataframes, cast numerical columns to integers, join points information and starting positions to driver rows
    def __clean_results_tables(self):

        # Merge starting position info to grid column of a race table from either quali session or previous race, optionally adding quali points column
        def merge_qualy_info(race_table, qualy_table, add_qualy_points=False):

            qualy_table = qualy_table.reset_index()
            race_table = race_table.reset_index()

            if add_qualy_points:
                qualy_table = qualy_table[["Pos", "Driver", "Points"]]
                qualy_table = qualy_table.rename(columns={"Pos": "Grid", "Points": "Qualify Points"})
            else:
                qualy_table = qualy_table[["Pos", "Driver"]]
                qualy_table = qualy_table.rename(columns={"Pos": "Grid"})

            race_table = race_table.merge(qualy_table, how='left', on="Driver")

            race_table["Grid"] = race_table["Grid"].fillna(-1)
            # Pandas issue where NaN values cause ints to become floats?
            race_table["Grid"] = race_table["Grid"].astype(int)
            race_table["Pos"] = race_table["Pos"].astype(int)
            race_table["Laps"] = race_table["Laps"].astype(int)

            if add_qualy_points:
                race_table["Qualify Points"] = race_table["Qualify Points"].fillna(0)
                race_table["Qualify Points"] = race_table["Qualify Points"].astype(int)

            race_table = race_table.set_index("Pos")

            return race_table

        # TODO remove quote stripping since quotechar fixes this for us
        # Strip quotes and whitespace from strings, cast position and laps to integers, drop unnamed columns and rows for non-participants, convert fastest laps to datetimes
        for name, table_df in self.tables.items():
            table_df = table_df.apply(lambda s: s.str.strip(' \'"'), axis=1)
            table_df = table_df.rename(columns=lambda c: c.strip(' \'"'))
            table_df = table_df.apply(lambda s: s.str.replace('(.*\d\d*\.\d{3})0$', r'\1'), axis=1)

            table_df["Pos"] = table_df["Pos"].astype(int)
            table_df = table_df.set_index("Pos")

            table_df["Laps"] = table_df["Laps"].astype(int)

            table_df = table_df[table_df["Laps"] > 0]

            table_df = table_df[table_df.columns.drop(list(table_df.filter(regex='Unnamed*')))]
            table_df = table_df.dropna(how='all', axis='columns')

            table_df["Best lap time"] = pd.to_datetime(table_df["Best lap"], format="%M:%S.%f", errors='coerce')

            self.tables[name] = table_df

        # Merge points column to both quali and race sessions, for race sessions: get attatched qualifying or previous race to get starting positions and show (probable) DNFs
        for name, table_df in self.tables.items():

            if name.startswith("Qualify"):
                points_column = pd.Series(np.zeros(len(table_df))).add(self.points_table["qualy_points"].astype(int),
                                                                       fill_value=0)
                table_df["Points"] = points_column.astype(int)

            if name.startswith("Race"):

                table_df["Time/Retired"] = table_df["Time/Retired"].str.replace('^\s*$', "")
                table_df["Consistency"] = table_df["Consistency"].str.replace('^-$', "")

                points_column = pd.Series(np.zeros(len(table_df) + 1)).add(self.points_table["points"].astype(int),
                                                                           fill_value=0)
                table_df["Points"] = points_column.astype(int)

                session_num = int(re.findall('(?:Qualify|Race)\s(\d+)\sresult|$', name)[0])
                qualy_table_name = "Qualify result" if session_num == 1 and "Qualify result" in self.tables.keys() else "Qualify {} result".format(
                    session_num)
                previous_race_table_name = "Race {} result".format(session_num - 1)
                if qualy_table_name in self.tables:
                    table_df = merge_qualy_info(table_df, self.tables[qualy_table_name], add_qualy_points=True)
                elif previous_race_table_name in self.tables:
                    table_df = merge_qualy_info(table_df, self.tables[previous_race_table_name])
                else:
                    table_df["Grid"] = ""

                table_df["DNF"] = table_df["Laps"] < table_df["Laps"].max() // 2

            # Validate drivers are in the driver table
            for driver in table_df["Driver"]:
                assert driver in self.drivers_table.index, "{} not found in drivers table".format(driver)

            print("cleaned dataframe:", name)
            self.tables[name] = table_df
