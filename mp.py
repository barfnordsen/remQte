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
from subprocess import check_output
from samsungtvws import SamsungTVWS
co = ConfigParser()
ini_tvs = ConfigParser()
ini_tvs.read("tvs.ini")
ini_chn = ConfigParser()
ini_chn.read("channels.ini")
class pseudo:
    pass

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

class stvws:
    port = 8002
    name = 'remQte'
    default = '192.168.2.134'
    cnf = {}
    def __init__(self):
    
        cnf = {}
        ini_tvs.read('tvs.ini')
        for i in ini_tvs.sections():
            c = ini_tvs[i]
            cnf[i] = pseudo()
            cnf[i].src = c['src']
            cnf[i].dst = c['dst']
            cnf[i].mac = c['mac']
            cnf[i].token = c['token']
            cnf[i].friendlyName = c['friendlyName']
            cnf[i].manufacturer = c['manufacturer']
            cnf[i].modelname = c['modelname']
            cnf[i].productcap = c['productcap']
            cnf[i].port = self.port
            cnf[i].name = self.name
            cnf[i].tv = SamsungTVWS(c['dst'],port=self.port,token=c['token'],name=self.name)
        self.cnf = cnf
        self.setDefault(i)

        print(len(cnf))
        
    def setDefault(self,ip):
        print(self.cnf)
        self.default = ip
        self.rc = self.cnf[ip]
    def register(self):
        t = self.rc.tv
        t.open()
        if t.token != self.rc.token:
            print('token changed.')
            self.__updToken(t.token)
        print(t.token)
        t.close()
    def __updToken(self,token):
        self.rc.token = token
        self.cnf[self.default].token = token
        ini_tvs[self.default]['token'] = token
        with open('tvs.ini', 'w') as conf:
            ini_tvs.write(conf)
    def push(self, btn, val=""):
        t = self.rc.tv
        t.open()
        if t.token != self.rc.token:
            print('new token')
            self.__updToken(t.token)
            t.close()
            self.push(btn,val)
        t.send_key(btn)
        t.close()
    def pwr(self):
        self.push('KEY_POWER')
    def menu(self):
        self.push('KEY_MENU')
    def smarthub(self):
        self.push('KEY_HOME')
    def source(self):
        self.push('KEY_SOURCE')
    def chup(self):
        self.push('KEY_CHUP')
    def chdw(self):
        self.push('KEY_CHDOWN')
    def guide(self):
        self.push('KEY_GUIDE')
    def chlist(self):
        self.push('KEY_CH_LIST')
    def voup(self):
        self.push('KEY_VOLUP')
    def vodw(self):
        self.push('KEY_VOLDOWN')
    def mute(self):
        self.push('KEY_MUTE')
    def up(self):
        self.push('KEY_UP')
    def down(self):
        self.push('KEY_DOWN')
    def left(self):
        self.push('KEY_LEFT')
    def right(self):
        self.push('KEY_RIGHT')
    def enter(self):
        self.push('KEY_ENTER')
    def tools(self):
        self.push('KEY_TOOLS')
    def info(self):
        self.push('KEY_INFO')
    def rtrn(self):
        self.push('KEY_RETURN')
    def exit(self):
        self.push('KEY_EXIT')
    def rwd(self):
        self.push('KEY_REWIND')
    def play(self):
        self.push('KEY_PLAY')
    def fwd(self):
        self.push('KEY_FF')
    def stop(self):
        self.push('KEY_STOP')
    def pause(self):
        self.push('KEY_PAUSE')
    def rec(self):
        self.push('KEY_REC')
    def red(self):
        self.push('KEY_RED')
    def green(self):
        self.push('KEY_GREEN')
    def yellow(self):
        self.push('KEY_YELLOW')
    def blue(self):
        self.push('KEY_BLUE')
    def digit(self,d):
        d = str(d)
        self.push('KEY_%s'%d)
    def txt(self):
        self.push('KEY_TXT_MIX')
    def prech(self):
        self.push('KEY_PRECH')
    def channel(self, ch):
        for c in str(ch):
            self.digit(c)
        self.enter()



stv = None
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
    def getmac(self,ip,platform):
        if platform.startswith('win'):
    #    mac_address_validate_pattern = "^([0-9a-f]{2}[:-]){5}([0-9a-f]{2})$"
            stream = check_output(['C:\Windows\System32\ARP.EXE','-g','%s'%ip])
            if 'No ARP Entries Found.' in str(stream):
                st = '00:00:00:00:00:00'
            else:
                st = str(stream).split("\\r\\n")[3].split(' ')[11].replace('-',':')
            return st
        elif platform.startswith('linux'):
            stream = check_output(['/usr/bin/ip','neigh'],text=True)
            lns = stream.split('\n')
            st = '00:00:00:00:00:00'
            for i in lns:
                if ip in i:
                    st = i.split(' ')[4]
            return st
        else:
            return '00:00:00:00:00:00'
    def getnetwork(self,ip):
        ip = ip.split('.')
        return "%s.%s.%s.0"%(ip[0], ip[1], ip[2])


