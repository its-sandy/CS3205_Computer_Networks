import threading
import socket
import argparse
import time

class goBackNClient (args):
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

    def addPacketToBuffer(self):
        self.lock.acquire()
        if len(self.buffer) < self.args.bufferSize:

            if len(self.buffer) == 0:
                self.bufferSeqNums.append((self.LARseq + 1)%self.maxSeqNum)
            else:
                self.bufferSeqNums.append((self.bufferSeqNums[-1] + 1)%self.maxSeqNum)

            self.buffer.append(''.join([random.choice(string.ascii_letters  string.digits) for n in range(self.args.packetLength)]))
            self.lock.release()
            return True
        else:
            self.lock.release()
            return False

    def packetGenerator(self):
        i = 0
        while i < self.args.maxPackets:
            time.sleep(1/float(self.args.packetGenRate))
            if self.addPacketToBuffer():
                i += 1

    def ackReceiver(self, sock):
        while self.totalPacketsAck < self.maxPackets:  #change this
            ack, server = sock.recvfrom(512)
            self.lock.acquire()
            if len(self.buffer) > 0 and int(ack) == self.bufferSeqNums[0]:

                self.windowTimer.cancel()
                self.buffer.pop(0)
                self.bufferSeqNums.pop(0)
                self.LPSindex -= 1
                self.LARseq = int(ack)
                self.totalPacketsAck += 1

                if self.buffer:
                    self.windowTimer = threading.Timer(0.1, self.timeout, args=(self.bufferSeqNums[0]))
                    self.windowTimer.start()
            self.lock.release()

    def timeout(self, seqNum):
        #takes sequence number of the start of the window as parameter
        self.lock.acquire()
        if len(self.buffer) > 0 and seqNum == self.bufferSeqNums[0]:
            self.LPSindex = -1 #timer restarted in goBackNSender
        else:
            pass
        self.lock.release()
    
    def goBackNSender(self):
        #establish udp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #start ackreceiver thread
        t1 = threading.Thread(target=self.ackReceiver, args=(sock))
        t1.start()
        #start packetGenerator thread
        t2 = threading.Thread(target=self.packetGenerator)
        t2.start()

        while self.totalPacketsAck < self.args.maxPackets:  #change this
            if self.LPSindex < len(self.buffer)-1 and self.LPSindex < self.args.windowSize-1:
                self.lock.acquire()
                self.LPSindex += 1
                message = string(self.bufferSeqNums[self.LPSindex]) + "*" + self.buffer[self.LPSindex]
                if self.LPSindex == 0:
                    self.windowTimer = threading.Timer(0.1, self.timeout, args=(self.bufferSeqNums[0]))
                    self.windowTimer.start() #will lock make an issue
                self.lock.release()

                sock.sendto(message, (self.args.receiverIP, self.args.receiverPortNo))
                

                #start timer
                #RTTaverage calculation
        t2.join()
        t1.join()
        sock.close()


    #gobacknpacket sender should call timeout
    # ack receiver 

#thread to keep adding to input buffer
#should be able to receive ACK while sending packets
#should be able to send packets while waiting for ACK
#input and output sockets should be able to work simultaneously and also pile up


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", help="turn ON debug mode", action = "store_true")
    parser.add_argument("-s", type=str, action="store", dest="receiverIP", default="127.0.0.1",help="receiver name/ IP address")
    parser.add_argument("-p", type=int, action="store", dest="receiverPortNo", default=10000, help="receiver port number")
    parser.add_argument("-l", type=int, action="store", dest="packetLength", help="packet length (bytes)")
    parser.add_argument("-r", type=int, action="store", dest="packetGenRate", help="packet generation rate (pkts/sec)")
    parser.add_argument("-n", type=int, action="store", dest="maxPackets", help="maximum number of packets to be acknowledged")
    parser.add_argument("-w", type=int, action="store", dest="windowSize", help="sender window size")
    parser.add_argument("-b", type=int, action="store", dest="bufferSize", help="sender buffer size (must be greater than window size)")

	args = parser.parse_args()

    sender = goBackNClient(args)


    #check if you can replace the one lock for everything with more locks, or if u can remove any locks
    #check if buffer becoming empty is handled well
    #add error checks
    #terminating message to terminate both programs
    #will there be collision if both ends of UDP have data?
    #can many threads share the same socket?
    #replace list with queues

    #include assumption about timer in notes