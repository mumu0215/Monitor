# _*_ coding=utf-8 _*_
from viewforUser import Ui_Form
from PyQt5.QtWidgets import QWidget,QApplication
import sys
import pyqtgraph as pg
class widgetView(QWidget,Ui_Form):
    def __init__(self,id):
        super(widgetView,self).__init__()
        self.setupUi(self)
        self.setWindowTitle('NetFlow of %s'%id)

    def print_info(self,event=None):
        if event==None:
            print('事件为空')
        else:
            pos=event[0]
            try:
                if self.idPlt.sceneBoundingRect().contains(pos):
                    mousePoint=self.idPlt.vb.mapSceneToView(pos)
                    index=int(mousePoint.x())
                    y_pos=mousePoint.y()
                    if -1<index<len(list(self.xdict.keys())) and -1<y_pos<2+max(max(self.sendl),max(self.rel)):
                        self.label.setHtml("<p style='color:white'><strong>Date：{0}</strong></p><p style='color:white'><strong>Send：{1}Mb</strong></p><p style='color:white'><strong>Receive：{2}Mb</strong></p>".format(
                                self.xdict[index],self.sendl[index],self.rel[index]))
                        self.label.setPos(mousePoint.x(),mousePoint.y())
                    self.vLine.setPos(mousePoint.x())
                    self.hLine.setPos(mousePoint.y())
            except Exception as e:
                print(e)

    def plotall(self,stringAxis,xdict,send_list,re_list):
        self.xdict=xdict;self.sendl=send_list;self.rel=re_list
        self.idview=pg.GraphicsView()
        self.idPlt=pg.PlotItem(title='Network Flow', axisItems={'bottom': stringAxis})
        self.idPlt.setLabel(axis='left',text='数据量(Mb)')
        self.idPlt.showGrid(y=True,alpha=0.3)
        self.idview.setCentralWidget(self.idPlt)
        self.horizontalLayout.addWidget(self.idview)

        self.label = pg.TextItem()
        self.idPlt.addItem(self.label)
        self.vLine = pg.InfiniteLine(angle=90, movable=False, )
        self.hLine = pg.InfiniteLine(angle=0, movable=False, )
        self.idPlt.addItem(self.vLine, ignoreBounds=True)
        self.idPlt.addItem(self.hLine, ignoreBounds=True)

        self.idPlt.addLegend()
        self.idPlt.plot(list(xdict.keys()), send_list, pen=pg.mkPen(color='r', width=1),symbolBrush=(255, 0, 0), name='send')

        self.idPlt.plot(list(xdict.keys()), re_list, pen=pg.mkPen(color='y', width=1),symbolBrush=(255, 255, 0), name='receive')
        self.move_slot = pg.SignalProxy(self.idPlt.scene().sigMouseMoved, rateLimit=60, slot=self.print_info)

    def __del__(self):
        del self.xdict,self.sendl,self.rel
        self.close()