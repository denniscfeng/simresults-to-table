from Championship import Championship
from TableWriter import TableWriter


class TeamsStandingsWriter(TableWriter):
    pos_width = 60
    team_width = 270
    driver_num_width = 55

    header_1_team_format = """|=(% colspan="1" rowspan="2" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {team_width}px;" %)Team"""
    header_1_number_format = """|=(% colspan="1" rowspan="2" scope="row" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {number_width}px" %)No."""

    standing_row_pos_format = """|=(% colspan="1" rowspan="{num_drivers}" style="text-align: center; background-color: rgb(234, 236, 240); width: {pos_width}px; vertical-align: middle;" %){pos}"""
    standing_row_team_format = """|(% colspan="1" rowspan="{num_drivers}" style="text-align:center; vertical-align:middle; width:{team_width}px" %){team}"""
    standing_row_driver_num_format = """|(% style="text-align:center; vertical-align:middle; width:{driver_num_width}px" %){driver_num}"""
    standing_row_points_format = """|(% colspan="1" rowspan="{num_drivers}" style="text-align:center; vertical-align:middle; width:{points_width}px" %){points}"""

    def __init__(self, championship, output_file_name="teams_standings.txt"):
        super().__init__(championship, output_file_name)

        self.table_width = self.pos_width + self.team_width + self.driver_num_width + len(
            self.championship.series_tracks_table) * self.track_width + self.points_width

    def _generate_table_header(self):
        header_0 = self.header_0_format.format(table_width=self.table_width)

        header_1_substrings = [self.header_1_pos_format.format(pos_width=self.pos_width),
                               self.header_1_team_format.format(team_width=self.team_width),
                               self.header_1_number_format.format(number_width=self.driver_num_width),
                               self._generate_header_1_tracks_list(),
                               self.header_1_points_format.format(points_width=self.points_width)]
        header_1 = "".join(header_1_substrings)

        header_2 = self._generate_header_2_sessions_list()

        lines_buffer = [header_0, header_1, header_2]
        return lines_buffer

    def _generate_driver_row(self, driver):
        driver_info = self.championship.series_drivers_table.loc[driver]
        driver_num = driver_info["number"]
        standing_row_driver_num = self.standing_row_driver_num_format.format(driver_num_width=self.driver_num_width,
                                                                             driver_num=driver_num)
        return standing_row_driver_num + self._generate_standing_row_results_list(driver)

    def _generate_table_rows(self):
        lines_buffer = []

        for pos, team in enumerate(self.championship.teams_totals_table.index):
            pos += 1

            team_totals = self.championship.teams_totals_table.loc[team]
            drivers_list = team_totals["drivers_list"]
            num_drivers = len(drivers_list)

            team_row_pos = self.standing_row_pos_format.format(num_drivers=num_drivers, pos_width=self.pos_width,
                                                               pos=pos)
            team_row_team = self.standing_row_team_format.format(num_drivers=num_drivers, team_width=self.team_width,
                                                                 team=team)

            # the first driver's results go in the row with the pos, team name, and total points
            team_row_substrings = [team_row_pos, team_row_team, self._generate_driver_row(drivers_list[0])]

            team_total = team_totals["total"]

            if self.championship.drop_week:
                team_total_with_drop_week = team_totals["total_with_drop_week"]
                points_string = "**{}**".format(team_total_with_drop_week)
                if not team_total_with_drop_week == team_total:
                    points_string = "{}^^{}^^".format(points_string, team_total)
            else:
                points_string = "**{}**".format(team_total)

            team_row_points = self.standing_row_points_format.format(num_drivers=num_drivers,
                                                                     points_width=self.points_width,
                                                                     points=points_string)
            team_row_substrings.append(team_row_points)

            team_row = "".join(team_row_substrings)
            lines_buffer.append(team_row)

            # the remaining drivers results go on their own rows
            for driver in drivers_list[1:]:
                lines_buffer.append(self._generate_driver_row(driver))

        return lines_buffer


if __name__ == "__main__":
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 5

    championship = Championship(series, series_sessions, rounds_to_include)
    writer = TeamsStandingsWriter(championship)

    writer.write_lines()
