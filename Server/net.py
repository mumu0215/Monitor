# _*_ coding=utf-8 _*_
import time,psutil
from PyQt5 import QtCore
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
