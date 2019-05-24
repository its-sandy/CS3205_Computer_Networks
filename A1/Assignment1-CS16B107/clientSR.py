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
        self.LAS = -1 #last assigned sequence number
        self.lock = threading.Lock()
        self.buffer = []
        self.bufferSeqNums = []
        self.totalPacketsAck = 0
        self.winLeftSeq = 0 #sequence number of left end of window (0 to maxSeqNum-1)
        self.winRightSeq = self.args.windowSize - 1 #sequence number of right end of window
        self.timeoutTime = self.args.timeoutTime
        self.sock = None
        self.args.seqNumFieldLength = int((self.args.seqNumFieldLength + 7)/8) #now in bytes
        self.maxSeqNum = 1<<(self.args.seqNumFieldLength*8)
        self.seqNumTimers = [None] * self.maxSeqNum

        # Book-keeping Data
        self.seqSendTimes = [None]*self.maxSeqNum
        self.seqGenTimes = [None]*self.maxSeqNum
        self.senderStartTime = time.time()
        self.seqNumAttempts = [0]*self.maxSeqNum
        self.RTTavg = 0.0
        self.totalNumTransmissions = 0

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

    def printStatistics(self):
        print("packet generation rate: %d" %self.args.packetGenRate)
        print("packet length: %d" %self.args.packetLength)
        print("retransmission rate: %f" % (float(self.totalNumTransmissions)/self.totalPacketsAck))
        print("average RTT (ms): %0.3f" % (self.RTTavg*1000))

    def isInWindow(self, seqNum):
        if self.winLeftSeq <= seqNum and seqNum <= self.winRightSeq:
            return True
        elif self.winLeftSeq > self.winRightSeq and (self.winLeftSeq <= seqNum or seqNum <= self.winRightSeq):
            return True
        else:
            return False

    def bookKeeping(self, seqNum):
        #called inside lock
        curtime = time.time()
        self.RTTavg = ((float(self.RTTavg) * (self.totalPacketsAck - 1)) + (curtime - self.seqSendTimes[seqNum]))/self.totalPacketsAck

        if self.totalPacketsAck >= 10:
            self.timeoutTime = 5*self.RTTavg

        if self.args.debug:
            print(datetime.datetime.now() ,"Seq #%d:  Time Generated: %0.3f ;  RTT: %0.3f ;  Number of Attempts: %d" % (seqNum, (self.seqGenTimes[seqNum]-self.senderStartTime)*1000, (curtime-self.seqSendTimes[seqNum])*1000, self.seqNumAttempts[seqNum]))

        self.seqNumAttempts[seqNum] = 0

    def addPacketToBuffer(self):
        self.lock.acquire()
        if len(self.buffer) < self.args.bufferSize:
            
            self.LAS = (self.LAS + 1)%self.maxSeqNum
            self.bufferSeqNums.append(self.LAS)
            self.seqGenTimes[self.bufferSeqNums[-1]] = time.time()
            self.buffer.append(''.join([random.choice(string.ascii_letters + string.digits) for n in range(random.randint(40,self.args.packetLength))]))
            
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

    def ackReceiver(self):
        print("ACK_RECEIVER thread started\n")
        while self.totalPacketsAck < self.args.maxPackets:  #change this
            ack, server = self.sock.recvfrom(512)
            ack = ack.decode()
            ack = self.extractSeqNum(ack)

            if not self.isInWindow(ack):
                continue

            if self.args.verbose:
                print(datetime.datetime.now() ,"ACK #%d:  received" % ack)
            self.lock.acquire()

            ##################
            try:
                ind = self.bufferSeqNums.index(ack)

                self.buffer.pop(ind)
                self.bufferSeqNums.pop(ind)
                self.seqNumTimers[ack].cancel()
                self.LPSindex -= 1
                self.totalPacketsAck += 1

                #called while inside lock
                self.bookKeeping(ack)

                #move window
                if len(self.buffer) > 0:
                    self.winLeftSeq = self.bufferSeqNums[0]
                    self.winRightSeq = (self.winLeftSeq + self.args.windowSize - 1)%self.maxSeqNum
                else:
                    self.winLeftSeq = (self.LAS + 1)%self.maxSeqNum
                    self.winRightSeq = (self.winLeftSeq + self.args.windowSize - 1)%self.maxSeqNum

            except ValueError:
                #ack sequence number not in current buffer
                pass

            self.lock.release()

            if self.args.verbose:
                print(datetime.datetime.now() ,"Sender Window Left #%d: " % self.winLeftSeq)

    def timeout(self, seqNum):

        self.lock.acquire()
        try:
            ind = self.bufferSeqNums.index(seqNum)
            message =  self.generateMessage(seqNum, self.buffer[ind])
            self.totalNumTransmissions += 1
            self.lock.release()

            if self.args.verbose:
                print(datetime.datetime.now(), "Seq #%d: Timeout, packet resent" % seqNum)
            self.seqNumAttempts[seqNum] += 1
            if self.seqNumAttempts[seqNum] > 10:
                print("client terminated as number of transmissions for seqNum #%d exceeds 5"%seqNum)
                os._exit(1)
            self.seqSendTimes[seqNum] = time.time()
            self.seqNumTimers[seqNum] = threading.Timer(self.timeoutTime, self.timeout, args=(seqNum,))
            self.seqNumTimers[seqNum].start()
            self.sock.sendto(message.encode(), (self.args.receiverIP, self.args.receiverPortNo))

        except ValueError:
            #ack sequence number not in current buffer
            self.lock.release()
    
    def transmitData(self):

        if self.args.verbose:
            print(self.args, end='\n')
        
        #establish udp
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("socket connection established\n")
        #start ackreceiver thread
        t1 = threading.Thread(target=self.ackReceiver)
        t1.start()
        #start packetGenerator thread
        t2 = threading.Thread(target=self.packetGenerator)
        t2.start()

        while self.totalPacketsAck < self.args.maxPackets:
            self.lock.acquire()
            if self.LPSindex < len(self.buffer)-1 and self.isInWindow(self.bufferSeqNums[self.LPSindex+1]):
                
                self.LPSindex += 1
                seqNum = self.bufferSeqNums[self.LPSindex]
                message =  self.generateMessage(seqNum, self.buffer[self.LPSindex])
                self.totalNumTransmissions += 1
                self.lock.release()

                if self.args.verbose:
                    print(datetime.datetime.now(), "Seq #%d: packet sent" % seqNum)
                self.seqNumAttempts[seqNum] += 1
                
                if self.seqNumAttempts[seqNum] > 10:
                    print("client terminated as number of transmissions for seqNum #%d exceeds 5"%seqNum)
                    os._exit(1)

                self.seqSendTimes[seqNum] = time.time()
                self.seqNumTimers[seqNum] = threading.Timer(self.timeoutTime, self.timeout, args=(seqNum,))
                self.seqNumTimers[seqNum].start()
                self.sock.sendto(message.encode(), (self.args.receiverIP, self.args.receiverPortNo))

            else:    
                self.lock.release()
                
        t2.join()
        t1.join()
        self.sock.close()

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
    parser.add_argument("-t", type=float, action="store", dest="timeoutTime", default=0.3, help="sender timeout time")
    parser.add_argument("-m", type=int, action="store", dest="seqNumFieldLength", help="sequence number field length in bits")
    
    args = parser.parse_args()

    sender = ClientGBN(args)
    sender.transmitData()
