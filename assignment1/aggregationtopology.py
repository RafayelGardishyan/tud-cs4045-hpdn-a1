#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.link import TCLink

class AggTopo(Topo):
    def __init__(self, n, k):
        # Initialize topology
        Topo.__init__(self)
        prev = None
        prev_list = []
        agg_list = []
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
            # Add switch to previous not-aggregated switches list
            prev = s1
            prev_list.append(s1)
            
            if len(prev_list) == k:
                # Create aggregation switch
                a1 = self.addSwitch(f'a{len(agg_list)+1}')
                # Connect agg to every switch in prev_switches
                for s in prev_list:
                    self.addLink(a1, s, bw=25, delay='5ms', cls=TCLink)
                prev_list = []
                # Connect agg to every other agg
                for a in agg_list:
                    self.addLink(a1, a, bw=100, delay='5ms', cls=TCLink)
                agg_list.append(a1)
        # Handle case where switches are not divisible by k
        if len(prev_list) > 0:
            # Create aggregation switch
                a1 = self.addSwitch(f'a{len(agg_list)+1}')
                # Connect agg to every switch in prev_switches
                for s in prev_list:
                    self.addLink(a1, s, bw=25, delay='5ms', cls=TCLink)
                prev_list = []
                # Connect agg to every other agg
                for a in agg_list:
                    self.addLink(a1, a, bw=100, delay='5ms', cls=TCLink)
                agg_list.append(a1)
        
# Expose topology to mn
topos = {'aggtopo': AggTopo}
