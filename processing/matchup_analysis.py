import csv
import json
import copy


def analyze_match(match, win_played):
    """
    write stuff about what the fuck this does
    """

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

    return win_played


def calculate_winrate(win_played):
    """
    write stuff about what the fuck this does
    """

    
    total_games = {}

    mu_conv = {
        'P': 'Protoss',
        'T': 'Terran',
        'Z': 'Zerg',
        'R': 'Random'
    }

    for t, data in win_played.items():
        for mu, league in data.items():
            print(f'{mu}:')
            total_games[mu] = (0, 0)
            race = mu_conv[mu[0]]
            inner_race = mu_conv[mu[-1]]
            for l, v in league.items():
                if v[1] != 0:
                    print(f'  {l}: {round(v[0]/v[1]*100, 1)}% ({v[0]}/{v[1]})')

                    percent = round(v[0]/v[1]*100, 1)
                    games =  f'{v[0]}/{v[1]}'
                    win_played_export[t][l][race][inner_race] = (percent, games)
                    total_games[mu] = (total_games[mu][0]+v[0], total_games[mu][1]+v[1])

            if t == 'all':
                percent = round(total_games[mu][0]/total_games[mu][1]*100, 1)
                games =  f'{total_games[mu][0]}/{total_games[mu][1]}'
                win_played_export['all']['All'][race][inner_race] = (percent, games)
            print('')

    win_played_export['league']['All'] = copy.deepcopy(win_played_export['all']['All'])
    print(f'{round((count/len(matches))*100, 1)}% of total matches ({count}/{len(matches)})')


def main():
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
    with open('../../../matches.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            matches.append(Game(int(row[0]), row[1], int(row[5]), row[2],  json.loads(row[3]), json.loads(row[4])))


    races = ['Protoss', 'Terran', 'Zerg', 'Random']
    leagues = [
        'All',
        'Grandmaster',
        'Master',
        'Diamond',
        'Platinum',
        'Gold',
        'Silver',
        'Bronze'
    ]

    # the games won/played structure for the
    # inner race of the matchup 
    # <race>: (<games won>, <games played>)
    #
    # win_played structure is used to create
    # the winrate structure
    weekly_win_played_inner_template = {
        'Protoss': (0, 0),
        'Terran': (0, 0),
        'Zerg': (0, 0),
        'Random': (0, 0),
    }

    # the winrate structure for the
    # inner race of the matchup
    #
    # <race>: {value: (<winrate>, <games won/played>)}
    weekly_winrate_inner_template = {
        'Protoss': {'value': (0, '0/0')},
        'Terran': {'value': (0, '0/0')},
        'Zerg': {'value': (0, '0/0')},
        'Random': {'value': (0, '0/0')},
    }

    # the outer winrate structure for the
    # different data types and leagues
    #
    # <data type> : {
    #     <league>: <list of matchup winrates for each week>
    # }
    weekly_winrate_template = {
        'all': {
            'All': [],
            'Grandmaster': [],
            'Master': [],
            'Diamond': [],
            'Platinum': [],
            'Gold': [],
            'Silver': [],
            'Bronze': []
        },
        'league': {
            'All': [],
            'Grandmaster': [],
            'Master': [],
            'Diamond': [],
            'Platinum': [],
            'Gold': [],
            'Silver': [],
            'Bronze': []
        },
    }

    weekly_winrate = copy.deepcopy(weekly_winrate_template)

    all_win_played = {
        'all': {
            'All': {},
            'Grandmaster': {},
            'Master': {},
            'Diamond': {},
            'Platinum': {},
            'Gold': {},
            'Silver': {},
            'Bronze': {}
        },
        'league': {
            'All': {},
            'Grandmaster': {},
            'Master': {},
            'Diamond': {},
            'Platinum': {},
            'Gold': {},
            'Silver': {},
            'Bronze': {}
        },
    }


    # generate middle template for win_played structures
    # combine race with inner template to create nested
    # dict containing matchup games won/played values
    # 
    # matchup = <race> vs <inner race>
    # middle_template = {
    #    <race>: {
    #        <inner race>: (<games won>, <games played>)
    #    }
    # }
    win_played_middle_template = {}
    for race in races:
        win_played_middle_template[race] = copy.deepcopy(weekly_win_played_inner_template)


    # fill outer win_played templates with middle_template
    # to generate final structure for win_played type
    for league in leagues:
        all_win_played['all'][league] = copy.deepcopy(win_played_middle_template)
        all_win_played['league'][league] = copy.deepcopy(win_played_middle_template)

    # create copy for storing winrates during calculation
    # will overwrite win_played format on inner_template
    #
    # (current) win_played: <race>: (<games won>, <games played>)
    # (overwrite) winrate: <race>: (<winrate>, <games won/played>)
    all_winrate = copy.deepcopy(all_win_played)

    # create copy so contents can be reset each week of epochs
    weekly_win_played_template = copy.deepcopy(all_win_played)
    weekly_win_played = copy.deepcopy(all_win_played)

    # full structure for one week of epochs, including date bin
    weekly_winrate_middle_template = {'bin': 'date'}


    # generate full structure for one week of winrate data
    #
    # matchup = <race> vs <inner race>
    # weekly_winrate_template = {
    #   <race>: {
    #       <inner race>: {
    #           'value': (<winrate>, <games won/played>)
    #        }
    #   },
    #   'bin': <epoch/date bin>   
    # }
    for race in races:
        weekly_winrate_middle_template[race] = copy.deepcopy(weekly_winrate_inner_template)


    # matchup = <race> vs <inner race>
    # full_winrate_structure_example = {
    #     <data type>: {    -- outer structure
    #         <league>: [{
    #             <race>: {    -- middle structure
    #                 <inner race>: {    -- inner structure
    #                     'value': (<winrate>, <games won/played>)
    #                 }
    #             },
    #             'bin': <epoch/date bin>
    #         }]
    #     }
    # }


    # one week in epoch time
    one_week = 604800

    # December 31st 2018
    start_epoch = 1546214400

    for match in matches:
        if start_epoch < match.date < start_epoch + one_week:
            weekly_win_played['all'] = analyze_match(match, weekly_win_played['all'])
            if match.player1['league'] == match.player2['league']:
                weekly_win_played['league'] = analyze_match(match, weekly_win_played['league'])
        elif match.date > start_epoch + one_week:
            # calculate winrate based on current weekly_win_played
            # get full winrate structure back as return value
            #
            # ----- NEED TO MODIFY FUNCTION !!! -----
            current_weekly_winrate = calculate_winrate(weekly_win_played)

            # update overall weekly_winrate with current week's winrates
            # updates both 'all' and 'league' data types
            #
            # update all_win_played values with current week's win_played
            for t, data in current_weekly_winrate.items():
                for league, winrates in data.items():
                    weekly_winrate[t][league].append(winrates)

            # reset weekly_win_played for next week
            weekly_win_played = copy.deepcopy(weekly_win_played_template)

            # analyze new match
            weekly_win_played['all'] = analyze_match(match, weekly_win_played['all'])
            if match.player1['league'] == match.player2['league']:
                weekly_win_played['league'] = analyze_match(match, weekly_win_played['league'])

    # calculate winrate for all_win_played


    # store calculated winrates in all_winrates


    # store both weekly and all winrates in one structure


    with open('JSON/winrate.json', 'w', encoding='utf-8') as output:
            json.dump(win_played_export, output)

    return win_played_export
