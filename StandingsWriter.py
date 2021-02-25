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

    result_row_pos_format = """|=(% style="text-align: center; vertical-align: middle; background-color: rgb(234, 236, 240); width:{pos_width}px" %){pos}"""
    result_row_result_format = """|(% style="background-color:{result_color}; text-align:center; vertical-align:middle; width:{result_width}px" %){result}"""
    result_row_points_format = """|(% style="text-align:center; vertical-align:middle; width:{points_width}px" %){points}"""

    def __init__(self, championship, output_file_name):
        self.championship = championship
        self.output_file_name = output_file_name
        self.output_file = "{}/{}".format(championship.series, output_file_name)

        self.track_width = len(self.championship.series_race_sessions) * self.result_width

    def generate_table_strings(self):
        raise NotImplementedError

    def write_standings(self, lines_buffer=None):
        if not lines_buffer:
            lines_buffer = self.generate_table_strings()

        with open(self.output_file, "w+") as fp:
            table_string = "\n".join(lines_buffer) + "\n\n"
            fp.write(table_string)
            print("wrote standings:", self.output_file)
