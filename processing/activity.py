import json


def main():
    games_played = {}
    with open('JSON/games-played-dist.json', 'r', encoding='utf-8') as file:
        games_played = json.load(file)['data']
    return games_played


# import csv
# import json


# games_played_dist = {'data': []}
# with open('../ladder-data/data/player_info.csv', 'r', encoding='utf-8') as file:
#     reader = csv.reader(file)
#     next(reader)
#     for row in reader:
#         games_played_dist['data'].append({
#             'games': float(row[8]),
#             'proportion': round(float(row[1])*100, 1)
#         })
#         print(row)
#         if float(row[1]) == 0.990:
#             break

# with open('games-played-dist.json', 'w') as output:
#     json.dump(games_played_dist, output)