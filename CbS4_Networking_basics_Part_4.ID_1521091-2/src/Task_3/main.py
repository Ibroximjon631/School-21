#!/usr/bin/env python3
from scapy.all import IP, TCP, Raw, send

packet = (
    IP(dst="127.0.0.1") /
    TCP(dport=12345, flags="PA") /
    Raw(load=b"Dear Steel Cat! This is no attack, it's my humster Pinkie you should track")
)

send(packet, verbose=False)
print("Message sent to 127.0.0.1:12345")
