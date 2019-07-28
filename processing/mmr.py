import json
import math
import numpy as np


def main(player_dist, race_count):
    races = ['all', 'protoss', 'terran', 'zerg', 'random']
    leagues = ['all', 'grandmaster', 'master', 'diamond', 'platinum', 'gold', 'silver', 'bronze']
    bins = []
    mmr_dist = {
        'all': [],
        'grandmaster': [],
        'master': [],
        'diamond': [],
        'platinum': [],
        'gold': [],
        'silver': [],
        'bronze': []
    }

    # mmr_dist['all']['all'] = temp
    # mmr_bins['all']['all'] = bins

    for league in leagues:
        # all_temp = []
        for race in races:
            player_set = player_dist[league]
            mmr_list = []
            for player in player_set:
                if player['race'].lower() == race or race == 'all':
                    mmr_list.append(int(player['mmr']))

            if not mmr_list:
                break

            mmr_list.sort()

            bin_min = (math.floor(mmr_list[0]/100))*100
            bin_max = (math.ceil(mmr_list[-1]/100))*100
            bin_range = bin_max-bin_min

            raw_dist = np.histogram(mmr_list, bins=bin_range//100, range=(bin_min, bin_max))
            dist = raw_dist[0].tolist()
            bins = raw_dist[1].tolist()
            bins = list(map(lambda x: int(x), bins))

            for i in range(0, len(dist)):
                update = False
                for index, r in enumerate(mmr_dist[league]):
                    if r['bin'] == bins[i]+50:
                        mmr_dist[league][index][race] = {'value': round(dist[i]/race_count[league][race]*100, 1)}
                        update = True

                if update is False:
                    mmr_dist[league].append({
                        'all': {
                            'value': 0,
                        },
                        'protoss': {
                            'value': 0,
                        },
                        'zerg': {
                            'value': 0,
                        },
                        'terran': {
                            'value': 0,
                        },
                        'random': {
                            'value': 0,
                        },
                        'bin': 0
                    })
                    mmr_dist[league][-1].update({
                        race: {
                            'value': round(dist[i]/race_count[league][race]*100, 1)
                        },
                        'bin': bins[i]+50
                    })

                # update = False
                # for count, r in enumerate(all_temp):
                #   if r['bin'] == record['bin']:
                #       all_temp[count].update({
                #           'value': r['value']+record['value']
                #       })
                #       update = True
                # if update is False:
                #   all_temp.append(record)

            # mmr_dist[race][league] = temp

        # all_temp.sort(key=lambda x: x['bin'])
        # mmr_dist[race]['all'] = all_temp

    with open('JSON/mmr-dist.json', 'w') as output:
        json.dump(mmr_dist, output)

    return mmr_dist