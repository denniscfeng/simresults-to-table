import os

import numpy as np
import pandas as pd

import Utils
from RaceReport import RaceReport


class Championship:

    def __init__(self, series, series_sessions, rounds_to_include, drop_week=False, num_scoring_drivers_in_team=2):
        self.series = series
        self.series_sessions = series_sessions
        self.rounds_to_include = rounds_to_include
        self.drop_week = drop_week
        self.num_scoring_drivers_in_team = num_scoring_drivers_in_team

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
        self.teams_totals_table = self.__construct_teams_totals(self.drivers_totals_table)

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

    def __get_countback_array(self, driver_all_results):
        # convert driver results to an ascii string
        # a "higher" string value means more higher finishing positions
        countback_arr = np.zeros(len(self.series_drivers_table))
        for pos in range(1, len(self.series_drivers_table) + 1):
            num_finished_in_pos = driver_all_results.apply(lambda result_info: result_info.pos == pos).sum()
            countback_arr[pos - 1] = num_finished_in_pos
        return countback_arr

    def __index_sort_countback_arrays(self, countback_arrays):
        countback_arrays_stacked = np.stack(countback_arrays)
        index_col = np.array(range(countback_arrays_stacked.shape[0])).reshape(-1, 1)
        countback_arrays_sorted_with_index = np.hstack((index_col, countback_arrays_stacked))

        for col_to_sort_by in range(countback_arrays_sorted_with_index.shape[0] - 1, 0, -1):
            countback_arrays_sorted_with_index = countback_arrays_sorted_with_index[
                countback_arrays_sorted_with_index[:, col_to_sort_by].argsort(kind='mergesort')]

        return pd.Series(np.flip(countback_arrays_sorted_with_index[:, 0]))

    def __drop_lowest_score_for_driver(self, driver_row):
        return driver_row["total"] - min(driver_row)

    def __construct_drivers_totals_and_sort_drivers_points(self, drivers_points_table):

        tracks = drivers_points_table.columns.unique(level="track")
        drivers_totals_table = pd.DataFrame(index=self.series_drivers_table.index, columns=tracks)

        def get_total_weekend_points(driver_session_results):
            return driver_session_results.apply(lambda result_info: result_info.total_points).sum()

        for track in tracks:
            results_infos_for_weekend = drivers_points_table[track]
            drivers_totals_table[track] = results_infos_for_weekend.apply(get_total_weekend_points, axis=1)

        drivers_totals_table["total"] = drivers_totals_table.agg(sum, axis=1)
        drivers_totals_table["total_with_drop_week"] = drivers_totals_table.apply(self.__drop_lowest_score_for_driver,
                                                                                  axis=1)

        drivers_totals_table["countback_array"] = drivers_points_table.apply(self.__get_countback_array, axis=1)
        drivers_totals_table = drivers_totals_table.sort_values("countback_array", key=lambda x: np.argsort(
            self.__index_sort_countback_arrays(drivers_totals_table["countback_array"])))

        drivers_totals_table = drivers_totals_table[["total", "total_with_drop_week", "countback_array"]]

        if self.drop_week:
            drivers_totals_table = drivers_totals_table.sort_values("total_with_drop_week", ascending=False,
                                                                    kind="mergesort")  # mergesort is required to stable sort
        else:
            drivers_totals_table = drivers_totals_table.sort_values("total", ascending=False, kind="mergesort")

        drivers_points_table_sorted = drivers_points_table.reindex(drivers_totals_table.index)
        print("created drivers totals table")
        return drivers_totals_table, drivers_points_table_sorted

    def __add_teams_driver_scores(self, drivers_results):
        # note pandas groupby is stable and preserves drivers sorted order
        return drivers_results[:self.num_scoring_drivers_in_team].sum()

    def __add_countback_arrays(self, countback_arrays):
        countback_arrays_stacked = np.stack(countback_arrays)
        # must cast to list cause of Must produce aggregated value issue stackoverflow.com/questions/39840546/must-produce-aggregated-value-i-swear-that-i-am
        return list(np.sum(countback_arrays_stacked, axis=0))

    def __construct_teams_totals(self, drivers_totals_table):
        drivers_teams_table = self.series_drivers_table[["team"]]
        drivers_totals_table_with_teams = drivers_totals_table.merge(drivers_teams_table, how='left', left_index=True,
                                                                     right_index=True)

        teams_totals_table = drivers_totals_table_with_teams[["total", "total_with_drop_week", "team"]].groupby(
            "team").agg(self.__add_teams_driver_scores)

        teams_totals_table["countback_array"] = drivers_totals_table_with_teams.groupby("team")[
            "countback_array"].agg(self.__add_countback_arrays)
        teams_totals_table["countback_array"] = teams_totals_table["countback_array"].apply(lambda lst: np.array(lst))
        drivers_totals_table = drivers_totals_table.sort_values("countback_array", key=lambda x: np.argsort(
            self.__index_sort_countback_arrays(drivers_totals_table["countback_array"])))

        teams_totals_table["drivers_list"] = drivers_totals_table_with_teams[["team"]].reset_index().groupby("team",
                                                                                                             group_keys=True).agg(
            list)

        if self.drop_week:
            teams_totals_table = teams_totals_table.sort_values("total_with_drop_week", ascending=False,
                                                                kind="mergesort")  # mergesort is required to stable sort
        else:
            teams_totals_table = teams_totals_table.sort_values("total", ascending=False, kind="mergesort")

        return teams_totals_table


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
