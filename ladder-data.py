import requests; import json; import csv

__author__ = "Luke Holroyd/ZephyrBlu"
__status__ = "Development"


class Player:
	def __init__(self, name, race, mmr, league, wins, losses, ties, games_played, region):
		self.name = name
		self.race = race
		self.mmr = mmr
		self.league = league
		self.wins = wins
		self.losses = losses
		self.ties = ties
		self.games_played = games_played
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
			5: "Masters",
			6: "Grandmaster"
		}
		self.region_ids = {
			'us': 1,
			'eu': 2,
			'ko': 3,
			'tw': 3,
			'cn': 5
		}


	# gathers ladder ids which are required to access player data
	def _get_id_list(self, league):
		print(f"https://{self.region}.api.blizzard.com/data/sc2/season/current?{self.access_token}")

		# replace '40' with the season you want to collect data from
		season_data = requests.get(f"https://{self.region}.api.blizzard.com/data/sc2/season/40?{self.access_token}")

		# retry the API 3 times before moving on if there is an error
		for i in range(0, 4):
			if season_data.status_code != 200:
				print(f"The ladder ID request failed due to: {season_data.text}")
				season_data = requests.get(f"https://{self.region}.api.blizzard.com/data/sc2/season/40?{self.access_token}")
			else:
				break
		print("Finished trying\n")

		try:
			current_season = season_data.json()['id']
		except ValueError:
			print("JSONDecodeError occurred")
			return

		print(f"https://{self.region}.api.blizzard.com/data/sc2/league/{current_season}/201/0/{str(league)}?{self.access_token}")
		ladder_data = requests.get(f"https://{self.region}.api.blizzard.com/data/sc2/league/{current_season}/201/0/{str(league)}?{self.access_token}")

		for i in range(0, 4):
			if ladder_data.status_code != 200:
				print(f"The ladder data request failed due to: {ladder_data.text}")
				ladder_data = requests.get(f"https://{self.region}.api.blizzard.com/data/sc2/league/{current_season}/201/0/{str(league)}?{self.access_token}")
			else:
				break
		print("Finished trying\n")

		try:
			ladder_dict = ladder_data.json()
		except ValueError:
			print("JSONDecodeError occurred")
			return

		for section in ladder_dict['tier']:
			for ladder in section['division']:
				self.id_list.append(ladder['ladder_id'])


	def get_players(self):
		self._get_token()
		for league_id in range(self.min_league, self.max_league):
			print(self.leagues[league_id])
			self._get_id_list(league_id)

		for ladder_id in self.id_list:
			print(f"https://{self.region}.api.blizzard.com/data/sc2/ladder/{str(ladder_id)}?{self.access_token}")
			player_data = requests.get(f"https://{self.region}.api.blizzard.com/data/sc2/ladder/{str(ladder_id)}?{self.access_token}")

			for i in range(0, 4):
				if player_data.status_code != 200: #200 is good to go code, anything else is some sort of error
					print(f"The player data request failed due to: {player_data.text}")
					player_data = requests.get(f"https://{self.region}.api.blizzard.com/data/sc2/ladder/{str(ladder_id)}?{self.access_token}")
				else:
					break
			print("Finished trying\n")

			try:
				ladder_data = player_data.json()
			except ValueError:
				print("JSONDecoderError occurred")
				continue

			for player in ladder_data['team']:
				try:
					new_player = Player(
						player['member'][0]['character_link']['battle_tag'],
						player['member'][0]['played_race_count'][0]['race']['en_US'],
						player['rating'],
						self.leagues[ladder_data['league']['league_key']['league_id']],
						player['wins'],
						player['losses'],
						player['ties'],
						player['wins']+player['losses']+player['ties'],
						self.region
					)
					self._get_profile(player)
					self.players.append(new_player)
				except KeyError:
					print("There was a KeyError")
					self.errors += 1
					continue
		self.players.sort(reverse=True, key=lambda x: x.mmr)


	#This function is vital to connecting to the API. Getting an OAuth token allows unrestricted access
	def _get_token(self):
		#Unique keys given to your dev account
		client_id = "<INSERT YOUR BATTLENET DEV CLIENT ID HERE>"
		client_secret = "<INSERT YOUR BATTLENET DEV CLIENT SECRET HERE>"

		#OAuth token allows access to the API
		oauth = requests.get(f"https://{self.region}.battle.net/oauth/token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}")
		if oauth.status_code != 200:
			raise Exception(f"The token request failed due to: {oauth.text}")
		else:
			self.access_token = f"access_token={oauth.json()['access_token']}"


	def _get_profile(self, player):
		print(player)
		print(f"https://{self.region}.api.blizzard.com/sc2/legacy/profile/{self.region_ids[self.region]}/{player['member'][0]['legacy_link']['realm']}/{player['member'][0]['legacy_link']['id']}?{self.access_token}")	
		profile_data = requests.get(f"https://{self.region}.api.blizzard.com/sc2/legacy/profile/{self.region_ids[self.region]}/{player['member'][0]['legacy_link']['realm']}/{player['member'][0]['legacy_link']['id']}?{self.access_token}")

		# retry profile API 3 times
		for i in range(0, 4):
			if profile_data.status_code != 200:
				print(f"The profile request failed due to: {profile_data.text}\n")
				profile_data = requests.get(f"https://{self.region}.api.blizzard.com/sc2/legacy/profile/{self.region_ids[self.region]}/{player['member'][0]['legacy_link']['realm']}/{player['member'][0]['legacy_link']['id']}?{self.access_token}")
			else:
				break
		try:
			profile = profile_data.json()
		except ValueError:
			print("JSONDecoderError occurred")
			return
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
			return


def write2file(data, filename):
	with open(filename, 'w', encoding='utf-8') as output:
		writer = csv.writer(output, lineterminator='\n')
		writer.writerows(data)


def main():
	us = Ladder("us", 6, 6)
	print("Doing stuff")
	us.get_players()
	
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

	profile_info = []
	for profile in us.profiles:
		varList = []
		for key, val in vars(profile).items():
			varList.append(val)
		if varList != []:
			profile_info.append(varList)

	write2file(player_info, "player_info.csv")
	write2file(profile_info, "profile_info.csv")

	print("Done stuff")

main()