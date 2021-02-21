import os

import pandas as pd

import Utils
from RaceReport import RaceReport


class ChampionshipPoints:

    def __init__(self, series, series_sessions, rounds_to_include, drop_week):
        self.series = series
        self.series_sessions = series_sessions
        self.rounds_to_include = rounds_to_include
        self.drop_week = drop_week

        print("Creating championship points tables for:", series)

        self.series_drivers_table = Utils.read_drivers_table(series)
        self.series_scoring_table = Utils.read_scoring_table(series)
        self.series_tracks_table = Utils.read_tracks_table(series)

        self.series_race_sessions = [session for session in series_sessions if session.startswith("Race")]
        self.num_total_races = len(self.series_tracks_table) * len(self.series_race_sessions)
        self.race_reports = self.__read_race_reports()

        drivers_points_table_unsorted = self.__construct_drivers_points()
        self.drivers_totals_table, self.drivers_points_table = self.__construct_drivers_totals_and_sort_drivers_points(
            drivers_points_table_unsorted)

    def __read_race_reports(self):
        race_reports = {}

        for race, race_row in self.series_tracks_table.iterrows():

            race_path = "{}/{}".format(self.series, race)
            if os.path.isdir(race_path):
                try:
                    race_reports[race] = RaceReport(self.series_sessions, self.series, race,
                                                    drivers_table=self.series_drivers_table,
                                                    scoring_table=self.series_scoring_table,
                                                    csv_manual_adjustment=race_row["csv_manual_adjustment"])
                    print("read race report for", race)
                except FileNotFoundError:
                    print("no csv found for", race)
            else:
                print("no directory found for", race)

        return race_reports

    def __construct_drivers_points(self):

        drivers_points_table = pd.DataFrame(index=self.series_drivers_table.index, columns=pd.MultiIndex.from_product(
            [self.series_tracks_table.index, self.series_race_sessions], names=["track", "session"]))

        # loop through drivers index
        # construct series with the multindex
        # go thorugh race reports and count up points

        for driver in drivers_points_table.index:
            for track, session in drivers_points_table.columns:

                result_info = DriverRaceResultInfo()

                if track in self.race_reports:

                    race_table = self.race_reports[track].tables[session]
                    driver_race_result = race_table[race_table["Driver"] == driver]

                    if len(driver_race_result == 1):
                        pos = driver_race_result.index[0]
                        points = driver_race_result["Points"].item()
                        qualify_pos = driver_race_result["Grid"].item()
                        qualify_points = driver_race_result[
                            "Qualify Points"].item() if "Qualify Points" in driver_race_result.columns else 0
                        dnf = driver_race_result["DNF"].item()

                        result_info = DriverRaceResultInfo(pos, points, qualify_pos, qualify_points, dnf)

                drivers_points_table.loc[driver, (track, session)] = result_info

        # truncate results to only calculate up to rounds needed
        drivers_points_table = drivers_points_table.iloc[:, 0:(self.rounds_to_include * len(self.series_race_sessions))]
        print("created drivers points table")
        return drivers_points_table

    def __construct_drivers_totals_and_sort_drivers_points(self, drivers_points_table):

        tracks = drivers_points_table.columns.unique(level="track")
        drivers_totals_table = pd.DataFrame(index=self.series_drivers_table.index, columns=tracks)

        def get_total_weekend_points(driver_session_results):
            return driver_session_results.apply(lambda result_info: result_info.total_points).sum()

        for track in tracks:
            results_infos_for_weekend = drivers_points_table[track]
            drivers_totals_table[track] = results_infos_for_weekend.apply(get_total_weekend_points, axis=1)

        drivers_totals_table["total"] = drivers_totals_table.agg(sum, axis=1)
        drivers_totals_table["total_with_drop_week"] = drivers_totals_table.apply(
            lambda driver_row: driver_row["total"] - (min(driver_row)), axis=1)

        def get_countback_str(driver_all_results):
            # convert driver results to an ascii string
            # a "higher" string value means more higher finishing positions
            countback_str = ""
            for pos in range(1, len(self.series_drivers_table)):
                num_finished_in_pos = driver_all_results.apply(lambda result_info: result_info.pos == pos).sum()
                countback_str += chr(48 + num_finished_in_pos)
            return countback_str

        drivers_totals_table["countback_str"] = drivers_points_table.apply(get_countback_str, axis=1)

        if self.drop_week:
            drivers_totals_table = drivers_totals_table.sort_values("countback_str", ascending=False)
            drivers_totals_table = drivers_totals_table.sort_values("total_with_drop_week", ascending=False,
                                                                    kind="mergesort")  # mergesort is required to stable sort
        else:
            drivers_totals_table = drivers_totals_table.sort_values("countback_str", ascending=False)
            drivers_totals_table = drivers_totals_table.sort_values("total", ascending=False, kind="mergesort")

        drivers_points_table_sorted = drivers_points_table.reindex(drivers_totals_table.index)
        print("created drivers totals table")
        return drivers_totals_table, drivers_points_table_sorted


# compressed race result info obj for a driver and session
class DriverRaceResultInfo:

    def __init__(self, pos=-1, points=0, qualy_pos=-1, qualy_points=0, dnf=False):
        self.pos = pos
        self.points = points
        self.qualy_pos = qualy_pos
        self.qualy_points = qualy_points
        self.dnf = dnf
        self.participated = not bool(pos == -1 and qualy_pos == -1)
        self.total_points = self.points + self.qualy_points

    def __str__(self):
        if (self.pos < 0) and (self.qualy_pos < 0):
            return "NP"
        elif self.dnf:
            return "DNF"
        else:
            return str(self.total_points)

    def __repr__(self):
        return "DriverRaceResultInfo({},{},{},{},{})".format(self.pos, self.points, self.qualy_pos,
                                                             self.qualy_points, self.dnf)
