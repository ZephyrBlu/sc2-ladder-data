import csv
import math
import json
import numpy as np
from offrace import main as get_offrace
from mmr import main as get_mmr_dist
from activity import main as get_activity
from matchup_analysis import main as get_winrate


def write2file(data, filename):
    with open(filename, 'w', encoding='utf-8') as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(data)


raw_player_info = []
player_info = {}

with open('../data/test/player_info.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    # next(reader)
    for row in reader:
        raw_player_info.append(tuple(row))

for player in raw_player_info:
    if player[1] not in player_info:
        player_info[player[1]] = {
            player[2]: {
                'mmr': player[3],
                'league': player[4],
                'wins': player[5],
                'losses': player[6],
                'ties': player[7],
                'region': player[9]
            }   
        }

    elif player[2] not in player_info[player[1]]:
        player_info[player[1]].update({
            player[2]: {
                'mmr': player[3],
                'league': player[4],
                'wins': player[5],
                'losses': player[6],
                'ties': player[7],
                'region': player[9]
            }   
        })

raw_num_players = len(player_info.keys())

# print(player_info['SpeCial#11949'])

for player, races in player_info.items():
    active = False
    inactive = 0
    max_mmr = 0
    player_main_race = None

    for race, info in races.items():
        if int(info['mmr']) > max_mmr:
            max_mmr = int(info['mmr'])
            player_main_race = race.lower()
        else:
            inactive += 1

    for race, info in races.items():
        if race.lower() == player_main_race:
            player_info[player][player_main_race.capitalize()].update({
                'main_race': True
            })
        else:
            player_info[player][race].update({
                'main_race': False
            })
            
player_list = []
mmr_list = []
player_dist = {
    'all': [],
    'grandmaster': [],
    'master': [],
    'diamond': [],
    'platinum': [],
    'gold': [],
    'silver': [],
    'bronze': []
}

races = ['all', 'protoss', 'terran', 'zerg', 'random']
race_count = {
    'all': {},
    'grandmaster': {},
    'master': {},
    'diamond': {},
    'platinum': {},
    'gold': {},
    'silver': {},
    'bronze': {}
}

for league, r in race_count.items():
    for race in races:
        r[race] = 0

count = 0
for player, races in player_info.items():
    for race, info in races.items():
        count += 1
        
        # if int(info['wins'])+int(info['losses']) >= 30:
        info.update({
            'race': race,
            'battletag': player
        })

        if info['main_race'] is True and len(races) > 1:
            race_count['all']['all'] += 1
            race_count['all'][race.lower()] += 1
            race_count[info['league'].lower()][race.lower()] += 1
            race_count[info['league'].lower()]['all'] += 1

            player_dist[info['league'].lower()].append(info)
            player_dist['all'].append(info)

        del info['ties']
        del info['region']
        player_list.append(info)

# print(player_info['SpeCial#11949'])

player_list.sort(key=lambda x: int(x['mmr']))

# print(games_played_dist)

pie_offrace, radar_offrace = get_offrace(player_info)
mmr = get_mmr_dist(player_dist, race_count)
activity = get_activity()
winrates = get_winrate()

all_data = {
    'mmr': mmr,
    'activity': activity,
    'offrace': {
        'pie': pie_offrace,
        'radar': radar_offrace
    },
    'winrate': winrates
}

with open('JSON/data.json', 'w', encoding='utf-8') as output:
        json.dump(all_data, output)
