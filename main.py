from collections import defaultdict
from datetime import datetime
from encodings import utf_8
import os
from time import time

import attributeParser
import plot
import yaml
from os.path import exists

from PyQt6.QtWidgets import QApplication, QMainWindow,QTableView,QFileDialog,QDialog,QDialogButtonBox
import PyQt6.QtCore as QtCore
import PyQt6.QtWidgets as QtWidgets
import PyQt6.QtGui as QtGui

import hashlib

class Config:
    config = defaultdict(lambda: None)
    def __getitem__(self, name):
        if(exists('config.yaml')):
            with open('config.yaml', 'r') as infile:
                config = yaml.load(infile, Loader=yaml.FullLoader)
                self.config = defaultdict(lambda:None, config)
                return self.config[name]
        return self.config[name]
    def __setitem__(self, name, value):
        self.config[name] = value
        with open('config.yaml', 'w') as outfile:
            yaml.dump(dict(self.config), outfile)

    def __contains__(self, item):
        return item in self.config

class Table(QTableView):
    def sizeHint(self) -> QtCore.QSize:
        horizontal = self.horizontalHeader()
        vertical = self.verticalHeader()
        frame = self.frameWidth() * 2
        return QtCore.QSize(horizontal.length() + vertical.width() + frame,
                    vertical.length() + horizontal.height() + frame)

class App(QMainWindow):
    def __init__(self,config):
        super().__init__()
        self.setHuntLocation()
        toolbar = self.addToolBar("Toolbar")
        toolbar.addAction("Set Hunt Location", lambda: self.setHuntLocation(reset=True))
        toolbar.addAction("Plot MMR", self.plot)
        toolbar.addAction("Reset History",self.resetHistory)
        self.addToolBar(toolbar)
        self.config = config
        self.lastmodified = 0
        self.setWindowTitle("Hunt MMR Tracker")
        self.layout().setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)
        self.tableview = Table()    
        self.tableview.horizontalHeader().setVisible(True)
        self.tableview.verticalHeader().setVisible(False)
        self.model = QtGui.QStandardItemModel()
        self.tableview.setModel(self.model)
        self.setCentralWidget(self.tableview)
        self.tableview.setSortingEnabled(True)
        self.tableview.setEditTriggers(self.tableview.EditTrigger.NoEditTriggers)
        self.tableview.setShowGrid(False)

        self.timer = QtCore.QTimer()
        self.timer.timerType = QtCore.Qt.TimerType.VeryCoarseTimer
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.showLastMatch)
        self.timer.start()
        self.showLastMatch()
        self.tableview.doubleClicked.connect(self.doubleClicked)
    def doubleClicked(self,e : QtCore.QModelIndex):
        profileid = e.model().item(e.row(),7).text()
        if "profileid" in self.config:
            if profileid == self.config["profileid"]:
                self.config["profileid"] = ""
                self.showLastMatch(force=True)
                return
        self.config["profileid"] = profileid
        self.showLastMatch(force=True)

    def setHuntLocation(self, reset=False):
        if reset:
            self.config["path"] = ""
        while(not exists(config["path"] + "/user/profiles/default/attributes.xml")):
            path = QFileDialog.getExistingDirectory(self, "Select Hunt Showdown Directory", "", QFileDialog.Option.ShowDirsOnly)
            config["path"] = path

    def showLastMatch(self, force=False):
        filename = config["path"] + "/user/profiles/default/attributes.xml"
        modtime = os.path.getmtime(filename)
        if modtime == self.lastmodified and not force:
            return
        self.lastmodified = modtime
        parsed = attributeParser.parse(config)
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Team", "Name", "MMR", "Downed By Me", "Killed By Me", "Downed Me", "Killed Me","profileid"])
        
        #find match hash to avoid duplicates
        put_into_log = True
        hashstr = '|'.join([str(player[2]['profileid'])+str(player[2]["mmr"]) for player in sorted(parsed,key = lambda p: int(p[2]["profileid"]))])
        hash = hashlib.md5(hashstr.encode()).hexdigest()
        if "lastmatchhash" in self.config and hash == self.config["lastmatchhash"]:
            put_into_log = False
        else:
            self.config["lastmatchhash"] = hash
        for player in parsed:
            #self.mmr_table.insert(parent='', index='end', tags=tags, values=(player[0], player[2]['blood_line_name'], player[2]['mmr'], player[2]['downedbyme'], player[2]['killedbyme'], player[2]['downedme'], player[2]['killedme']))
            data = [str(player[0]), player[2]['blood_line_name'], player[2]['mmr'], player[2]['downedbyme'], player[2]['killedbyme'], player[2]['downedme'], player[2]['killedme'],player[2]['profileid']]
            data = [QtGui.QStandardItem(x) for x in data]
            if(put_into_log):
                self.handlePlayerMMR(player[2]['blood_line_name'],player[2]['profileid'],player[2]["mmr"])
            if player[2]["profileid"] == self.config["profileid"]:
                for x in data:
                    x.setBackground(QtGui.QColorConstants.Svg.lightgreen)
            elif player[2]["isOwnTeam"]:
                for x in data:
                    x.setBackground(QtGui.QColorConstants.Svg.lightblue)
            elif player[2]["killedme"] == "1":
                for x in data:
                    x.setBackground(QtGui.QColorConstants.Svg.rosybrown)
            elif player[2]["downedme"] == "1":
                for x in data:
                    x.setBackground(QtGui.QColorConstants.Svg.wheat)
            self.model.insertRow(self.model.rowCount(),data)   
        self.tableview.resizeColumnsToContents()
        self.tableview.updateGeometry()
    def handlePlayerMMR(self, profileid, name, mmr):
        if not exists("mmr_log.csv"):
            with open("mmr_", "w") as outfile:
                outfile.write("")
        with open("mmr_log.csv", "a", encoding="utf8") as outfile:
            outfile.write(f"{profileid},{name},{str(mmr)},{time()}" + "\n")
    def plot(self):
        if(not exists("mmr_log.csv") or config["lastmatchhash"] == "" or config["profileid"] == ""):
            error =  QtWidgets.QDialog(self)
            error.setWindowTitle("Error")
            error.layout = QtWidgets.QVBoxLayout()
            error.label = QtWidgets.QLabel("Highlight (double click) a player to view their MMR history")
            error.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            error.buttonBox.accepted.connect(error.accept)
            error.layout.addWidget(error.label)
            error.layout.addWidget(error.buttonBox)
            error.setLayout(error.layout)
            error.exec()
        else:
            self.plotwindow = plot.GraphWindow(self.config)
            self.plotwindow.show()
    def resetHistory(self):
        with open("mmr_log.csv", "w") as outfile:
            outfile.write("")
        config["lastmatchhash"] = ""
        self.showLastMatch(force=True)

def gui(config):
    app = QApplication([])
    window = App(config)
    window.show()
    app.exec()

if __name__ == "__main__":
    import sys
    config = Config()
    if(config["path"] == None):
        config["path"] = "C:/Program Files (x86)/Steam/steamapps/common/Hunt Showdown"
    gui(config)