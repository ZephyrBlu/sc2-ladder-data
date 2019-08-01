import csv
import json
import copy
import datetime


def analyze_match(match, win_played):
    """
    Increments the number of games won and/or played
    based on matchup and league

    Returns an updated version of the input
    """

    if match.winner == 1:
        # matchup = match.player1['race'][0]+'v'+match.player2['race'][0]
        p1_race = match.player1['race']
        p2_race = match.player2['race']
        player = match.player1

        win_played[player['league']][p1_race][f'{p2_race}Inner'] = (
            win_played[player['league']][p1_race][f'{p2_race}Inner'][0]+1,
            win_played[player['league']][p1_race][f'{p2_race}Inner'][1]+1
        )

        win_played[match.player2['league']][p2_race][f'{p1_race}Inner'] = (
            win_played[match.player2['league']][p2_race][f'{p1_race}Inner'][0],
            win_played[match.player2['league']][p2_race][f'{p1_race}Inner'][1]+1
        )
    elif match.winner == 2:
        # matchup = match.player2['race'][0]+'v'+match.player1['race'][0]
        p1_race = match.player1['race']
        p2_race = match.player2['race']
        player = match.player2

        win_played[player['league']][p2_race][f'{p1_race}Inner'] = (
            win_played[player['league']][p2_race][f'{p1_race}Inner'][0]+1,
            win_played[player['league']][p2_race][f'{p1_race}Inner'][1]+1
        )

        win_played[match.player1['league']][p1_race][f'{p2_race}Inner'] = (
            win_played[match.player1['league']][p1_race][f'{p2_race}Inner'][0],
            win_played[match.player1['league']][p1_race][f'{p2_race}Inner'][1]+1
        )

    return win_played


