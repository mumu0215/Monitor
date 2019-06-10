# _*_ coding=utf-8 _*_
from PyQt5 import QtCore
import socket,threading,json
class communicateS(QtCore.QThread):
    signal = QtCore.pyqtSignal(list)
    signal2=QtCore.pyqtSignal(list)
    signal3=QtCore.pyqtSignal(str)
    signal4=QtCore.pyqtSignal(list)
    signal5=QtCore.pyqtSignal(str)
    signal6=QtCore.pyqtSignal(list)
    def __init__(self, parent=None):
        super(communicateS, self).__init__(parent)
        self.info=''
        # self.ip=''
        self.ip=self.get_host_ip()
        self.addr_list=[]
        self.serverSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    def __del__(self):
        del self.addr_list
        self.serverSocket.close()
        self.terminate()
        self.wait()

    def get_host_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def printIP(self):
        if self.ip!='':
            return self.ip
        else:return False

    def run(self):
        self.ip=self.get_host_ip()
        self.serverSocket.bind((self.ip,9999))
        self.serverSocket.listen(5)
        while True:
            sock,addr=self.serverSocket.accept()
            self.addr_list.append([sock,addr])
            print('get in %s:%s'%addr)
            new_t=threading.Thread(target=self.getin,args=(sock,addr))
            new_t.start()

    def set_info(self,info):
        self.info=info

    def requestHistory(self,dest):
        for i in self.addr_list:
            if dest==i[1][0]:
                msg=[{'code':77}]         #获取历史记录
                msg_json=json.dumps(msg)
                i[0].send(msg_json.encode())

    def requestKey(self,dest):
        for i in self.addr_list:
            if dest==i[1][0]:
                msg=[{'code':66}]            #获取键盘记录
                msg_json=json.dumps(msg)
                i[0].send(msg_json.encode())

    def check_cap(self,dest):
        for i in self.addr_list:
            if dest==i[1][0]:
                msg=[{'code':88}]
                msg_json=json.dumps(msg)
                i[0].send(msg_json.encode())
    def stop_cap(self,dest):
        for i in self.addr_list:
            if dest==i[1][0]:
                msg = [{'code': 55}]
                msg_json = json.dumps(msg)
                i[0].send(msg_json.encode())

    #通信交流格式[{'code':1,'msg':''}] json
    #code 1:登录 内容：账户 系统 时间 host info time
    #     2:登出 内容：账户 时间
    def getin(self,sock,addr):
        import time
        date_info=QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate)
        while True:
            re_msg=sock.recv(4096).decode('utf-8')
            msg=json.loads(re_msg,strict=False)
            # print(msg)
            if msg[0]['code']==1:
                self.signal.emit([msg[0]['host'],addr[0],msg[0]['info'],date_info+' '+msg[0]['time']])
                with open('record.log','a') as f:
                    f.write(date_info+' '+msg[0]['time']+'    '+msg[0]['host']+'  login\n')
            elif msg[0]['code']==2:
                self.signal2.emit([msg[0]['host'],addr[0],msg[0]['IO'],msg[0]['time']])
                with open('record.log','a') as f:
                    f.write('   '+date_info+' '+msg[0]['time']+'    '+msg[0]['host']+'  quit\n')
                break
            elif msg[0]['code']==100:
                self.signal3.emit(msg[0]['id'])
                time.sleep(1)
                if self.info!='' and msg[0]['password_m5']==self.info:
                    back_msg=[{'code':99}]
                    back_msg_json=json.dumps(back_msg)
                    sock.send(back_msg_json.encode())
                    self.info=''
                else:
                    self.info=''
                    back_msg=[{'code':101}]
                    back_msg_json=json.dumps(back_msg)
                    sock.send(back_msg_json.encode())
            elif msg[0]['code']==233:
                self.signal4.emit(msg[0]['net'])
            elif msg[0]['code']==67:
                self.signal5.emit(msg[0]['text'])
            elif msg[0]['code']==78:
                self.signal6.emit([msg[0]['history'],msg[0]['cnkey'],msg[0]['enkey']])
            else:
                print('err code!')
        sock.close()

