import os

import numpy as np
import pandas as pd

import Utils
from RaceReport import RaceReport


class Championship:

    def __init__(self, series, series_sessions, rounds_to_include, drop_week=False, num_scoring_drivers_in_team=2,
                 debug_csv_parse=False):
        self.series = series
        self.series_sessions = series_sessions
        self.rounds_to_include = rounds_to_include
        self.drop_week = drop_week
        self.num_scoring_drivers_in_team = num_scoring_drivers_in_team
        self.debug_csv_parse = debug_csv_parse

        print("creating championship points tables for:", series)

        self.series_drivers_table = Utils.read_drivers_table(series)
        self.series_scoring_table = Utils.read_scoring_table(series)
        self.series_tracks_table = Utils.read_tracks_table(series)
        assert 1 <= self.rounds_to_include <= len(
            self.series_tracks_table), "rounds_to_include must be between 1 and {}".format(
            len(self.series_tracks_table))
        assert 1 <= self.num_scoring_drivers_in_team <= len(
            self.series_drivers_table), "rounds_to_include must be between 1 and {}".format(
            len(self.series_drivers_table))

        self.race_reports = self._read_race_reports()
        self.series_quali_sessions = list(self.race_reports.values())[0].quali_sessions
        self.series_race_sessions = list(self.race_reports.values())[0].race_sessions
        self.num_total_races = len(self.series_tracks_table) * len(self.series_race_sessions)

        drivers_points_table_unsorted = self._construct_drivers_points()
        self.drivers_totals_table, self.drivers_points_table = self._construct_drivers_totals_and_sort_drivers_points(
            drivers_points_table_unsorted)
        self.teams_and_drivers_table = self._construct_teams_and_drivers_table(self.drivers_totals_table)
        self.teams_totals_table = self._construct_teams_totals(self.drivers_totals_table)
        self.summary_table = self._construct_summary()
        self.drivers_participation_table = self._construct_drivers_participation(self.drivers_points_table)

    def _read_race_reports(self):
        race_reports = {}

        for i, race_and_race_row in enumerate(self.series_tracks_table.iterrows()):
            if i == self.rounds_to_include:
                break

            race, race_row = race_and_race_row
            race_path = os.path.join(self.series, race)
            if os.path.isdir(race_path):
                try:
                    race_reports[race] = RaceReport(self.series_sessions, self.series, race,
                                                    drivers_table=self.series_drivers_table,
                                                    scoring_table=self.series_scoring_table,
                                                    csv_manual_adjustment=race_row["csv_manual_adjustment"],
                                                    debug_csv_parse=self.debug_csv_parse)
                    print("read race report for", race_path)
                except FileNotFoundError:
                    print("no csv found for", race)
            else:
                print("no directory found for", race)

        return race_reports

    def _construct_drivers_points(self):
        drivers_points_table = pd.DataFrame(index=self.series_drivers_table.index, columns=pd.MultiIndex.from_product(
            [self.series_tracks_table.index, self.series_race_sessions], names=["track", "session"]))
        # truncate table to only calculate up to rounds needed
        drivers_points_table = drivers_points_table.iloc[:, 0:(self.rounds_to_include * len(self.series_race_sessions))]

        for driver in drivers_points_table.index:
            for track, session in drivers_points_table.columns:

                result_info = DriverRaceResultInfo()

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

        print("computed drivers points table")
        return drivers_points_table

    def _construct_teams_and_drivers_table(self, drivers_points_table):
        # note that this will contains only drivers that have participated at anything
        # drivers_lists will be in order of highest points scorers, but teams will be alphabetically sorted
        drivers_teams_table = self.series_drivers_table[["team"]]
        teams_and_drivers_table = drivers_points_table.merge(drivers_teams_table, left_index=True, right_index=True)
        teams_and_drivers_table = teams_and_drivers_table.reset_index()[["ign", "team"]]
        teams_and_drivers_table = teams_and_drivers_table.groupby("team").agg(lambda drivers: drivers.values.tolist())
        teams_and_drivers_table = teams_and_drivers_table.sort_index().rename(columns={"ign": "drivers_list"})
        if Utils.NO_TEAM in teams_and_drivers_table.index:
            index = teams_and_drivers_table.index.tolist()
            index.remove(Utils.NO_TEAM)
            teams_and_drivers_table = teams_and_drivers_table.reindex(index + [Utils.NO_TEAM])
        return teams_and_drivers_table

    def _get_countback_array(self, driver_all_results):
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
        drivers_totals_table = drivers_points_table.groupby(level=0, axis=1, sort=False).agg(self._get_weekend_totals)

        drivers_totals_table["drop_week"] = drivers_totals_table.agg(self._get_drop_week_name, axis=1)
        drivers_totals_table["total"] = drivers_totals_table.drop(columns="drop_week").sum(axis=1)
        drivers_totals_table["total_with_drop_week"] = drivers_totals_table.apply(
            self._subtract_drop_week_score_from_driver_total, axis=1)

        drivers_totals_table["countback_array"] = drivers_points_table.apply(self._get_countback_array, axis=1)
        drivers_totals_table = drivers_totals_table.sort_values("countback_array", key=lambda x: np.argsort(
            self._index_sort_countback_arrays(drivers_totals_table["countback_array"])))

        if self.drop_week:
            drivers_totals_table = drivers_totals_table.sort_values("total_with_drop_week", ascending=False,
                                                                    kind="mergesort")  # mergesort is required to stable sort
        else:
            drivers_totals_table = drivers_totals_table.sort_values("total", ascending=False, kind="mergesort")

        drivers_points_table_sorted = drivers_points_table.reindex(drivers_totals_table.index)
        print("computed drivers totals table")
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
        drivers_totals_table_with_teams = drivers_totals_table.merge(drivers_teams_table, left_index=True,
                                                                     right_index=True)
        # drivers without teams don't participate in team scoring
        drivers_totals_table_with_teams = drivers_totals_table_with_teams[
            -(drivers_totals_table_with_teams["team"] == Utils.NO_TEAM)]
        drivers_weekend_totals_with_drop_week_and_teams = drivers_totals_table_with_teams.drop(
            columns=["total", "total_with_drop_week", "countback_array"])

        teams_totals_by_weekend = drivers_weekend_totals_with_drop_week_and_teams.drop(columns="drop_week").groupby(
            "team").agg(self._add_teams_driver_scores)
        total_column = teams_totals_by_weekend.sum(axis=1)

        drivers_weekend_totals_with_drop_week_score_deleted_and_teams = drivers_weekend_totals_with_drop_week_and_teams.apply(
            self._delete_drop_week_score_from_drivers_weekend_totals, axis=1)
        teams_totals_with_drop_week_by_weekend = drivers_weekend_totals_with_drop_week_score_deleted_and_teams.drop(
            columns="drop_week").groupby("team").agg(self._add_teams_driver_scores)
        total_with_drop_week_column = teams_totals_with_drop_week_by_weekend.sum(axis=1)

        countback_array_column = drivers_totals_table_with_teams.groupby("team")["countback_array"].agg(
            self._add_countback_arrays).apply(lambda lst: np.array(lst))

        teams_totals_table = pd.concat(
            [total_column, total_with_drop_week_column, countback_array_column], axis=1)
        teams_totals_table.columns = ["total", "total_with_drop_week", "countback_array"]

        drivers_totals_table = drivers_totals_table.sort_values("countback_array", key=lambda x: np.argsort(
            self._index_sort_countback_arrays(drivers_totals_table["countback_array"])))

        if self.drop_week:
            teams_totals_table = teams_totals_table.sort_values("total_with_drop_week", ascending=False,
                                                                kind="mergesort")  # mergesort is required to stable sort
        else:
            teams_totals_table = teams_totals_table.sort_values("total", ascending=False, kind="mergesort")
        print("computed teams totals table")
        return teams_totals_table

    def _construct_summary(self):
        summary_table = pd.DataFrame(
            index=pd.MultiIndex.from_product([self.series_tracks_table.index, self.series_race_sessions],
                                             names=["track", "session"]), columns=["link", "pole", "fastest", "winner"])
        # truncate results to only calculate up to rounds needed
        summary_table = summary_table.iloc[0:(self.rounds_to_include * len(self.series_race_sessions))]

        for track, session in summary_table.index:
            race_report = self.race_reports[track]
            race_table = race_report.tables[session]

            summary_table.loc[(track, session), "link"] = race_report.simresults_url
            summary_table.loc[(track, session), "winner"] = race_table.iloc[0]["Driver"]
            summary_table.loc[(track, session), "fastest"] = race_table.sort_values("Best lap time").iloc[0]["Driver"]
            # only show pole driver if grid determined by a quali session
            summary_table.loc[(track, session), "pole"] = None
            if race_report.race_session_grid_determined_by[session] in self.series_quali_sessions:
                summary_table.loc[(track, session), "pole"] = race_table.sort_values("Grid").iloc[0]["Driver"]

        drivers_teams_table = self.series_drivers_table[["team"]]
        summary_table = summary_table.merge(drivers_teams_table, how='left', left_on="winner", right_index=True)

        print("computed results summary table")
        return summary_table

    def _get_weekend_participation(self, weekend_results):
        weekend_total_points = weekend_results.applymap(lambda result_info: result_info.participated)
        return weekend_total_points.all(axis=1)

    def _get_participation_string(self, driver_participations):
        participation_sequences = []
        sequence = None
        for i, participated in enumerate(driver_participations):
            if participated:
                if sequence is None:
                    sequence = [i + 1, i + 1]
                else:
                    sequence[1] = i + 1
            elif sequence:
                participation_sequences.append(sequence)
                sequence = None
        if sequence:
            participation_sequences.append(sequence)

        participation_string = ", ".join(
            ["{}-{}".format(s[0], s[1]) if s[1] - s[0] > 0 else str(s[0]) for s in participation_sequences])
        return participation_string

    def _construct_drivers_participation(self, drivers_points_table):
        drivers_participation_table = drivers_points_table.groupby(level=0, axis=1, sort=False).agg(
            self._get_weekend_participation)
        drivers_participation_table["participation_string"] = drivers_participation_table.apply(
            self._get_participation_string, axis=1)

        print("computed drivers participation table")
        return drivers_participation_table


# compressed race result info obj for a driver and session
class DriverRaceResultInfo:

    def __init__(self, pos=-1, points=0, quali_pos=-1, quali_points=0, dnf=False):
        self.pos = pos
        self.points = points
        self.quali_pos = quali_pos
        self.quali_points = quali_points
        self.dnf = dnf
        self.participated = not bool(pos == -1 and quali_pos == -1)
        self.total_points = self.points + self.quali_points

    def __str__(self):
        if (self.pos < 0) and (self.quali_pos < 0):
            return "NP"
        elif self.dnf:
            return "DNF"
        else:
            return str(self.total_points)

    def __repr__(self):
        return "DriverRaceResultInfo({},{},{},{},{})".format(self.pos, self.points, self.quali_pos,
                                                             self.quali_points, self.dnf)
