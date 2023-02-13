import argparse
import os
import re
from dotenv import dotenv_values
import sqlite3

config = dotenv_values('.env')

parser = argparse.ArgumentParser()
parser.add_argument('file', help="Name of the orders file to ingest")
parser.add_argument('--db', help="Path to the database [Default is from .env]", default=config['DB'])
parser.add_argument('--season', help="The season to ingest into [Default is assumed from filename]")
parser.add_argument('--day', help="The day to ingest into [Default is assumed from filename]")

args = parser.parse_args()

db = sqlite3.connect(args.db)

fname = args.file
season = args.season
day = args.day
if season is None or day is None:
    base_fname = os.path.basename(fname)
    match = re.match(r'(\d*)-(\d*)', base_fname)
    day = match[1]
    season = match[2]

print(f"Importing data from {fname} into orders database {args.db}")
print(f"This is for Season {season}, Day {day}.")
input("Press ENTER to continue, ^C to quit.\n")

query = '''
    INSERT INTO plans (season, day, territory, tier, quota)
    VALUES (?, ?, 
        (SELECT id FROM territory WHERE name=? COLLATE NOCASE), 
    ?, ?)
'''

with open(fname, "r") as input:
    for line in input:
        tname, tier, quota = line.strip().split(',')
        try:
            db.execute(query, (season, day, tname, tier, quota))
            db.commit()
            print(f"Order '{line.strip()}' successful.")
        except sqlite3.Error as err:
            print(f"Order '{line.strip()}' rejected.  Is that a valid territory? Was this plan already ingested?")

