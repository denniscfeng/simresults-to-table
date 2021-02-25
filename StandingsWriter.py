import re
import textwrap


class StandingsWriter:
    pos_width = 55
    result_width = 45
    points_width = 92

    header_0_format = """(% border="1" cellpadding="1" style="width:{table_width}px"%)"""
    header_1_pos_format = """|=(% colspan="1" rowspan="2" scope="row" style="border-color: rgb(0, 0, 0); text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width: {pos_width}px" %)Pos"""
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

    standing_row_pos_format = """|=(% style="text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width:{pos_width}px" %){pos}"""
    standing_row_result_format = """|(% style="background-color:{result_color}; text-align:center; vertical-align:middle; width:{result_width}px" %){result}"""
    standing_row_points_format = """|(% style="text-align:center; vertical-align:middle; width:{points_width}px" %){points}"""

    def __init__(self, championship, output_file_name):
        self.championship = championship
        self.output_file_name = output_file_name
        self.output_file = "{}/{}".format(championship.series, output_file_name)

        self.track_width = len(self.championship.series_race_sessions) * self.result_width

    def generate_header_1_tracks_list(self):
        header_1_tracks_list = []
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
            header_1_tracks_list.append(header_1_track)
        return "".join(header_1_tracks_list)

    def generate_header_2_sessions_list(self):
        header_2_sessions_list = []
        for _ in self.championship.series_tracks_table.index:
            for session in self.championship.series_race_sessions:
                session_number = re.findall('\d', session)[0]
                session_abbrev = "R{}".format(session_number)
                header_2_session = self.header_2_session_format.format(result_width=self.result_width,
                                                                       session_abbrev=session_abbrev)
                header_2_sessions_list.append(header_2_session)
        return "".join(header_2_sessions_list)

    def generate_standing_row_results_list(self, driver):
        row_results_substrings = []
        for i in range(self.championship.num_total_races):

            result_string = ""
            result_color = self.result_color_default

            if i >= len(self.championship.drivers_points_table.columns):
                driver_row_result = self.standing_row_result_format.format(result_color=result_color,
                                                                           result_width=self.result_width,
                                                                           result=result_string)
                row_results_substrings.append(driver_row_result)
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

            driver_row_result = self.standing_row_result_format.format(result_color=result_color,
                                                                       result_width=self.result_width,
                                                                       result=result_string)
            row_results_substrings.append(driver_row_result)
        return "".join(row_results_substrings)

    def generate_table_header(self):
        raise NotImplementedError

    def generate_standing_rows(self):
        raise NotImplementedError

    def generate_table_strings(self):
        return self.generate_table_header() + self.generate_standing_rows()

    def write_standings(self, lines_buffer=None):
        if not lines_buffer:
            lines_buffer = self.generate_table_strings()

        with open(self.output_file, "w+") as fp:
            table_string = "\n".join(lines_buffer) + "\n\n"
            fp.write(table_string)
            print("wrote standings:", self.output_file)
