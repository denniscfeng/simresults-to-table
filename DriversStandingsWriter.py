import re
import textwrap

from Championship import Championship


class DriversPointsWriter:
    pos_width = 55
    driver_width = 170
    result_width = 45
    points_width = 92

    header_0_format = """(% border="1" cellpadding="1" style="width:{table_width}px"%)"""
    header_1_pos_driver_format = """|=(% colspan="1" rowspan="2" scope="row" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {pos_width}px" %)Pos|=(% colspan="1" rowspan="2" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {driver_width}px;" %)Driver"""
    header_1_track_format = """|=(% colspan="2" rowspan="1" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {track_width}px" %)((({header_1_track_flag_and_abbrev})))"""
    header_1_track_flag_and_abbrev_format = textwrap.dedent("""
    [[image:{track_flag}||height="14" width="23"]]

    {track_abbrev}
    """)
    header_1_points_format = """|=(% colspan="1" rowspan="2" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {points_width}px" %)Points"""
    header_2_session_format = """|(% style="background-color:#eaecf0; text-align:center; vertical-align:middle; width:{result_width}px" %)**{session_abbrev}**"""

    result_color_top_3 = ["#ffffbf", "#dfdfdf", "#ffdf9f"]
    result_color_points = "#dfffdf"
    result_color_no_points = "#cfcfff"
    result_color_ret = "#efcfff"
    result_color_default = "#ffffff"

    driver_row_pos_format = """|=(% style="text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width:{pos_width}px" %){pos}"""
    driver_row_driver_format = """|(% style="width:{driver_width}px" %)[[image:{driver_flag}||height="14" width="23"]] {driver}"""
    driver_row_result_format = """|(% style="background-color:{result_color}; text-align:center; vertical-align:middle; width:{result_width}px" %){result}"""
    driver_row_points_format = """|(% style="text-align:center; vertical-align:middle; width:{points_width}px" %){points}"""

    def __init__(self, championship, output_file_name="drivers_standings.txt"):
        self.championship = championship
        self.output_file_name = output_file_name
        self.output_file = "{}/drivers_standings.txt".format(championship.series)

        self.track_width = len(self.championship.series_race_sessions) * self.result_width
        self.table_width = self.pos_width + self.driver_width + len(
            self.championship.series_tracks_table) * self.track_width + self.points_width

    def __generate_table_header(self):
        header_0 = self.header_0_format.format(table_width=self.table_width)

        header_1_substrings = [
            self.header_1_pos_driver_format.format(pos_width=self.pos_width, driver_width=self.driver_width)]
        for track in self.championship.series_tracks_table.index:
            track_info = self.championship.series_tracks_table.loc[track]
            track_abbrev = track_info["abbrev"]
            if track in self.championship.race_reports:
                track_abbrev = "[[{}>>{}]]".format(track_abbrev, self.championship.race_reports[track].simresults_url)
            header_1_track_flag_and_abbrev = self.header_1_track_flag_and_abbrev_format.format(
                track_flag=track_info["flag"],
                track_abbrev=track_abbrev)
            header_1_track = self.header_1_track_format.format(track_width=self.track_width,
                                                               header_1_track_flag_and_abbrev=header_1_track_flag_and_abbrev)
            header_1_substrings.append(header_1_track)
        header_1_substrings.append(self.header_1_points_format.format(points_width=self.points_width))
        header_1 = "".join(header_1_substrings)

        header_2_substrings = []
        for _ in self.championship.series_tracks_table.index:
            for session in self.championship.series_race_sessions:
                session_number = re.findall('\d', session)[0]
                session_abbrev = "R{}".format(session_number)
                header_2_session = self.header_2_session_format.format(result_width=self.result_width,
                                                                       session_abbrev=session_abbrev)
                header_2_substrings.append(header_2_session)
        header_2 = "".join(header_2_substrings)

        lines_buffer = [header_0, header_1, header_2]
        return lines_buffer

    def __generate_driver_rows(self):
        lines_buffer = []

        for pos, driver in enumerate(self.championship.drivers_points_table.index):
            pos += 1

            driver_row_pos = self.driver_row_pos_format.format(pos_width=self.pos_width, pos=pos)

            driver_info = self.championship.series_drivers_table.loc[driver]
            driver_flag = driver_info["flag"]
            driver_full_name = driver_info["name"]
            driver_row_driver = self.driver_row_driver_format.format(driver_width=self.driver_width,
                                                                     driver_flag=driver_flag,
                                                                     driver=driver_full_name)

            driver_row_substrings = [driver_row_pos, driver_row_driver]

            for i in range(self.championship.num_total_races):

                result_string = ""
                result_color = self.result_color_default

                if i >= len(self.championship.drivers_points_table.columns):
                    driver_row_result = self.driver_row_result_format.format(result_color=result_color,
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

                driver_row_result = self.driver_row_result_format.format(result_color=result_color,
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

            driver_row_points = self.driver_row_points_format.format(points_width=self.points_width,
                                                                     points=points_string)
            driver_row_substrings.append(driver_row_points)

            driver_row = "".join(driver_row_substrings)
            lines_buffer.append(driver_row)

        return lines_buffer

    def generate_table_strings(self):
        return self.__generate_table_header() + self.__generate_driver_rows()

    def write_drivers_standings(self, lines_buffer=None):
        if not lines_buffer:
            lines_buffer = self.generate_table_strings()

        with open(self.output_file, "w+") as fp:
            table_string = "\n".join(lines_buffer) + "\n\n"
            fp.write(table_string)
            print("wrote drivers standings to", self.output_file)


if __name__ == "__main__":
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 4

    championship = Championship(series, series_sessions, rounds_to_include)
    writer = DriversPointsWriter(championship)

    writer.write_drivers_standings()
