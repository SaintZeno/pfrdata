## pfrdata scraper ##
Pro-Football-Reference (pfr) table scraping class that allows users to scrape data from http://pro-football-reference.com/ tables.


Discription of PfrData Class:

pfrdata.py holds the `PfrData` class which does the scraping. `PfrData` requires a valid pfr url upon instantiation via the `url_string` parameter. Various methods use this url to scrape data and pull information from the corresponding page.

There are two main methods to use once a `PfrData` object is created:
`list_tables()` -- this method lists the available tables from the inputted url and stores them in the `table_ids` attribute. this method has to be run before you can scrape data from the page.
`scrape_table(table_id, header_row, return_obj)` -- this method scrapes the data from the table corresponding to the provided `table_id` and uses the `header_row` parameter to discern what row the table headers are stored on. Finally, this method will store the result in a dict on the `table_data` attribute and return the result as a pandas DataFrame if the `return_obj` is True.

## see sample main file for example usage ##

