#!/usr/bin/env python3
"""
模拟抓包测试，检查content字段是否正确添加
"""

import sys
import os
import time
import queue

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from network_capture_tool.core.capture_engine import CaptureEngine

# 创建队列和抓包引擎
packet_queue = queue.Queue()
engine = CaptureEngine(packet_queue)

# 模拟数据包
class MockPacket:
    def __init__(self, src, dst, sport, dport, payload):
        self.src = src
        self.dst = dst
        self.sport = sport
        self.dport = dport
        self.payload = payload
        self.haslayer_calls = []
    
    def haslayer(self, layer):
        self.haslayer_calls.append(layer)
        if layer in ['IP', 'TCP', 'Raw']:
            return True
        return False
    
    def __getitem__(self, layer):
        if layer == 'IP':
            return self
        elif layer == 'TCP':
            return self
        elif layer == 'Raw':
            return self
        raise Exception(f"Unknown layer: {layer}")
    
    def __len__(self):
        return len(self.payload)

# 模拟数据包
mock_packets = [
    MockPacket('192.168.1.6', '120.240.112.94', 49298, 443, b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n'),
    MockPacket('120.240.112.94', '192.168.1.6', 443, 49298, b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nHello'),
    MockPacket('192.168.1.6', '8.8.8.8', 5353, 53, b'DNS query'),
]

print("模拟抓包测试")
print("=" * 60)

for i, mock_packet in enumerate(mock_packets):
    print(f"\n处理数据包 #{i+1}")
    print(f"  源: {mock_packet.src}:{mock_packet.sport}")
    print(f"  目标: {mock_packet.dst}:{mock_packet.dport}")
    
    # 解析数据包
    packet_info = engine.parse_packet(mock_packet, i+1)
    
    if packet_info:
        print(f"  解析成功!")
        print(f"  数据包键: {list(packet_info.keys())}")
        
        if 'content' in packet_info:
            print(f"  ✅ 包含content字段")
            print(f"  content: {packet_info['content']}")
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
