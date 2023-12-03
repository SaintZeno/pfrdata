import requests
import bs4
import pandas as pd
from pfrdata import PfrData



base_url = 'https://www.sports-reference.com'
cfb_url = base_url + '/cfb'
all_schools_page_url = cfb_url + '/schools'
desired_year = 2022



## pull list of schools
pfr = PfrData(all_schools_page_url)
table_names = pfr.list_tables()
#print(f'tables on page {all_schools_page_url}: {table_names}')
#print(f'html on page: {pfr.html_text}')
df = pfr.scrape_table('schools', header_row=2, return_obj=True)

df.columns = [str(i).lower() for i in df.columns] ## lowercase columns

## filter out bogus rows
df = df[~(df.school.isin(['Overall', 'School', 'overall', 'school']))]

## filter down to schools who go thru `desired_year`
#print(df.keys())
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
for i in range(len(schools_page_url)):
    x = schools_page_url[i]
    print(f"school {x['school']}")
    ## scrape team history page to get conference and wins/losses
    pfr = PfrData(base_url + x['linkcol'])
    table_names = pfr.list_tables()
    if len(table_names)>1:
        msg = f'unexpected number of tables returned for school {x["school"]}'
        msg += '\n check url: {base_url + x["linkcol"]}'
        raise Exception(msg)
    #print(f"table_names: {table_names}")
    school_stats_df = pfr.scrape_table(table_names[0],
                                     header_row=2,
                                    return_obj=True)
    ## process pd table so we can easily join with other dfs.
    school_stats_df['school'] = str(x['school'])
    school_stats_df.school = school_stats_df.school.astype(str)
    school_stats_df.year  = [i.replace('*', '').replace('.0', '') for i in school_stats_df.year.astype(str)]
    school_stats_df = school_stats_df.loc[school_stats_df.year==str(desired_year)]
    school_stats_df = school_stats_df.loc[:,['school', 'conf', 'w', 'l']]
    school_stats_df.rename({'w':'overall_wins', 'l':'overall_losses', 'conf': 'conference'}, inplace=True, axis='columns')

    ## now we scrape the team yearly stats page with player data
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
        ## ok, pandas is so bad it can't figure out column types?????????

        subres['school'] = str(x['school'])
        subres['school'] = subres['school'].astype(str)

        subres['pfr_school_link'] = x['linkcol']

        ## join subres and school_stats_df
        subres = pd.merge(subres, school_stats_df, how = 'left', on = ['school'])

        if 'linkcol' in subres.keys():
            subres['pfr_player_link'] = subres['linkcol']
        if t_name not in res.keys():
            res[t_name] = subres
        else:
            res[t_name] = pd.concat([res[t_name], subres], ignore_index=True)

    print(f'iteration {i+1} of {len(schools_page_url)} complete. Percent complete: {100*(i+1)/len(schools_page_url):.2f}%')


## format each table so the column names are.... good
passing_name_dict = {'cmp': 'passing_cmp', 'att': 'passing_att', 'pct': 'passing_cmp_pct',
                     'yds': 'passing_yards', 'ya': 'ypa', 'aya':'aypa', 'td': 'passing_td',
                     'rate': 'passer_rating'}

passing_name_dict = {str(k): v for k, v in passing_name_dict.items()}


r_n_r_name_dict = {'att': 'rush_att', 'yds': 'rush_yards', 'avg': 'rush_ypc',
                   'td': 'rush_td', 'yds_1': 'rec_yards', 'avg_1': 'rec_ypc',
                   'td_1': 'rec_td', 'plays': 'number_of_plays',
                   'yds_2': 'total_yards', 'avg_2': 'total_ypt', 'td_2': 'total_td'}

r_n_r_name_dict = {str(k): v for k, v in r_n_r_name_dict.items()}

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


## now we loop thru each table type and grab the player class info
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
    player_links = [i for i in player_links if i]
    for i in range(len(player_links)):
        p = player_links[i]
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
        print(f'iteration {i+1} of {len(player_links)} complete for {k}. Percent complete: {100*(i+1)/len(player_links):.2f}% for {k}')


## write to disk!!
for k, v in res.items():
    fs = '_'.join(['pfr', 'cfb', k, str(desired_year)])
    v.to_csv(fs + '.csv', index=False)
