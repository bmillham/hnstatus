""" Log usage and status information to a sqlite3 database """

import sqlite3
#from sqlite import Error


class Log(object):
    """ Log class based on sqlite3 """

    def __init__(self, database=None):
        self.database = database

    def open(self):
        self.connection = sqlite3.connect(self.database)
        self.cursor = self.connection.cursor()

    def _create_table(self):
        pass
