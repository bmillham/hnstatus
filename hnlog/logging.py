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
        # Create table to store modem information
        s = """CREATE TABLE IF NOT EXISTS
               sysinfo(date DATETIME PRIMARY KEY,
               anytime_allowance INTEGER,
               bonus_allowance INTEGER,
               cpn STRING,
               mac_addr STRING,
               rpn STRING,
               rsn STRING,
               sernum STRING,
               mbpartno STRING,
               cores INTEGER,
               bldyear INTEGER,
               boardtype STRING,
               code STRING,
               esn STRING,
               fallbackvers STRING,
               wifi STRING,
               memtotal INTEGER,
               nspdisplayname STRING,
               sai STRING,
               san STRING,
               sdlwifivers STRING,
               wifivers STRING,
               wifimodvers STRING,
               fwvers STRING,
               beamid INTEGER,
               gatewayid INTEGER,
               orid INTEGER,
               satname STRING,
               lanaddr STRING);"""
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

    def addsysinfo(self, si=None, anytime=0, bonus=0):
        if not si:
            print("No sysinfo to log")
            return
        now = datetime.now()
        s = """INSERT INTO sysinfo(date, anytime_allowance, bonus_allowance,
               cpn, mac_addr, rpn, rsn, sernum, mbpartno, cores, bldyear,
               boardtype, code, esn, fallbackvers, memtotal,
               nspdisplayname, sai, san, sdlwifivers, wifivers, fwvers,
               beamid, gatewayid, orid, satname, lanaddr) VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
               ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        self.execute(s, params=(now, anytime, bonus, si['id']['cpn'],
                                si['id']['mac_addr'], si['id']['rpn'],
                                si['id']['rsn'],
                                si['terminal']['FactorySerNum'],
                                si['terminal']['MotherBoardPN'],
                                si['terminal']['active_cores'],
                                si['terminal']['bld_year'],
                                si['terminal']['board_type'],
                                si['terminal']['code'],
                                si['terminal']['esn'],
                                si['terminal']['fallback_version'],
                                si['terminal']['memory_total_kb'],
                                si['terminal']['nsp_display_name'],
                                si['terminal']['sai'], si['terminal']['san'],
                                si['terminal']['sdl_wifi_sw_version'],
                                si['terminal']['version'],
                                si['terminal']['wifi_module_sw_version'],
                                si['sat_info']['beam_id'],
                                si['sat_info']['gateway_id'],
                                si['sat_info']['or_id'],
                                si['sat_info']['sat_name'],
                                si['lan']['addr']))
        self.connection.commit()

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
