#!/usr/bin/env python3
"""
测试数据包解析是否包含content字段
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from network_capture_tool.core.capture_engine import CaptureEngine
from queue import Queue

# 创建队列和抓包引擎
queue = Queue()
engine = CaptureEngine(queue)

# 测试数据包解析
from scapy.all import IP, TCP, UDP, Raw, DNS, DNSQR
from scapy.layers.http import HTTPRequest, HTTPResponse

# 创建测试数据包
test_packets = [
    # HTTP请求
    IP(src="192.168.1.1", dst="10.0.0.1") / 
    TCP(sport=12345, dport=80) / 
    HTTPRequest(Method=b"GET", Path=b"/index.html", Http_Version=b"HTTP/1.1") / 
    Raw(load=b"test data"),
    
    # HTTP响应
    IP(src="10.0.0.1", dst="192.168.1.1") / 
    TCP(sport=80, dport=12345) / 
    HTTPResponse(Http_Version=b"HTTP/1.1", Status_Code=b"200", Reason_Phrase=b"OK") / 
    Raw(load=b"<html><body>Hello</body></html>"),
    
    # DNS查询
    IP(src="192.168.1.1", dst="8.8.8.8") / 
    UDP(sport=5353, dport=53) / 
    DNS(qr=0, qdcount=1) / 
    DNSQR(qname=b"example.com", qtype=1, qclass=1),
    
    # 普通TCP数据包
    IP(src="192.168.1.1", dst="10.0.0.1") / 
    TCP(sport=12345, dport=22) / 
    Raw(load=b"SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3"),
]

print("测试数据包解析是否包含content字段...")
print("=" * 60)

for i, packet in enumerate(test_packets):
    print(f"\n测试数据包 #{i+1}:")
    print(f"类型: {type(packet)}")
    
    # 解析数据包
    packet_info = engine.parse_packet(packet, i+1)
    
    if packet_info:
        print(f"  解析成功!")
        print(f"  数据包键: {list(packet_info.keys())}")
        
        if 'content' in packet_info:
            print(f"  ✅ 包含content字段")
            print(f"  content类型: {packet_info['content'].get('type', 'Unknown')}")
            print(f"  content内容: {packet_info['content']}")
        else:
            print(f"  ❌ 缺少content字段")
    else:
        print(f"  ❌ 解析失败")

print("\n" + "=" * 60)
print("测试完成")
