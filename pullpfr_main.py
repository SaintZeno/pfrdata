from pfrdata import PfrData


url = "https://www.pro-football-reference.com/teams/nwe/2017.htm"


## instantiate pfr object
pfr = PfrData(url)

## Listing tables on url
pfr.list_tables()

## Pull 'defense' table from url into a dataframe `defense_df`
defense_df = pfr.scrape_table('defense', header_row=2, return_obj=True)

pass_df = pfr.scrape_table('passing', header_row=1, return_obj=True)
