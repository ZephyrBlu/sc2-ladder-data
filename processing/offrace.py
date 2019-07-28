import copy
import json


def main(player_info):
    main_races = [
        'protoss',
        'zerg',
        'terran',
        'random'
    ]

    template = {}

    # {'name': <insert race name here>, 'value': <insert race count here>}
    for race in main_races:
        template[race] = []
        for race2 in main_races:
            if race != race2:
                template[race].append({'name': race2, 'value': 0})

    leagues = [
        'grandmaster',
        'master',
        'diamond',
        'platinum',
        'gold',
        'silver',
        'bronze',
    ]

    # {'league': , 'protoss': , 'zerg': , 'terran': , 'random': , 'max': }
    radar_offrace_dist = []
    pie_offrace_dist = {}
    total_dist = []

    pie_offrace_dist['all'] = copy.deepcopy(template)
    for league in leagues:
        pie_offrace_dist[league] = copy.deepcopy(template)
        radar_offrace_dist.append({
            'league': league.capitalize(),
            'protoss': 0,
            'zerg': 0,
            'terran': 0,
            'random': 0
        })

    total_dist = copy.deepcopy(radar_offrace_dist)

    count = 0
    for player, races in player_info.items():
        main_race = None
        for race, info in races.items():
            if info['main_race'] is True:
                main_race = info
                main_race.update({
                    'race': race.lower()
                })

                for index, league in enumerate(radar_offrace_dist):
                    if league['league'] == info['league']:
                        total_dist[index][main_race['race']] += 1
                        if len(races) > 1:
                            radar_offrace_dist[index][main_race['race']] += 1

        for race, info in races.items():
            if info['main_race'] is False:
                count += 1
                for index, r in enumerate(pie_offrace_dist[main_race['league'].lower()][main_race['race']]):
                    if r['name'] == race.lower():
                        pie_offrace_dist[main_race['league'].lower()][main_race['race']][index]['value'] += 1

                for index, r in enumerate(pie_offrace_dist['all'][main_race['race']]):
                    if r['name'] == race.lower():
                        pie_offrace_dist['all'][main_race['race']][index]['value'] += 1

    # print(pie_offrace_dist['all'])
    # print('\n')
    # print(radar_offrace_dist)
    # print(total_dist)

    temp_dist = []
    for i in range(0, len(total_dist)):
        offrace_record = radar_offrace_dist[i]
        total_record = total_dist[i]

        record = {'league': total_dist[i]['league']}
        for race in main_races:
            prop = offrace_record[race.lower()]/total_record[race.lower()]
            record.update({
                race.lower(): round(prop*100, 1)
            })
        temp_dist.append(record)

    # print('\n')
    # print(temp_dist)

    radar_offrace_dist = {
        'data': temp_dist,
        'raw': {
            'percentage': round(count/len(player_info)*100, 1),
            'fraction': f'{count}/{len(player_info)}'
        }
    }

    for league, races in pie_offrace_dist.items():
        for race, offrace in races.items():
            total = 0
            for r in offrace:
                total += r['value']

            for index, r in enumerate(offrace):
                if total == 0:
                    pie_offrace_dist[league][race][index]['value'] = 0
                else:
                    pie_offrace_dist[league][race][index]['value'] = round((r['value']/total)*100, 1)

    # print('\n')
    # print(pie_offrace_dist['grandmaster'])
    # print(radar_offrace_dist['raw'])

    with open('JSON/offrace-pie-dist.json', 'w', encoding='utf-8') as output:
        json.dump(pie_offrace_dist, output)

    with open('JSON/offrace-radar-dist.json', 'w', encoding='utf-8') as output:
        json.dump(radar_offrace_dist, output)

    return pie_offrace_dist, radar_offrace_dist
