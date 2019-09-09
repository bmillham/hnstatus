""" Log usage and status information to a sqlite3 database """

import sqlite3
from datetime import datetime
#from sqlite import Error


class Log(object):
    """ Log class based on sqlite3 """

    def __init__(self, database=None, commit_after=0, ro=False):
        self.database = database
        self.commit_count = self.commit_after = commit_after
        self.ro = ro

    def open(self):
        if self.ro:
            file = "file:{}?mode=ro".format(self.database)
            uri = True
        else:
            file = self.database
            uri = False
        self.connection = sqlite3.connect(file, uri=uri)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        # Create the table if new database
        s = """CREATE TABLE IF NOT EXISTS
               activity(date DATETIME PRIMARY KEY,
               rx REAL, tx REAL, ss INTEGER,
               anytime INTEGER, bonus INTEGER,
               association STRING, fap STRING);"""
        self.execute(s)

    def execute(self, sql, params=None, commit=True):
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        if commit:
            self.commit_count -= 1
            if self.commit_count == 0:
                self.connection.commit()
                self.commit_count = self.commit_after

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        self.connection.commit()
        self.connection.close()

    def adddata(self, status=None):
        if not status:
            print("No status to log")
            return
        now = datetime.now()
        s = """INSERT INTO activity(date, rx, tx, ss, anytime, bonus,
               association, fap)
               VALUES(?, ?, ?, ?, ?, ?, ?, ?);"""

        self.execute(s, params=(now,
                                status.last_rx_raw,
                                status.last_tx_raw,
                                status.signal_strength,
                                status._anytime_remaining_bytes,
                                status._bonus_remaining_bytes,
                                status._association['association_state_code'],
                                status.fap_status))
