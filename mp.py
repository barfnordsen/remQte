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
            ip = ifaddresses(iface).setdefault(AF_INET, [{'addr':'No IP addr'}] )[0]['addr']
            netmask = ifaddresses(iface).setdefault(AF_INET, [{'addr':'No IP addr'}] )[0]['netmask']
            if ip != '127.0.0.1':
                net = ip.split('.')
                net = '%s.%s.%s.0'%(net[0],net[1],net[2])
                print(net)
                self.ifs[ip] = "%s / %s"%(net,netmask)
        print(self.ifs)
    def dlna(self,address):
        self.client = SSDPClient(address=address)
        self.data = self.client.m_search(st='urn:schemas-upnp-org:device:MediaRenderer:1')
        return self.data
    def set(self,event,ip):
        self.ifs[ip] = event
        print(self.ifs)
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
        worker = Worker(self.ssdp) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(worker)
#        for i in nett.ifs:
##            ssdp.append({'ip':i})
#            print(i, nett.ifs[i])
#            state = nett.ifs[i]
#            if state == True:
#                print('checked', i)
#                self.lblDesc.setText("scanning %s ..."%nett.getnetwork(i))
#                nwobj = {'ip':i,'data':nett.dlna(i)}
#                self.lblDesc.setText("scanning %s ...\t[DONE]"%nett.getnetwork(i))
#                pg +=40
#                self.progressBar.setValue(pg)
#                ssdp.append(nwobj)
#            elif state == False:
#                pg += 40
#                self.progressBar.setValue(pg)
#            self.update()
#        dbug(ssdp)
    def ssdp(self, progress_callback):
        pg = 0;
        ips = {}
        for i in self.nett.ifs:
            self.scanning = i;
            pg +=10
            progress_callback.emit(pg)
            if self.nett.ifs[i] == True:
                client = SSDPClient(address=i)
#                print(dir(client.m_search))
                self.data = client.m_search(st='urn:schemas-upnp-org:device:MediaRenderer:1')
 #               print(len(self.data),self.data)
                for x in self.data:
                    ip = x['location'].split('/')[2].split(':')[0]
                    ips[ip] = x['location'] 
            pg += 30
            progress_callback.emit(pg)
        u = urllib
        self.tvsfound = {}
        print(len(ips))
        tvs = {}
        pgup = round(20/len(ips))
        for k in ips:
            tvs[k] = {}
            print(k)
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
        print(tvs)
            

    def progress_fn(self, n):
        self.lblDesc.setText("scanning %s ..."%self.scanning)
        self.progressBar.setValue(n)
        print("%s done" % n)

    def execute_this_fn(self, progress_callback):
        for n in range(1, 6):
            time.sleep(1)
            mul = (n*100)
            div = int(mul/5)
            print(n,mul,div)
            progress_callback.emit(div)

        return "Done."

    def print_output(self, s):
        print(s)

    def thread_complete(self):
        uic.loadUi("./qtui/main_scan_nets.ui", self)
        tb = self.tableWidget
        it = QTableWidgetItem
        tb.setColumnCount(2)
        tb.setHorizontalHeaderLabels(("TV","compatible"))
        tb.setRowCount(len(self.tvsfound))
        print("THREAD COMPLETE!")
        o = 0
        for itm in self.tvsfound:
            i = self.tvsfound[itm]
            tb.setItem(o,0, it("%s (%s)"%(i['friendlyName'],itm)))
            comp = 'YES'
            try:
                if i['incompatible']:
                    comp = 'NO'
            except:
                print('jibbet nich')
            tb.setItem(o,1, it(comp))
            print(dir(tb.currentRow()))
#           tb.setItem(o,2, it(itm['type']))
            o += 1

    def oh_no(self):
    # Pass the function to execute
        worker = Worker(self.execute_this_fn) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(worker)


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
class networks:
    ifs = {}
    def get(self):
        for iface in interfaces():
            ip = ifaddresses(iface).setdefault(AF_INET, [{'addr':'No IP addr'}] )[0]['addr']
            netmask = ifaddresses(iface).setdefault(AF_INET, [{'addr':'No IP addr'}] )[0]['netmask']
            if ip != '127.0.0.1':
                net = ip.split('.')
                net = '%s.%s.%s.0'%(net[0],net[1],net[2])
                print(net)
                self.ifs[ip] = "%s / %s"%(net,netmask)
        print(self.ifs)
    def dlna(self,address):
        self.client = SSDPClient(address=address)
        self.data = self.client.m_search(st='urn:schemas-upnp-org:device:MediaRenderer:1')
        return self.data
#        for i in self.data:
 #           print(i['location'])
    def set(self,event,ip):
        self.ifs[ip] = event
        print(self.ifs)
#        print(self.data)
    def getnetwork(self,ip):
        ip = ip.split('.')
        return "%s.%s.%s.0"%(ip[0], ip[1], ip[2])
app = QApplication([])
window = MainWindow()
app.exec()

