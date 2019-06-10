# _*_ coding=utf-8 _*_
from admin import Ui_MainWindow

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton,QHBoxLayout, QMessageBox,QLineEdit,QTableWidgetItem,QHeaderView
from PyQt5.QtGui import QPalette
from PyQt5 import QtCore
from scapy.all import *
from communicate import communicateS
from net import monitorNet
import sys,mysql.connector,time
import pyqtgraph as pg

class threadwork(QtCore.QThread):
    signal=QtCore.pyqtSignal(list)
    signal1=QtCore.pyqtSignal(list)
    def __init__(self,hostIP,addr,port, parent=None):
        super(threadwork, self).__init__(parent)
        self.hostIP=hostIP
        self.addr=addr
        self.port=port
        self.count=[0,0,0] #tcp,udp,all
        self.timeclock=None

    def run(self):
        port_str = ''
        if len(self.port) > 0:
            for i in range(len(self.port)):
                port_str += 'port %s or ' % self.port[i]
        else:
            pass
        port_str = '(' + port_str.rstrip('or ') + ')' if len(port_str) > 0 else ''
        if self.addr == 'None' and self.hostIP!=False:
            netaddr=self.hostIP.split('.')
            filter_str = 'src net %s.%s.%s'%(netaddr[0],netaddr[1],netaddr[2])
        else:
            filter_str = 'src host ' + self.addr.split(':')[1]
        all_str = filter_str + ' and ' + port_str if len(port_str) > 0 else filter_str
        self.timeclock=time.time()
        while True:
            if int(time.time()-self.timeclock)>10:
                self.signal1.emit(self.count)
                self.timeclock=time.time()
                self.count=[0,0,0]
            packet = sniff(filter=all_str, count=1)
            self.count[2]+=1
            if packet[0].haslayer('TCP') or packet[0].haslayer('UDP'):
                if packet[0].haslayer('TCP'):
                    proto='TCP'
                    self.count[0]+=1
                else:
                    proto='UDP'
                    self.count[1]+=1
                out_list = []
                out_list.append(str(packet[0][IP].src) + ':' + str(packet[0][IP].payload.sport))
                out_list.append(str(packet[0][IP].dst) + ':' + str(packet[0][IP].payload.dport))
                out_list.append(QtCore.QTime.currentTime().toString(QtCore.Qt.DefaultLocaleLongDate))
                out_list.append(proto)
                self.signal.emit(out_list)
                del out_list

    def __del__(self):
        self.terminate()
        self.wait()

