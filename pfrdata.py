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
        self.table_data = {}


    def set_html(self):
        """
        Method that pulls html string and replaces <!-- or --> string with ''
        (this substitution is turning off the comments that
        are blocking things we need to pull)
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




    def check_scrape_table_args(self, table_id, header_row, return_obj):
        """
        Method that ensures table_id is a string value and is in self.table_ids
        ensures header_row is int
        ensures return_bj is bool
        note: there's probably a better way to do this?
        not familiar w/ robust error handeling
        :param table_id: object to check
        :param header_row: object to check
        :param return_obj: object to check
        :return: None
        """

        if self.table_ids is None:
            raise Exception('Please run `PullPfrData.list_tables()` before you run this method')

        if table_id not in self.table_ids:
            msg = 'Table id `{}` is not an available table.'.format(table_id)
            msg += ' Run `PullPfrData.list_tables()` to see list of tables.'
            raise Exception(msg)

        if type(table_id) != str:
            raise Exception('Please input a string for the Table ID (table_id)')

        if type(header_row) != int:
            raise Exception('Please input an int for the header row (header_row)')

        if type(return_obj) != bool:
            raise Exception('Please input a boolean for the return (object return_obj)')
        pass





    def scrape_table(self, table_id, header_row=2, return_obj = False):
        """
        Method that scrapes a table that's obtained by self.list_tables().
        Must run self.list_tables before running this method else error.
        :param table_id: str of valid tables to pull
        :param header_row: int of row # to pick headers from; typically row 2 or 1 for pfr
        :param return_obj: boolean for returning the data frame object that's scraped
        :return: dataframe if return_obj else None
        """
        self.check_scrape_table_args(table_id, header_row, return_obj)
        soup = bs4.BeautifulSoup(self.html_text, 'lxml')
        soup_table = soup.findAll('table', id=table_id)[0]  ## should be 1 table
        soup_rows = soup_table.findAll('tr')
        res = []
        for i in soup_rows:
            res.append([x.getText() for x in i.findAll(['th', 'td'])])
        res = pd.DataFrame(res)
        for c in res.keys():
            res[c] = pd.to_numeric(res[c], errors = 'ignore')
        cols = res.loc[header_row - 1].tolist()
        cols = self.slug_str_list(cols, include_space=False)
        ## hacky way to count duplicate columns and then append occurence # to the string
        ## there's def a better way to do this w/ lists and arrays...
        t = pd.DataFrame([], columns = cols)
        cols = pd.Series(t.columns)
        for d in t.columns.get_duplicates():
            cols[t.columns.get_loc(d)] = [
                d + '_' + str(d_idx) if d_idx != 0 else d for d_idx in range(t.columns.get_loc(d).sum())
                ]
        res.drop([i for i in range(header_row)], inplace=True)
        res.columns = cols
        if 'player' in res.columns:
            res['player'] = self.slug_str_list(res['player'].tolist(),
                                               include_space=True)
        self.table_data = {table_id: res}
        if not return_obj:
            res = None
        return (res)


    def slug_str_list(self, cols, include_space = True, do_slug = True):
        """
        Method that converts list of string to alphanumeric and spaces
        :param cols: list of strings
        :param include_space: bool to include spaces in sting or not
        :param do_slug: bool to actually do the slug
        :return: slugged string list
        """
        res = []
        for c in cols:
            if do_slug:
                if include_space:
                    try:
                        c = "".join(s for s in c if (s.isalnum() or s == ' ')).lower()
                    except:
                        print('Couldnt convert string')
                else:
                    try:
                        c = "".join(s for s in c if s.isalnum()).lower()
                    except:
                        print('Couldnt conver string')
            res.append(c.lower())
        return (res)



