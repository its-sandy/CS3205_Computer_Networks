import threading
import socket
import argparse
import time
import random
import datetime
import heapq

class serverSR:
    def __init__(self, args):
        self.args = args
        self.winLeftSeq = 0 #sequence number of left end of window (0 to maxSeqNum-1)
        self.winRightSeq = self.args.windowSize - 1 #sequence number of right end of window
        self.totalPacketsAck = 0
        self.receiverStartTime = None
        self.numBuffered = 0
        self.args.seqNumFieldLength = int((self.args.seqNumFieldLength + 7)/8) #now in bytes
        self.args.maxSeqNum = 1<<(self.args.seqNumFieldLength*8)
        self.seqArrivalTimes = [0]*self.args.maxSeqNum #non-zero time ensures that it is an acknowledgef packet in the current window
        
    def generateMessage(self, seqNum, data):
        msg = data
        for _ in range(0, self.args.seqNumFieldLength):
            msg = chr(seqNum%256) + msg
            seqNum = seqNum>>8
        return msg

    def extractSeqNum(self, msg):
        seqNum = 0
        for i in range(0, self.args.seqNumFieldLength):
            seqNum = (seqNum<<8)+ord(msg[i])
        return seqNum

    def isInWindow(self, seqNum):
        if self.winLeftSeq <= seqNum and seqNum <= self.winRightSeq:
            return True
        elif self.winLeftSeq > self.winRightSeq and (self.winLeftSeq <= seqNum or seqNum <= self.winRightSeq):
            return True
        else:
            return False

    def listen(self):

        if self.args.verbose:
            print(self.args, end='\n')

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (self.args.receiverIP, self.args.receiverPortNo)
        sock.bind(server_address)
        self.receiverStartTime = time.time()

        while self.totalPacketsAck < self.args.maxPackets:
            data, address = sock.recvfrom(2048)
            curtime = time.time()
            data = data.decode()

            seqNum = self.extractSeqNum(data[:self.args.seqNumFieldLength])

            if random.random() <= self.args.packetErrorRate:
                # print("seqnum got = %d, case 1"%seqNum)
                if self.args.verbose:
                    print(datetime.datetime.now(), "Seq #%d:  Time Received (ms): %0.3f;  Packet Lost" % (seqNum, (curtime-self.receiverStartTime)*1000))
                continue

            if not(self.isInWindow(seqNum)):
                #packet not in current receiver window
                # print("seqnum got = %d, case 2"%seqNum)
                sock.sendto((self.generateMessage(seqNum,"")).encode(), address)
                if self.args.verbose:
                    print(datetime.datetime.now(), "Seq #%d:  Time Received (ms): %0.3f;  ACK resent" % (seqNum, (self.seqArrivalTimes[self.winLeftSeq]-self.receiverStartTime)*1000))
            elif self.seqArrivalTimes[seqNum] != 0:
                #packet already acknowledged
                # print("seqnum got = %d, case 3"%seqNum)
                sock.sendto((self.generateMessage(seqNum,"")).encode(), address)
                if self.args.verbose:
                    print(datetime.datetime.now(), "Seq #%d:  Time Received (ms): %0.3f;  ACK resent" % (seqNum, (self.seqArrivalTimes[self.winLeftSeq]-self.receiverStartTime)*1000))
            else:
                #unacknowledged packet in current window
                if self.numBuffered <= self.args.bufferSize-2 or seqNum == self.winLeftSeq:
                    # print("seqnum got = %d, case 4"%seqNum)
                    #packet added to buffer keeping one space always available for immediately next inorder packet
                    sock.sendto((self.generateMessage(seqNum,"")).encode(), address)

                    self.seqArrivalTimes[seqNum] = curtime
                    self.totalPacketsAck += 1
                    self.numBuffered += 1

                    if self.args.verbose:
                        print(datetime.datetime.now(), "Seq #%d:  Packet added to buffer" % seqNum)

                    #shift window
                    while self.seqArrivalTimes[self.winLeftSeq] != 0:
                        #look into empty window
                        if self.args.debug:
                            print(datetime.datetime.now(), "Seq #%d:  Time Received (ms): %0.3f;  Packet Forwarded to upper layer in order" % (self.winLeftSeq, (self.seqArrivalTimes[self.winLeftSeq]-self.receiverStartTime)*1000))
                        self.numBuffered -= 1
                        self.seqArrivalTimes[self.winLeftSeq] = 0
                        self.winLeftSeq = (self.winLeftSeq + 1)%self.args.maxSeqNum
                        self.winRightSeq = (self.winRightSeq + 1)%self.args.maxSeqNum
                else:
                    # print("seqnum got = %d, case 5"%seqNum)
                    if self.args.verbose:
                        print(datetime.datetime.now(), "Seq #%d:  Time Received (ms): %0.3f;  Packet Dropped due to Buffer Constraint" % (seqNum, (curtime-self.receiverStartTime)*1000))
                
        sock.close()    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="turn ON debug mode", action = "store_true")
    parser.add_argument("-v", "--verbose", help="turn ON verbose mode", action = "store_true")
    parser.add_argument("-s", type=str, action="store", dest="receiverIP", default="127.0.0.1",help="receiver name/ IP address")
    parser.add_argument("-p", type=int, action="store", dest="receiverPortNo", default=10000, help="receiver port number")
    parser.add_argument("-n", type=int, action="store", dest="maxPackets", help="maximum number of packets to be acknowledged")
    parser.add_argument("-e", type=float, action="store", dest="packetErrorRate", help="sender window size")
    parser.add_argument("-m", type=int, action="store", dest="seqNumFieldLength", help="sequence number field length in bits")
    parser.add_argument("-w", type=int, action="store", dest="windowSize", help="receiver window size")
    parser.add_argument("-b", type=int, action="store", dest="bufferSize", help="receiver buffer size (must be greater than window size)")
    
    args = parser.parse_args()

    receiver = serverSR(args)
    receiver.listen()