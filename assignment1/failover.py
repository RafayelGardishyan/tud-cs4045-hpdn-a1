###### HDPN Assignment 1.6 ######
#                               #
#   Author: Rafayel Gardishyan  #
#   Student nr.: 5686547        #
#                               #
#################################

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib import hub

class ThreePathsController(app_manager.RyuApp):
    """ Skeleton taken from ryu/app/simple_switch_13.py
    Adapted to handle the following network:
        
                /--- TCP / Unknown ---\
        h1 --- s1 ------- UDP ------- s2 --- h2
                \-------- ICMP -------/

    All TCP traffic takes Path 1 (port 2)
    All UDP traffic takes Path 2 (port 3)
    All ICMP traffic takes Path 3 (port 4)
    All other traffic takes Path 1 (port 2) - Everything that is not IPv4 or is a different protocol than the abovementioned

    Main logic for this routing to be found in `_packet_in_handler`

    Note: No flows are installed for the traffic in the "other" category - this is to make the flow_dump more readable
    """
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ThreePathsController, self).__init__(*args, **kwargs)

        ### SOME ASSIGNMENT RELATED INITIALISATION ###
        self.switch_datapath = None
        self.last_byte_count = 0
        hub.spawn(self.monitor)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if self.switch_datapath is None:
            self.switch_datapath = datapath

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
            
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        ipv4_pkt = pkt.get_protocols(ipv4.ipv4)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d")
        
        out_port = -1
        
        if in_port != 1:
            out_port = 1
        else:
            if ipv4_pkt:
                proto = ipv4_pkt[0].proto
                if proto == 6:
                    out_port = 2
                elif proto == 17:
                    out_port = 3
                elif proto == 1:
                    out_port = 4
                else:
                    # Other traffic, just using path 2
                    out_port = 2
                
            else:
                out_port = 2

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != -1:
            if ipv4_pkt and in_port == 1:
                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_type=0x0800,
                    ip_proto=ipv4_pkt[0].proto,
                    eth_dst=dst
                )

                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                    return
                else:
                    self.add_flow(datapath, 1, match, actions)


        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    ### MAIN ASSIGNMENT 1.6A LOGIC ###

    def monitor(self):
        while True:
            hub.sleep(1)
            if self.switch_datapath is None:
                continue
            ofp = self.switch_datapath.ofproto
            ofp_parser = self.switch_datapath.ofproto_parser

            cookie = cookie_mask = 0
            match = ofp_parser.OFPMatch(eth_type=0x0800)
            req = ofp_parser.OFPFlowStatsRequest(self.switch_datapath, 0,
                                                ofp.OFPTT_ALL,
                                                ofp.OFPP_ANY, ofp.OFPG_ANY,
                                                cookie, cookie_mask,
                                                match)
            self.switch_datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def stats_handler(self, ev):
        body = ev.msg.body

        for stat in body:
            if stat.match.get('ip_proto') != 6:
                continue

            bw = stat.byte_count - self.last_byte_count
            bw *= 8
            bw /= 1000000

            self.logger.info(f"bandwidth = {bw} Mbps")

            self.last_byte_count = stat.byte_count

    ### END MAIN ASSIGNMENT 1.6A LOGIC ###