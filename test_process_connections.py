#!/usr/bin/env python3
"""
测试进程连接获取
"""

import sys
import os
import time
import psutil

print("=" * 60)
print("测试进程连接获取")
print("=" * 60)

# 获取浏览器进程
browsers = []
for proc in psutil.process_iter(['pid', 'name']):
    try:
        name = proc.info['name'].lower()
        if 'msedge.exe' in name or 'chrome.exe' in name or 'firefox.exe' in name:
            browsers.append(proc.info)
            print(f"  找到浏览器: PID={proc.info['pid']}, Name={proc.info['name']}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if not browsers:
    print("  没有找到浏览器进程，使用当前Python进程")
    test_pid = os.getpid()
else:
    test_pid = browsers[0]['pid']

print(f"\n使用测试PID: {test_pid}")

# 测试1: 使用process.connections()
print("\n[测试1] 使用process.connections()")
try:
    process = psutil.Process(test_pid)
    connections = process.connections(kind='inet')
    print(f"  找到 {len(connections)} 个连接")
    for conn in connections:
        print(f"  连接: {conn.laddr} -> {conn.raddr} ({conn.status})")
except Exception as e:
    print(f"  错误: {e}")

# 测试2: 使用psutil.net_connections()
print("\n[测试2] 使用psutil.net_connections()")
try:
    all_connections = psutil.net_connections(kind='inet')
    process_connections = [conn for conn in all_connections if conn.pid == test_pid]
    print(f"  找到 {len(process_connections)} 个连接")
    for conn in process_connections:
        print(f"  连接: {conn.laddr} -> {conn.raddr} ({conn.status})")
except Exception as e:
    print(f"  错误: {e}")

# 测试3: 检查端口
print("\n[测试3] 检查端口")
try:
    all_connections = psutil.net_connections(kind='inet')
    process_ports = set()
    for conn in all_connections:
        if conn.pid == test_pid:
            if conn.laddr:
                process_ports.add(conn.laddr.port)
            if conn.raddr:
                process_ports.add(conn.raddr.port)
    print(f"  进程使用的端口: {process_ports}")
except Exception as e:
    print(f"  错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
