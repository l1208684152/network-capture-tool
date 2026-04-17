#!/usr/bin/env python3
"""
模拟UI测试，检查show_packet_detail方法
"""

import sys
import os

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

print("模拟UI测试 - 检查show_packet_detail方法")
print("=" * 60)

# 模拟show_packet_detail方法的逻辑
def simulate_show_packet_detail(packet):
    """模拟show_packet_detail方法"""
    print(f"\n处理数据包:")
    print(f"  源: {packet['src']}:{packet['src_port']}")
    print(f"  目标: {packet['dst']}:{packet['dst_port']}")
    print(f"  协议: {packet['proto']}")
    
    # 显示内容解析
    content_detail = "=== 内容解析 ===\n"
    try:
        if 'content' in packet:
            content = packet['content']
            if content:
                content_type = content.get('type', 'Unknown')
                content_detail += f"类型: {content_type}\n\n"
                
                if content_type == 'HTTP Request':
                    content_detail += "HTTP请求信息:\n"
                    if 'method' in content:
                        content_detail += f"方法: {content['method']}\n"
                    if 'path' in content:
                        content_detail += f"路径: {content['path']}\n"
                    if 'version' in content:
                        content_detail += f"版本: {content['version']}\n"
                    if 'headers' in content:
                        content_detail += "\n请求头:\n"
                        for key, value in content['headers'].items():
                            content_detail += f"  {key}: {value}\n"
                    if 'body' in content:
                        content_detail += "\n请求体:\n"
                        content_detail += content['body'][:1000] + ("..." if len(content['body']) > 1000 else "")
                
                elif content_type == 'HTTP Response':
                    content_detail += "HTTP响应信息:\n"
                    if 'version' in content:
                        content_detail += f"版本: {content['version']}\n"
                    if 'status' in content:
                        content_detail += f"状态码: {content['status']}\n"
                    if 'reason' in content:
                        content_detail += f"原因: {content['reason']}\n"
                    if 'headers' in content:
                        content_detail += "\n响应头:\n"
                        for key, value in content['headers'].items():
                            content_detail += f"  {key}: {value}\n"
                    if 'body' in content:
                        content_detail += "\n响应体:\n"
                        content_detail += content['body'][:1000] + ("..." if len(content['body']) > 1000 else "")
                
                elif content_type == 'DNS Query':
                    content_detail += "DNS查询信息:\n"
                    if 'qname' in content:
                        content_detail += f"查询域名: {content['qname']}\n"
                    if 'qtype' in content:
                        content_detail += f"查询类型: {content['qtype']}\n"
                    if 'qclass' in content:
                        content_detail += f"查询类: {content['qclass']}\n"
                
                elif content_type == 'DNS Response':
                    content_detail += "DNS响应信息:\n"
                    if 'qr' in content:
                        content_detail += f"QR: {content['qr']}\n"
                    if 'rcode' in content:
                        content_detail += f"响应码: {content['rcode']}\n"
                    if 'ancount' in content:
                        content_detail += f"回答数: {content['ancount']}\n"
                
                elif content_type == 'Raw Data':
                    content_detail += "原始数据:\n"
                    if 'payload' in content:
                        content_detail += content['payload'][:1000] + ("..." if len(content['payload']) > 1000 else "")
                
                elif content_type == 'Binary Data':
                    content_detail += "二进制数据:\n"
                    if 'length' in content:
                        content_detail += f"长度: {content['length']} bytes\n"
                        content_detail += "（二进制数据已省略）"
                
                elif content_type == 'Basic Packet':
                    content_detail += "基本数据包信息:\n"
                    if 'protocol' in content:
                        content_detail += f"协议: {content['protocol']}\n"
                    if 'src_port' in content:
                        content_detail += f"源端口: {content['src_port']}\n"
                    if 'dst_port' in content:
                        content_detail += f"目标端口: {content['dst_port']}\n"
            else:
                content_detail += "Content为空字典\n"
        else:
            content_detail += "无Content字段\n"
    except Exception as e:
        content_detail += f"显示内容解析失败: {str(e)}\n"
    
    print(content_detail)

# 测试每个数据包
for i, packet in enumerate(test_packets):
    print(f"\n测试数据包 #{i+1}")
    # 解析数据包
    packet_info = engine.parse_packet(packet, i+1)
    
    if packet_info:
        print(f"  解析成功!")
        # 模拟显示详情
        simulate_show_packet_detail(packet_info)
    else:
        print(f"  ❌ 解析失败")

print("\n" + "=" * 60)
print("测试完成")
