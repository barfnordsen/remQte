from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6.QtCore import *

from ssdpy import SSDPClient
from netifaces import interfaces, ifaddresses, AF_INET
import time
import traceback, sys
import xml.etree.ElementTree as ET
import urllib
from urllib import request
import re
from configparser import ConfigParser
co = ConfigParser()
class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):

        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  
        finally:
            self.signals.finished.emit()

class networks:
    ifs = {}
    def get(self):
        for iface in interfaces():
            ip = ifaddresses(iface).setdefault(AF_INET, [{'addr':'No IP addr','netmask':'no netmask'}] )[0]['addr']
            netmask = ifaddresses(iface).setdefault(AF_INET, [{'addr':'No IP addr','netmask':'no netmask'}])[0]['netmask']
            if ip != '127.0.0.1' and ip != 'No IP addr':
                net = ip.split('.')
                net = self.getnetwork(ip)
                self.ifs[ip] = "%s / %s"%(net,netmask)
    def dlna(self,address):
        self.client = SSDPClient(address=address)
        self.data = self.client.m_search(st='urn:schemas-upnp-org:device:MediaRenderer:1')
        return self.data
    def set(self,event,ip):
        self.ifs[ip] = event
    def getnetwork(self,ip):
        ip = ip.split('.')
        return "%s.%s.%s.0"%(ip[0], ip[1], ip[2])


class MainWindow(QMainWindow):

    nett = networks()
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.counter = 0
        uic.loadUi("./qtui/main_start.ui", self)
        self.btnscan.clicked.connect(self.network)


        self.show()
        
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timeloop)
        self.timer.start()
    def network(self):
        uic.loadUi("./qtui/main_scan_choose_nets.ui", self)
        self.progressBar.setVisible(False)
        self.cb = {}
        self.nett.get()
        for i in self.nett.ifs:
            self.cb[i] = QCheckBox(self.nett.ifs[i], self)
            self.cb[i].setChecked(True)
            self.cb[i].value = i
            self.nett.set(True,i)
            self.cb[i].toggled.connect(CB(self.nett.set,i))
            self.verticalLayout_3.addWidget(self.cb[i])
        self.btnscan.clicked.connect(self.doscan)
    def doscan(self, ret):
        self.lblHead.setText("remQte >> scan for active TVs")
        self.lblHeadline.setText("Scannning ready to start")
        self.lblDesc.setText("click [start scan] to start scanning selected networks for attached Samsung TVs.")
        self.btnscan.setText("s&tart scan")
        self.lblSubhl.setText("Progress:")
        self.progressBar.setVisible(True)
        for i in self.cb:
            self.cb[i].toggled.disconnect()
            self.cb[i].close()
            self.verticalLayout_3.removeWidget(self.cb[i])
        self.btnscan.clicked.disconnect()
        self.btnscan.setEnabled(False)
        self.scan(True)
    def scan(self, ret ):
        self.lblHead.setText("remQte >> scanning in progress")
        self.lblHeadline.setText("Scannning ...")
        self.lblDesc.setText("")
        worker = Worker(self.ssdp)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

        self.threadpool.start(worker)
    def ssdp(self, progress_callback):
        pg = 0;
        ips = {}
        for i in self.nett.ifs:
            self.scanning = i;
            pg +=10
            progress_callback.emit(pg)
            if self.nett.ifs[i] == True:
                client = SSDPClient(address=i)
                self.data = client.m_search(st='urn:schemas-upnp-org:device:MediaRenderer:1')
                for x in self.data:
                    ip = x['location'].split('/')[2].split(':')[0]
                    ips[ip] = x['location'] 
            pg += 30
            progress_callback.emit(pg)
        u = urllib
        self.tvsfound = {}
        tvs = {}
        pgup = round(20/len(ips))
        for k in ips:
            tvs[k] = {}
            xml = u.request.urlopen(ips[k])
            xml = xml.read()
            xml = ET.fromstring(xml)
            srch = ('friendlyName','modelName','ProductCap','manufacturer')
            for child in xml[1]:
                key = child.tag.split('}')[1]
                if key in srch:
                    tvs[k][key] = child.text
                    if key == 'ProductCap':
                        m = re.search('Y[2][0][0-9][0-9]',child.text)
                        year = m.group(0).split('Y')[1]
                        if int(year)<=2015:
                            tvs[k]['incompatible'] = '%s older than 2016, not supported'%m.group(0)
                    if key == 'manufacturer' and child.text != 'Samsung Electronics':
                        tvs[k]['incompatible'] = 'Wrong manufacturer: %s'%child.text
            pg += pgup
            progress_callback.emit(pg)
        self.tvsfound = tvs
            

    def progress_fn(self, n):
        self.lblDesc.setText("scanning %s ..."%self.nett.getnetwork(self.scanning))
        self.progressBar.setValue(n)


    def print_output(self, s):
        print(s)

    def thread_complete(self):
        uic.loadUi("./qtui/main_scan_nets.ui", self)
        tb = self.tableWidget
        it = QTableWidgetItem
        tb.setColumnCount(3)
        tb.setColumnWidth(0, 10);
        tb.setColumnWidth(1, 230);
        tb.setColumnWidth(2, 65);
        tb.setHorizontalHeaderLabels(("cb","TV","supported"))
        tb.setRowCount(len(self.tvsfound))
        print("THREAD COMPLETE!")
        o = 0
        cbox = {}
        self.importtvs = {}
        for itm in self.tvsfound:
            i = self.tvsfound[itm]
#            self.importtvs[itm] = True
            cbox[itm] = {}
            cbox[itm]['Qcb'] = QCheckBox()
            cbox[itm]['Qcb'].toggled.connect(CB(self.togglecb,itm))
            cbox[itm]['Qcb'].setStyleSheet("margin:0 0 0 12")
            cbox[itm]['Qcb'].setChecked(True)
#            cbox[itm].config(padx=5)
            tb.setCellWidget(o,0, cbox[itm]['Qcb'])
            tb.setItem(o,1, it("%s (%s)"%(i['friendlyName'],itm)))
            comp = 'YES'
            try:
                if i['incompatible']:
#                    self.importtvs[itm]=False
                    comp = 'NO'
                    cbox[itm]['Qcb'].setEnabled(False)
                    cbox[itm]['Qcb'].setChecked(False)
            except:
                print('jibbet nich')
            tb.setItem(o,2, it(comp))
#           tb.setItem(o,2, it(itm['type']))
            o += 1
        #self.btnscan.clicked.disconnect()
        self.btnscan.clicked.connect(self.importTV)
    def importTV(self):
        print('btnclicked')
        for i in self.importtvs:
            print(i,self.importtvs[i])
            if self.importtvs[i] == True:
                tvs = self.tvsfound
                tvs[i]['ip'] = i
                co[i] = tvs[i]

        with open('tvs.ini', 'w') as conf:
            co.write(conf)

        uic.loadUi("./qtui/remote.ui",self)
    def togglecb(self,checkstate,itm):
        self.importtvs[itm] = checkstate

    def timeloop(self):
        self.counter +=1
        if self.counter%60==0:
            print("Counter: %d" % self.counter)
class CB:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def __call__(self,event):
        self.func(event,*self.args, **self.kwargs)

app = QApplication([])
window = MainWindow()
app.exec()

