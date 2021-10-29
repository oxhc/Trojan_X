## TrojanX

##### 介绍

基于Python的可视化远程控制软件, 界面使用PyQt5, 通讯使用TCP与UDP. 

本项目包括两个入口, 包括控制端和被控端. 主要功能包括: 主机管理、远程监控、洪水攻击、文件传输、远程命令执行等. 

###### 界面

主界面

![](https://s3.bmp.ovh/imgs/2021/10/413617e48abf1e1c.png)

控制界面

![](https://s3.bmp.ovh/imgs/2021/10/8392bca1ed651fa2.png)


###### requirements

- pyqt5
- scapy(用于被控端洪水攻击使用)

##### 配置

在启动前, 需要将程序正确配置. 

```ini
[server]
ip=100.95.210.184
tcpPort=8877
udpSendPort=8089
udpRecvPort=8083

[client]
masterIp=100.95.221.22
masterUdpPort=8083
masterTcpPort=8877
```

​	控制端和被控端都读取config.ini配置文件, 当控制端和被控端不在同一工作目录时, 配置文件中可只有`server`或`client`配置. 

​	被控端的`masterUdpPort`需要与控制端的`udpRecvPort`相同, 被控端的`masterTcpPort`需要与控制端的`tcpPort`相同. 



##### 用法

###### 启动控制端程序

```shell
python3 main.py
```

###### 启动被控端

```shell
python3 client.py
```

