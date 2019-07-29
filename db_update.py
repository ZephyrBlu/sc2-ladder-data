import psycopg2
from db_secret import *


# print('Started')

with open("ladder_data.py") as file:
	exec(file.read())

# print('Got ladder data')

with open("match_history.py") as file:
	exec(file.read())

# print('Got match history data')

hostname = 'localhost'

def query(conn):
	cur = conn.cursor()
	cur.execute("CREATE TEMP TABLE temp_table (LIKE matches INCLUDING DEFAULTS);")
	cur.execute("ALTER TABLE temp_table DROP COLUMN id;")
	cur.execute("COPY temp_table(date, matchup, map, player1, player2, win, region) from 'C://Users/Luke/Desktop/SC2 Ladder Analysis/ladder-data/data/matches.csv' WITH (FORMAT csv);")
	cur.execute("INSERT INTO matches (date, matchup, map, player1, player2, win, region) SELECT * from temp_table ON CONFLICT DO NOTHING;")
	conn.commit() 

connection = psycopg2.connect(
	host=hostname,
	user=USERNAME,
	password=PASSWORD,
	dbname=DATABASE
)

query(connection)

connection.close()
