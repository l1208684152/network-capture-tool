#!/usr/bin/env python3
"""
验证修复后的抓包功能
"""

import sys
import os
import time
import logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("验证修复后的抓包功能")
print("=" * 60)

# 测试抓包
try:
    from network_capture_tool.core.capture_engine import CaptureEngine
    import queue
    import psutil

    print("\n[1] 创建抓包引擎...")
    packet_queue = queue.Queue()
    engine = CaptureEngine(packet_queue)

    print("\n[2] 获取测试进程...")
    # 查找有网络连接的进程
    test_pid = None
    try:
        all_connections = psutil.net_connections(kind='inet')
        # 按进程分组
        process_connections = {}
        for conn in all_connections:
            if conn.pid:
                if conn.pid not in process_connections:
                    process_connections[conn.pid] = []
                process_connections[conn.pid].append(conn)
        
        # 选择一个有网络连接的进程
        for pid, conns in process_connections.items():
            if len(conns) > 0:
                try:
                    process = psutil.Process(pid)
                    print(f"  选择进程: PID={pid}, Name={process.name()}")
                    print(f"  连接数: {len(conns)}")
                    for conn in conns[:2]:
                        print(f"    连接: {conn.laddr} -> {conn.raddr}")
                    test_pid = pid
                    break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    except Exception as e:
        print(f"  查找进程失败: {e}")

    if not test_pid:
        print("  未找到有网络连接的进程，使用当前Python进程")
        test_pid = os.getpid()

    print(f"\n[3] 使用测试PID: {test_pid}")
    print(f"\n[4] 开始抓包（10秒超时）...")
    print("  请在此时使用浏览器访问网站...")

    engine.start_capture(test_pid)

    # 等待一段时间，让抓包线程运行
    start_time = time.time()
    packet_count = 0

    while time.time() - start_time < 10:
        try:
            packet = packet_queue.get(timeout=1)
            if isinstance(packet, dict):
                packet_count += 1
                print(f"\n  捕获数据包 #{packet_count}:")
                print(f"    时间: {packet['time']}")
                print(f"    源: {packet['src']}:{packet['src_port']}")
                print(f"    目标: {packet['dst']}:{packet['dst_port']}")
                print(f"    协议: {packet['proto']}")
                print(f"    长度: {packet['length']}")
                print(f"    信息: {packet['info']}")
            elif isinstance(packet, tuple):
                if packet[0] == 'update':
                    print(f"  更新: {packet[1]}")
                elif packet[0] == 'error':
                    print(f"  错误: {packet[1]}")
        except queue.Empty:
            continue

    print(f"\n[5] 停止抓包...")
    engine.stop_capture()

    print("\n" + "=" * 60)
    if packet_count > 0:
        print(f"✓ 成功捕获 {packet_count} 个数据包！")
        print("  修复成功！")
    else:
        print("✗ 未能捕获到任何数据包")
        print("  可能的原因：")
        print("  1. 目标进程没有网络活动")
        print("  2. 进程过滤逻辑仍有问题")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
