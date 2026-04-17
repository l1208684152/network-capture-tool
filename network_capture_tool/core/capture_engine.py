import threading
import time
import platform
import logging

# 创建日志记录器
logger = logging.getLogger(__name__)

class CaptureEngine:
    """抓包引擎类"""
    
    def __init__(self, queue):
        self.queue = queue
        self.running = False
        self.paused = False
        self.capture_thread = None
        self.capture = None
    
    def start_capture(self, pid):
        """开始抓包"""
        logger.info(f"开始抓包，PID: {pid}")
        self.running = True
        self.paused = False
        self.capture_thread = threading.Thread(target=self.capture_packets, args=(pid,), daemon=True)
        self.capture_thread.start()
        logger.info(f"抓包线程已启动")
    
    def pause_capture(self, paused):
        """暂停/继续抓包"""
        logger.info(f"{'暂停' if paused else '继续'}抓包")
        self.paused = paused
    
    def stop_capture(self):
        """停止抓包"""
        logger.info("停止抓包")
        self.running = False
        if self.capture:
            try:
                self.capture.stop()
                logger.info("已停止抓包")
            except Exception as e:
                logger.error(f"停止抓包时出错: {e}")
        if self.capture_thread:
            logger.info("等待抓包线程结束")
            self.capture_thread.join(timeout=1)
            logger.info("抓包线程已结束")
    
    def capture_packets(self, pid):
        """抓包线程"""
        logger.info(f"进入抓包线程，PID: {pid}")
        try:
            # 导入必要的模块
            import os
            import psutil
            logger.info("导入必要模块成功")
            
            # 使用scapy进行抓包
            self.queue.put(("update", f"正在初始化抓包..."))
            
            # 导入scapy
            from scapy.all import sniff, conf
            
            # 获取指定PID的进程
            try:
                process = psutil.Process(pid)
                logger.info(f"找到进程: {process.name()} (PID: {pid})")
            except psutil.NoSuchProcess:
                logger.error(f"未找到PID为 {pid} 的进程")
                self.queue.put(("error", f"未找到PID为 {pid} 的进程"))
                return
            except psutil.AccessDenied:
                logger.error(f"无法访问PID为 {pid} 的进程")
                self.queue.put(("error", f"无法访问PID为 {pid} 的进程，请以管理员身份运行本程序"))
                return
            
            # 获取可用网络接口
            interfaces = conf.ifaces.values()
            interface_names = [iface.name for iface in interfaces]
            logger.info(f"可用网络接口: {interface_names}")
            
            # 选择网络接口
            if not interface_names:
                logger.error("没有可用的网络接口")
                self.queue.put(("error", "没有可用的网络接口"))
                return
            
            # 尝试找到合适的网络接口
            selected_interface = None
            for iface in interfaces:
                if 'wlan' in iface.name.lower() or '无线' in iface.description.lower() or 'wifi' in iface.name.lower():
                    selected_interface = iface.name
                    logger.info(f"选择WLAN接口: {selected_interface}")
                    break
                elif 'ethernet' in iface.name.lower() or '以太网' in iface.description.lower():
                    selected_interface = iface.name
                    logger.info(f"选择以太网接口: {selected_interface}")
                    break
            
            if not selected_interface:
                selected_interface = interface_names[0]
                logger.info(f"未找到WLAN或以太网接口，使用第一个接口: {selected_interface}")
            
            # 获取进程的网络连接
            def get_process_connections():
                """获取进程的网络连接"""
                try:
                    connections = process.connections(kind='inet')
                    return connections
                except Exception as e:
                    logger.error(f"获取进程连接失败: {e}")
                    return []
            
            # 构建数据包处理函数
            packet_no = [0]  # 使用列表来实现可变变量
            max_test_packets = 10
            
            def packet_handler(packet):
                if not self.running:
                    return False  # 停止抓包
                
                if self.paused:
                    time.sleep(0.1)
                    return True
                
                # 获取进程的网络连接
                connections = get_process_connections()
                
                # 检查数据包是否与进程的网络连接匹配
                if not self.is_packet_from_process(packet, connections):
                    return True  # 不是目标进程的数据包，跳过
                
                packet_no[0] += 1
                
                # 解析数据包
                packet_info = self.parse_packet(packet, packet_no[0])
                if packet_info:
                    # 数据包已经在parse_packet中添加到队列
                    # 这里只需要记录日志
                    if packet_no[0] % 100 == 0:
                        logger.info(f"已捕获 {packet_no[0]} 个数据包")
                    
                    # 测试阶段，只捕获几个数据包就记录一次状态
                    if packet_no[0] <= max_test_packets:
                        logger.info(f"测试阶段：已捕获 {packet_no[0]} 个数据包")
                
                return True
            
            self.queue.put(("update", f"抓包初始化完成，开始捕获数据包..."))
            logger.info("抓包初始化完成，开始捕获数据包...")
            
            # 开始抓包
            try:
                logger.info(f"开始在接口 {selected_interface} 上抓包")
                # 使用scapy的sniff函数进行抓包
                # 过滤TCP和UDP数据包
                self.capture = sniff(
                    iface=selected_interface,
                    filter="tcp or udp",
                    prn=packet_handler,
                    store=False
                )
            except Exception as e:
                logger.error(f"抓包循环中发生错误: {e}")
                import traceback
                logger.debug(f"错误详情: {traceback.format_exc()}")
                    
        except ImportError as e:
            logger.error(f"导入scapy失败: {e}")
            self.queue.put(("error", f"导入scapy失败: {e}"))
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            self.queue.put(("error", "抓包需要管理员权限，请以管理员身份运行本程序！"))
        except Exception as e:
            logger.error(f"抓包过程中发生错误：{type(e).__name__}: {str(e)}")
            import traceback
            logger.debug(f"错误详情: {traceback.format_exc()}")
            self.queue.put(("error", f"抓包过程中发生错误：{type(e).__name__}: {str(e)}"))
    
    def is_packet_from_process(self, packet, connections):
        """检查数据包是否来自目标进程"""
        try:
            # 检查数据包是否有IP和TCP/UDP层
            if not (packet.haslayer('IP') or packet.haslayer('IPv6')):
                return False
            
            if not (packet.haslayer('TCP') or packet.haslayer('UDP')):
                return False
            
            # 获取数据包的IP和端口信息
            if packet.haslayer('IP'):
                src_ip = packet['IP'].src
                dst_ip = packet['IP'].dst
            else:  # IPv6
                src_ip = packet['IPv6'].src
                dst_ip = packet['IPv6'].dst
            
            if packet.haslayer('TCP'):
                src_port = packet['TCP'].sport
                dst_port = packet['TCP'].dport
            else:  # UDP
                src_port = packet['UDP'].sport
                dst_port = packet['UDP'].dport
            
            # 检查是否与进程的网络连接匹配
            for conn in connections:
                # 检查本地地址和端口
                if (conn.laddr.ip == src_ip and conn.laddr.port == src_port) or \
                   (conn.raddr and conn.raddr.ip == src_ip and conn.raddr.port == src_port):
                    return True
                # 检查远程地址和端口
                if (conn.laddr.ip == dst_ip and conn.laddr.port == dst_port) or \
                   (conn.raddr and conn.raddr.ip == dst_ip and conn.raddr.port == dst_port):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"检查数据包来源失败: {e}")
            return False
    
    def parse_packet(self, packet, packet_no):
        """解析数据包信息"""
        try:
            # 基本信息
            import datetime
            sniff_time = datetime.datetime.now()
            
            # 格式化时间戳
            packet_time = sniff_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 协议信息
            proto = 'Unknown'
            src_ip = dst_ip = src_port = dst_port = 'N/A'
            length = len(packet)
            
            # IP信息
            if packet.haslayer('IP'):
                src_ip = packet['IP'].src
                dst_ip = packet['IP'].dst
                if packet.haslayer('TCP'):
                    proto = 'TCP'
                    src_port = packet['TCP'].sport
                    dst_port = packet['TCP'].dport
                elif packet.haslayer('UDP'):
                    proto = 'UDP'
                    src_port = packet['UDP'].sport
                    dst_port = packet['UDP'].dport
            elif packet.haslayer('IPv6'):
                src_ip = packet['IPv6'].src
                dst_ip = packet['IPv6'].dst
                if packet.haslayer('TCP'):
                    proto = 'TCP'
                    src_port = packet['TCP'].sport
                    dst_port = packet['TCP'].dport
                elif packet.haslayer('UDP'):
                    proto = 'UDP'
                    src_port = packet['UDP'].sport
                    dst_port = packet['UDP'].dport
            
            # 详细信息
            info = ''
            if proto == 'TCP':
                flags = []
                tcp_layer = packet['TCP']
                if tcp_layer.flags & 0x02:  # SYN
                    flags.append('SYN')
                if tcp_layer.flags & 0x10:  # ACK
                    flags.append('ACK')
                if tcp_layer.flags & 0x01:  # FIN
                    flags.append('FIN')
                if tcp_layer.flags & 0x04:  # RST
                    flags.append('RST')
                if tcp_layer.flags & 0x08:  # PSH
                    flags.append('PSH')
                if tcp_layer.flags & 0x20:  # URG
                    flags.append('URG')
                info = f"TCP {','.join(flags)} "
            elif proto == 'UDP':
                info = f"UDP "
            
            # 应用层信息
            if packet.haslayer('HTTPRequest'):
                http_layer = packet['HTTPRequest']
                info += f"HTTP {http_layer.Method.decode('utf-8', errors='ignore')}"
            elif packet.haslayer('HTTPResponse'):
                info += f"HTTP Response"
            elif packet.haslayer('DNS'):
                dns_layer = packet['DNS']
                if dns_layer.qr == 0:  # 查询
                    if dns_layer.haslayer('DNSQR'):
                        qr = dns_layer['DNSQR']
                        info += f"DNS {qr.qname.decode('utf-8', errors='ignore')}"
                else:  # 响应
                    info += f"DNS Response"
            
            # 构建数据包信息
            packet_info = {
                'no': packet_no,
                'time': packet_time,
                'src': src_ip,
                'dst': dst_ip,
                'proto': proto,
                'src_port': src_port,
                'dst_port': dst_port,
                'length': length,
                'info': info,
                'raw': str(packet)
            }
            
            # 将数据包添加到队列
            self.queue.put(packet_info)
            
            return packet_info
        except Exception as e:
            logging.error(f"解析数据包失败: {str(e)}")
            return None