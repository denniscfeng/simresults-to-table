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

    def __init__(self, championship, output_file_name="summary_table.txt"):
        super().__init__(championship, output_file_name)

    def _generate_table_header(self):
        header_0 = self.header_0_format.format(table_width=self.table_width)

        header_1 = self.header_1_format.format(round_width=self.round_width, circuit_width=self.circuit_width, pole_width=self.pole_width, fastest_lap_width=self.fastest_lap_width, winner_width=self.winner_width, team_width=self.team_width, link_width=self.link_width)

        lines_buffer = [header_0, header_1]
        return lines_buffer

    def _generate_table_rows(self):
        lines_buffer = []

        return lines_buffer


if __name__ == "__main__":
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 5

    championship = Championship(series, series_sessions, rounds_to_include)
    writer = SummaryTableWriter(championship)

    writer.write_lines()
