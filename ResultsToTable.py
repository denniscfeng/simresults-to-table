import argparse

from Championship import Championship
from DriversStandingsWriter import DriversStandingsWriter
from ParticipationTableWriter import ParticipationTableWriter
from RaceReportWriter import RaceReportWriter
from SummaryTableWriter import SummaryTableWriter
from TeamsStandingsWriter import TeamsStandingsWriter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read Simresults exported `.csv`s, calculate drivers' and teams' championship standings, and generate XWiki markdown text for championship standings tables and race reports. Please see README.md for complete usage.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    required_args = parser.add_argument_group(title="Required Arguments")
    required_args.add_argument("--series", required=True, type=str,
                               help='Name of directory containing series data. (e.x. "simresults/MX5")')
    required_args.add_argument("--sessions", required=True, nargs="+",
                               help='List of names of session tables in results CSVs from this series. Space separate with double quotes. (e.x. "Qualify result" "Race 1 result" "Race 2 result")')
    required_args.add_argument("--rounds-to-include", required=True, type=int,
                               help="Number of series rounds that should be considered in points calculations. (i.e. perform points calculations after 'n' rounds in the series)")

    optional_args = parser.add_argument_group(title="Optional Arguments")
    optional_args.add_argument("--drop-week", action="store_true",
                               help="Whether this series has a drop week that needs to factor into points calculations.")
    optional_args.add_argument("--num-scoring-drivers-in-team", type=int, default=2,
                               help="How many driver contribute to the team score per round. (i.e. the top 'n' drivers' scores from every round will be added to the team total)")
    optional_args.add_argument("--write-race-reports", action="store_true",
                               help="Also write race report tables for each round in addition to series standings tables.")
    optional_args.add_argument("--debug-csv-parse", action="store_true",
                               help="Print out the lines in the Simresults CSVs that are being read into dataframes. Use for debugging CSV manual adjustments.")

    return parser.parse_args()


def run(args):
    championship = Championship(args.series, args.sessions, args.rounds_to_include, args.drop_week,
                                args.num_scoring_drivers_in_team, args.debug_csv_parse)
    driver_standings_writer = DriversStandingsWriter(championship)
    driver_standings_writer.write_lines()

    teams_standings_writer = TeamsStandingsWriter(championship)
    teams_standings_writer.write_lines()

    summary_table_writer = SummaryTableWriter(championship)
    summary_table_writer.write_lines()

    participation_table_writer = ParticipationTableWriter(championship)
    participation_table_writer.write_lines()

    if args.write_race_reports:
        for race in championship.series_tracks_table.index:
            if race in championship.race_reports:
                race_report_writer = RaceReportWriter(championship.race_reports[race])
                race_report_writer.write_generated_tables()


if __name__ == '__main__':
    run(parse_args())
