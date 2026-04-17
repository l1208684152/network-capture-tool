#!/usr/bin/env python3
"""
全面测试抓包程序，诊断为什么抓不到任何数据
"""

import sys
import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("开始全面测试抓包程序")
print("=" * 60)

# 测试1：检查Python环境和依赖
print("\n[测试1] 检查Python环境和依赖...")
logger.info("检查Python环境和依赖...")
try:
    import scapy
    print(f"✓ Scapy版本: {scapy.__version__}")
    logger.info(f"Scapy版本: {scapy.__version__}")
except Exception as e:
    print(f"✗ Scapy导入失败: {e}")
    logger.error(f"Scapy导入失败: {e}")
    sys.exit(1)

try:
    import psutil
    print(f"✓ Psutil版本: {psutil.__version__}")
    logger.info(f"Psutil版本: {psutil.__version__}")
except Exception as e:
    print(f"✗ Psutil导入失败: {e}")
    logger.error(f"Psutil导入失败: {e}")
    sys.exit(1)

# 测试2：检查网络接口
print("\n[测试2] 检查网络接口...")
logger.info("检查网络接口...")
try:
    from scapy.all import conf
    interfaces = conf.ifaces.values()
    print(f"✓ 找到 {len(list(interfaces))} 个网络接口")
    logger.info(f"找到 {len(list(interfaces))} 个网络接口")

    # 重新获取接口列表
    interfaces = list(conf.ifaces.values())
    for i, iface in enumerate(interfaces):
        print(f"  接口 {i}: {iface.name}")
        print(f"    描述: {iface.description}")
        print(f"    MAC: {iface.mac}")
        logger.info(f"接口 {i}: {iface.name}, 描述: {iface.description}, MAC: {iface.mac}")
except Exception as e:
    print(f"✗ 获取网络接口失败: {e}")
    logger.error(f"获取网络接口失败: {e}")
    sys.exit(1)

# 测试3：测试基本抓包（不使用进程过滤）
print("\n[测试3] 测试基本抓包（不使用进程过滤）...")
logger.info("测试基本抓包（不使用进程过滤）...")

try:
    from scapy.all import sniff, IP, TCP, UDP

    packet_count = [0]

    def basic_packet_handler(packet):
        packet_count[0] += 1
        print(f"  捕获数据包 #{packet_count[0]}")
        logger.info(f"捕获数据包 #{packet_count[0]}")

        if packet.haslayer(IP):
            ip_layer = packet[IP]
            print(f"    源IP: {ip_layer.src}, 目标IP: {ip_layer.dst}")
            logger.info(f"源IP: {ip_layer.src}, 目标IP: {ip_layer.dst}")

            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                print(f"    协议: TCP, 源端口: {tcp_layer.sport}, 目标端口: {tcp_layer.dport}")
                logger.info(f"协议: TCP, 源端口: {tcp_layer.sport}, 目标端口: {tcp_layer.dport}")
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                print(f"    协议: UDP, 源端口: {udp_layer.sport}, 目标端口: {udp_layer.dport}")
                logger.info(f"协议: UDP, 源端口: {udp_layer.sport}, 目标端口: {udp_layer.dport}")

        return packet_count[0] < 5  # 只捕获5个数据包

    # 选择第一个接口
    if interfaces:
        selected_iface = interfaces[0]
        print(f"  使用接口: {selected_iface.name}")
        logger.info(f"使用接口: {selected_iface.name}")

        print("  开始抓包（5秒超时）...")
        logger.info("开始抓包（5秒超时）...")

        # 使用timeout参数
        packets = sniff(
            iface=selected_iface.name,
            prn=basic_packet_handler,
            store=False,
            timeout=5
        )

        print(f"  基本抓包完成，共捕获 {packet_count[0]} 个数据包")
        logger.info(f"基本抓包完成，共捕获 {packet_count[0]} 个数据包")

        if packet_count[0] == 0:
            print("  ⚠ 警告：没有捕获到任何数据包！")
            logger.warning("没有捕获到任何数据包！")
        else:
            print(f"  ✓ 成功捕获 {packet_count[0]} 个数据包")
            logger.info(f"成功捕获 {packet_count[0]} 个数据包")
    else:
        print("  ✗ 没有可用的网络接口")
        logger.error("没有可用的网络接口")
        sys.exit(1)

except Exception as e:
    print(f"  ✗ 基本抓包测试失败: {e}")
    logger.error(f"基本抓包测试失败: {e}")
    import traceback
    traceback.print_exc()
    logger.error(f"错误详情: {traceback.format_exc()}")

# 测试4：检查当前的网络连接
print("\n[测试4] 检查当前的网络连接...")
logger.info("检查当前的网络连接...")
try:
    connections = psutil.net_connections(kind='inet')
    print(f"  找到 {len(connections)} 个网络连接")
    logger.info(f"找到 {len(connections)} 个网络连接")

    # 显示前10个连接
    for i, conn in enumerate(connections[:10]):
        print(f"  连接 {i}: {conn.laddr} -> {conn.raddr} ({conn.status})")
        logger.info(f"连接 {i}: {conn.laddr} -> {conn.raddr} ({conn.status})")

