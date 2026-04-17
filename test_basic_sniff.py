#!/usr/bin/env python3
"""
测试基本抓包（不进行进程过滤）
"""

import sys
import os
import time

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 60)
print("测试基本抓包（不使用进程过滤）")
print("=" * 60)

try:
    from scapy.all import sniff, IP, TCP, UDP, conf

    print("\n[1] 获取网络接口...")
    interfaces_list = list(conf.ifaces.values())
    print(f"    找到 {len(interfaces_list)} 个接口")

    # 选择WLAN接口
    selected_iface = None
    for iface in interfaces_list:
        iface_name = iface.name.lower()
        if 'wlan' in iface_name:
            selected_iface = iface.name
            print(f"    选择WLAN接口: {iface.name} ({iface.description})")
            break

    if not selected_iface:
        selected_iface = interfaces_list[0].name
        print(f"    未找到WLAN，使用第一个接口: {selected_iface}")

    print(f"\n[2] 开始抓包（5秒超时）...")
    print("    请在此时使用浏览器访问网站...")

    packet_count = [0]

    def packet_handler(packet):
        packet_count[0] += 1
        print(f"\n    捕获数据包 #{packet_count[0]}:")
        if packet.haslayer(IP):
            ip_layer = packet[IP]
            print(f"      源IP: {ip_layer.src} -> 目标IP: {ip_layer.dst}")

            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                print(f"      协议: TCP, 源端口: {tcp_layer.sport}, 目标端口: {tcp_layer.dport}")
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                print(f"      协议: UDP, 源端口: {udp_layer.sport}, 目标端口: {udp_layer.dport}")

        return packet_count[0] < 10  # 最多显示10个数据包

    packets = sniff(
        iface=selected_iface,
        prn=packet_handler,
        store=False,
        timeout=5
    )

    print(f"\n[3] 抓包完成，共捕获 {packet_count[0]} 个数据包")

    if packet_count[0] == 0:
        print("\n⚠️ 警告：没有捕获到任何数据包！")
        print("   可能的原因：")
        print("   1. Npcap/WinPcap 驱动未正确安装")
        print("   2. 需要管理员权限")
        print("   3. 接口选择不正确")
        print("   4. 网络没有活动")
    else:
        print(f"\n✓ 成功捕获 {packet_count[0]} 个数据包！")

except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
