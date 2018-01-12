## Author: Zeno Muscarella
## version 0.1 1/12/2018

import requests
import bs4
import pandas as pd
## may need to pip install lxml



class PfrData():
    """
    Class that will pull pro-football focus data using any given url
    example usage:
    pfr = PullPfrData(url_string = url)
    pfr.list_tables()
    hold = pfr.scrape_table('defense', 2) ## df of table data
    """

    def __init__(self, url_string):
        self.url = url_string
        self.set_html()
        self.table_ids = None

    def set_html(self):
        """
        Method that pulls html string and replaces <!-- or --> string with ''
        (this substitution is turning off the comments that
        are blocking tables to load nicely)
        """
        html_text = requests.get(self.url).text
        self.html_text = html_text.replace('<!--', '').replace('-->', '')
        # print(self.html_text)

    def list_tables(self):
        """
        Method that will list all tables in a given pfr url
        """
        soup = bs4.BeautifulSoup(self.html_text, 'lxml')
        tab_w_id = soup.findAll('table', {'id': True})
        self.table_ids = [i['id'] for i in tab_w_id]
        return (self.table_ids)

    def scrape_table(self, table_id, header_row=2):
        """
        Method that scrapes a table that's obtained by self.list_tables().
        Must run self.list_tables before running this method else error.
        Must input valid table_id
        table_id:: str of valid tables to pull
        header_row:: int of row # to pick headers from; typically row 2 for pfr
        """
        if self.table_ids is None:
            raise Exception('Please run `PullPfrData.list_tables()` before you run this method')
        if table_id not in self.table_ids:
            msg = 'Table id `{}` is not an available table.'.format(table_id)
            msg += ' Run `PullPfrData.list_tables()` to see list of tables.'
            raise Exception(msg)
        soup = bs4.BeautifulSoup(self.html_text, 'lxml')
        soup_table = soup.findAll('table', id=table_id)[0]  ## should be 1 table
        soup_rows = soup_table.findAll('tr')
        data = []
        for i in soup_rows:
            data.append([x.getText() for x in i.findAll(['th', 'td'])])
        data = pd.DataFrame(data)
        cols = data.loc[header_row - 1].tolist()
        cols = self.slug_cols(cols)
        data.drop([i for i in range(header_row)], inplace=True)
        data.columns = cols
        return (data)

    def slug_cols(self, cols):
        """
        Method that replaces strings with ''
        there's probably a better way to do this...
        cols:: list of strings to replace
        """
        res = []
        ## feel free to append stuff to this list
        ## or update the code to replace txt w/
        ## stuff other than '' (ie maybe I want '.' -> '_' )
        to_replace = ['\xa0', '.']
        for c in cols:
            for i in to_replace:
                c = c.replace(i, '')
            res.append(c)
        return (res)



