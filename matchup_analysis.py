import csv
import json
import copy


class Game:
    def __init__(self, date, matchup, winner, game_map, player1, player2):
        self.date = date
        self.matchup = matchup
        self.game_map = game_map
        self.winner = winner
        self.player1 = player1
        self.player2 = player2

    def __repr__(self):
        return self.matchup


matches = []
with open('data/matches.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        matches.append(Game(int(row[0]), row[1], int(row[5]), row[2],  json.loads(row[3]), json.loads(row[4])))


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

count = 0
for match in matches:
    if match.date > 1560124800:
        count += 1
        if match.player1['league'] == match.player2['league']:
            if match.winner == 1:
                matchup = match.player1['race'][0]+'v'+match.player2['race'][0]
                player = match.player1

                win_played[matchup][player['league']] = (
                    win_played[matchup][player['league']][0]+1,
                    win_played[matchup][player['league']][1]+1
                )

                win_played[matchup[::-1]][match.player2['league']] = (
                    win_played[matchup[::-1]][match.player2['league']][0],
                    win_played[matchup[::-1]][match.player2['league']][1]+1
                )
            elif match.winner == 2:
                matchup = match.player2['race'][0]+'v'+match.player1['race'][0]
                player = match.player2

                win_played[matchup][player['league']] = (
                    win_played[matchup][player['league']][0]+1,
                    win_played[matchup][player['league']][1]+1
                )

                win_played[matchup[::-1]][match.player1['league']] = (
                    win_played[matchup[::-1]][match.player1['league']][0],
                    win_played[matchup[::-1]][match.player1['league']][1]+1
                )

for mu, league in win_played.items():
    print(f'{mu}:')
    for l, v in league.items():
        if v[1] != 0:
            print(f'  {l}: {round(v[0]/v[1]*100, 1)}% ({v[0]}/{v[1]})')
    print('')

print(f'{round((count/len(matches))*100, 1)}% of total matches ({count}/{len(matches)})')