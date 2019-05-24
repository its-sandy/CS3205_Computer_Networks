import argparse
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, action="store", default=50, help="number of users sharing the channel")
    parser.add_argument("-w", type=int, action="store", default=2, help="initial collision window size")
    parser.add_argument("-p", type=float, action="store", default=0.02, help="packet generation rate")
    parser.add_argument("-m", type=int, action="store", default=4000, help="max packets")
    parser.add_argument("-v", help="turn ON verbose mode", action = "store_true")

    args = parser.parse_args()

    window_sizes = [args.w]*args.n #current collision window size
    k = [0]*args.n #backoff counter
    packet_generation_times = [list() for i in range(args.n)] #stores generation times of packets 
    current_time = 0
    num_packets_transmitted = 0
    average_delay = 0

    if args.v:
        print("#",current_time,"; pkt gen times = ", packet_generation_times ,"; windows = ", window_sizes, "; k = ", k, "num_packets_transmitted = ", num_packets_transmitted)
        print()

    while num_packets_transmitted < args.m:

        current_time += 1
        transmitting_nodes = []

        for i in range(args.n):
            if random.uniform(0,1) < args.p and len(packet_generation_times[i]) < 2:
                packet_generation_times[i].append(current_time)

            k[i] = max(0,k[i]-1)

            if k[i] == 0 and len(packet_generation_times[i]) > 0:
                transmitting_nodes.append(i)

        if len(transmitting_nodes) == 1:
            average_delay = (average_delay*num_packets_transmitted + (current_time - packet_generation_times[transmitting_nodes[0]].pop(0)))/(num_packets_transmitted + 1)
            num_packets_transmitted += 1
            k[transmitting_nodes[0]] = 0
            window_sizes[transmitting_nodes[0]] = max(2,int(window_sizes[transmitting_nodes[0]]*0.75))
            if args.v:
                print("#",current_time,"; transmitted from node: ", transmitting_nodes[0])
        else: #collision
            for i in transmitting_nodes:
                k[i] = random.randint(1,window_sizes[i])
                window_sizes[i] = min(256, window_sizes[i]*2)
            if args.v:
                print("#",current_time,"; collision between nodes: ", transmitting_nodes)
        
        if args.v:
            print("#",current_time,"; pkt gen times = ", packet_generation_times ,"; windows = ", window_sizes, "; k = ", k, "num_packets_transmitted = ", num_packets_transmitted)
            print()

    print("No. of Nodes (n) = ", args.n, "; w = ", args.w, "; p = ", args.p, "; Utilization = ", num_packets_transmitted/current_time, "; Average Packet Delay = ", average_delay)