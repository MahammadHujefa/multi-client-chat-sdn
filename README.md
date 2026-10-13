# Multi-Client Chat Network Using SDN

## 1. Project Overview

The Multi-Client Chat Network is a networked chat application developed
using TCP socket programming and Software-Defined Networking (SDN).

The application allows multiple users to communicate through a browser-based
interface. A TCP server manages client connections and chat messages,
while an SDN controller manages packet forwarding in the Mininet network.

The project demonstrates socket programming, concurrent client handling,
network topology design, SDN traffic classification, and performance testing.

## 2. Objectives

- Implement client-server communication using TCP sockets.
- Support multiple simultaneous chat clients.
- Provide a browser-based chat interface.
- Deploy the chat server in a Mininet network.
- Use an SDN controller with OpenFlow 1.3.
- Identify and classify chat traffic.
- Evaluate application response time and concurrent connections.

## 3. Technologies Used

- Python
- TCP socket programming
- HTML, CSS, and JavaScript
- WebSockets
- Mininet
- Open vSwitch
- OS-Ken SDN controller
- OpenFlow 1.3
- Linux Ubuntu

## 4. System Architecture

The system contains the following components:

1. Browser clients
2. Frontend interface
3. WebSocket bridge
4. TCP chat server
5. Mininet network
6. Open vSwitch
7. OS-Ken SDN controller

The browser communicates with the WebSocket bridge.
The bridge forwards chat communication to the TCP server running
inside Mininet host h4.

The SDN controller communicates with the Open vSwitch and manages
packet-forwarding rules.

## 5. Network Topology

The Mininet topology contains four hosts and one switch.

| Device | IP Address | Purpose |
|--------|------------|---------|
| h1 | 10.0.0.1 | Mininet client |
| h2 | 10.0.0.2 | Mininet client |
| h3 | 10.0.0.3 | Mininet client |
| h4 | 10.0.0.4 | TCP chat server |
| s1 | OpenFlow switch | Packet forwarding |
| Controller | 127.0.0.1:6653 | SDN control connection |

The TCP chat server listens on port 5000.

The SDN controller uses OpenFlow 1.3 to communicate with the switch.

## 6. TCP Chat Server

The TCP server is implemented in Python.

It uses socket programming to accept client connections and threading
to handle multiple clients concurrently.

The server supports the following chat operations:

- User registration using a username
- Communication between users
- Default general chat room
- Joining chat rooms
- Listing available rooms
- Listing users
- Private messaging
- Help commands

The TCP server listens on port 5000.

## 7. SDN Controller

The SDN controller is implemented using OS-Ken.

Its responsibilities include:

- Communicating with the OpenFlow switch
- Learning source MAC addresses
- Forwarding packets
- Identifying TCP chat traffic on port 5000
- Classifying traffic direction
- Installing higher-priority flow rules for matching chat traffic

The controller has displayed logs identifying chat traffic and
installing high-priority OpenFlow rules.

A higher-priority rule determines which matching flow rule takes precedence.
It does not, by itself, guarantee improved latency or bandwidth.

## 8. Project Directory

The main project files are organized as follows:

    multi-client-chat/
    ├── client/
    ├── frontend/
    │   ├── index.html
    │   ├── script.js
    │   └── style.css
    ├── sdn/
    │   ├── controller.py
    │   ├── run_controller.py
    │   └── topology.py
    ├── server/
    │   └── server.py
    ├── web/
    │   └── web_server.py
    ├── tests/
    │   ├── performance_test.py
    │   └── scalability_test.py
    └── README.md

Additional backup files may exist in the working directory.

## 9. Starting the Application

The following instructions describe the intended startup sequence.
Run each component in a separate terminal.

### Terminal 1: Start the SDN Controller

    cd ~/multi-client-chat/sdn
    source ryu-venv/bin/activate
    python controller.py

Wait for the controller to report that the switch has connected.

### Terminal 2: Start Mininet

    cd ~/multi-client-chat/sdn
    sudo mn -c
    sudo python3 topology.py

Wait for the mininet> prompt.

### Start the TCP Server Inside h4

At the mininet> prompt, run:

    h4 python3 /home/mahammad-hujefa/multi-client-chat/server/server.py > /tmp/chat-server.log 2>&1 &

The server should listen on 10.0.0.4:5000.

### Terminal 3: Start the WebSocket Bridge

    cd ~/multi-client-chat/web
    source ../web-venv/bin/activate
    python3 web_server.py

### Terminal 4: Start the Frontend

    cd ~/multi-client-chat/frontend
    python3 -m http.server 8080

Open the following address in the Ubuntu browser:

    http://127.0.0.1:8080

Use different usernames in separate browser tabs to test multiple clients.

Note: These commands reflect the current project setup and should be
verified against the final source files before submission.

## 10. Testing Procedures

### Test 1: Browser Communication

1. Open the frontend.
2. Log in with one username.
3. Open another browser tab.
4. Log in with a different username.
5. Exchange messages.
6. Test the available chat features.

### Test 2: TCP Server

Check the listening socket inside Mininet:

    h4 ss -lntp | grep ':5000'

The server should show port 5000 in the LISTEN state.

### Test 3: SDN Traffic Classification

Generate chat traffic and inspect the controller terminal.

The controller should identify matching TCP traffic on port 5000
and report the associated forwarding rule.

### Test 4: Response-Time Evaluation

Run the performance test from the Ubuntu terminal:

    cd ~/multi-client-chat
    python3 tests/performance_test.py

The test connects multiple clients to the TCP server and measures
the time between sending a help request and receiving a response.

## 11. Initial Performance Results

The initial five-client test produced the following measurements:

| Metric | Measured Result |
|--------|-----------------|
| Clients tested | 5 |
| Successful clients | 5 |
| Failed clients | 0 |
| Success rate | 100% |
| Average response time | 0.36 ms |
| Minimum response time | 0.02 ms |
| Maximum response time | 0.78 ms |

These are results from one test run in the current environment.
They are not guaranteed performance figures.

The measurements represent application-level request-response time,
not pure network latency.

A larger scalability test is required to evaluate performance under
different concurrent client loads.

## 12. Limitations

- Performance results depend on the test environment.
- Larger concurrent-client tests are still required.
- Higher-priority OpenFlow rules do not guarantee QoS.
- The complete startup procedure must be verified before reproduction.
- The system has not yet been independently reproduced on another machine.

## 13. Future Improvements

- Perform larger scalability and throughput tests.
- Record repeatable performance measurements.
- Improve traffic monitoring and reporting.
- Add automated test reports.
- Improve error handling and connection management.
- Publish the final source code and documentation on GitHub.

## 14. Conclusion

The project demonstrates a TCP-based multi-client chat application
integrated with a Mininet network and an OS-Ken SDN controller.

Initial tests demonstrated browser communication, concurrent TCP client
connections, response-time measurement, and SDN classification of chat
traffic.

Further scalability testing and final reproduction checks are required
to complete the evaluation and prepare the project for submission.