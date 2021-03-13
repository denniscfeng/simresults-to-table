from Championship import Championship
from TableWriter import TableWriter

class ParticpationTableWriter(TableWriter):

    team_width = 230
    number_width = 55
    driver_width = 165
    rounds_width = 100

    table_width = team_width + number_width + driver_width + rounds_width

    header_1_format = """|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: {team_width}px; text-align: center; vertical-align: middle;" %)Team|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: {number_width}px; text-align: center; vertical-align: middle;" %)No|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: {driver_width}px; text-align: center; vertical-align: middle;" %)Driver|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: {rounds_width}px; text-align: center; vertical-align: middle;" %)Rounds"""
    row_team_format = """|(% colspan="1" rowspan="{num_drivers}" style="text-align:center; vertical-align:middle; width:{team_width}px" %){team}"""
    row_number_format = """|(% style="text-align:center; vertical-align:middle; width:{number_width}px" %){number}"""
    row_rounds_format = """|(% style="text-align:center; vertical-align:middle; width:{rounds_width}px" %){rounds}"""

    def __init__(self, championship, output_file_name="participation_table.txt"):
        super().__init__(championship, output_file_name)

    def _generate_table_header(self):
        header_0 = self.header_0_format.format(table_width=self.table_width)

        header_1 = self.header_1_format.format(team_width=self.team_width, number_width=self.number_width, driver_width=self.driver_width, rounds_width=self.rounds_width)

        lines_buffer = [header_0, header_1]
        return lines_buffer

    def _generate_driver_and_participation_row(self, driver):
        number = self.championship.series_drivers_table.loc[driver, "number"]
        row_number = self.row_number_format.format(number_width=self.number_width, number=number)

        driver_flag_and_name = self._generate_driver_flag_and_name(driver, self.driver_width)

        participation_string = self.championship.drivers_participation_table.loc[driver, "participation_string"]
        row_rounds = self.row_rounds_format.format(rounds_width=self.rounds_width, rounds=participation_string)

        substrings = [row_number, driver_flag_and_name, row_rounds]
        return "".join(substrings)

    def _generate_table_rows(self):
        lines_buffer = []

        for team in self.championship.teams_and_drivers_table.index:
            drivers_list = self.championship.teams_and_drivers_table.loc[team, "drivers_list"]

            row_team = self.row_team_format.format(num_drivers=len(drivers_list), team_width=self.team_width, team=team)
            row_driver_and_participation = self._generate_driver_and_participation_row(drivers_list[0])

            row_substrings = [row_team, row_driver_and_participation]
            row = "".join(row_substrings)
            lines_buffer.append(row)

            for driver in drivers_list[1:]:
                lines_buffer.append(self._generate_driver_and_participation_row(driver))

        return lines_buffer


if __name__ == "__main__":
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 5

    championship = Championship(series, series_sessions, rounds_to_include)
    writer = ParticpationTableWriter(championship)

    writer.write_lines()
