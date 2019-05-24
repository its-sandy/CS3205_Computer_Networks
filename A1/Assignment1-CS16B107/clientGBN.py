import threading
import socket
import argparse
import time
import string
import random
import sys
import os
import datetime

class ClientGBN:
    def __init__(self, args):
        self.args = args
        self.LPSindex = -1 #last packets sent's buffer index
        self.LARseq = -1 #last acknowledgement received packet's sequence number
        self.maxSeqNum = 2*self.args.windowSize + 1
        self.lock = threading.Lock()
        self.buffer = []
        self.bufferSeqNums = []
        self.windowTimer = None
        self.totalPacketsAck = 0
        self.timeoutTime = self.args.timeoutTime

        # Book-keeping Data
        self.seqSendTimes = [None]*self.maxSeqNum
        self.seqRecTimes = [None]*self.maxSeqNum
        self.seqGenTimes = [None]*self.maxSeqNum
        self.senderStartTime = time.time()
        self.seqNumAttempts = [0]*self.maxSeqNum
        self.RTTavg = 0.0
        self.totalNumTransmissions = 0

    def printStatistics(self):
        print("packet generation rate: %d" %self.args.packetGenRate)
        print("packet length: %d" %self.args.packetLength)
        print("retransmission rate: %f" % (float(self.totalNumTransmissions)/self.totalPacketsAck))
        print("average RTT (ms): %0.3f" % (self.RTTavg*1000))

    def bookKeeping(self, seqNum):
        #called inside lock
        self.RTTavg = ((float(self.RTTavg) * (self.totalPacketsAck - 1)) + (self.seqRecTimes[seqNum] - self.seqSendTimes[seqNum]))/self.totalPacketsAck

        if self.totalPacketsAck >= 10:
            self.timeoutTime = 5*self.RTTavg

        if self.args.debug:
            print(datetime.datetime.now() ,"Seq #%d:  Time Generated: %0.3f ;  RTT: %0.3f ;  Number of Attempts: %d" % (seqNum, (self.seqGenTimes[seqNum]-self.senderStartTime)*1000, (self.seqRecTimes[seqNum]-self.seqSendTimes[seqNum])*1000, self.seqNumAttempts[seqNum]))

        self.seqNumAttempts[seqNum] = 0

    def addPacketToBuffer(self):
        self.lock.acquire()
        if len(self.buffer) < self.args.bufferSize:

            if len(self.buffer) == 0:
                self.bufferSeqNums.append((self.LARseq + 1)%self.maxSeqNum)
            else:
                self.bufferSeqNums.append((self.bufferSeqNums[-1] + 1)%self.maxSeqNum)

            self.seqGenTimes[self.bufferSeqNums[-1]] = time.time()

            self.buffer.append(''.join([random.choice(string.ascii_letters + string.digits) for n in range(self.args.packetLength)]))
            self.lock.release()
            return True
        else:
            self.lock.release()
            return False

    def packetGenerator(self):
        print("PACKET_GENERATOR started\n")
        i = 0
        while i < self.args.maxPackets:
            time.sleep(1/float(self.args.packetGenRate))
            if self.addPacketToBuffer():
                i += 1

    def ackReceiver(self, sock):
        print("ACK_RECEIVER thread started\n")
        while self.totalPacketsAck < self.args.maxPackets:  #change this
            ack, server = sock.recvfrom(512)
            ack = ack.decode()
            self.seqRecTimes[int(ack)] = time.time()

            self.lock.acquire()

            if len(self.buffer) > 0 and int(ack) == self.bufferSeqNums[0]:

                self.windowTimer.cancel()
                self.buffer.pop(0)
                self.bufferSeqNums.pop(0)
                self.LPSindex -= 1
                self.LARseq = int(ack)
                self.totalPacketsAck += 1

                #called while inside lock
                self.bookKeeping(int(ack))

                if self.buffer:
                    self.windowTimer = threading.Timer(self.timeoutTime, self.timeout, args=(self.bufferSeqNums[0],))
                    self.windowTimer.start()
            self.lock.release()

    def timeout(self, seqNum):
        #takes sequence number of the start of the window as parameter
        if self.args.verbose:
            print(datetime.datetime.now(), "Seq #%d: Timeout" % seqNum)

        self.lock.acquire()
        if len(self.buffer) > 0 and seqNum == self.bufferSeqNums[0]:
            self.LPSindex = -1 #timer restarted in goBackNSender
        else:
            pass
        self.lock.release()
    
    def transmitData(self):
        #establish udp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("socket connection established\n")
        #start ackreceiver thread
        t1 = threading.Thread(target=self.ackReceiver, args=(sock,))
        t1.start()
        #start packetGenerator thread
        t2 = threading.Thread(target=self.packetGenerator)
        t2.start()

        while self.totalPacketsAck < self.args.maxPackets:  #change this
            self.lock.acquire()
            if self.LPSindex < len(self.buffer)-1 and self.LPSindex < self.args.windowSize-1:
                
                self.LPSindex += 1
                message = str(self.bufferSeqNums[self.LPSindex]) + "*" + self.buffer[self.LPSindex]
                if self.LPSindex == 0:
                    self.windowTimer = threading.Timer(self.timeoutTime, self.timeout, args=(self.bufferSeqNums[0],))
                    self.windowTimer.start() #will lock make an issue
                
                #book-keeping
                self.seqNumAttempts[self.bufferSeqNums[self.LPSindex]] += 1
                if self.seqNumAttempts[self.bufferSeqNums[self.LPSindex]] > 5:
                    print("client terminated as number of transmissions for seqNum #%d exceeds 5"%self.bufferSeqNums[self.LPSindex])
                    os._exit(1)

                if self.args.verbose:
                    print(datetime.datetime.now(), "Seq #%d: packet sent" % self.bufferSeqNums[self.LPSindex])

                self.totalNumTransmissions += 1
                self.seqSendTimes[self.bufferSeqNums[self.LPSindex]] = time.time()
                self.lock.release()
                sock.sendto(message.encode(), (self.args.receiverIP, self.args.receiverPortNo))

            else:    
                self.lock.release()

        t2.join()
        t1.join()
        sock.close()

        self.printStatistics()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="turn ON debug mode", action = "store_true")
    parser.add_argument("-v", "--verbose", help="turn ON verbose mode", action = "store_true")
    parser.add_argument("-s", type=str, action="store", dest="receiverIP", default="127.0.0.1",help="receiver name/ IP address")
    parser.add_argument("-p", type=int, action="store", dest="receiverPortNo", default=10000, help="receiver port number")
    parser.add_argument("-l", type=int, action="store", dest="packetLength", help="packet length (bytes)")
    parser.add_argument("-r", type=int, action="store", dest="packetGenRate", help="packet generation rate (pkts/sec)")
    parser.add_argument("-n", type=int, action="store", dest="maxPackets", help="maximum number of packets to be acknowledged")
    parser.add_argument("-w", type=int, action="store", dest="windowSize", help="sender window size")
    parser.add_argument("-b", type=int, action="store", dest="bufferSize", help="sender buffer size (must be greater than window size)")
    parser.add_argument("-t", type=float, action="store", dest="timeoutTime", default=0.1, help="sender timeout time")
    
    args = parser.parse_args()
    print(args)

    sender = ClientGBN(args)
    sender.transmitData()