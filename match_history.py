import csv
import requests
import asyncio
import aiohttp
import async_timeout
import time
import copy
import json
from secret import *


class Player:
    def __init__(self, account_id, battletag, realm):
        self.account_id = account_id
        self.battletag = battletag
        self.ranked = []
        self.realm = realm
        self.region = 'us'
        self.games = []

    def __eq__(self, other):
        return self.account_id == other.account_id

    def __hash__(self):
        return hash(self.account_id)

    def __str__(self):
        return self.battletag

    def __repr__(self):
        return self.battletag 


class Ranked:
    def __init__(self, race, mmr, league):
        self.race = race
        self.mmr = mmr
        self.league = league

    def __eq__(self, other):
        return self.race == other.race

    def __repr__(self):
        return self.race

    def __str__(self):
        return self.race


def write2file(data, filename):
    with open(filename, 'w', encoding='utf-8') as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(data)


def get_token():
    #Unique keys given to your dev account
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    #OAuth token allows access to the API
    oauth = requests.get(f"https://us.battle.net/oauth/token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}")
    if oauth.status_code != 200:
        raise Exception(f"The token request failed due to: {oauth.text}")
    else:
        access_token = f"access_token={oauth.json()['access_token']}"
    return access_token


def parse_matches(player, matches, match_list):
    for match in matches:
        if match['type'] == '1v1':
            game_map = match['map']
            result = match['decision']

            if match['date'] in match_list:
                match_list[match['date']].append({
                    'player': player,
                    'map': game_map,
                    'result': result
                })
            else:
                match_list[match['date']] = [{
                    'player': player,
                    'map': game_map,
                    'result': result
                }]
    return match_list


async def fetch(session, player, access_token):
    url = f"https://us.api.blizzard.com/sc2/legacy/profile/1/{player.realm}/{player.account_id}/matches?{access_token}"
    async with async_timeout.timeout(100):
        # print(f"https://us.api.blizzard.com/sc2/legacy/profile/1/{player.realm}/{player.account_id}/matches?{access_token}")
        # print('\n')
        try:
            async with session.get(url) as response:
                return await response.json()
        except Exception as error:
            # print(error)
            return


async def players(player_info, access_token):
    tasks = []
    players = []
    all_responses = []
    connector = aiohttp.TCPConnector(limit=64)
    async with aiohttp.ClientSession(connector=connector) as session:
        for count, player in enumerate(player_info):
            if count % 5000 == 0:
                responses = await asyncio.gather(*tasks)
                all_responses.extend(responses)
                tasks = []
            task = asyncio.ensure_future(fetch(session, player, access_token))
            tasks.append(task)
            players.append(player)

        responses = await asyncio.gather(*tasks)
        all_responses = all_responses+responses
        return list(zip(players, all_responses))
            

