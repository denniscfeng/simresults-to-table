from Championship import Championship
from DriversStandingsWriter import DriverStandingsWriter
from ParticipationTableWriter import ParticipationTableWriter
from SummaryTableWriter import SummaryTableWriter
from TeamsStandingsWriter import TeamsStandingsWriter


def run():
    series = "MX5"
    series_sessions = ["Qualify result", "Race 1 result", "Race 2 result"]
    rounds_to_include = 5

    championship = Championship(series, series_sessions, rounds_to_include)

    driver_standings_writer = DriverStandingsWriter(championship)
    driver_standings_writer.write_lines()

    teams_standings_writer = TeamsStandingsWriter(championship)
    teams_standings_writer.write_lines()

    summary_table_writer = SummaryTableWriter(championship)
    summary_table_writer.write_lines()

    participation_table_writer = ParticipationTableWriter(championship)
    participation_table_writer.write_lines()


if __name__ == '__main__':
    run()
