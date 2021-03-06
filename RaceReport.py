import os
import re

import numpy as np
import pandas as pd

import Utils


class RaceReport:

    # Constructor, optionally pass in already-parsed drivers and points table info and whether to debug print csv lines when parsing
    def __init__(self, session_names, series_directory, race_directory, drivers_table=None, scoring_table=None,
                 csv_manual_adjustment=0, debug_csv_parse=False):

        self.session_names = session_names
        self.debug_csv_parse = debug_csv_parse

        self.drivers_table = drivers_table if drivers_table is not None else Utils.read_drivers_table(
            series_directory)
        self.scoring_table = scoring_table if scoring_table is not None else Utils.read_scoring_table(series_directory)

        self.race_directory_path = os.path.join(series_directory, race_directory)
        assert os.path.isdir(self.race_directory_path), "Race directory path does not exist: {}".format(
            self.race_directory_path)
        print("creating race report:", self.race_directory_path)

        csv_files = [file for file in os.listdir(self.race_directory_path) if file.endswith(".csv")]
        if len(csv_files) < 1:
            raise FileNotFoundError()
        simresults_file_name = [file for file in os.listdir(self.race_directory_path) if file.endswith(".csv")][0]
        simresults_code = os.path.splitext(simresults_file_name)[0]
        self.results_file = os.path.join(self.race_directory_path, "{}.csv".format(simresults_code))
        print("reading results file:", self.results_file)

        self.simresults_url = "https://simresults.net/{}".format(simresults_code)

        self.race_sessions = [name for name in session_names if name.startswith("Race")]
        self.quali_sessions = [name for name in session_names if name.startswith("Qualify")]
        self.race_session_grid_determined_by = self._get_race_session_grid_determined_by()

        self.csv_manual_adjustment = csv_manual_adjustment
        self.tables = self._read_results_tables()
        self._clean_results_tables()

    # Get attached qualifying or previous race to get starting positions
    def _get_race_session_grid_determined_by(self):

        race_session_grid_determined_by = {}

        for race_session_name in self.race_sessions:

            session_number = int(re.findall('(?:Qualify|Race)\s(\d+)\sresult|$', race_session_name)[0])
            quali_session_name = "Qualify result" if session_number == 1 and "Qualify result" in self.session_names else "Qualify {} result".format(
                session_number)
            previous_race_session_name = "Race {} result".format(session_number - 1)

            grid_determining_session = None
            if quali_session_name in self.quali_sessions:
                grid_determining_session = quali_session_name
            elif previous_race_session_name in self.race_sessions:
                grid_determining_session = previous_race_session_name

            assert grid_determining_session in self.session_names, "could not find grid-determining session for race {}".format(
                race_session_name)
            race_session_grid_determined_by[race_session_name] = grid_determining_session

        return race_session_grid_determined_by

    # Return race result pandas dataframes in dict keyed by session_names
    def _read_results_tables(self):

        rows = {name: [0, 0] for name in self.session_names}
        with open(self.results_file) as fp:
            current_table = ""
            for i, row in enumerate(fp):
                if current_table:
                    if row == "\n":
                        rows[current_table][1] = i
                        print("ending line {}".format(rows[current_table][1]))
                        current_table = ""
                    elif i >= rows[current_table][0]:
                        if self.debug_csv_parse: print(row, end="")
                else:
                    for name in self.session_names:
                        if row.startswith(name):
                            current_table = name
                            rows[current_table][0] = i + 2
                            print("found table '{}' starting line {} ".format(current_table, rows[current_table][0]))

        tables = {}
        for name in self.session_names:
            table_skiprows = rows[name][0] + self.csv_manual_adjustment
            table_nrows = rows[name][1] - table_skiprows - 1 + self.csv_manual_adjustment
            table_df = pd.read_csv(self.results_file, skiprows=table_skiprows, nrows=table_nrows, index_col=False,
                                   skipinitialspace=True, quotechar='"', dtype=object)
            print("read to dataframe:", name)
            tables[name] = table_df

        return tables

    # Clean race result dataframes, cast numerical columns to integers, join points information and starting positions to driver rows
    def _clean_results_tables(self):

        # Merge starting position info to grid column of a race table from either quali session or previous race, optionally adding quali points column
        # TODO doesnt work with reverse grid!
        def merge_quali_info(race_table, quali_table, add_quali_points=False):

            quali_table = quali_table.reset_index()
            race_table = race_table.reset_index()

            if add_quali_points:
                quali_table = quali_table[["Pos", "Driver", "Points"]]
                quali_table = quali_table.rename(columns={"Pos": "Grid", "Points": "Qualify Points"})
            else:
                quali_table = quali_table[["Pos", "Driver"]]
                quali_table = quali_table.rename(columns={"Pos": "Grid"})

            race_table = race_table.merge(quali_table, how='left', on="Driver")

            race_table["Grid"] = race_table["Grid"].fillna(-1)
            # Pandas issue where NaN values cause ints to become floats?
            race_table["Grid"] = race_table["Grid"].astype(int)
            race_table["Pos"] = race_table["Pos"].astype(int)
            race_table["Laps"] = race_table["Laps"].astype(int)

            if add_quali_points:
                race_table["Qualify Points"] = race_table["Qualify Points"].fillna(0)
                race_table["Qualify Points"] = race_table["Qualify Points"].astype(int)

            race_table = race_table.set_index("Pos")

            return race_table

        # Cast position and laps to integers, drop unnamed columns and rows for non-participants, convert fastest laps to datetimes
        for name, table_df in self.tables.items():
            # Strip quotes and whitespace from strings?
            # table_df = table_df.apply(lambda s: s.str.strip(' \'"'), axis=1)
            # table_df = table_df.rename(columns=lambda c: c.strip(' \'"'))

            # Trim simresults laptime/racetime format
            table_df = table_df.apply(lambda s: s.str.replace('(.*\d\d*\.\d{3})0$', r'\1'), axis=1)

            table_df["Pos"] = table_df["Pos"].astype(int)
            table_df = table_df.set_index("Pos")

            table_df["Laps"] = table_df["Laps"].astype(int)

            table_df = table_df[table_df["Laps"] > 0]

            table_df = table_df[table_df.columns.drop(list(table_df.filter(regex='Unnamed*')))]
            table_df = table_df.dropna(how='all', axis='columns')

            table_df["Best lap time"] = pd.to_datetime(table_df["Best lap"], format="%M:%S.%f", errors='coerce')

            self.tables[name] = table_df

        # Merge points column to both quali and race sessions
        for name, table_df in self.tables.items():

            if name.startswith("Qualify"):
                points_column = pd.Series(np.zeros(len(table_df))).add(self.scoring_table["quali_points"].astype(int),
                                                                       fill_value=0)
                table_df["Points"] = points_column.astype(int)

            if name.startswith("Race"):

                table_df["Time/Retired"] = table_df["Time/Retired"].str.replace('^\s*$', "")
                table_df["Consistency"] = table_df["Consistency"].str.replace('^-$', "")

                points_column = pd.Series(np.zeros(len(table_df) + 1)).add(self.scoring_table["points"].astype(int),
                                                                           fill_value=0)
                table_df["Points"] = points_column.astype(int)

                session_grid_determined_by = self.race_session_grid_determined_by[name]
                if session_grid_determined_by in self.quali_sessions:
                    table_df = merge_quali_info(table_df, self.tables[session_grid_determined_by],
                                                add_quali_points=True)
                elif session_grid_determined_by in self.race_sessions:
                    table_df = merge_quali_info(table_df, self.tables[session_grid_determined_by])

                # Show driver is DNF if they don't complete half the laps (this is a guess)
                table_df["DNF"] = table_df["Laps"] < table_df["Laps"].max() // 2

            # Validate drivers are in the driver table
            for driver in table_df["Driver"]:
                assert driver in self.drivers_table.index, "{} not found in drivers table".format(driver)

            print("cleaned dataframe:", name)
            self.tables[name] = table_df
