# sc2-ladder-data

This is a Python script you can use to gather data from Blizzards Starcraft II API.

It's not what I'd call 'production' code since it contains print statements, probably has some bloat and
could probably be written more cleanly, but it gets the job done.

I make no promises about updating or maintaining this repository, but the code should be stable since it uses Blizzard's updated API endpoints

## Functionality

The script can easily gather ladder and profile data from a range of leagues from any region.
If you want to gather data from multiple regions it should be easy to implement that yourself.

Each API call will be printed before it's executed.

The script will attempt to access endpoints multiple times before giving up and by
default will generate CSV files for both player and profile data.

## Performance

The entire NA ladder takes ~1min of runtime to gather all the data (150k ranked players).

In my experience the EU endpoint is notoriously unreliable.

It is recommended that you don't gather profile data if it's not required, as it adds a lot of overhead (~30min). However, you may have better luck since I live in NZ not the US.

## How to Use

1) Add your Battlenet Developer credentials in the `_get_token` method to allow you to access the API

2) In the `_get_id_list` method, replace the season number in the request with your desired season

3) Change the region and league range in `main` to suit your needs (Format is `Ladder(<region>, <min_League>, <max_league>)`)

4) Change the output files to your desired name/directory

5) Run it!

## To Do

- Update repo with most recent script. Includes fetching player profiles and updated asynchronous code.
