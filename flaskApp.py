#!/usr/bin/env python3
import sqlite3
import json
from time import localtime, strftime, sleep
from sys import exit, argv
from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_cors import CORS
import threading
import os
from inotify_simple import INotify, flags
from flask_sock import Sock
dbFile = "clock.db"

weekdayNumbers = [128, 64, 32, 16, 8, 4, 2]
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]


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


def addAlarm(time, dow, radio):
    db = sqlite3.connect(dbFile)
    c = db.cursor()
    c.execute("INSERT INTO alarms VALUES (NULL, '" + time + "' , "+str(dow)+", "+str(radio)+")")
    db.commit()
    db.close()


def removeAlarm(alarmID):
    db = sqlite3.connect(dbFile)
    c = db.cursor()
    c.execute("DELETE FROM alarms WHERE alarm_ID = " + alarmID)
    db.commit()
    db.close()


def refreshAlarmList(alarms):
    alarms.clear()
    for alarm in readDB():
        alarms.append(alarm.toJson())
    return None


app = Flask(__name__)
sock = Sock(app)
app.config.from_object(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})
alarms = []
refreshAlarmList(alarms)
inotify = INotify()
wd = inotify.add_watch(dbFile, flags.MODIFY)
sendAlarms = threading.Event()
""" Defines the routes flask serves
    If no methods are provided, route
    only responds to GET request
        """


def watchingDB(sendAlarms):
    while True:
        for event in inotify.read():
            refreshAlarmList(alarms)
            sendAlarms.set()


watchDB = threading.Thread(target=watchingDB, name="WatchDB", daemon=True, args=(sendAlarms,)).start()


@sock.route('/alarmSocket')
def alarmSocket(sock):
    while True:
        if sendAlarms.is_set():
            sock.send(json.dumps(alarms))
            sendAlarms.clear()


#
# def socketReceiver(sock):
#     data = json.loads(sock.receive())
#     print(data)
#     print(data["command"])
#     match data["command"]:
#         case "add":
#             print("Adding new alarm")
#             addAlarm(data["time"], sum(data["activeDays"]), data["radio"])
#         case "delete":
#             print("Deleting alarm")
#         case "edit":
#             print("Editing alarm")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/vue')
def vueDemo():
    return render_template('vueFlaskCORS.html')


@app.route('/alarms', methods=['GET', 'POST'])
def alarmsRest():
    response_object = {'status': 'success'}
    if request.method == 'POST':
        postData = request.get_json()
        print(postData)
        time = postData.get('time')
        dow = sum(postData.get('activeDays'))
        radio = postData.get('radio')
        repeat = postData.get('repeat')
        try:
            addAlarm(time, dow, radio)
            response_object['message'] = {"response": "ok"}
        except:
            response_object['message'] = {"response": "fail"}
        return response_object['message']
    if request.method == 'GET':
        return alarms


@app.route('/add', methods=['GET', 'POST'])
def addForm():
    if request.method == 'GET':
        return render_template('addform.html')
    if request.method == 'POST':
        time = request.form['alarmTime']
        activeDays = (request.form.getlist('days'))
        dow = sum(list(map(int, activeDays)))
        try:
            addAlarm(time, dow, 0)
        except:
            print("db error")
        return redirect(url_for('home'))


@app.route('/delete', methods=['POST'])
def deleteAlarm():
    response_object = {'status': 'success'}
    if request.method == 'POST':
        if request.form['alarmID'].isdigit():
            alarmID = request.form['alarmID']
            removeAlarm(alarmID)
            response_object['message'] = 'Alarm deleted'
    return jsonify(response_object)


if __name__ == '__main__':
    app.run()
