from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch, Host
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel


def main():

    net = Mininet(
        controller=None,
        switch=OVSKernelSwitch,
        link=TCLink
    )

    # SDN controller
    c0 = RemoteController(
        'c0',
        ip='127.0.0.1',
        port=6653
    )
    net.addController(c0)

    # Open vSwitch
    s1 = net.addSwitch(
        's1',
        protocols='OpenFlow13'
    )

    # Mininet hosts
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    h4 = net.addHost('h4', ip='10.0.0.4/24')

    # Host-side connection.
    # This allows Ubuntu itself to reach the Mininet network.
    root0 = net.addHost(
        'root0',
        ip='10.0.0.254/24',
        inNamespace=False
    )

    # Links
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s1)
    net.addLink(root0, s1)

    net.start()

    print()
    print("======================================")
    print(" Multi-Client Chat SDN Network")
    print("======================================")
    print("h1 = 10.0.0.1")
    print("h2 = 10.0.0.2")
    print("h3 = 10.0.0.3")
    print("h4 = 10.0.0.4  <- Chat Server")
    print("root0 = 10.0.0.254 <- Ubuntu")
    print("======================================")
    print()

    CLI(net)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    main()
