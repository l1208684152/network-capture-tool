#!/usr/bin/env python3
"""
测试数据包解析和内容显示
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from network_capture_tool.core.capture_engine import CaptureEngine
from queue import Queue

# 创建队列和抓包引擎
packet_queue = Queue()
engine = CaptureEngine(packet_queue)

# 测试数据包解析
from scapy.all import IP, TCP, UDP, Raw, DNS, DNSQR

# 创建测试数据包
test_packets = [
    # HTTP请求
    IP(src="192.168.1.1", dst="10.0.0.1") / 
    TCP(sport=12345, dport=80) / 
    Raw(load=b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"),
    
    # DNS查询
    IP(src="192.168.1.1", dst="8.8.8.8") / 
    UDP(sport=5353, dport=53) / 
    DNS(qr=0, qdcount=1) / 
    DNSQR(qname=b"example.com", qtype=1, qclass=1),
    
    # 普通TCP数据包
    IP(src="192.168.1.1", dst="10.0.0.1") / 
    TCP(sport=12345, dport=22) / 
    Raw(load=b"SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3"),
    
    # 普通UDP数据包
    IP(src="192.168.1.1", dst="10.0.0.1") / 
    UDP(sport=12345, dport=53) / 
    Raw(load=b"DNS query data"),
]

print("测试数据包解析和内容显示")
print("=" * 60)

for i, packet in enumerate(test_packets):
    print(f"\n测试数据包 #{i+1}")
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
        
        # 检查队列中的数据包
        while not packet_queue.empty():
            queue_item = packet_queue.get()
            if isinstance(queue_item, dict) and 'content' in queue_item:
                print(f"  队列中的数据包包含content字段: {queue_item['content']}")
            else:
                print(f"  队列中的数据包: {type(queue_item)}")
    else:
        print(f"  ❌ 解析失败")

print("\n" + "=" * 60)
print("测试完成")
