import zipfile, io, os
import sqlite3, codecs
import tempfile
tmpdir = tempfile.gettempdir()+'\\remQte\\'
if not os.path.exists(tmpdir):
    os.makedirs(tmpdir)
#print(tmpdir)
class channels:
    chnnls = []
    def add(self,row):
        itm = {'channel':row[0],'name':row[1],'type':'tv'}
        if int(row[0]) >= 1000:
            itm['type'] = 'radio'
        if int(row[0]) >= 4000:
            itm['type'] = 'iptv'
        if int(row[0]) >= 10000:
            itm['type'] = 'data'
        self.chnnls.append(itm)
chs = channels()
class sqschnell:
    def __init__(self,file,filename):
        self.con = sqlite3.connect(file)
        self.cur = self.con.cursor()
        self.file = file
        self.fname = filename
    def inspect(self):
        res = self.cur.execute("select name from sqlite_master where type='table' and name ='SRV'")
        result = res.fetchone()
        if result:
            res = self.cur.execute("select srvName from SRV")
            result = res.fetchone()
            if isinstance(result[0],bytes):
                res = self.cur.execute("select major, srvName from SRV order by major")
                results = res.fetchall()
                for i in results:
                    row = []
                    name = i[1].decode('iso-8859-1')
                    row.append(i[0])
                    typ = 'tv'
                    name_clean = ''
                    for c in str(name):
                        if c.isdigit() or c.isalpha() or c in (' ','(',')','.'):
                            name_clean += c
                    row.append(name_clean)
                    chs.add(row)

            else:
                res = self.cur.execute("select major, srvName from SRV order by major")
                results = res.fetchall()
                for i in results:
                    chs.add(i)
        self.con.close()
class readzip:
    def __init__(self,zipf):
        self.zipf = zipf
    def importdata(self):
        with zipfile.ZipFile(self.zipf) as myzip:
            f = {}
            fo ={}
            sql = {}
            for file in myzip.namelist():
                if file.endswith('.xml'):
                    continue
                myzip.extract(file,tmpdir)
        for fn in os.listdir(tmpdir):
            f = os.path.join(tmpdir, fn)
            if os.path.isfile(f):
                #print("processing: %s"%f)
                sql = sqschnell(f,fn)
                sql.inspect()
                os.remove(f)
        return chs.chnnls
