from Championship import Championship
from StandingsWriter import StandingsWriter


class DriverStandingsWriter(StandingsWriter):
    driver_width = 170

    header_1_driver_format = """|=(% colspan="1" rowspan="2" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {driver_width}px;" %)Driver"""

    result_row_driver_format = """|(% style="width:{driver_width}px" %)[[image:{driver_flag}||height="14" width="23"]] {driver}"""

    def __init__(self, championship, output_file_name="drivers_standings.txt"):
        super().__init__(championship, output_file_name)

        self.table_width = self.pos_width + self.driver_width + len(
            self.championship.series_tracks_table) * self.track_width + self.points_width

    def generate_table_header(self):
        header_0 = self.header_0_format.format(table_width=self.table_width)

        header_1 = self.header_1_pos_format.format(pos_width=self.pos_width) + \
                   self.header_1_driver_format.format(driver_width=self.driver_width) + \
                   self.generate_header_1_tracks_list() + \
                   self.header_1_points_format.format(points_width=self.points_width)

        header_2 = self.generate_header_2_sessions_list()

        lines_buffer = [header_0, header_1, header_2]
        return lines_buffer

    def __generate_driver_rows(self):
        lines_buffer = []

        for pos, driver in enumerate(self.championship.drivers_points_table.index):
            pos += 1

            driver_row_pos = self.result_row_pos_format.format(pos_width=self.pos_width, pos=pos)

            driver_info = self.championship.series_drivers_table.loc[driver]
            driver_flag = driver_info["flag"]
            driver_full_name = driver_info["name"]
            driver_row_driver = self.result_row_driver_format.format(driver_width=self.driver_width,
                                                                     driver_flag=driver_flag,
                                                                     driver=driver_full_name)

            driver_row_substrings = [driver_row_pos, driver_row_driver]

            for i in range(self.championship.num_total_races):

                result_string = ""
                result_color = self.result_color_default

                if i >= len(self.championship.drivers_points_table.columns):
                    driver_row_result = self.result_row_result_format.format(result_color=result_color,
                                                                             result_width=self.result_width,
                                                                             result=result_string)
                    driver_row_substrings.append(driver_row_result)
                    continue

                result_info = self.championship.drivers_points_table.loc[
                    driver, self.championship.drivers_points_table.columns[i]]

                if result_info.pos > 0:
                    result_color = self.result_color_no_points
                    result_string = str(result_info.pos)
                    if result_info.points > 0:
                        result_color = self.result_color_points
                    if result_info.pos <= 3:
                        result_color = self.result_color_top_3[result_info.pos - 1]
                    if result_info.dnf:
                        result_string = "RET"
                        result_color = self.result_color_ret
                    if result_info.qualy_points > 0:
                        result_string = "{}^^{}^^".format(result_string, result_info.qualy_pos)

                driver_row_result = self.result_row_result_format.format(result_color=result_color,
                                                                         result_width=self.result_width,
                                                                         result=result_string)
                driver_row_substrings.append(driver_row_result)

            driver_totals = self.championship.drivers_totals_table.loc[driver]
            driver_total = driver_totals["total"]

            if not self.championship.drivers_points_table.loc[driver].apply(
                    lambda r_info: r_info.participated).any():
                continue

            if self.championship.drop_week:
                driver_total_with_drop_week = driver_totals["total_with_drop_week"]
                points_string = "**{}**".format(driver_total_with_drop_week)
                if not driver_total_with_drop_week == driver_total:
                    points_string = "{}^^{}^^".format(points_string, driver_totals["total"])
            else:
                points_string = "**{}**".format(driver_total)

            driver_row_points = self.result_row_points_format.format(points_width=self.points_width,
                                                                     points=points_string)
            driver_row_substrings.append(driver_row_points)

            driver_row = "".join(driver_row_substrings)
            lines_buffer.append(driver_row)

        return lines_buffer

    def generate_table_strings(self):
        return self.generate_table_header() + self.__generate_driver_rows()


if __name__ == "__main__":
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 4

    championship = Championship(series, series_sessions, rounds_to_include)
    writer = DriverStandingsWriter(championship)

    writer.write_standings()
