import sys
import csv
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSlot
from configparser import ConfigParser
co = ConfigParser()
class channels:
    chnnls = []
    def add(self,row):
        itm = {'channel':row[0],'name':row[1],'type':'tv'}
        if int(row[0]) >= 1000:
            itm['type'] = 'radio'
        self.chnnls.append(itm)
c = channels()
class append(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("./qtui/importcsv_s1.ui", self)
        self.pushButton.clicked.connect(self.open_dialog)
    @pyqtSlot()
    def open_dialog(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(
        self,
        "Open File",
        "",
        "CSV Files (*.csv);; Text Files (*.text)",
        )
        self.lineEdit.setText(fname[0])
        self.csvfile = fname[0]
        self.pushButton_2.setEnabled(True)
        self.pushButton_2.clicked.connect(self.step2)
    def step2(self):
        self.__import()
        uic.loadUi("./qtui/importcsv_s2.ui", self)
        self.btnback.clicked.connect(self.step1)
        tb = self.tableWidget
        it = QtWidgets.QTableWidgetItem
        tb.setColumnCount(3)
        tb.setHorizontalHeaderLabels(("Channel No.","Name","Type"))
        tb.setRowCount(len(c.chnnls))
        o = 0
        for itm in c.chnnls:
            tb.setItem(o,0, it(itm['channel']))
            tb.setItem(o,1, it(itm['name']))
            tb.setItem(o,2, it(itm['type']))
            o += 1
        self.btnimp.setEnabled(True)
        self.btnimp.clicked.connect(self.finalize)
    def step1(self):
        uic.loadUi("./qtui/importcsv_s1.ui", self)
        self.lineEdit.setText(self.csvfile)
        self.pushButton_2.setEnabled(True)
        self.pushButton_2.clicked.connect(self.step2)
    def finalize(self):
        uic.loadUi("./qtui/importcsv_s3.ui", self)
        cnt = {}
        cnt[0] = 0
        cnt[1] = 0
        cnt[2] = 0
        for itm in c.chnnls:
            co[itm['channel']] = itm
            cnt[0] += 1
            if itm['type']=='radio':
                cnt[2] += 1
            elif itm['type']=='tv':
                cnt[1] += 1
        with open('channels.ini', 'w') as conf:
            co.write(conf)  
        self.successlabel.setText('Imported %s channels. %s TV channels and %s radio channels.'%(cnt[0],cnt[1],cnt[2]))
        self.btnclose.clicked.connect(QtWidgets.QApplication.instance().quit)

    def __import(self):
        c.chnnls = []
        with open(self.csvfile,'r',newline='\n') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=";")
            next(spamreader)
            for row in spamreader:
                c.add(row)
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = append()
    win.show()
    sys.exit(app.exec())

