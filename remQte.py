# remQte.py
"""
python script to remote control some samsung smart tvs. uses samsungtvws for communiction. supports tv models newer than 2016.
"""
import sys, time
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSlot
from configparser import ConfigParser
from netifaces import interfaces, ifaddresses, AF_INET
from ssdpy import SSDPClient
from multiprocessing import Process, freeze_support
co = ConfigParser()
def dbug(obj):
    d = dir(obj)
    for i in d:
        print(i)
class CB:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def __call__(self,event):
        self.func(event,*self.args, **self.kwargs)

class qtobj(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("./qtui/main_start.ui", self)
        self.btnscan.clicked.connect(self.network)
    def network(self):
        uic.loadUi("./qtui/main_scan_choose_nets.ui", self)
        self.progressBar.setVisible(False)
        self.cb = {}
        for i in nett.ifs:
            self.cb[i] = QtWidgets.QCheckBox(nett.ifs[i], self)
            self.cb[i].setChecked(True)
            self.cb[i].value = i
            nett.set(True,i)
            self.cb[i].toggled.connect(CB(nett.set,i))
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
        self.btnscan.clicked.connect(self.scanresults)
    def scanresults(self, ret ):
        self.lblHead.setText("remQte >> scanning in progress")
        self.lblHeadline.setText("Scannning ...")
        self.lblDesc.setText("")
        pg = 0
        ssdp = []
        freeze_support()
        p = Process(target=scn,args=(nett,'self.lblDesc')).start()

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
def scn(nett, lbl):
        ssdp = []
        for i in nett.ifs:
#            ssdp.append({'ip':i})
            print(i, nett.ifs[i])
            state = nett.ifs[i]
            if state == True:
                print('checked', i)
#                lbl.setText("scanning %s ..."%nett.getnetwork(i))
                nwobj = {'ip':i,'data':nett.dlna(i)}
 #               lbl.setText("scanning %s ...\t[DONE]"%nett.getnetwork(i))
                pg +=40
                self.progressBar.setValue(pg)
                ssdp.append(nwobj)
            elif state == False:
                pg += 40
                self.progressBar.setValue(pg)
            self.update()
        dbug(ssdp)

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
nett = networks()
nett.get()
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = qtobj()
    win.show()
    sys.exit(app.exec())

