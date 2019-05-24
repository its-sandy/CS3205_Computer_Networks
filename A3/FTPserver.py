import socket
import argparse
import os

class FTPServer:
    def __init__(self, args):
        self.serverRootDir = os.getcwd()
        self.socket = None
        self.serverIP = '0.0.0.0'
        self.serverPortNo = args.serverPortNo
        self.verbose = args.verbose

    def getReply(self):
        reply = self.sock.recv(1024)
        reply = reply.decode()
        reply = reply.split('\x00') #python null character
        return reply

    def NLST(self, command):
        if len(command) == 2: #Directory not given in input
            dir = os.getcwd()
        else:
            dir = command[1]

        try:
            reply = ('\x00'.join(os.listdir(dir))) + '\x00'
        except:
            reply = 'Directory Error\x00'
        
        self.sock.sendall(reply.encode())
    
    def CWD(self, command):
        if len(command) == 2: #Directory not given in input
            dir = self.serverRootDir
        else:
            dir = command[1]

        try:
            os.chdir(dir)
            reply = os.getcwd() + '\x00'
        except:
            reply = 'Directory Error\x00' + os.getcwd() + '\x00'
        
        self.sock.sendall(reply.encode())

    def PWD(self, command):
        self.sock.sendall((os.getcwd() + '\x00').encode())

    def RETR(self, command):
        if os.path.isfile(command[1]):
            self.sock.sendall(('File Name OK\x00').encode())
        else:
            self.sock.sendall(('File Error\x00').encode())
            return
        
        with open(command[1],'rb') as f:
            while True:
                l = f.read(1024)
                if len(l) < 1024:
                    l = l + '\x00'.encode()
                    self.sock.sendall(l)
                    if self.verbose:
                        print('sent ',len(l),' bytes')
                    break
                else:
                    self.sock.sendall(l)
                    if self.verbose:
                        print('sent ',len(l),' bytes')
        
    def STOR(self, command):
        self.sock.sendall(('OK to SEND File\x00').encode())

        with open(command[1], 'wb') as f:
            # print('file opened')
            while True:
                # print('receiving data...')
                data = self.sock.recv(1024)
                if self.verbose:
                    print('received ',len(data),' bytes')
                # print('data=%s', (data))
                if data[-1] == 0:
                    data = data[:-1] #removing null character that denotes end of data in the last packet
                    if len(data) > 0:
                        f.write(data)
                    break
                else:
                    f.write(data)
        self.sock.sendall(('File Received\x00').encode()) #acknowledgement

    def runServer(self):

        print('Server Started')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.serverIP, self.serverPortNo))
        s.listen(5)
        self.sock, addr = s.accept()
        print('Connection Established')

        while True:
            
            command = self.getReply()

            if self.verbose:
                print('Command Received: ',command)

            if command[0] == 'NLST':
                self.NLST(command)
            elif command[0] == 'CWD':
                self.CWD(command)
            elif command[0] == 'RETR':
                self.RETR(command)
            elif command[0] == 'STOR':
                self.STOR(command)
            elif command[0] == 'PWD':
                self.PWD(command)
            elif command[0] == 'QUIT':
                break

        self.sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="turn ON verbose mode", action = "store_true")
    parser.add_argument("-p", type=int, action="store", dest="serverPortNo", default=10000, help="server port number")
    
    args = parser.parse_args()

    server = FTPServer(args)
    server.runServer()
