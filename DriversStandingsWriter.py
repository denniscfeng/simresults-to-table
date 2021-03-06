from Championship import Championship
from TableWriter import TableWriter


class DriversStandingsWriter(TableWriter):
    driver_width = 170

    header_1_driver_format = """|=(% colspan="1" rowspan="2" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {driver_width}px;" %)Driver"""

    standing_row_pos_format = """|=(% style="text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width:{pos_width}px" %){pos}"""
    standing_row_points_format = """|(% style="text-align:center; vertical-align:middle; width:{points_width}px" %){points}"""

    def __init__(self, championship, output_file_name="drivers_standings.txt"):
        super().__init__(championship, output_file_name)

        self.table_width = self.pos_width + self.driver_width + len(
            self.championship.series_tracks_table) * self.track_width + self.points_width

    def _generate_table_header(self):
        header_0 = self.header_0_format.format(table_width=self.table_width)

        header_1_substrings = [self.header_1_pos_format.format(pos_width=self.pos_width),
                               self.header_1_driver_format.format(driver_width=self.driver_width),
                               self._generate_header_1_tracks_list(),
                               self.header_1_points_format.format(points_width=self.points_width)]
        header_1 = "".join(header_1_substrings)

        header_2 = self._generate_header_2_sessions_list()

        lines_buffer = [header_0, header_1, header_2]
        return lines_buffer

    def _generate_table_rows(self):
        lines_buffer = []

        for pos, driver in enumerate(self.championship.drivers_points_table.index):
            pos += 1

            driver_row_pos = self.standing_row_pos_format.format(pos_width=self.pos_width, pos=pos)
            driver_row_driver = self._generate_driver_flag_and_name(driver, self.driver_width)
            driver_row_results_list = self._generate_standing_row_results_list(driver)

            driver_row_substrings = [driver_row_pos, driver_row_driver, driver_row_results_list]

            driver_totals = self.championship.drivers_totals_table.loc[driver]
            driver_total = driver_totals["total"]

            if self.championship.drop_week:
                driver_total_with_drop_week = driver_totals["total_with_drop_week"]
                points_string = "**{}**".format(driver_total_with_drop_week)
                if not driver_total_with_drop_week == driver_total:
                    points_string = "{}^^{}^^".format(points_string, driver_total)
            else:
                points_string = "**{}**".format(driver_total)

            driver_row_points = self.standing_row_points_format.format(points_width=self.points_width,
                                                                       points=points_string)
            driver_row_substrings.append(driver_row_points)

            driver_row = "".join(driver_row_substrings)
            lines_buffer.append(driver_row)

        return lines_buffer


if __name__ == "__main__":
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 5

    championship = Championship(series, series_sessions, rounds_to_include)
    writer = DriversStandingsWriter(championship)

    writer.write_lines()
