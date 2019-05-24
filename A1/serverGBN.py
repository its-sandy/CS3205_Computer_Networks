import threading
import socket
import argparse
import time
import random
import datetime

class serverGBN:
    def __init__(self, args):
        self.args = args
        self.LASseq = -1 #last acknowledgement sent packet's sequence number
        self.totalPacketsAck = 0
        self.receiverStartTime = None

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (self.args.receiverIP, self.args.receiverPortNo)
        sock.bind(server_address)
        self.receiverStartTime = time.time()

        while self.totalPacketsAck < self.args.maxPackets:
            data, address = sock.recvfrom(2048)
            
            data = data.decode()
            seqNum, message = data.split("*")
            seqNum = int(seqNum)

            if random.random() <= self.args.packetErrorRate:
                if self.args.debug:
                    print(datetime.datetime.now(), "Seq #%d:  Time Received: %0.3f;  Packet Dropped = true" % (seqNum, (time.time()-self.receiverStartTime)*1000))
                continue

            if seqNum == (self.LASseq + 1)%self.args.maxSeqNum:
                self.LASseq = seqNum
                self.totalPacketsAck += 1
                
            sock.sendto((str(self.LASseq)).encode(), address)
            if self.args.debug:
                print(datetime.datetime.now(), "Seq #%d:  Time Received: %0.3f;  Packet Dropped = false;  ACK = %d" % (seqNum, (time.time()-self.receiverStartTime)*1000, self.LASseq))

        sock.close()    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="turn ON debug mode", action = "store_true")
    parser.add_argument("-v", "--verbose", help="turn ON debug mode", action = "store_true")
    parser.add_argument("-s", type=str, action="store", dest="receiverIP", default="127.0.0.1",help="receiver name/ IP address")
    parser.add_argument("-p", type=int, action="store", dest="receiverPortNo", default=10000, help="receiver port number")
    parser.add_argument("-n", type=int, action="store", dest="maxPackets", help="maximum number of packets to be acknowledged")
    parser.add_argument("-e", type=float, action="store", dest="packetErrorRate", help="sender window size")
    parser.add_argument("-m", type=int, action="store", dest="maxSeqNum", help="maximum sequence number")
    
    args = parser.parse_args()
    print(args)

    receiver = serverGBN(args)
    receiver.listen()