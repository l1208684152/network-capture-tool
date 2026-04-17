#!/usr/bin/env python3
"""
测试scapy库是否能够正常工作
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("开始测试scapy库...")
logger.info("开始测试scapy库...")

try:
    # 导入scapy
    from scapy.all import sniff, conf, IP, TCP, UDP
    print("scapy导入成功")
    logger.info("scapy导入成功")
    
    # 获取可用网络接口
    interfaces = conf.ifaces.values()
    interface_names = [iface.name for iface in interfaces]
    print(f"可用网络接口: {interface_names}")
    logger.info(f"可用网络接口: {interface_names}")
    
    # 测试数据包解析
    print("测试数据包解析...")
    logger.info("测试数据包解析...")
    
    # 测试抓包功能
    print("测试抓包功能...")
    logger.info("测试抓包功能...")
    
    # 定义一个简单的数据包处理函数
    packet_count = 0
    max_packets = 3
    
    def packet_handler(packet):
        nonlocal packet_count
        packet_count += 1
        print(f"捕获到数据包 #{packet_count}")
        logger.info(f"捕获到数据包 #{packet_count}")
        
        # 解析数据包
        if packet.haslayer(IP):
            ip_layer = packet[IP]
            print(f"  源IP: {ip_layer.src}, 目标IP: {ip_layer.dst}")
            logger.info(f"  源IP: {ip_layer.src}, 目标IP: {ip_layer.dst}")
            
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                print(f"  协议: TCP, 源端口: {tcp_layer.sport}, 目标端口: {tcp_layer.dport}")
                logger.info(f"  协议: TCP, 源端口: {tcp_layer.sport}, 目标端口: {tcp_layer.dport}")
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                print(f"  协议: UDP, 源端口: {udp_layer.sport}, 目标端口: {udp_layer.dport}")
                logger.info(f"  协议: UDP, 源端口: {udp_layer.sport}, 目标端口: {udp_layer.dport}")
        
        return packet_count < max_packets
    
    # 开始抓包
    if interface_names:
        selected_interface = interface_names[0]
        print(f"在接口 {selected_interface} 上开始抓包，将捕获 {max_packets} 个数据包...")
        logger.info(f"在接口 {selected_interface} 上开始抓包，将捕获 {max_packets} 个数据包...")
        
        try:
            sniff(
                iface=selected_interface,
                filter="tcp or udp",
                prn=packet_handler,
                store=False,
                timeout=10
            )
            print("抓包测试完成")
            logger.info("抓包测试完成")
        except Exception as e:
            print(f"抓包测试失败: {e}")
            logger.error(f"抓包测试失败: {e}")
    else:
        print("没有可用的网络接口")
        logger.error("没有可用的网络接口")
        
except ImportError as e:
    print(f"导入scapy失败: {e}")
    logger.error(f"导入scapy失败: {e}")
except Exception as e:
    print(f"测试过程中发生错误: {e}")
    logger.error(f"测试过程中发生错误: {e}")

print("测试完成")
logger.info("测试完成")
