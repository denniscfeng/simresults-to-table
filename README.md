SimResults To Table
===================================

Read Simresults exported `.csv`s, calculate drivers' and teams' championship standings, and generate XWiki markdown text for championship standings tables and race reports. For use on [Phoenix Racing Club Wiki](https://xwiki.phoenix-racing-club.org/).

## Install
1. Download/clone repository
2. Install Python
3. In powershell/cmd/terminal:
    1. Navigate to repository
    2. `pip install -r requirements.txt`
    
## Usage
```
$ python ResultsToTable.py --help
usage: ResultsToTable.py [-h] --series SERIES --sessions SESSIONS [SESSIONS ...] --rounds-to-include ROUNDS_TO_INCLUDE [--drop-week]
                         [--num-scoring-drivers-in-team NUM_SCORING_DRIVERS_IN_TEAM] [--write-race-reports] [--debug-csv-parse]

Read Simresults exported `.csv`s, calculate drivers' and teams' championship standings, and generate XWiki markdown text for championship standings
tables and race reports. Please see README.md for complete usage.

optional arguments:
  -h, --help            show this help message and exit

Required Arguments:
  --series SERIES       Name of directory containing series data. (e.x. "simresults/MX5") (default: None)
  --sessions SESSIONS [SESSIONS ...]
                        List of names of session tables in results CSVs from this series. Space separate with double quotes. (e.x. "Qualify result" "Race
                        1 result" "Race 2 result") (default: None)
  --rounds-to-include ROUNDS_TO_INCLUDE
                        Number of series rounds that should be considered in points calculations. (i.e. perform points calculations after 'n' rounds in
                        the series) (default: None)

Optional Arguments:
  --drop-week           Whether this series has a drop week that needs to factor into points calculations. (default: False)
  --num-scoring-drivers-in-team NUM_SCORING_DRIVERS_IN_TEAM
                        How many driver contribute to the team score per round. (i.e. the top 'n' drivers' scores from every round will be added to the
                        team total) (default: 2)
  --write-race-reports  Also write race report tables for each round in addition to series standings tables. (default: False)
  --debug-csv-parse     Print out the lines in the Simresults CSVs that are being read into dataframes. Use for debugging CSV manual adjustments.
                        (default: False)

```

