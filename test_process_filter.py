#!/usr/bin/env python3
"""
测试进程过滤逻辑
"""

import sys
import os
import time
import psutil
from scapy.all import sniff, IP, TCP, UDP, conf

print("=" * 60)
print("测试进程过滤逻辑")
print("=" * 60)

# 获取测试进程
test_pid = None
test_process_name = None

try:
    all_connections = psutil.net_connections(kind='inet')
    process_connections = {}
    for conn in all_connections:
        if conn.pid:
            if conn.pid not in process_connections:
                process_connections[conn.pid] = []
            process_connections[conn.pid].append(conn)
    
    for pid, conns in process_connections.items():
        if len(conns) > 0:
            try:
                process = psutil.Process(pid)
                print(f"  选择进程: PID={pid}, Name={process.name()}")
                print(f"  连接数: {len(conns)}")
                for conn in conns[:2]:
                    print(f"    连接: {conn.laddr} -> {conn.raddr}")
                test_pid = pid
                test_process_name = process.name()
                break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
except Exception as e:
    print(f"  查找进程失败: {e}")

if not test_pid:
    print("  未找到有网络连接的进程，使用当前Python进程")
    test_pid = os.getpid()
    test_process_name = "python.exe"

print(f"\n使用测试PID: {test_pid}, 进程名: {test_process_name}")

# 构建进程端口集合
process_ports = set()
try:
    all_connections = psutil.net_connections(kind='inet')
    for conn in all_connections:
        if conn.pid == test_pid:
            if conn.laddr:
                process_ports.add(conn.laddr.port)
            if conn.raddr:
                process_ports.add(conn.raddr.port)
        else:
            # 检查同名进程
            try:
                other_process = psutil.Process(conn.pid)
                if other_process.name() == test_process_name:
                    if conn.laddr:
                        process_ports.add(conn.laddr.port)
                    if conn.raddr:
                        process_ports.add(conn.raddr.port)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    print(f"  进程使用的端口: {process_ports}")
except Exception as e:
    print(f"  获取端口失败: {e}")

# 选择网络接口
selected_iface = None
interfaces_list = list(conf.ifaces.values())
for iface in interfaces_list:
    iface_name = iface.name.lower()
    if 'wlan' in iface_name:
        selected_iface = iface.name
        print(f"  选择WLAN接口: {iface.name}")
        break

if not selected_iface:
    selected_iface = interfaces_list[0].name
    print(f"  未找到WLAN，使用第一个接口: {selected_iface}")

print(f"\n开始抓包（5秒超时）...")
print("  请在此时使用浏览器访问网站...")

packet_count = [0]
matching_count = [0]

# 简单的数据包处理函数
def packet_handler(packet):
    packet_count[0] += 1
    
    if not packet.haslayer(IP):
        return True
    
    ip_src = packet[IP].src
    ip_dst = packet[IP].dst
    
    if packet.haslayer(TCP):
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
        proto = "TCP"
    elif packet.haslayer(UDP):
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
        proto = "UDP"
    else:
        return True
    
    # 检查是否匹配进程端口
    if src_port in process_ports or dst_port in process_ports:
        matching_count[0] += 1
        print(f"\n  [匹配] 数据包 #{matching_count[0]}:")
        print(f"    源: {ip_src}:{src_port}")
        print(f"    目标: {ip_dst}:{dst_port}")
        print(f"    协议: {proto}")
    
    return packet_count[0] < 50

# 开始抓包
try:
    packets = sniff(
        iface=selected_iface,
        prn=packet_handler,
        store=False,
        timeout=5
    )
    
    print(f"\n抓包完成：")
    print(f"  总共捕获: {packet_count[0]} 个数据包")
    print(f"  匹配进程: {matching_count[0]} 个数据包")
    
    if matching_count[0] > 0:
        print("\n✓ 成功捕获到匹配进程的数据包！")
    else:
        print("\n✗ 未捕获到匹配进程的数据包")
        print("  可能的原因：")
        print("  1. 进程没有网络活动")
        print("  2. 端口集合不完整")
        print("  3. 进程过滤逻辑有问题")
        
except Exception as e:
    print(f"\n✗ 抓包失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
