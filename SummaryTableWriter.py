from Championship import Championship
from TableWriter import TableWriter


class SummaryTableWriter(TableWriter):
    round_number_width = 40
    round_race_width = 40
    round_width = round_number_width + round_race_width
    circuit_width = 155

    pole_width = 165
    fastest_lap_width = 165
    winner_width = 165
    team_width = 210
    link_width = 80

    table_width = round_width + circuit_width + pole_width + fastest_lap_width + winner_width + team_width + link_width

    header_1_format = """|=(% colspan="2" rowspan="1" scope="row" style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {round_width}px;" %)Round|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {circuit_width}px;" %)Circuit|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {pole_width}px;" %)Pole Position|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {fastest_lap_width}px;" %)Fastest Lap|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {winner_width}px;" %)Winning Driver|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {team_width}px;" %)Winning Team|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: {link_width}px; text-align: center; vertical-align: middle;" %)Results"""

    row_round_number_format = """|=(% colspan="1" rowspan="{num_race_sessions}" style="background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {round_number_width}px;" %){round_number}"""
    row_round_race_format = """|(% style="background-color: rgb(234, 236, 240); text-align: center; vertical-align: middle; width: {round_race_width}px;" %)**{session_abbrev}**"""
    row_circuit_format = """|(% colspan="1" rowspan="{num_race_sessions}" style="text-align:center; vertical-align:middle; width:{circuit_width}px" %)[[image:{track_flag}||height="14" width="23"]] {track_name}"""

    row_winning_team_format = """|(% style="text-align:center; vertical-align:middle; width:{team_width}px" %){team}"""
    row_results_link_format = """|(% colspan="1" rowspan="{num_race_sessions}" style="text-align:center; vertical-align:middle; width:{link_width}px" %)[[Result>>{link}]]"""

    row_session_drivers_and_team_empty = "".join([TableWriter.empty_cell_format.format(width=pole_width),
                                                  TableWriter.empty_cell_format.format(width=fastest_lap_width),
                                                  TableWriter.empty_cell_format.format(width=winner_width),
                                                  TableWriter.empty_cell_format.format(width=team_width)])

    def __init__(self, championship, output_file_name="summary_table.txt"):
        super().__init__(championship, output_file_name)

    def _generate_table_header(self):
        header_0 = self.header_0_format.format(table_width=self.table_width)

        header_1 = self.header_1_format.format(round_width=self.round_width, circuit_width=self.circuit_width,
                                               pole_width=self.pole_width, fastest_lap_width=self.fastest_lap_width,
                                               winner_width=self.winner_width, team_width=self.team_width,
                                               link_width=self.link_width)

        lines_buffer = [header_0, header_1]
        return lines_buffer

    def _generate_summary_row_drivers_and_team(self, track, session):
        summary_table_row = self.championship.summary_table.loc[(track, session)]

        pole_driver = summary_table_row["pole"]
        pole_driver_driver_flag_and_name = self.empty_cell_format.format(width=self.pole_width)
        if pole_driver is not None:
            pole_driver_driver_flag_and_name = self._generate_driver_flag_and_name(pole_driver, self.pole_width)

        fastest_lap_driver = summary_table_row["fastest"]
        fastest_lap_driver_flag_and_name = self._generate_driver_flag_and_name(fastest_lap_driver,
                                                                               self.fastest_lap_width)

        winning_driver = summary_table_row["winner"]
        winning_driver_flag_and_name = self._generate_driver_flag_and_name(winning_driver, self.winner_width)

        winning_driver_team = summary_table_row["team"]
        winning_team = self.row_winning_team_format.format(team_width=self.team_width, team=winning_driver_team)

        session_row_substrings = [pole_driver_driver_flag_and_name, fastest_lap_driver_flag_and_name,
                                  winning_driver_flag_and_name, winning_team]
        return "".join(session_row_substrings)

    def _generate_table_rows(self):
        lines_buffer = []

        for i, track in enumerate(self.championship.series_tracks_table.index):

            round_number = i + 1
            row_round_number = self.row_round_number_format.format(num_race_sessions=self.num_race_sessions,
                                                                   round_number_width=self.round_number_width,
                                                                   round_number=round_number)
            first_session = self.championship.series_race_sessions[0]

            session_abbrev = self._get_race_session_abbrev(first_session)
            row_round_race = self.row_round_race_format.format(round_race_width=self.round_race_width,
                                                               session_abbrev=session_abbrev)

            track_info = self.championship.series_tracks_table.loc[track]
            row_circuit = self.row_circuit_format.format(num_race_sessions=self.num_race_sessions,
                                                         circuit_width=self.circuit_width,
                                                         track_flag=track_info["flag"],
                                                         track_name=track_info["full_name"])

            row_results_link = self.empty_multirow_cell_format.format(rows=self.num_race_sessions,
                                                                      width=self.link_width)
            row_session_drivers_and_team = self.row_session_drivers_and_team_empty
            if i < self.championship.rounds_to_include:
                results_link = self.championship.summary_table.loc[(track, first_session), "link"]
                row_results_link = self.row_results_link_format.format(num_race_sessions=self.num_race_sessions,
                                                                       link_width=self.link_width, link=results_link)
                row_session_drivers_and_team = self._generate_summary_row_drivers_and_team(track, first_session)

            summary_row_substrings = [row_round_number, row_round_race, row_circuit, row_session_drivers_and_team,
                                      row_results_link]
            summary_row = "".join(summary_row_substrings)

            lines_buffer.append(summary_row)

            for session in self.championship.series_race_sessions[1:]:
                session_abbrev = self._get_race_session_abbrev(session)
                round_race = self.row_round_race_format.format(round_race_width=self.round_race_width,
                                                               session_abbrev=session_abbrev)

                row_session_drivers_and_team = self.row_session_drivers_and_team_empty
                if i < self.championship.rounds_to_include:
                    row_session_drivers_and_team = self._generate_summary_row_drivers_and_team(track, session)

                substrings = [round_race, row_session_drivers_and_team]
                row = "".join(substrings)
                lines_buffer.append(row)

        return lines_buffer


if __name__ == "__main__":
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 5

    championship = Championship(series, series_sessions, rounds_to_include)
    writer = SummaryTableWriter(championship)

    writer.write_lines()
