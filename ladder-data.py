import requests
import json
import csv
import asyncio
import aiohttp
import async_timeout
from secret import *

__author__ = "Luke Holroyd/ZephyrBlu"
__status__ = "Development"


class Player:
    def __init__(self, account_id, name, race, mmr, league, wins, losses, ties, games_played, realm, region):
        self.account_id = account_id
        self.name = name
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
    def __init__(self, display_name, primary_race, primary_race_wins, career_games):
        self.display_name = display_name
        self.primary_race = primary_race
        self.primary_race_wins = primary_race_wins
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
        async with async_timeout.timeout(10):
            async with session.get(url) as response:
                return await response.json()


    # gathers ladder ids which are required to access player data
    async def _get_id_list(self, session, league):
        print(self.leagues[league])

        print(f"https://{self.region}.api.blizzard.com/data/sc2/season/current?{self.access_token}")
        url = f"https://{self.region}.api.blizzard.com/data/sc2/season/current?{self.access_token}"

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
        while response is None:
            try:
                response = await self._fetch(session, url)
            except Exception:
                pass
        return response


    async def get_players(self):
        self._get_token()
        connector = aiohttp.TCPConnector(limit=60)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._get_id_list(session, league_id) for league_id in range(self.min_league, self.max_league)]
            for task in asyncio.as_completed(tasks):
                await task

            tasks = [self._get_player_data(session, ladder_id) for ladder_id in self.id_list]
            for task in asyncio.as_completed(tasks):
                ladder_data = await task

                # tasks = [self._get_profile(session, player) for player in ladder_data['team']]
                # for task in asyncio.as_completed(tasks):
                #     await task
                
                for player in ladder_data['team']:
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
                    except KeyError as error:
                        print(f"There was a KeyError: {error}")
                        self.errors += 1
                        continue
            self.players.sort(reverse=True, key=lambda x: x.mmr)


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


    async def _get_profile(self, session, player):
        print(f"https://{self.region}.api.blizzard.com/sc2/legacy/profile/{self.region_ids[self.region]}/{player['member'][0]['legacy_link']['realm']}/{player['member'][0]['legacy_link']['id']}?{self.access_token}") 
        url = f"https://{self.region}.api.blizzard.com/sc2/legacy/profile/{self.region_ids[self.region]}/{player['member'][0]['legacy_link']['realm']}/{player['member'][0]['legacy_link']['id']}?{self.access_token}"
       
        response = None
        while response is None:
            try:
                response = await self._fetch(session, url)
            except Exception:
                pass
        profile = response
        try:
            new_profile = Profile(
                player['member'][0]['character_link']['battle_tag'],
                profile['displayName'],
                profile['career']['primaryRace'],
                profile['career']['careerTotalGames']
            )
            self.profiles.append(new_profile)
        except KeyError:
            print("A KeyError occurred")
            self.errors += 1


def write2file(data, filename):
    with open(filename, 'w', encoding='utf-8') as output:
        writer = csv.writer(output, lineterminator='\n')
        writer.writerows(data)


async def main():
    us = Ladder("us", 0, 6)
    print("Doing stuff")
    await us.get_players()
    
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
    # for profile in us.profiles:
    #   varList = []
    #   for key, val in vars(profile).items():
    #       varList.append(val)
    #   if varList != []:
    #       profile_info.append(varList)

    write2file(player_info, "player_info.csv")
    # write2file(profile_info, "profile_info.csv")

    print("Done stuff")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
