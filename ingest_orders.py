#!/usr/bin/env python

import argparse
import os
import shutil
import time
import re
from constants import DB
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument('file', help="Name of the orders file to ingest")
parser.add_argument('--db', help="Path to the database [Default is from .env]", default=DB)
parser.add_argument('--season', help="The season to ingest into [Default is assumed from filename]")
parser.add_argument('--day', help="The day to ingest into [Default is assumed from filename]")
parser.add_argument('--backup', default=True, help="Back up the database file [Default is TRUE]", action='store_true')
parser.add_argument('--no-backup', dest='backup', help="...or not", action='store_false')

args = parser.parse_args()

if args.backup:
    backup = f"{DB}.{int(time.time())}"
    print()
    print(f"Backing up {DB} to {backup}...")
    print()
    shutil.copy(DB, backup)
else:
    print()
    print("WARNING: No backup of the database is being created!")
    print()

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
        if len(line.strip()) == 0 or line.startswith('#'):
            continue

        tname, tier, quota = line.strip().split(',')
        try:
            db.execute(query, (season, day, tname, tier, quota))
            db.commit()
            print(f"Order '{line.strip()}' successful.")
        except sqlite3.Error as err:
            print(f"Order '{line.strip()}' rejected.  Is that a valid territory? Was this plan already ingested?")
