#!/usr/bin/env python3
"""
检查所有进程的网络连接
"""

import sys
import os
import psutil

print("=" * 60)
print("检查所有进程的网络连接")
print("=" * 60)

try:
    all_connections = psutil.net_connections(kind='inet')
    print(f"找到 {len(all_connections)} 个网络连接")
    
    # 按进程分组
    process_connections = {}
    for conn in all_connections:
        if conn.pid:
            if conn.pid not in process_connections:
                process_connections[conn.pid] = []
            process_connections[conn.pid].append(conn)
    
    print(f"有网络连接的进程数: {len(process_connections)}")
    
    # 显示前5个进程的连接
    print("\n前5个有网络连接的进程:")
    count = 0
    for pid, conns in process_connections.items():
        if count >= 5:
            break
        try:
            process = psutil.Process(pid)
            name = process.name()
            print(f"\n  进程: PID={pid}, Name={name}")
            print(f"  连接数: {len(conns)}")
            for conn in conns[:3]:  # 只显示前3个连接
                print(f"    连接: {conn.laddr} -> {conn.raddr} ({conn.status})")
            count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # 检查是否有浏览器相关进程
    print("\n浏览器相关进程的连接:")
    for pid, conns in process_connections.items():
        try:
            process = psutil.Process(pid)
            name = process.name().lower()
            if any(x in name for x in ['edge', 'chrome', 'firefox', 'browser']):
                print(f"  进程: PID={pid}, Name={process.name()}")
                print(f"  连接数: {len(conns)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # 检查端口
    all_ports = set()
    for conn in all_connections:
        if conn.laddr:
            all_ports.add(conn.laddr.port)
        if conn.raddr:
            all_ports.add(conn.raddr.port)
    print(f"\n所有连接使用的端口数: {len(all_ports)}")
    print(f"前20个端口: {list(all_ports)[:20]}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
