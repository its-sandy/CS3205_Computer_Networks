import socket
import argparse
import os

class FTPClient:
    def __init__(self, args):
        self.clientRootDir = os.getcwd()
        self.socket = None
        self.serverIP = args.serverIP
        self.serverPortNo = args.serverPortNo
        self.verbose = args.verbose

    def getReply(self):
        reply = self.sock.recv(1024)
        reply = reply.decode()
        reply = reply.split('\x00') #python null character
        return reply

    def ls(self, command):
        if len(command) == 1:
            self.sock.sendall('NLST\x00'.encode())
        else:
            self.sock.sendall(('NLST\x00' + command[1] + '\x00').encode())

        reply = self.getReply()

        if reply[0] == 'Directory Error':
            print('ERROR: Directory does not exist')
        else:
            for file in reply:
                if file != '':
                    print(file)
    
    def cd(self, command):
        if len(command) == 1: #Directory input not given
            self.sock.sendall('CWD\x00'.encode())
        else:
            self.sock.sendall(('CWD\x00' + command[1]  + '\x00').encode())
        
        reply = self.getReply()

        if reply[0] == 'Directory Error' and len(reply) == 3:
            print('ERROR: Directory does not exist')
            print('Current Server Working Directory: ',reply[1])
            return False
        else:
            print('Current Server Working Directory: ',reply[0])
            return True

    def lcd(self, command):
        if len(command) == 1: #Directory input not given
            os.chdir(self.clientRootDir)
        else:
            try:
                os.chdir(command[1])
            except:
                print('ERROR: Directory does not exist')
                
        print('Current Client Working Directory: ',os.getcwd())  

    def pwd(self, command):
        #prints present working directories of both client and server
        self.sock.sendall('PWD\x00'.encode())
        
        reply = self.getReply()

        print('Current Server Working Directory: ',reply[0])
        print('Current Client Working Directory: ',os.getcwd())

    def get(self, command):
        directoryError = False

        if len(command) == 3: #Directory given in input
            directoryError = not self.cd(['cd', command[2]])

        if directoryError:
            return

        self.sock.sendall(('RETR\x00' + command[1] + '\x00').encode())
        reply = self.getReply()

        if reply[0] == 'File Error':
            print('ERROR: File does not exist at server')
        elif reply[0] == 'File Name OK':
            with open(command[1], 'wb') as f:
                # print('file opened')
                while True:
                    # print('receiving data...')
                    data = self.sock.recv(1024)
                    if self.verbose:
                        print('received ',len(data),' bytes')
                    if data[-1] == 0:
                        data = data[:-1] #removing null character that denotes end of data in the last packet
                        if len(data) > 0:
                            f.write(data)
                        break
                    else:
                        f.write(data)
            print('File Received Successfully')

    def put(self, command):
        directoryError = False

        if len(command) == 3: #Directory given in input
            directoryError = not self.cd(['cd', command[2]])

        if directoryError:
            return

        if not os.path.isfile(command[1]): #check for File Error
            print('ERROR: File does not exist at client')
            return

        self.sock.sendall(('STOR\x00' + command[1] + '\x00').encode())
        reply = self.getReply() #waits for acknowledgement to send

        if reply[0] == 'OK to SEND File':
            with open(command[1],'rb') as f:
                while True:
                    l = f.read(1024) #reads as chunks of 1024 bytes
                    if len(l) < 1024:
                        l = l + '\x00'.encode()
                        self.sock.sendall(l)
                        if self.verbose:
                            print('sent ',len(l),' bytes') #includes null character
                        break
                    else:
                        self.sock.sendall(l)
                        if self.verbose:
                            print('sent ',len(l),' bytes')
        
        reply = self.getReply() #acknowledgement
        if reply[0] == 'File Received':
            print('File Sent Successfully')

    def runClient(self):

        print('Client Started')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.serverIP, self.serverPortNo))
        print('Connection Established')

        while True:
            
            command = input('\n(FTP)>>> ')
            command = command.split(' ')

            if command[0] == 'ls':
                self.ls(command)
            elif command[0] == 'cd':
                self.cd(command)
            elif command[0] == 'lcd':
                self.lcd(command)
            elif command[0] == 'pwd':
                self.pwd(command)
            elif command[0] == 'get':
                self.get(command)
            elif command[0] == 'put':
                self.put(command)
            elif command[0] == 'quit':
                self.sock.sendall('QUIT\x00'.encode())
                print('Client Terminating')
                break
            else:
                print('Invalid Command')

        self.sock.close()
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="turn ON verbose mode", action = "store_true")
    parser.add_argument("-s", type=str, action="store", dest="serverIP", default="127.0.0.1",help="server IP address")
    parser.add_argument("-p", type=int, action="store", dest="serverPortNo", default=10000, help="server port number")
    
    args = parser.parse_args()

    client = FTPClient(args)
    client.runClient()