def calculate_winrate(win_played, *, winrate_template=None, current_epoch, all_data=False):
    """
    Calculates the winrates for all data types,
    leagues and matchup and stores them in a
    new dictionary structure
    """

    def epoch2datetime(epoch_time):
        date_time = datetime.datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d')
        return date_time

    # stores the total games for each
    # matchup across all leagues
    total_games = {}

    if not all_data:
        winrate_template_empty = copy.deepcopy(winrate_template)

    winrates = copy.deepcopy(win_played)

    # quick conversion to proper race names
    mu_conv = {
        'P': 'Protoss',
        'T': 'Terran',
        'Z': 'Zerg',
        'R': 'Random'
    }

    # calculates winrates for each data type,
    # each matchup and each league
    for data_type, data in win_played.items():
        total_games = {}
        for league, matchups in data.items():
            for race, inner_races in matchups.items():
                if race not in total_games:
                    total_games[race] = {}

                # values = (<games won>, <games played>)
                for inner_race, values in inner_races.items():
                    if inner_race not in total_games[race]:
                        total_games[race][inner_race] = (0, 0)

                    print(f'Epoch: {current_epoch}, {data_type}, {league}, {race} vs {inner_race}', values)
                    if values[1] != 0:
                        # calculate winrate
                        val_tuple = (round(values[0]/values[1]*100, 1), f'{values[0]}/{values[1]}')
                    else:
                        val_tuple = (0, '0/0')

                    if all_data:
                        winrates[data_type][league][race][inner_race] = val_tuple
                    else:
                        winrate_template['bin'] = epoch2datetime(current_epoch)

                        # storing data, league and matchup specific data
                        winrate_template[race][inner_race] = {'value': val_tuple}

                    # aggregating all games from current matchup across all leagues
                    total_games[race][inner_race] = (
                        total_games[race][inner_race][0]+values[0],
                        total_games[race][inner_race][1]+values[1]
                    )
            
            if not all_data:
                # store current all matchup winrates for current league
                winrates[data_type][league] = winrate_template

                # reset matchup winrate template
                winrate_template = copy.deepcopy(winrate_template_empty)

        # calculate 'All' league winrate in current matchup
        if data_type == 'all':
            for race, inner_races in total_games.items():
                for inner_race, values in inner_races.items():
                    if values[1] != 0:
                        percent = round(
                            total_games[race][inner_race][0]/total_games[race][inner_race][1]*100, 1
                        )
                        games =  f'{total_games[race][inner_race][0]}/{total_games[race][inner_race][1]}'
                    else:
                        percent = 0
                        games =  '0/0'
                    winrates['all']['All'][race][inner_race] = (percent, games)

    # 'league' -> 'All' is the same as 'all' -> 'All', so copy data
    winrates['league']['All'] = copy.deepcopy(winrates['all']['All'])
    return winrates


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
            matches.append(
                Game(
                    int(row[0]),
                    row[1],
                    int(row[5]),
                    row[2],
                    json.loads(row[3]),
                    json.loads(row[4])
                )
            )


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
        'ProtossInner': (0, 0),
        'TerranInner': (0, 0),
        'ZergInner': (0, 0),
        'RandomInner': (0, 0),
    }

    # the winrate structure for the
    # inner race of the matchup
    #
    # <race>: {value: (<winrate>, <games won/played>)}
    weekly_winrate_inner_template = {
        'ProtossInner': {'value': (0, '0/0')},
        'TerranInner': {'value': (0, '0/0')},
        'ZergInner': {'value': (0, '0/0')},
        'RandomInner': {'value': (0, '0/0')},
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

    weekly_winrates = copy.deepcopy(weekly_winrate_template)

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

    monthly_win_played = copy.deepcopy(all_win_played)

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

    current_month_epoch = 1561852800

    matches.sort(key= lambda x: x.date)

    for match in matches:
        # if match.date >= current_month_epoch:
        #     # analyze_match(<match>, <current weekly games won/played>)
        #     monthly_win_played['all'] = analyze_match(match, monthly_win_played['all'])

        #     # if players are in the same league, store in different data type
        #     if match.player1['league'] == match.player2['league']:
        #         monthly_win_played['league'] = analyze_match(match, monthly_win_played['league'])

        if match.date < start_epoch:
            continue

        elif start_epoch < match.date <= start_epoch + one_week:

            # analyze_match(<match>, <current weekly games won/played>)
            weekly_win_played['all'] = analyze_match(match, weekly_win_played['all'])

            # if players are in the same league, store in different data type
            if match.player1['league'] == match.player2['league']:
                weekly_win_played['league'] = analyze_match(match, weekly_win_played['league'])
        else:
            # update all_win_played values with current week's win_played
            for data_type, data in weekly_win_played.items():
                for league, matchups in data.items():
                    for race, inner_races in matchups.items():
                        for inner_race, values in inner_races.items():
                            all_win_played[data_type][league][race][inner_race] = (
                                all_win_played[data_type][league][race][inner_race][0]+weekly_win_played[data_type][league][race][inner_race][0],
                                all_win_played[data_type][league][race][inner_race][1]+weekly_win_played[data_type][league][race][inner_race][1]
                            )

            current_weekly_winrates = calculate_winrate(
                weekly_win_played,
                winrate_template=weekly_winrate_middle_template,
                current_epoch=start_epoch
            )

            # update overall weekly_winrate with current week's winrates
            # updates both 'all' and 'league' data types
            for data_type, data in current_weekly_winrates.items():
                for league, matchups in data.items():
                    weekly_winrates[data_type][league].append(matchups)    

            # reset weekly_win_played for next week
            weekly_win_played = copy.deepcopy(weekly_win_played_template)

            # increment start_epoch to next week with a match
            print()
            print(f'Current Epoch: {start_epoch}')
            print(f'Match Date Epoch: {match.date}')
            start_epoch += one_week
            print(f'New Epoch: {start_epoch}')

            # analyze new match
            weekly_win_played['all'] = analyze_match(match, weekly_win_played['all'])
            if match.player1['league'] == match.player2['league']:
                weekly_win_played['league'] = analyze_match(match, weekly_win_played['league'])

    current_weekly_winrates = calculate_winrate(
        weekly_win_played,
        winrate_template=weekly_winrate_middle_template,
        current_epoch=start_epoch
    )

    # update overall weekly_winrate with current week's winrates
    # updates both 'all' and 'league' data types
    for data_type, data in current_weekly_winrates.items():
        for league, matchups in data.items():
            weekly_winrates[data_type][league].append(matchups)    

    # reset weekly_win_played for next week
    weekly_win_played = copy.deepcopy(weekly_win_played_template)

    # increment start_epoch
    start_epoch += one_week

    # calculate winrate for all_win_played
    all_winrates = calculate_winrate(
        all_win_played,
        winrate_template=None,
        current_epoch=start_epoch,
        all_data=True
    )

    winrates = {
        'all': all_winrates,
        'weekly': weekly_winrates
    }

    print()
    print(all_winrates)

    # store calculated winrates in all_winrate


    # store both weekly and all winrates in one structure


    with open('JSON/winrate.json', 'w', encoding='utf-8') as output:
            json.dump(winrates, output)

    return winrates
