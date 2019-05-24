import threading
import socket
import argparse
import time

class client (args):
    def __init__(self, args):
        self.args = args
        self.LPS = 0 #last packets sent
        self.LAR = 0 #last acknowledgement received
        self.SWS = args.windowSize #sender window size
        self.maxSeqNum = 2*self.SWS + 1
        self.lock = threading.Lock()
        self.curBufferCount = 0
        self.buffer = ["filler"] * args.bufferSize
        self.bufferSeqNums = [0] * args.bufferSize

    def advanceSeqNum (seqNum, jump):
        return (seqNum + jump)%self.maxSeqNum

    def timeout(self, seqNum):
        self.lock.acquire()
        if  seqNum == self.advanceSeqNum(self.LAR, 1):
            self.LPS = self.LAR
        else:
            pass
        self.lock.release()

    def addPacket(self):
        self.lock.acquire()
        if self.curBufferCount != self.args.bufferSize:
            self.curBufferCount += 1
            self.buffer[self.advanceSeqNum(self.LAR, self.curBufferCount)] = (
                ''.join([random.choice(string.ascii_letters  string.digits) for n in range(self.args.packetLength)]))
            self.lock.release()
            return True
        else:
            self.lock.release()
            return False

    def packetGenerator(self):
        i = 0
        while i < self.args.maxPackets:
            time.sleep(1/float(self.args.packetGenRate))
            if self.addPacket:
                i += 1    

    #gobacknpacket sender should call timeout
    # ack receiver 

#thread to keep adding to input buffer
#should be able to receive ACK while sending packets
#should be able to send packets while waiting for ACK
#input and output sockets should be able to work simultaneously and also pile up


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", help="turn ON debug mode", action = "store_true")
    parser.add_argument("-s", type=str, action="store", dest="receiverIP", help="receiver name/ IP address")
    parser.add_argument("-p", type=int, action="store", dest="receiverPortNo", help="receiver port number")
    parser.add_argument("-l", type=int, action="store", dest="packetLength", help="packet length (bytes)")
    parser.add_argument("-r", type=int, action="store", dest="packetGenRate", help="packet generation rate (pkts/sec)")
    parser.add_argument("-n", type=int, action="store", dest="maxPackets", help="maximum number of packets to be acknowledged")
    parser.add_argument("-w", type=int, action="store", dest="windowSize", help="sender window size")
    parser.add_argument("-b", type=int, action="store", dest="bufferSize", help="sender buffer size")

	args = parser.parse_args()

    #check if you can replace the one lock for everything with more locks, or if u can remove any locks
    #check if buffer becoming empty is handled well