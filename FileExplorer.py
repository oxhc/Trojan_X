import os


class FileExplorer:
    def __init__(self):
        self.list = None
        self.getList()

    def getList(self):
        try:
            ls = os.listdir()
        except:
            ls = []
        self.list = [(i, os.path.isdir(i)) for i in ls]

    def exec(self, commands:str):
        cmd = commands.split(' ')
        if "ls" == cmd[0]:
            return self.list
        elif "pwd" == cmd[0]:
            return os.getcwd()
        elif "cd" == cmd[0]:
            os.chdir(' '.join(cmd[1:]))
            self.getList()
            return os.getcwd()
        elif "select" == cmd[0]:
            num = int(cmd[1])
            return os.path.join(os.getcwd(), self.list[num][0])



if __name__ == '__main__':
    explorer = FileExplorer()
    while True:
        cmd = input('$:')
        if cmd == "exit":
            break
        print(explorer.exec(cmd))