except Exception as e:
    print(f"  ✗ 检查网络连接失败: {e}")
    logger.error(f"检查网络连接失败: {e}")

# 测试5：获取浏览器进程
print("\n[测试5] 获取浏览器进程...")
logger.info("获取浏览器进程...")
try:
    browsers = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if 'chrome' in name or 'firefox' in name or 'msedge' in name or 'browser' in name:
                browsers.append(proc.info)
                print(f"  浏览器进程: PID={proc.info['pid']}, Name={proc.info['name']}")
                logger.info(f"浏览器进程: PID={proc.info['pid']}, Name={proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not browsers:
        print("  ⚠ 没有找到常见的浏览器进程")
        logger.warning("没有找到常见的浏览器进程")
        # 显示所有进程
        print("  所有进程:")
        for proc in psutil.process_iter(['pid', 'name'])[:10]:
            try:
                print(f"    PID={proc.info['pid']}, Name={proc.info['name']}")
                logger.info(f"PID={proc.info['pid']}, Name={proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    else:
        print(f"  ✓ 找到 {len(browsers)} 个浏览器进程")
        logger.info(f"找到 {len(browsers)} 个浏览器进程")

except Exception as e:
    print(f"  ✗ 获取浏览器进程失败: {e}")
    logger.error(f"获取浏览器进程失败: {e}")

# 测试6：测试带进程过滤的抓包
print("\n[测试6] 测试带进程过滤的抓包...")
logger.info("测试带进程过滤的抓包...")

if browsers:
    test_pid = browsers[0]['pid']
    print(f"  使用测试PID: {test_pid}")
    logger.info(f"使用测试PID: {test_pid}")

    try:
        process = psutil.Process(test_pid)
        print(f"  进程名称: {process.name()}")
        logger.info(f"进程名称: {process.name()}")

        # 获取进程的网络连接
        process_connections = process.connections(kind='inet')
        print(f"  进程网络连接数: {len(process_connections)}")
        logger.info(f"进程网络连接数: {len(process_connections)}")

        for i, conn in enumerate(process_connections):
            print(f"    连接 {i}: {conn.laddr} -> {conn.raddr} ({conn.status})")
            logger.info(f"连接 {i}: {conn.laddr} -> {conn.raddr} ({conn.status})")

        # 构建端口集合
        process_ports = set()
        for conn in process_connections:
            process_ports.add(conn.laddr.port)
            if conn.raddr:
                process_ports.add(conn.raddr.port)

        print(f"  进程使用的端口: {process_ports}")
        logger.info(f"进程使用的端口: {process_ports}")

        # 测试抓包
        from scapy.all import sniff, IP, TCP, UDP

        filtered_packet_count = [0]

        def filtered_packet_handler(packet):
            if not packet.haslayer(IP):
                return True

            if packet.haslayer(TCP):
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
            elif packet.haslayer(UDP):
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
            else:
                return True

            # 检查端口是否匹配
            if src_port in process_ports or dst_port in process_ports:
                filtered_packet_count[0] += 1
                print(f"  [匹配] 数据包 #{filtered_packet_count[0]}: {packet[IP].src}:{src_port} -> {packet[IP].dst}:{dst_port}")
                logger.info(f"[匹配] 数据包 #{filtered_packet_count[0]}: {packet[IP].src}:{src_port} -> {packet[IP].dst}:{dst_port}")

            return filtered_packet_count[0] < 5

        print("  开始抓包（10秒超时）...")
        logger.info("开始抓包（10秒超时）...")

        packets = sniff(
            iface=interfaces[0].name,
            prn=filtered_packet_handler,
            store=False,
            timeout=10
        )

        print(f"  带进程过滤的抓包完成，共捕获 {filtered_packet_count[0]} 个匹配的数据包")
        logger.info(f"带进程过滤的抓包完成，共捕获 {filtered_packet_count[0]} 个匹配的数据包")

        if filtered_packet_count[0] == 0:
            print("  ⚠ 警告：没有捕获到与进程匹配的数据包！")
            logger.warning("没有捕获到与进程匹配的数据包！")
        else:
            print(f"  ✓ 成功捕获 {filtered_packet_count[0]} 个匹配的数据包")
            logger.info(f"成功捕获 {filtered_packet_count[0]} 个匹配的数据包")

    except Exception as e:
        print(f"  ✗ 带进程过滤的抓包测试失败: {e}")
        logger.error(f"带进程过滤的抓包测试失败: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"错误详情: {traceback.format_exc()}")
else:
    print("  ⚠ 没有找到浏览器进程，跳过测试")
    logger.warning("没有找到浏览器进程，跳过测试")

print("\n" + "=" * 60)
print("全面测试完成")
print("=" * 60)
