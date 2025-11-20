from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4

class ThreePathsController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ThreePathsController, self).__init__(*args, **kwargs)
        self.mac_to_prt = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

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
            
        self.logger.info(
            "++ Installing flow | dp=%016x priority=%d buffer_id=%s match=%s actions=%s",
            datapath.id,
            priority,
            str(buffer_id),
            match,
            actions,
        )
        
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

        self.logger.info(f"Packet came in at switch_{dpid} from port {in_port}\n  (source: {src}; destination: {dst})")

        out_port = -1
        
        if in_port != 1:
            out_port = 1
        else:
            if ipv4_pkt:
                proto = ipv4_pkt[0].proto
                if proto == 6:
                    self.logger.info("    > It is a TCP packet")
                    out_port = 2
                elif proto == 17:
                    self.logger.info("    > It is a UDP packet")
                    out_port = 3
                elif proto == 1:
                    self.logger.info("    > It is an ICMP packet")
                    out_port = 4
                else:
                    # Unknown, just using path 2
                    self.logger.info("    > It is an unknown IPv4 protocol")
                    out_port = 2
                
                self.logger.info(f"        > We decided to forward packets like this to port {out_port}")
            else:
                self.logger.info("    > It is not a IPv4 protocol packet - Default port is 2")
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
            # elif in_port == 1:
            #     match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # else:
            #     match = parser.OFPMatch(in_port=in_port, eth_dst=dst)

        if msg.buffer_id != ofproto.OFP_NO_BUFFER:
            self.add_flow(datapath, 1, match, actions, msg.buffer_id)
            return
        else:
            self.add_flow(datapath, 1, match, actions)

        self.logger.info("        > Installed flow! Yippieee")

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
