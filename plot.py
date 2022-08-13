from PyQt6.QtWidgets import QMainWindow
import PyQt6.QtCore as QtCore
import PyQt6.QtWidgets as QtWidgets
import PyQt6.QtGui as QtGui
import PyQt6.QtCharts as QtCharts

import time as time

class GraphWindow(QMainWindow):
    def __init__(self,config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Graph")
        self.chart = QtCharts.QChart()
        self.chartview = QtCharts.QChartView(self.chart)
        self.series = QtCharts.QLineSeries()
        self.lastplayernames = {}
        with open("mmr_log.csv", "r",encoding="utf8") as f:
            for line in f:
                try:
                    line = [x.strip() for x in line.split(",")]
                    self.lastplayernames[line[1]] = line[0]
                    if(line[1] != self.config["profileid"]):
                        continue
                    mmr, time = int(line[2]), int(float(line[3])*1000)
                    self.series.append(time, mmr)
                except Exception as e:
                    print(e)
                
        self.series.setName("MMR over time for " + self.lastplayernames[self.config["profileid"]])
        self.chart.addSeries(self.series)
        axisX = QtCharts.QDateTimeAxis()
        axisX.setTickCount(10)
        axisX.setFormat("dd/MM/yyyy")
        self.chart.addAxis(axisX, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.series.attachAxis(axisX)
        axisY = QtCharts.QValueAxis()
        axisY.setLabelFormat("%i")
        self.chart.addAxis(axisY, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(axisY)
        self.setCentralWidget(self.chartview)
    def sizeHint(self) -> QtCore.QSize:
        supersizehint = super().sizeHint()
        return QtCore.QSize(max(1600,supersizehint.width()), max(800,supersizehint.height()))

