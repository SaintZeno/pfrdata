import requests
import bs4
import pandas as pd
from pfrdata import PfrData



base_url = 'https://www.sports-reference.com'
cfb_url = base_url + '/cfb'
all_schools_page_url = cfb_url + '/schools'
desired_year = 2018



## pull list of schools
pfr = PfrData(all_schools_page_url)
table_names = pfr.list_tables()
df = pfr.scrape_table('schools', header_row=2, return_obj=True)

df.columns = [str(i).lower() for i in df.columns] ## lowercase columns

## filter out bogus rows
df = df[~(df.school.isin(['Overall', 'School', 'overall', 'school']))]

## filter down to schools who go thru `desired_year`
print(df.keys())
ind1 = pd.to_numeric(df['to']) >= desired_year
ind2 = pd.to_numeric(df['from']) <= desired_year

df = df[ind1 & ind2]

## generate list of school links to grab from
schools_page_url = df[['school', 'linkcol']].to_dict(orient='records')

## list of expected table names
tables = ['team', 'passing', 'rushing_and_receiving',
          'defense_and_fumbles', 'returns', 'kicking_and_punting', 'scoring']

tables = ['passing', 'rushing_and_receiving', 'team']
## initiate result object
#res = {i: [] for i in tables}
res = {}

## iterate thru list of schools and store data
for x in schools_page_url:
    print(x['school'])
    pfr = PfrData(base_url + x['linkcol'] + str(desired_year) + '.html')
    table_names = pfr.list_tables()
    ## make sure all expected tables appear
    if not(all([i in table_names for i in tables])):
        print('missing a table for school {0} and url {1} !!'.format(x['school'], x['linkcol']))
        continue
    ## pluck tables and append to res
    table_names = [i for i in table_names if i not in tables]
    #for t_name in table_names:
    for t_name in tables:
        print(t_name)
        subres = pfr.scrape_table(t_name, header_row=2, return_obj=True)
        subres['school'] = x['school']
        subres['pfr_school_link'] = x['linkcol']
        if 'linkcol' in subres.keys():
            subres['pfr_player_link'] = subres['linkcol']
        if t_name not in res.keys():
            res[t_name] = subres
        else:
            res[t_name] = pd.concat([res[t_name], subres], ignore_index=True)


## format each table so the column names are.... good
passing_name_dict = {'cmp': 'passing_cmp', 'att': 'passing_att', 'pct': 'passing_cmp_pct',
                     'yds': 'passing_yards', 'ya': 'ypa', 'aya':'aypa', 'td': 'passing_td',
                     'rate': 'passer_rating'}

passing_name_dict = {unicode(k): v for k, v in passing_name_dict.items()}


r_n_r_name_dict = {'att': 'rush_att', 'yds': 'rush_yards', 'avg': 'rush_ypc',
                   'td': 'rush_td', 'yds_1': 'rec_yards', 'avg_1': 'rec_ypc',
                   'td_1': 'rec_td', 'plays': 'number_of_plays',
                   'yds_2': 'total_yards', 'avg_2': 'total_ypt', 'td_2': 'total_td'}

r_n_r_name_dict = {unicode(k): v for k, v in r_n_r_name_dict.items()}

team_name_dict = { 'cmp': 'passing_cmp', 'att': 'passing_att',
                   'pct': 'passing_cmp_pct', 'yds': 'passing_yards',
                   'td': 'passing_td', 'att_1': 'rush_att',
                   'yds_1': 'rush_yards', 'avg': 'rush_ypc',
                   'td_1': 'rush_td', 'plays': 'total_plays',
                   'yds_2': 'total_yards', 'avg_1': 'total_ypc',
                   'pass': 'first_down_pass', 'rush': 'first_down_rush',
                   'pen': 'first_down_by_penalty', 'tot': 'total_first_downs',
                   'no': 'no_penalties', 'yds_3': 'penalty_yards',
                   'fum': 'fum_lost', 'tot_1': 'total_turnovers'}


rename_dict = {'rushing_and_receiving': r_n_r_name_dict,
               'passing': passing_name_dict,
               'team': team_name_dict}

for k,v in res.items():
    print(k)
    if k in rename_dict.keys():
        res[k].rename(rename_dict[k], inplace=True, axis='columns')
    if 'year' in res[k].keys():
        res[k].year = [i.replace('*', '').replace('.0', '') for i in res[k].year.astype(str)]
    res[k]['pos'] = 'NA'
    res[k]['games'] = 0
    res[k]['class'] = 'NA'
    player_links = []
    if 'pfr_player_link' in res[k].keys():
        player_links = res[k].pfr_player_link.unique()
    for p in [i for i in player_links if i]:
        print(p)
        pfr = PfrData(base_url + p)
        table_names = pfr.list_tables()
        subres = pfr.scrape_table(table_names[0], header_row=2, return_obj=True)
        subres.year = [i.replace('*', '').replace('.0', '') for i in subres.year.astype(str)]
        pos = subres.pos[subres.year.astype(str) == str(desired_year)].tolist()
        pos = ', '.join(pos)
        res[k].loc[res[k].pfr_player_link == p, 'pos'] = pos
        games = subres.g[subres.year.astype(str) == str(desired_year)].tolist()
        res[k].loc[res[k].pfr_player_link == p, 'games'] = games[0]
        p_class = subres.loc[subres.year.astype(str) == str(desired_year), 'class'].tolist()
        res[k].loc[res[k].pfr_player_link == p, 'class'] = p_class[0]

for k, v in res.items():
    fs = '_'.join(['pfr', 'cfb', k, str(desired_year)])
    v.to_csv(fs + '.csv', index=False)