async def main():
    player_set = set()
    set_add = player_set.add

    with open('data/player_info.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[1]+row[2] not in player_set:
                player = Player(row[0], row[1], row[9])
                ranked_race = Ranked(row[2], row[3], row[4])
                if ranked_race.race not in player.ranked:
                    player.ranked.append(ranked_race)
                set_add(player)
    # print('finished reading file')

    player_info = list(player_set)
                
    access_token = get_token()
    # print('got token')

    match_list = {}
    match_history_list = []
    final_match_history_list = []
    init_count = len(player_info)
    prev_count = 0
    count = 0

    while True:
        match_history_list = await players(player_info, access_token)

        # print('got all matches')

        prev_count = count
        count = 0
        none_matches = []
        for match_history in match_history_list:
            if match_history[1] is None:
                none_matches.append(match_history[0])
                count += 1
            else:
                final_match_history_list.append(match_history)

        # print(f'Players: {len(player_info)}')
        # print(f'Total: {len(match_history_list)}, None: {count}, %: {count/len(match_history_list)*100}%')
        # time.sleep(10)

        if count == 0 or prev_count == count:
            break
        else:
            player_info = none_matches

    # print(f'Match Historys pulled: {len(final_match_history_list)}, Init: {init_count}, % of Total: {len(final_match_history_list)/init_count*100}%')

    for matches in final_match_history_list:
        match_list = parse_matches(matches[0], matches[1]['matches'], match_list)

    # print(len(match_list))

    date_len = []

    for date, games in match_list.items():
        date_len.append(len(games))
        games.sort(key=lambda x: x['player'].account_id)
        raw_games = games
        for r_game in raw_games:
            del games[0]
            for index, game in enumerate(games):
                if game['map'] == r_game['map'] and game['result'] != r_game['result']:
                    r_game.update({
                        'date': date,
                        'opponent': game['player']
                    })
                    r_game['player'].games.append(r_game)

                    game.update({
                        'date': date,
                        'opponent': r_game['player']
                    })
                    game['player'].games.append(game)

                    del games[index]
                    break

    # print(f'Avg Date Cluster Size: {sum(date_len)/len(date_len)}')
    template = {
        'Grandmaster': (0, 0),
        'Master': (0, 0),
        'Diamond': (0, 0),
        'Platinum': (0, 0),
        'Gold': (0, 0),
        'Silver': (0, 0),
        'Bronze': (0, 0)
    }

    races = ['Protoss', 'Terran', 'Zerg', 'Random']
    win_played = {}

    for race in races:
        for race2 in races:
            mu = f'{race[0]}v{race2[0]}'
            win_played[mu] = copy.deepcopy(template)

    matches = []
    matches_seen = set()
    match_add = matches_seen.add
    player_info = list(player_set)
    for player in player_info:
        for game in player.games:
            mmr_diff = 9999
            matchup = []

            for race in player.ranked:
                for opp_race in game['opponent'].ranked:
                    current_diff = abs(int(race.mmr) - int(opp_race.mmr))
                    if current_diff < mmr_diff:
                        mmr_diff = current_diff
                        matchup = [race.race, opp_race.race]
                        p1 = race
                        p2 = opp_race
            
            matchup_sort = f'{sorted(matchup)[0][0]}v{sorted(matchup)[1][0]}'
            matchup = f'{matchup[0][0]}v{matchup[1][0]}'

            # print(matchup)
            # print(game)
            # print('\n')

            player1 = {
                'battletag': player.battletag,
                'account_id': int(player.account_id),
                'race': p1.race,
                'league': p1.league,
                'mmr': int(p1.mmr),
                'realm': int(player.realm),
            }

            player2 = {
                'battletag': game['opponent'].battletag,
                'account_id': int(game['opponent'].account_id),
                'race': p2.race,
                'league': p2.league,
                'mmr': int(p2.mmr),
                'realm': int(game['opponent'].realm),
            }

            result = None

            
            if game['result'] == 'Win':
                result = 1
                if race.league == opp_race.league:
                    win_played[matchup][race.league] = (
                        win_played[matchup][race.league][0]+1,
                        win_played[matchup][race.league][1]+1
                    )
            else:
                result = 2
                if race.league == opp_race.league:
                    win_played[matchup][race.league] = (
                        win_played[matchup][race.league][0],
                        win_played[matchup][race.league][1]+1
                    )

            match = [
                game['date'],
                matchup_sort,
                game['map'],
                json.dumps(player1),
                json.dumps(player2),
                result,
                player.region
            ]

            if (match[0], match[1], match[2]) not in matches_seen:
                matches.append(match)
                match_add((match[0], match[1], match[2]))

    # for mu, league in win_played.items():
    #     print(f'{mu}:')
    #     for l, v in league.items():
    #         if v[1] != 0:
    #             print(f'  {l}: {round(v[0]/v[1]*100, 1)}% ({v[0]}/{v[1]})')
    #     print('')

    write2file(matches, 'data/matches.csv')

    # for player in player_info:
    #     for game in player.games:
    #         print(game)
    #     print('\n')

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
