from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER
from os_ken.controller.handler import MAIN_DISPATCHER
from os_ken.controller.handler import set_ev_cls
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib.packet import packet
from os_ken.lib.packet import ethernet
from os_ken.lib.packet import ether_types
from os_ken.lib.packet import ipv4
from os_ken.lib.packet import tcp


class ChatSDNController(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # TCP port used by the Multi-Client Chat Server
    CHAT_PORT = 5000

    def __init__(self, *args, **kwargs):
        super(ChatSDNController, self).__init__(*args, **kwargs)

        # MAC address table
        self.mac_to_port = {}

    # ============================================================
    # SWITCH CONNECTION
    # ============================================================

    @set_ev_cls(
        ofp_event.EventOFPSwitchFeatures,
        CONFIG_DISPATCHER
    )
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath

        print(
            f"[SDN] Switch connected: DPID={datapath.id}"
        )

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Default rule:
        # packets that do not match another rule
        # are sent to the controller.
        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(
            datapath=datapath,
            priority=0,
            match=match,
            actions=actions
        )

        print(
            f"[SDN] Controller ready for DPID={datapath.id}"
        )

    # ============================================================
    # ADD FLOW
    # ============================================================

    def add_flow(
        self,
        datapath,
        priority,
        match,
        actions
    ):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions
        )

        datapath.send_msg(flow_mod)

    # ============================================================
    # PACKET-IN HANDLER
    # ============================================================

    @set_ev_cls(
        ofp_event.EventOFPPacketIn,
        MAIN_DISPATCHER
    )
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        dpid = datapath.id

        in_port = msg.match["in_port"]

        # Decode packet
        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(
            ethernet.ethernet
        )

        if eth is None:
            return

        # Ignore LLDP packets
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src = eth.src
        dst = eth.dst

        # ========================================================
        # MAC LEARNING
        # ========================================================

        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}

        self.mac_to_port[dpid][src] = in_port

        # ========================================================
        # CHECK FOR CHAT TRAFFIC
        # ========================================================

        is_chat = False

        chat_direction = None

        tcp_src_port = None
        tcp_dst_port = None

        ip_pkt = pkt.get_protocol(
            ipv4.ipv4
        )

        tcp_pkt = pkt.get_protocol(
            tcp.tcp
        )

        if ip_pkt is not None and tcp_pkt is not None:

            tcp_src_port = tcp_pkt.src_port
            tcp_dst_port = tcp_pkt.dst_port

            # Client -> Chat Server
            if tcp_dst_port == self.CHAT_PORT:

                is_chat = True
                chat_direction = "CLIENT_TO_SERVER"

            # Chat Server -> Client
            elif tcp_src_port == self.CHAT_PORT:

                is_chat = True
                chat_direction = "SERVER_TO_CLIENT"

        # ========================================================
        # TRAFFIC CLASSIFICATION
        # ========================================================

        if is_chat:

            print()
            print(
                "[SDN] ========================================"
            )

            print(
                "[SDN] CHAT TRAFFIC DETECTED"
            )

            print(
                f"[SDN] Direction: {chat_direction}"
            )

            print(
                f"[SDN] Source MAC: {src}"
            )

            print(
                f"[SDN] Destination MAC: {dst}"
            )

            print(
                f"[SDN] TCP: "
                f"{tcp_src_port} -> {tcp_dst_port}"
            )

            print(
                "[SDN] ========================================"
            )

        else:

            print(
                f"[SDN] Normal traffic: "
                f"{src} -> {dst}"
            )

        # ========================================================
        # FIND DESTINATION PORT
        # ========================================================

        if dst in self.mac_to_port[dpid]:

            out_port = self.mac_to_port[dpid][dst]

        else:

            out_port = ofproto.OFPP_FLOOD

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        # ========================================================
        # INSTALL FLOW
        # ========================================================

        if out_port != ofproto.OFPP_FLOOD:

            # ----------------------------------------------------
            # CHAT FLOW
            # ----------------------------------------------------

            if is_chat:

                if chat_direction == "CLIENT_TO_SERVER":

                    # Client -> Chat Server
                    match = parser.OFPMatch(
                        in_port=in_port,
                        eth_type=ether_types.ETH_TYPE_IP,
                        ip_proto=6,
                        tcp_dst=self.CHAT_PORT,
                        eth_dst=dst
                    )

                else:

                    # Chat Server -> Client
                    match = parser.OFPMatch(
                        in_port=in_port,
                        eth_type=ether_types.ETH_TYPE_IP,
                        ip_proto=6,
                        tcp_src=self.CHAT_PORT,
                        eth_dst=dst
                    )

                # Higher priority for chat traffic
                priority = 100

                print(
                    "[SDN] Installing HIGH PRIORITY "
                    "CHAT FLOW"
                )

                self.add_flow(
                    datapath=datapath,
                    priority=priority,
                    match=match,
                    actions=actions
                )

            # ----------------------------------------------------
            # NORMAL TRAFFIC FLOW
            # ----------------------------------------------------

            else:

                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst
                )

                priority = 10

                self.add_flow(
                    datapath=datapath,
                    priority=priority,
                    match=match,
                    actions=actions
                )

        # ========================================================
        # FORWARD CURRENT PACKET
        # ========================================================

        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:

            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)

        print(
            f"[SDN] Forwarded: "
            f"{src} -> {dst}"
        )


# ================================================================
# START OS-KEN
# ================================================================

if __name__ == "__main__":

    # Custom startup.
    # This avoids the HubThread.kill()
    # compatibility problem in your OS-Ken installation.

    app_mgr = app_manager.AppManager.get_instance()

    app_mgr.load_apps([
        "controller"
    ])

    contexts = app_mgr.create_contexts()

    services = app_mgr.instantiate_apps(
        **contexts
    )

    from os_ken.lib import hub

    hub.joinall(services)
