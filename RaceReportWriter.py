import os

from RaceReport import RaceReport


class RaceReportWriter:
    # Race report table format strings TODO use parameterized print format like in TableWriter
    quali_row_0 = """(% border="1" style="width:554px" %)"""
    quali_row_1 = """|=(% scope="row" style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 41px; text-align: center;" %)Pos|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 44px; text-align: center;" %)No|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 155px; text-align: center;" %)Driver|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 233px; text-align: center;" %)Team|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 77px; text-align: center;" %)Time"""
    quali_row_2 = """|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; width: 41px;" %){}|(% style="border-color:#000000; text-align:center; width:44px" %){}|(% style="border-color:#000000; width:155px" %)[[image:{}||height="14" width="23"]] {}|(% style="text-align:center; border-color:#000000; width:233px" %){}|(% style="text-align:center; border-color:#000000; width:77px" %){}"""
    quali_row = """|=(% style="background-color: rgb(234, 236, 240); text-align: center; width: 41px;" %){}|(% style="text-align:center; width:44px" %){}|(% style="width:155px" %)[[image:{}||height="14" width="23"]] {}|(% style="text-align:center; width:233px" %){}|(% style="text-align:center; width:77px" %){}"""
    quali_row_last = """|=(% colspan="5" style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; width: 552px;" %)[[Source>>{}]]"""
    race_row_0 = """(% border="1" style="width:747px" %)"""
    race_row_1 = """|=(% scope="row" style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 41px; text-align: center;" %)Pos|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 44px; text-align: center;" %)No|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 155px; text-align: center;" %)Driver|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 229px; text-align: center;" %)Team|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 44px; text-align: center;" %)Laps|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 111px; text-align: center;" %)Time/Retired|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 53px; text-align: center;" %)Grid|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); width: 62px; text-align: center;" %)Points"""
    race_row_2 = """|=(% style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; width: 41px;" %){}|(% style="border-color:#000000; text-align:center; width:44px" %){}|(% style="border-color:#000000; width:155px" %)[[image:{}||height="14" width="23"]] {}|(% style="text-align:center; border-color:#000000; width:233px" %){}|(% style="text-align:center; border-color:#000000; width:44px" %){}|(% style="text-align:center; border-color:#000000; width:111px" %){}|(% style="text-align:center; border-color:#000000; width:53px" %){}|(% style="text-align:center; border-color:#000000; width:62px" %){}"""
    race_row = """|=(% style="background-color: rgb(234, 236, 240); text-align: center; width: 41px;" %){}|(% style="text-align:center; width:44px" %){}|(% style="width:155px" %)[[image:{}||height="14" width="23"]] {}|(% style="text-align:center; width:233px" %){}|(% style="text-align:center; width:44px" %){}|(% style="text-align:center; width:111px" %){}|(% style="text-align:center; width:53px" %){}|(% style="text-align:center; width:62px" %){}"""
    race_row_last = """|=(% colspan="8" style="border-color: rgb(0, 0, 0); background-color: rgb(234, 236, 240); text-align: center; width: 745px;" %)[[Source>>{}]]"""
    race_row_fastestlap = """Fastest lap:  [[image:{}||height="14" width="23"]] {} - {}"""

    def __init__(self, race_report, output_file_name="wiki_tables.txt"):
        self.race_report = race_report
        self.output_file_name = output_file_name
        self.output_file = os.path.join(self.race_report.race_directory_path, output_file_name)
        print("writing race report tables to:", self.output_file)

    # Generate quali table markdown from quali session dataframe, result is a list of lines
    def generate_quali_table_strings(self, table_name):

        table_df = self.race_report.tables[table_name]

        lines_buffer = [table_name, self.quali_row_0, self.quali_row_1]

        for i, df_row in table_df.iterrows():

            driver = df_row["Driver"]

            driver_info = self.race_report.drivers_table.loc[driver]

            position = i
            number = driver_info["number"]
            flag = driver_info["flag"]
            name = driver_info["name"]
            team = driver_info["team"] if driver_info["team"] else "Independent"
            time = df_row["Best lap"]
            if position == 1:
                time = "**{}**".format(time)

            line = self.quali_row_2.format(position, number, flag, name, team,
                                           time) if i == 0 else self.quali_row.format(position, number, flag, name,
                                                                                      team, time)
            lines_buffer.append(line)

        lines_buffer.append(self.quali_row_last.format(self.race_report.simresults_url))

        return lines_buffer

    def generate_race_table_strings(self, table_name):

        table_df = self.race_report.tables[table_name]

        lines_buffer = [table_name, self.race_row_0, self.race_row_1]

        for i, df_row in table_df.iterrows():

            driver = df_row["Driver"]

            driver_info = self.race_report.drivers_table.loc[driver]

            position = i
            number = driver_info["number"]
            flag = driver_info["flag"]
            name = driver_info["name"]
            team = driver_info["team"]
            laps = df_row["Laps"]
            points = df_row["Points"]
            timeorretired = df_row["Time/Retired"] if df_row["Time/Retired"] else "DNF"
            grid = df_row["Grid"] if df_row["Grid"] > 0 else "DNQ"

            if "Qualify Points" in table_df.columns:
                points = str(df_row["Points"] + df_row["Qualify Points"]) + (
                    "^^{}^^".format(grid) if df_row["Qualify Points"] > 0 else "")

            line = self.race_row_2.format(position, number, flag, name, team, laps, timeorretired, grid,
                                          points) if i == 0 else self.race_row.format(position, number, flag, name,
                                                                                      team, laps, timeorretired, grid,
                                                                                      points)
            lines_buffer.append(line)

        lines_buffer.append(self.race_row_last.format(self.race_report.simresults_url))

        fastest_driver = table_df.loc[table_df["Best lap time"] == table_df["Best lap time"].min()].iloc[0]["Driver"]
        fastest_driver_flag = self.race_report.drivers_table.loc[fastest_driver, "flag"]

        fastest_time = table_df.loc[table_df["Driver"] == fastest_driver]["Best lap"].item()
        lines_buffer.append(self.race_row_fastestlap.format(fastest_driver_flag, fastest_driver, fastest_time))

        return lines_buffer

    # Generate table markdown for all table_names, result is map from table names to table markdown string
    def generate_tables_strings(self):
        tables_strings = {}

        for name in self.race_report.session_names:
            lines_buffer = ["error!"]
            if name.startswith("Qualify"):  # TODO use new sessions lists
                lines_buffer = self.generate_quali_table_strings(name)
            elif name.startswith("Race"):
                lines_buffer = self.generate_race_table_strings(name)
            tables_strings[name] = "\n".join(lines_buffer) + "\n\n"

        return tables_strings

    # Write table markdown for all table_names, optionally provide the generated table strings
    def write_generated_tables(self, tables_strings=None):  # TODO rename stuff to 'align' with TableWriter interface
        if not tables_strings:
            tables_strings = self.generate_tables_strings()

        with open(self.output_file, "w+") as fp:
            for name in self.race_report.session_names:
                fp.write(tables_strings[name])
                print("appended table {} to {}".format(name, self.output_file))


if __name__ == "__main__":
    series_directory = "MX5"
    race_directory = "donington"
    table_names = ["Qualify result", "Race 1 result", "Race 2 result"]

    race_report = RaceReport(table_names, series_directory, race_directory, csv_manual_adjustment=0)
    writer = RaceReportWriter(race_report)

    writer.write_generated_tables()
