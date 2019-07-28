ladder_data = []
main_race_data = []
mmr_all = []

winrate = {
    'protoss': {
        'grandmaster': [],
        'masters': [],
        'diamond': [],
        'platinum': [],
        'gold': [],
        'silver': [],
        'bronze': []
    },
    'terran' : {
        'grandmaster': [],
        'masters': [],
        'diamond': [],
        'platinum': [],
        'gold': [],
        'silver': [],
        'bronze': []
    }
}
avg_winrate = {
    'protoss': {
        'grandmaster': 0,
        'masters': 0,
        'diamond': 0,
        'platinum': 0,
        'gold': 0,
        'silver': 0,
        'bronze': 0
    },
    'terran' : {
        'grandmaster': 0,
        'masters': 0,
        'diamond': 0,
        'platinum': 0,
        'gold': 0,
        'silver': 0,
        'bronze': 0
    }
}
games = 0

for player, races in player_info.items():
    max_mmr = 0
    player_main_race = None
    active = False
    for race, info in races.items():
        mmr_all.append(int(info['mmr']))
        games += int(info['wins'])+int(info['losses'])
        if int(info['wins'])+int(info['losses']) >= 30:
            wr = int(info['wins'])/(int(info['wins'])+int(info['losses']))
            if race.lower() == 'protoss' or race.lower() == 'terran':
                winrate[race.lower()][info['league'].lower()].append(wr)

            active = True
            ladder_data.append([
                race,
                info['mmr'],
                info['wins'],
                info['losses'],
                info['ties']
            ])
            if int(info['mmr']) > max_mmr:
                max_mmr = int(info['mmr'])
                player_main_race = race.lower()
    if active is True:
        race_info = races[player_main_race.capitalize()]
        main_race_data.append([
            player_main_race.capitalize(),
            race_info['mmr'],
            race_info['wins'],
            race_info['losses'],
            race_info['ties']
        ])

for race, leagues in winrate.items():
    for league, winrates in leagues.items():
        avg = sum(winrates)/len(winrates)
        avg_winrate[race][league] = avg

print(avg_winrate)
print('\n')
print(games)

# write2file(ladder_data, 'ladder-data.csv')
# write2file(main_race_data, 'main-race-data.csv')

mean = sum(mmr_all)/len(mmr_all)
print(mean)
mmr_all.sort()
print(mmr_all[0])
print(mmr_all[-1])

std_dev = []
for v in mmr_all:
    std_dev.append((v-mean)**2)

print(f'Variance: {sum(std_dev)/len(std_dev)}')
print(f'Std Dev: {math.sqrt(sum(std_dev)/len(std_dev))}')