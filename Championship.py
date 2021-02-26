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
        self.race_reports = self._read_race_reports()

        drivers_points_table_unsorted = self._construct_drivers_points()
        self.drivers_totals_table, self.drivers_points_table = self._construct_drivers_totals_and_sort_drivers_points(
            drivers_points_table_unsorted)
        self.teams_totals_table = self._construct_teams_totals(self.drivers_totals_table)

    def _read_race_reports(self):
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

    def _construct_drivers_points(self):

        drivers_points_table = pd.DataFrame(index=self.series_drivers_table.index, columns=pd.MultiIndex.from_product(
            [self.series_tracks_table.index, self.series_race_sessions], names=["track", "session"]))

        # loop through drivers index
        # construct series with the multindex
        # go through race reports and count up points

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

        # drop drivers without no results at all
        no_shows = []
        for driver in drivers_points_table.index:
            if not drivers_points_table.loc[driver].apply(lambda r_info: r_info.participated).any():
                no_shows.append(driver)
        drivers_points_table = drivers_points_table.drop(index=no_shows)

        # truncate results to only calculate up to rounds needed
        drivers_points_table = drivers_points_table.iloc[:, 0:(self.rounds_to_include * len(self.series_race_sessions))]
        print("created drivers points table")
        return drivers_points_table

    def _get_countback_array(self, driver_all_results):
        # convert driver results to an ascii string
        # a "higher" string value means more higher finishing positions
        countback_arr = np.zeros(len(self.series_drivers_table))
        for pos in range(1, len(self.series_drivers_table) + 1):
            num_finished_in_pos = driver_all_results.apply(lambda result_info: result_info.pos == pos).sum()
            countback_arr[pos - 1] = num_finished_in_pos
        return countback_arr

    def _index_sort_countback_arrays(self, countback_arrays):
        countback_arrays_stacked = np.stack(countback_arrays)
        index_col = np.array(range(countback_arrays_stacked.shape[0])).reshape(-1, 1)
        countback_arrays_sorted_with_index = np.hstack((index_col, countback_arrays_stacked))

        for col_to_sort_by in range(countback_arrays_sorted_with_index.shape[0] - 1, 0, -1):
            countback_arrays_sorted_with_index = countback_arrays_sorted_with_index[
                countback_arrays_sorted_with_index[:, col_to_sort_by].argsort(kind='mergesort')]

        return pd.Series(np.flip(countback_arrays_sorted_with_index[:, 0]))

    def _get_weekend_totals(self, weekend_results):
        weekend_total_points = weekend_results.applymap(lambda result_info: result_info.total_points)
        return weekend_total_points.sum(axis=1)

    def _get_drop_week_name(self, driver_row):
        return driver_row.index[np.argmin(driver_row)]

    def _subtract_drop_week_score_from_driver_total(self, driver_row):
        return driver_row["total"] - driver_row.loc[driver_row["drop_week"]]

    def _construct_drivers_totals_and_sort_drivers_points(self, drivers_points_table):

        drivers_totals_table = drivers_points_table.groupby(level=0, axis=1).agg(self._get_weekend_totals)

        drivers_totals_table["drop_week"] = drivers_totals_table.agg(self._get_drop_week_name, axis=1)
        drivers_totals_table["total"] = drivers_totals_table.drop(columns="drop_week").sum(axis=1)
        drivers_totals_table["total_with_drop_week"] = drivers_totals_table.apply(self._subtract_drop_week_score_from_driver_total, axis=1)

        drivers_totals_table["countback_array"] = drivers_points_table.apply(self._get_countback_array, axis=1)
        drivers_totals_table = drivers_totals_table.sort_values("countback_array", key=lambda x: np.argsort(
            self._index_sort_countback_arrays(drivers_totals_table["countback_array"])))

        if self.drop_week:
            drivers_totals_table = drivers_totals_table.sort_values("total_with_drop_week", ascending=False,
                                                                    kind="mergesort")  # mergesort is required to stable sort
        else:
            drivers_totals_table = drivers_totals_table.sort_values("total", ascending=False, kind="mergesort")

        drivers_points_table_sorted = drivers_points_table.reindex(drivers_totals_table.index)
        print("created drivers totals table")
        return drivers_totals_table, drivers_points_table_sorted

    def _add_teams_driver_scores(self, drivers_results):
        return drivers_results.sort_values(ascending=False)[:self.num_scoring_drivers_in_team].sum()

    def _delete_drop_week_score_from_drivers_weekend_totals(self, driver_weekend_totals_row):
        driver_weekend_totals_row.loc[driver_weekend_totals_row["drop_week"]] = 0
        return driver_weekend_totals_row


    def _add_countback_arrays(self, countback_arrays):
        countback_arrays_stacked = np.stack(countback_arrays)
        # must cast to list cause of Must produce aggregated value issue stackoverflow.com/questions/39840546/must-produce-aggregated-value-i-swear-that-i-am
        return list(np.sum(countback_arrays_stacked, axis=0))

    def _construct_teams_totals(self, drivers_totals_table):
        drivers_teams_table = self.series_drivers_table[["team"]]
        drivers_totals_table_with_teams = drivers_totals_table.merge(drivers_teams_table, left_index=True, right_index=True)
        # drivers without teams are in the "Independent" team and don't participate in team scoring
        drivers_totals_table_with_teams = drivers_totals_table_with_teams[drivers_totals_table_with_teams["team"] != "Independent"]
        drivers_weekend_totals_with_drop_week_and_teams = drivers_totals_table_with_teams.drop(columns=["total", "total_with_drop_week", "countback_array"])

        teams_totals_by_weekend = drivers_weekend_totals_with_drop_week_and_teams.drop(columns="drop_week").groupby("team").agg(self._add_teams_driver_scores)
        total_column = teams_totals_by_weekend.sum(axis=1)

        drivers_weekend_totals_with_drop_week_score_deleted_and_teams = drivers_weekend_totals_with_drop_week_and_teams.apply(self._delete_drop_week_score_from_drivers_weekend_totals, axis=1)
        teams_totals_with_drop_week_by_weekend = drivers_weekend_totals_with_drop_week_score_deleted_and_teams.drop(columns="drop_week").groupby("team").agg(self._add_teams_driver_scores)
        total_with_drop_week_column = teams_totals_with_drop_week_by_weekend.sum(axis=1)

        countback_array_column = drivers_totals_table_with_teams.groupby("team")["countback_array"].agg(self._add_countback_arrays).apply(lambda lst: np.array(lst))

        drivers_list_column = drivers_totals_table_with_teams[["team"]].reset_index().groupby("team",group_keys=True).agg(list)

        teams_totals_table = pd.concat([total_column, total_with_drop_week_column, countback_array_column, drivers_list_column], axis=1)
        teams_totals_table.columns = ["total", "total_with_drop_week", "countback_array", "drivers_list"]

        drivers_totals_table = drivers_totals_table.sort_values("countback_array", key=lambda x: np.argsort(self._index_sort_countback_arrays(drivers_totals_table["countback_array"])))

        if self.drop_week:
            teams_totals_table = teams_totals_table.sort_values("total_with_drop_week", ascending=False, kind="mergesort")  # mergesort is required to stable sort
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