class MyAdmin(QMainWindow,Ui_MainWindow):
    signal=QtCore.pyqtSignal(str)
    signal2=QtCore.pyqtSignal(str)
    def __init__(self):
        super(MyAdmin, self).__init__()
        self.setupUi(self)
        #self.tableWidget.resizeColumnsToContents()
        p=QPalette()
        p.setColor(QPalette.WindowText, QtCore.Qt.red)  # 设置字体颜色
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setPalette(p)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeToContents)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_3.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeToContents)
        self.tableWidget_3.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setWindowTitle('Monitor')

        # Mysql
        self.sql_conn = mysql.connector.connect(user='root', password='linyu17476', database='test')
        self.sql_cursor = self.sql_conn.cursor()
        self.sql_cursor.execute('create table if not exists users(id varchar(20) primary key,password varchar(15),password_m5 varchar(32))')
        self.sql_cursor.execute('create table if not exists loginfo_table(id varchar(20),io_send float,io_receive float,action_time varchar(20))')
        self.sql_cursor.close()
        self.flush()

        self.localmonitor=monitorNet()
        self.localmonitor.signal.connect(self.updatelocal)
        self.localmonitor.start()

        self.localview=pg.GraphicsView()
        self.localplt=pg.PlotItem(title='监控端网络状况')
        self.localplt.setLabel(axis='left', text='网速(kb/s)')
        self.localplt.showGrid(y=True,alpha=0.3)
        self.remoteview=pg.GraphicsView()
        self.remoteplt=pg.PlotItem(title='受控端网络状况')
        self.remoteplt.setLabel(axis='left', text='网速(kb/s)')
        self.remoteplt.showGrid(y=True,alpha=0.3)

        self.localview.setCentralWidget(self.localplt)
        self.remoteview.setCentralWidget(self.remoteplt)
        self.gridLayout.addWidget(self.localview,1,0)
        self.gridLayout.addWidget(self.remoteview,0,0)

        self.xlabel=[]
        self.y1label=[]
        self.y2label=[]

        self.userxlabel=[]
        self.usery1label = []
        self.usery2label = []

        self.connect_sock = communicateS()
        self.connect_sock.signal.connect(self.update_host)
        self.connect_sock.signal2.connect(self.del_host)
        self.connect_sock.signal3.connect(self.check_login)
        self.connect_sock.signal4.connect(self.updateusernet)
        self.connect_sock.signal5.connect(self.keyinView)
        self.connect_sock.signal6.connect(self.viewofHistory)
        self.signal.connect(self.connect_sock.set_info)
        self.signal2.connect(self.connect_sock.check_cap)
        self.connect_sock.start()
        self.hostIP=self.connect_sock.printIP()

    def __del__(self):
        del self.xlabel,self.usery1label,self.usery2label,self.y1label,self.y2label,self.userxlabel,self.hisView,self.newWidget
        self.sql_cursor.close()
        self.sql_conn.close()

    def flush(self):
        self.sql_cursor=self.sql_conn.cursor()
        self.sql_cursor.execute('select id,password from users')
        values=self.sql_cursor.fetchall()
        self.sql_cursor.close()
        self.tableWidget_3.clearContents()
        self.tableWidget_3.setRowCount(0)
        for col_one in values:
            num_row=self.tableWidget_3.rowCount()
            self.tableWidget_3.setRowCount(num_row+1)
            self.tableWidget_3.setItem(num_row,0,QTableWidgetItem(col_one[0]))
            self.tableWidget_3.setItem(num_row,1,QTableWidgetItem(col_one[1]))
            self.tableWidget_3.setItem(num_row,2,QTableWidgetItem(QtCore.QTime.currentTime().toString(QtCore.Qt.DefaultLocaleLongDate)))
            self.tableWidget_3.setCellWidget(num_row,3,self.addbutton(col_one[0]))

    def check_login(self,info):#直接将信号传给通信class，在class中进行判断
        if not self.check_sql(info):
            self.sql_cursor = self.sql_conn.cursor()
            self.sql_cursor.execute('select password_m5 from users where id=%s', (info,))
            back_msg = self.sql_cursor.fetchall()[0][0]
            self.sql_cursor.close()
            self.signal.emit(back_msg)
        else:self.signal.emit('Wrong')


    def update_host(self,one_in):
        num_row=self.tableWidget.rowCount()
        self.tableWidget.setRowCount(num_row+1)
        self.tableWidget.setItem(num_row, 0, QTableWidgetItem(one_in[0]))
        self.tableWidget.setItem(num_row, 1, QTableWidgetItem(one_in[1]))
        self.tableWidget.setItem(num_row, 2, QTableWidgetItem(one_in[2]))
        self.tableWidget.setItem(num_row, 3, QTableWidgetItem(one_in[3]))
        self.comboBox.addItem(one_in[0]+':'+one_in[1])
        self.comboBox_2.addItem(one_in[0]+':'+one_in[1])

    def del_host(self,addr):
        num_row=self.tableWidget.rowCount()
        for i in range(num_row):
            if self.tableWidget.item(i,1).text()==addr[1]:
                self.tableWidget.removeRow(i)
                self.comboBox.removeItem(i+1)
                self.comboBox_2.removeItem(i)
                break
        date_info=QtCore.QDate.currentDate().toString(QtCore.Qt.ISODate)
        self.sql_cursor=self.sql_conn.cursor()
        self.sql_cursor.execute('insert into loginfo_table(id,io_send,io_receive,action_time) values (%s,%s,%s,%s)',
                                [addr[0],addr[2][0],addr[2][1],date_info+' '+addr[3]])
        self.sql_conn.commit()
        self.sql_cursor.close()

    def getView(self,id):
        from UserView import widgetView
        self.sql_cursor=self.sql_conn.cursor()
        self.sql_cursor.execute('select io_send,io_receive,action_time from loginfo_table where id=%s',(id,))
        back_msg=self.sql_cursor.fetchall()
        if back_msg!=[]:
            info = {}
            for i in back_msg:
                datestr = i[2].split(' ')[0]
                if datestr not in info.keys():
                    info[datestr] = [i[0], i[1]]
                else:
                    info[datestr][0], info[datestr][1] = round(info[datestr][0] + i[0], 4), round(
                        info[datestr][1] + i[1], 4)
            plot_tuple = sorted(info.items(), key=lambda f: f[0])
            key_label = [k[0] for k in plot_tuple]
            send_list = [k[1][0] for k in plot_tuple]
            re_list = [k[1][1] for k in plot_tuple]
            xdict = dict(enumerate(key_label))
            stringaxis = pg.AxisItem(orientation='bottom')
            stringaxis.setTicks([xdict.items()])
            self.newWidget = widgetView(id)
            self.newWidget.plotall(stringaxis, xdict, send_list, re_list)
            self.newWidget.show()
        else:QMessageBox.warning(self, "Warning", "No Data!", QMessageBox.Yes)

    def getHistory(self,id):
        num_row=self.tableWidget.rowCount()
        err_count=0
        for i in range(num_row):
            if self.tableWidget.item(i,0).text()==id:
                dest=self.tableWidget.item(i,1).text()
                self.connect_sock.requestHistory(dest)
            else:err_count+=1
        if err_count==num_row:
            QMessageBox.warning(self, "Warning", "Host Not Online!", QMessageBox.Yes)

    def viewofHistory(self,dataIN):
        from HistoryPlot import widgetView
        self.hisView=widgetView()
        self.hisView.plotHistory(dataIN)
        self.hisView.show()

    def addbutton(self,id):
        widget = QWidget()
        Btn = QPushButton('流量')
        Btn.setToolTip('Push to get view')
        Btn.setStyleSheet(''' text-align : center;background-color : NavajoWhite;height : 30px;
                                                 border-style: outset;font : 13px  ''')
        Btn.clicked.connect(lambda:self.getView(id))

        Btn2=QPushButton('历史')
        Btn2.setToolTip('Push to get history')
        Btn2.setStyleSheet(''' text-align : center;background-color : DarkSeaGreen;height : 30px;
                                                 border-style: outset;font : 13px  ''')
        Btn2.clicked.connect(lambda :self.getHistory(id))
        hlayout=QHBoxLayout()
        hlayout.addWidget(Btn)
        hlayout.addWidget(Btn2)
        hlayout.setContentsMargins(5,2,5,2)
        widget.setLayout(hlayout)
        return widget

    def getRate(self,onein):
        tcprate=round(float(onein[0]/onein[2]),4)
        udprate=round(float(onein[1]/onein[2]),4)
        self.label_5.setText('tcp:{:.2%}  udp:{:.2%}   total:{}'.format(tcprate,udprate,onein[2]))

    def startcap(self):
        _translate = QtCore.QCoreApplication.translate
        if self.pushButton.isChecked()==True:
            self.pushButton.setText(_translate("MainWindow", "stop"))
            port_list=self.lineEdit_2.text().split(',') if self.lineEdit_2.text()!='' else []
            self.thread = threadwork(self.hostIP,self.comboBox.currentText(),port_list)
            self.label_3.setText(self.comboBox.currentText())
            dest=self.label_3.text().split(':')[1] if self.label_3.text()!='None' else 'None'
            if dest!='None':
                self.signal2.emit(dest)
            self.thread.signal.connect(self.get_update)
            self.thread.signal1.connect(self.getRate)
            self.thread.start()
        else:
            dest1 = self.label_3.text().split(':')[1] if self.label_3.text() != 'None' else 'None'
            if dest1 != 'None':
                self.connect_sock.stop_cap(dest1)
                self.userxlabel=[];self.usery1label=[];self.usery2label=[]
            self.pushButton.setText(_translate("MainWindow", "start"))
            self.thread.terminate()
            self.thread.wait()

    def clear(self):
        self.tableWidget_2.clearContents()
        self.tableWidget_2.setRowCount(0)

    def get_update(self,one_info):
        num_prerow=self.tableWidget_2.rowCount()
        self.tableWidget_2.setRowCount(num_prerow+1)
        self.tableWidget_2.setItem(num_prerow,0,QTableWidgetItem(one_info[0]))
        self.tableWidget_2.setItem(num_prerow, 1, QTableWidgetItem(one_info[1]))
        self.tableWidget_2.setItem(num_prerow,2,QTableWidgetItem(one_info[3]))
        self.tableWidget_2.setItem(num_prerow, 3,QTableWidgetItem(one_info[2]))

    def getkeyboard(self):
        if self.comboBox_2.currentText()!='':
            dest = self.comboBox_2.currentText().split(':')[1]
            self.connect_sock.requestKey(dest)

    def keyinView(self,alltext):
        self.textEdit.clear()
        self.textEdit.setText(alltext)

    def updatelocal(self,one_in):
        #print(one_in)
        count=len(self.xlabel)
        self.xlabel.append(count)
        self.y1label.append(one_in[0])  #send
        self.y2label.append(one_in[1])  #recevice
        self.localplt.clear()
        self.localplt.setRange(xRange=[(count - 9), (count + 1)])
        if len(self.xlabel)==2:
            self.localplt.addLegend()
            self.localplt.plot(self.xlabel, self.y1label, pen=pg.mkPen(color='r', width=1),symbolBrush=(255,0,0), name='Upload')
            self.localplt.plot(self.xlabel, self.y2label, pen=pg.mkPen(color='y', width=1),symbolBrush=(255,255,0), name='Download')
        else:
            self.localplt.plot(self.xlabel, self.y1label, pen=pg.mkPen(color='r', width=1),symbolBrush=(255,0,0))
            self.localplt.plot(self.xlabel, self.y2label, pen=pg.mkPen(color='y', width=1 ),symbolBrush=(255,255,0))


    def updateusernet(self,one_in):
        print(one_in)
        count=len(self.userxlabel)
        self.userxlabel.append(count)
        self.usery1label.append(one_in[0])
        self.usery2label.append(one_in[1])
        self.remoteplt.clear()
        self.remoteplt.setRange(xRange=[(count - 9), (count + 1)])
        if len(self.userxlabel)==2:
            self.remoteplt.addLegend()
            self.remoteplt.plot(self.userxlabel, self.usery1label, pen=pg.mkPen(color='r', width=1),symbolBrush=(255,0,0), name='Upload')
            self.remoteplt.plot(self.userxlabel, self.usery2label, pen=pg.mkPen(color='y', width=1),symbolBrush=(255,255,0), name='Upload')
        self.remoteplt.plot(self.userxlabel,self.usery1label,pen=pg.mkPen(color='r',width=1),symbolBrush=(255,0,0))
        self.remoteplt.plot(self.userxlabel,self.usery2label,pen=pg.mkPen(color='y',width=1),symbolBrush=(255,255,0))

    def check_sql(self,id):
        self.sql_cursor=self.sql_conn.cursor()
        self.sql_cursor.execute('select id from users')
        values=self.sql_cursor.fetchall()
        self.sql_cursor.close()
        values_list=[i[0] for i in values]
        if id in values_list:
            return False        #存在返回错
        else:return True        #不存在返回对

    def doUpdate(self):
        if self.comboBox_3.currentText()=='None':
            QMessageBox.warning(self, "Warning", "No Options Chosen!", QMessageBox.Yes)
        elif self.comboBox_3.currentText()=='Add':    #用户 密码
            edit_list=self.lineEdit.text().split(' ')
            if len(edit_list)!=2:
                QMessageBox.warning(self, "Warning", "Wrong Input!", QMessageBox.Yes)
            else:
                if self.check_sql(edit_list[0]):         #不存在
                    import hashlib
                    pass_m5 = hashlib.md5(edit_list[1].encode()).hexdigest()
                    self.sql_cursor = self.sql_conn.cursor()
                    self.sql_cursor.execute('insert into users(id,password,password_m5) values (%s,%s,%s)',
                                            [edit_list[0], edit_list[1], pass_m5])
                    self.sql_conn.commit()
                    self.sql_cursor.close()
                    self.flush()
                    self.lineEdit.setText('')
                else:               #已存在
                    QMessageBox.warning(self, "Warning", "Already in!\nUse Update!", QMessageBox.Yes)

        elif self.comboBox_3.currentText()=='Delete':
            edit_list = self.lineEdit.text()    #输入用户名
            if self.check_sql(edit_list):     #不存在
                QMessageBox.warning(self, "Warning", "No Such Record in Users!", QMessageBox.Yes)
            else:
                self.sql_cursor=self.sql_conn.cursor()
                self.sql_cursor.execute('delete from users where id=%s',(edit_list,))
                self.sql_conn.commit()
                self.sql_cursor.close()
                self.flush()
                self.lineEdit.setText('')
        else:           #id 和 新 password
            edit_list=self.lineEdit.text().split(' ')
            if self.check_sql(edit_list[0]):  #不存在
                QMessageBox.warning(self, "Warning", "No Such Record in Users!", QMessageBox.Yes)
            else:
                import hashlib
                pass_m5 = hashlib.md5(edit_list[1].encode()).hexdigest()
                self.sql_cursor=self.sql_conn.cursor()
                self.sql_cursor.execute('update users set password=%s,password_m5=%s where id=%s',(edit_list[1],pass_m5,edit_list[0],))
                self.sql_conn.commit()
                self.sql_cursor.close()
                self.flush()
                self.lineEdit.setText('')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = MyAdmin()
    MainWindow.show()
    sys.exit(app.exec_())