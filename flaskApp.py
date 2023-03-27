#!/usr/bin/env python3
import sqlite3
import json
from time import localtime, strftime
from sys import exit, argv
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS

dbFile = "clock.db"


class Alarm:
    """A class for alarms"""
    def __init__(self, alarmID, time, activeDays, repeat, radioStation):
        self.alarmID = alarmID
        self.time = time
        self.activeDays = activeDays

        self.repeat = repeat
        self.radioStation = radioStation

    def toJson(self):
        return {"alarmID": self.alarmID,
                "time": self.time,
                "activeDays": self.activeDays,
                "repeat": self.repeat,
                "radio": self.radioStation
                }


def readDB():  # Reads the DB storing alarms in a list of Alarm
    weekdayNumbers = [128, 64, 32, 16, 8, 4, 2]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]
    db = sqlite3.connect(dbFile)
    c = db.cursor()
    alarmList = []
    for dow, time, alarmID, radio in db.execute(
     "SELECT dow, time, alarm_ID, radio FROM alarms ORDER BY time ASC;"):
        """
        Selects the primary key, time and days of week
        sorted by time, loops for all alarms
        """
        activeDays = []
        for i in range(7):
            if dow - weekdayNumbers[i] >= 0:
                dow = dow - weekdayNumbers[i]
                activeDays.append(weekdays[i])
        if dow % 2:
            repeat = True
        else:
            repeat = False
        alarmList.append(Alarm(alarmID, time, activeDays, repeat, radio))
    return alarmList


app = Flask(__name__)
app.config.from_object(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})
alarms = []
for alarm in readDB():
    alarms.append(alarm.toJson())


@app.route('/alarms', methods=['GET', 'POST'])
def all_books():
    response_object = {'status': 'success'}
    #    if request.method == 'POST':
    #    post_data = request.get_json()
    #    time =   post_data.get('time'),
    #    dow =    post_data.get('dow'),
    #    radio =    post_data.get('radio'),
    #    response_object['message'] = 'alarm added!'
    #    print (time[0])
    #    print (dow[0])
    #    print (radio[0])
    #    add_alarm(time[0],dow[0],radio[0])
    return alarms


@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
