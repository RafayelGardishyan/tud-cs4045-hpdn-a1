#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.link import TCLink

class ParkingLotTopo(Topo):
    def __init__(self, n):
        # Initialize topology
        Topo.__init__(self)
        prev = None
        for i in range(n):
            # Add hosts and a switch
            h1 = self.addHost(f'h{2 * i + 1}')
            h2 = self.addHost(f'h{2 * i + 2}')
            s1 = self.addSwitch(f's{i+1}')
            # Connect hosts to the switch
            self.addLink(h1, s1, cls=TCLink)
            self.addLink(h2, s1, cls=TCLink)
            # Connect switch to previous switch
            if prev is not None:
                self.addLink(prev, s1, bw=10, delay='5ms', cls=TCLink)
            prev = s1
        
# Expose topology to mn
topos = {'parkinglottopo': ParkingLotTopo}
