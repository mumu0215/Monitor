# _*_ coding=utf-8 _*_
import matplotlib
# 使用 matplotlib中的FigureCanvas (在使用 Qt5 Backends中 FigureCanvas继承自QtWidgets.QWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from viewforUser import Ui_Form
from PyQt5.QtWidgets import QWidget,QApplication
from wordcloud import WordCloud
import sys
plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
class widgetView(QWidget,Ui_Form):
    def __init__(self):
        super(widgetView,self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Chrome浏览记录分析')
        self.figure=plt.figure()
        self.canvas=FigureCanvas(self.figure)
        self.horizontalLayout.addWidget(self.canvas)

    def plotHistory(self,dataIn):
        xlab=[i[0] for i in dataIn[:10]]
        y=[i[1] for i in dataIn[:10]]
        # print(xlab,y)
        arr_x=np.arange(len(xlab))
        arr_y=np.array(y)
        plt.ylabel('访问次数')
        plt.bar(range(len(xlab)),y,tick_label=xlab,color='blue',width=0.5)
        ax=plt.gca()
        for t in ax.get_xticklabels():
            t.set_rotation(20)
        for a,b in zip(arr_x,arr_y):
            plt.text(a,b,'%d'%b,ha='center',va='bottom')
        plt.title('History View')
        self.canvas.draw()

