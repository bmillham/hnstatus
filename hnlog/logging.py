""" Log usage and status information to a sqlite3 database """

import sqlite3
from datetime import datetime
#from sqlite import Error


class Log(object):
    """ Log class based on sqlite3 """

    def __init__(self, database=None):
        self.database = database

    def open(self):
        self.connection = sqlite3.connect(self.database)
        self.cursor = self.connection.cursor()
        # Create the table if new database
        s = """CREATE TABLE IF NOT EXISTS
               activity(adate DATETIME PRIMARY KEY,
               rx REAL, tx REAL, ss INTEGER);"""
        self._execute(s)

    def _execute(self, sql, params=None, commit=True):
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        if commit:
            self.connection.commit()

    def close(self):
        self.connection.close()

    def adddata(self, tx, rx, ss):
        now = datetime.now()
        s = """INSERT INTO activity(adate, rx, tx, ss)
               VALUES(?, ?, ?, ?);"""
        self._execute(s, params=(now, rx, tx, ss))
    
