#!/usr/bin/env python3
"""
简单测试scapy库是否能够正常导入
"""

print("开始测试scapy导入...")

try:
    # 导入scapy
    from scapy.all import IP, TCP, UDP
    print("scapy导入成功!")
    print("IP类:", IP)
    print("TCP类:", TCP)
    print("UDP类:", UDP)
    print("测试完成: scapy库正常工作")
except ImportError as e:
    print(f"导入scapy失败: {e}")
except Exception as e:
    print(f"测试过程中发生错误: {e}")
