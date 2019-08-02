import requests
import json
import csv
import time
import asyncio
import aiohttp
import async_timeout
from secret import *

__author__ = "Luke Holroyd/ZephyrBlu"
__status__ = "Development"


class Player:
    def __init__(self, account_id, battletag, race, mmr, league, wins, losses, ties, games_played, realm, region):
        self.account_id = account_id
        self.battletag = battletag
        self.race = race
        self.mmr = mmr
        self.league = league
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.games_played = games_played
        self.realm = realm
        self.region = region


class Profile: 
    def __init__(self, account_id, battletag, display_name, primary_race, mmr, career_games):
        self.account_id = account_id
        self.battletag = battletag
        self.display_name = display_name
        self.primary_race = primary_race
        self.mmr = mmr
        self.career_games = career_games


class Ladder:
    def __init__(self, region, min_league, max_league=None):
        self.region = region
        self.min_league = min_league
        if max_league is None:
            self.max_league = min_league+1
        else:
            self.max_league = max_league+1
        self.players = [] 
        self.profiles = []
        self.id_list = []
        self.access_token = None
        self.errors = 0
        self.leagues = {
            0: "Bronze",
            1: "Silver",
            2: "Gold",
            3: "Platinum",
            4: "Diamond",
            5: "Master",
            6: "Grandmaster"
        }
        self.region_ids = {
            'us': 1,
            'eu': 2,
            'ko': 3,
            'tw': 3,
            'cn': 5
        }

    async def _fetch(self, session, url):
        async with async_timeout.timeout(100):
            try:
                async with session.get(url) as response:
                    return await response.json()
            except Exception as error:
                print(error)
                return


    # gathers ladder ids which are required to access player data
    async def _get_id_list(self, session, league, season):
        print(f"https://{self.region}.api.blizzard.com/data/sc2/season/current?{self.access_token}")
        url = f"https://{self.region}.api.blizzard.com/data/sc2/season/{season}?{self.access_token}"

        response = None
        while response is None:
            try:
                response = await self._fetch(session, url)
            except Exception:
                pass
        current_season = response['id']
            
        print(f"https://{self.region}.api.blizzard.com/data/sc2/league/{current_season}/201/0/{str(league)}?{self.access_token}")
        url = f"https://{self.region}.api.blizzard.com/data/sc2/league/{current_season}/201/0/{str(league)}?{self.access_token}"
        
        response = None
        while response is None:
            try:
                response = await self._fetch(session, url)
            except Exception:
                pass

        ladder_data = response
        for section in ladder_data['tier']:
            for ladder in section['division']:
                self.id_list.append(ladder['ladder_id'])
        return


    async def _get_player_data(self, session, ladder_id):
        print(f"https://{self.region}.api.blizzard.com/data/sc2/ladder/{str(ladder_id)}?{self.access_token}")
        url = f"https://{self.region}.api.blizzard.com/data/sc2/ladder/{str(ladder_id)}?{self.access_token}"
        
        response = None
        while response is None or 'code' in response:
            try:
                response = await self._fetch(session, url)
                if 'code' in response:
                    print('\n')
                    print(f'404 ERROR URL: {url}')
                    print('\n')
            except Exception:
                pass
        return response


    async def get_players(self, *, profiles=False, season='current'):
        self._get_token()

        player_set = set()
        set_add = player_set.add
        all_players = []

        connector = aiohttp.TCPConnector(limit=64)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._get_id_list(session, league_id, season) for league_id in range(self.min_league, self.max_league)]
            for task in asyncio.as_completed(tasks):
                print('got ladder id list')
                await task

            tasks = [self._get_player_data(session, ladder_id) for ladder_id in self.id_list]
            for task in asyncio.as_completed(tasks):
                print('got player data')
                ladder_data = await task

                print('adding players')
                if 'team' not in ladder_data.keys():
                    print(ladder_data)
                for count, player in enumerate(ladder_data['team']):
                    try:
                        new_player = Player(
                            player['member'][0]['legacy_link']['id'],
                            player['member'][0]['character_link']['battle_tag'],
                            player['member'][0]['played_race_count'][0]['race']['en_US'],
                            player['rating'],
                            self.leagues[ladder_data['league']['league_key']['league_id']],
                            player['wins'],
                            player['losses'],
                            player['ties'],
                            player['wins']+player['losses']+player['ties'],
                            player['member'][0]['legacy_link']['realm'],
                            self.region
                        )
                        self.players.append(new_player)

                        if profiles:
                            if player['member'][0]['legacy_link']['id'] not in player_set:
                                all_players.append(new_player)
                                set_add(player['member'][0]['legacy_link']['id'])
                    except KeyError as error:
                        print(f"There was a KeyError: {error}")
                        self.errors += 1
                        continue
            self.players.sort(reverse=True, key=lambda x: x.mmr)

            if profiles:
                await self._get_profiles(session, all_players)


    #This function is vital to connecting to the API. Getting an OAuth token allows unrestricted access
    def _get_token(self):
        #Unique keys given to your dev account
        client_id = CLIENT_ID
        client_secret = CLIENT_SECRET

        #OAuth token allows access to the API
        oauth = requests.get(f"https://{self.region}.battle.net/oauth/token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}")
        if oauth.status_code != 200:
            raise Exception(f"The token request failed due to: {oauth.text}")
        else:
            self.access_token = f"access_token={oauth.json()['access_token']}"


    async def _get_profiles(self, session, player_list):
        tasks = []
        profile_list = []
        count = 0
        async with session:
            while True:
                players = []
                all_responses = []
                print('fetching player profiles')
                for index, player in enumerate(player_list):
                    if index % 1000 == 0:
                        print(f'completed {index} requests')
                        responses = await asyncio.gather(*tasks)
                        all_responses.extend(responses)
                        tasks = []
                    url = f"https://{self.region}.api.blizzard.com/sc2/legacy/profile/{self.region_ids[self.region]}/{player.realm}/{player.account_id}?{self.access_token}"
                    task = asyncio.ensure_future(self._fetch(session, url))
                    tasks.append(task)
                    players.append(player)

                print('sent all requests')
                responses = await asyncio.gather(*tasks)
                all_responses.extend(responses)
                all_responses = list(zip(players, all_responses))

                prev_count = count
                count = 0
                none_responses = []
                for response in all_responses:
                    if response[1] is None:
                        none_responses.append(response[0])
                        count += 1
                    else:
                        profile_list.append(response)

                print(f'Profiles: {len(profile_list)}')
                print(f'Total: {len(player_list)}, None: {count}, %: {count/len(player_list)*100}%')
                time.sleep(10)

                if count == 0 or prev_count == count:
                    break
                else:
                    player_list = none_responses
        self._parse_profiles(profile_list)


    def _parse_profiles(self, profile_list):
        print('parsing profiles')
        for data in profile_list:
            # print(data)
            player = data[0]
            profile = data[1]
            try:
                new_profile = Profile(
                    player.account_id,
                    player.battletag,
                    profile['displayName'],
                    profile['career']['primaryRace'],
                    player.mmr,
                    profile['career']['careerTotalGames']
                )
                self.profiles.append(new_profile)
                player.name = new_profile.display_name
                player.main_race = new_profile.primary_race
                player.career_games = new_profile.career_games
            except KeyError:
                print("A KeyError occurred")
                self.errors += 1
        self.profiles.sort(reverse=True, key=lambda x: x.mmr)


def write2file(data, filename):
    with open(filename, 'w', encoding='utf-8') as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(data)


async def main():
    us = Ladder("us", 0, 6)
    # print("Doing stuff")
    await us.get_players(profiles=False, season='current')
    
    mmr = []
    protoss = []
    terran = []
    zerg = []
    random = []

    player_info = []
    for player in us.players:
        varList = []
        for key, val in vars(player).items():
            varList.append(val)
        if varList != []:
            player_info.append(varList)

    # profile_info = []
    # for profile in sea_profiles:
    #   varList = []
    #   for key, val in vars(profile).items():
    #       varList.append(val)
    #   if varList != []:
    #       profile_info.append(varList)

    write2file(player_info, "data/player_info.csv")
    # write2file(profile_info, "data/profile_info.csv")

    # print("Done stuff")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