class MainWindow(QMainWindow):
    platform = sys.platform
    print('running on:  %s'%platform)
    nett = networks()
    def __init__(self, *args, **kwargs):
        global stv
        super(MainWindow, self).__init__(*args, **kwargs)

        self.counter = 0
        if len(ini_tvs) == 0:
            uic.loadUi("./qtui/main_start.ui", self)
            self.btnscan.clicked.connect(self.network)
        else:
            stv = stvws()
            uic.loadUi("./qtui/remote.ui", self)

        self.show()
        
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timeloop)
        self.timer.start()
#            self.remote()
    def start(self):
        if len(ini_tvs)>0:
            self.remote()
            
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
                    ips[ip] = pseudo() 
                    ips[ip].location = x['location'] 
                    ips[ip].dst = ip
                    ips[ip].src = i
                    
            pg += 30
            progress_callback.emit(pg)
        u = urllib
        self.tvsfound = {}
        tvs = {}
        pgup = round(20/len(ips))
        for k in ips:
            tvs[k] = {}
            tvs[k]['src'] = ips[k].src
            tvs[k]['dst'] = ips[k].dst
            tvs[k]['mac'] = self.nett.getmac(ips[k].dst,self.platform)
            tvs[k]['token'] = 'remQte'
            tvs[k]['default'] = True
            xml = u.request.urlopen(ips[k].location)
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
        global stv
        for i in self.importtvs:
            if self.importtvs[i] == True:
                tvs = self.tvsfound
                co[i] = tvs[i]

        with open('tvs.ini', 'w') as conf:
            co.write(conf)
            ini_tvs.read('tvs.ini')
        stv = stvws()
        self.remote()
    def remote(s):
        
        uic.loadUi("./qtui/remote.ui",s)
        s.btnpwr.clicked.connect(stv.pwr)
        s.btnsmarthub.clicked.connect(stv.smarthub)
        s.btnsrc.clicked.connect(stv.source)
        s.btnchup.clicked.connect(stv.chup)
        s.btnchdw.clicked.connect(stv.chdw)
        s.btnguide.clicked.connect(stv.guide)
        s.btnchlist.clicked.connect(stv.chlist)
        s.btnvoup.clicked.connect(stv.voup)
        s.btnvodw.clicked.connect(stv.vodw)
        s.btnmute.clicked.connect(stv.mute)
        s.btntools.clicked.connect(stv.tools)
        s.btninfo.clicked.connect(stv.info)
        s.btnreturn.clicked.connect(stv.rtrn)
        s.btnexit.clicked.connect(stv.exit)
        s.btnup.clicked.connect(stv.up)
        s.btndown.clicked.connect(stv.down)
        s.btnleft.clicked.connect(stv.left)
        s.btnright.clicked.connect(stv.right)
        s.btnok.clicked.connect(stv.enter)
        s.btnrwd.clicked.connect(stv.rwd)
        s.btnplay.clicked.connect(stv.play)
        s.btnfwd.clicked.connect(stv.fwd)
        s.btnstop.clicked.connect(stv.stop)
        s.btnpause.clicked.connect(stv.pause)
        s.btnrec.clicked.connect(stv.rec)
        s.btnred.clicked.connect(stv.red)
        s.btngreen.clicked.connect(stv.green)
        s.btnyellow.clicked.connect(stv.yellow)
        s.btnblue.clicked.connect(stv.blue)
        s.btn0.clicked.connect(CB(stv.digit,0))
        s.btn1.clicked.connect(CB(stv.digit,1))
        s.btn2.clicked.connect(CB(stv.digit,2))
        s.btn3.clicked.connect(CB(stv.digit,3))
        s.btn4.clicked.connect(CB(stv.digit,4))
        s.btn5.clicked.connect(CB(stv.digit,5))
        s.btn6.clicked.connect(CB(stv.digit,6))
        s.btn7.clicked.connect(CB(stv.digit,7))
        s.btn8.clicked.connect(CB(stv.digit,8))
        s.btn9.clicked.connect(CB(stv.digit,9))
        s.btntxt.clicked.connect(stv.txt)
        s.btnpre.clicked.connect(stv.prech)
        arial7 = QFont('Arial',7)
        s.comboBox.setFont(arial7)
        for i in ini_chn.sections():
#            print("ini_chn[i]['type']",ini_chn[i]['name'],i)
            s.comboBox.addItem(ini_chn[i]['name'], userData=i)
        s.comboBox.currentIndexChanged.connect(s.pr)
#        s.comboBox.styleSheet = 'font: 75 7 "Arial";'
#        print("itemData",s.comboBox.itemData(0))

    def pr(s,i):
        stv.channel(s.comboBox.itemData(i))
        #print('hier ->>>>>>>%s'%s.comboBox.itemData(i))
        #return True




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
t = QTimer()
t.singleShot(1000,window.start)
app.exec()
