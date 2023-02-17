import sqlite3
from constants import DB
from flask import g

###############################################################
#
# Database -- taken from https://flask.palletsprojects.com/en/2.2.x/patterns/sqlite3/
#
###############################################################

class Db:
    @staticmethod
    def get_db():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(DB)
        return db

    @staticmethod
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()
