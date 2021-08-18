#!/usr/bin/env python

import socket
import ssl
import SocketServer
import threading
import os

#https://tools.ietf.org/html/rfc1035
DNS_RETURN_CODE = { 
    0: 'Success',
    1: 'Format Error',
    2: 'Server failure',
    3: 'Name Error',
    4: 'Not Implemented',
    5: 'Refused'
}

def domain_lookup(dns_server, port, question, **kwargs):
    protocol = kwargs.get('protocol', 'tcp')
    server = (dns_server, port)

    ## General DNS Lookup
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect(server)
    # sock.send(query)

    ## DNS over TLS Lookup
    s = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    s.verify_mode = ssl.CERT_NONE
    s.check_hostname = False

    conn = s.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    conn.connect(server)
    conn.send(question)
    answer = conn.recv(1024)
    flags = answer[:6].encode("hex")
    rcode = int(str(flags)[11:],16)
    
    print DNS_RETURN_CODE.get(rcode, 'RCODE Error(6~15)')
    
    if protocol == 'udp':
        answer = answer[2:]
    
    return (rcode, answer)

class DNSUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        tcp_data = "\x00"+ chr(len(data)) + data

        (rcode, answer) = domain_lookup(os.environ['DNS_SERVER_IP'], int(os.environ['DNS_SERVER_PORT']), tcp_data, protocol = 'udp')

        if rcode == 0:
            print "(UDP) Response Domain lookup"
            socket.sendto(answer, self.client_address)
                
class DNSTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()

        (rcode, answer) = domain_lookup(os.environ['DNS_SERVER_IP'], int(os.environ['DNS_SERVER_PORT']), data)

        if rcode == 0:
            print "(TCP) Response Domain lookup"
            self.request.sendall(answer)

if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = int(os.environ['DOT_PORT'])
    
    #Bind TCP Proxy
    SocketServer.TCPServer.allow_reuse_address = True
    tcpserver = SocketServer.TCPServer((HOST, PORT), DNSTCPHandler)
    ts = threading.Thread(target=tcpserver.serve_forever)

    #Bind UDP Proxy
    SocketServer.UDPServer.allow_reuse_address = True
    udpserver = SocketServer.UDPServer((HOST, PORT), DNSUDPHandler)
    us = threading.Thread(target=udpserver.serve_forever)

    for th in ts, us:
        th.start()
            