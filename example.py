#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.link import TCLink

class SimpleTopo(Topo):
    def __init__(self):
        # Initialize topology
        Topo.__init__(self)
        # Add hosts and a switch
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch('s1')
        # Connect hosts to the switch
        self.addLink(h1, s1, bw=25, delay='15ms', loss=1, max_queue_size=80, cls=TCLink)
        self.addLink(h2, s1, bw=25, delay='15ms', loss=1, max_queue_size=80, cls=TCLink)
        
# Expose topology to mn
topos = {'simpletopo': SimpleTopo}
