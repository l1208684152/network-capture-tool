import threading
import time
import platform
import logging
import psutil

# 导入Scapy及必要的层
from scapy.all import sniff, conf, IP, TCP, UDP
# 导入HTTP和DNS层
from scapy.layers.http import HTTPRequest, HTTPResponse
from scapy.layers.dns import DNS, DNSQR

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
        # 使用daemon线程，确保主程序退出时线程能够自动退出
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
            # 使用超时机制，避免线程卡住
            self.capture_thread.join(timeout=2)
            if self.capture_thread.is_alive():
                logger.warning("抓包线程可能卡住，强制退出")
            else:
                logger.info("抓包线程已结束")
    
    def capture_packets(self, pid):
        """抓包线程"""
        logger.info(f"进入抓包线程，PID: {pid}")
        retry_count = 0
        max_retries = 3
        
        while self.running and retry_count < max_retries:
            try:
                # 导入必要的模块
                import os
                logger.info("导入必要模块成功")
                
                # 使用scapy进行抓包
                self.queue.put(("update", f"正在初始化抓包..."))
                
                # scapy已经在文件开头导入
                
                # 获取指定PID的进程
                process = None
                process_name = None
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                    logger.info(f"找到进程: {process_name} (PID: {pid})")
                except psutil.NoSuchProcess:
                    logger.error(f"未找到PID为 {pid} 的进程")
                    self.queue.put(("error", f"未找到PID为 {pid} 的进程"))
                    return
                except psutil.AccessDenied:
                    logger.error(f"无法访问PID为 {pid} 的进程")
                    self.queue.put(("error", f"无法访问PID为 {pid} 的进程，请以管理员身份运行本程序"))
                    return
                
                # 获取可用网络接口
                interfaces_list = list(conf.ifaces.values())
                interface_names = [iface.name for iface in interfaces_list]
                logger.info(f"可用网络接口: {interface_names}")
                
                # 选择网络接口
                if not interface_names:
                    logger.error("没有可用的网络接口")
                    self.queue.put(("error", "没有可用的网络接口"))
                    return
                
                # 尝试找到合适的网络接口（排除虚拟接口和Miniport）
                selected_interface = None
                for iface in interfaces_list:
                    iface_name = iface.name.lower()
                    iface_desc = iface.description.lower() if iface.description else ""
                    
                    # 跳过虚拟接口、Miniport、Loopback等
                    if any(x in iface_name for x in ['miniport', 'loopback', 'virtual', 'adapter', '本地连接']):
                        continue
                    
                    # 同时匹配中英文关键词
                    if ('wlan' in iface_name or 
                        'wifi' in iface_name or
                        'wireless' in iface_desc or
                        '无线' in iface_desc):
                        selected_interface = iface.name
                        logger.info(f"选择WLAN接口: {selected_interface} (描述: {iface.description})")
                        break
                    elif ('ethernet' in iface_name or 
                          '以太网' in iface_desc or
                          'eth' in iface_name):
                        selected_interface = iface.name
                        logger.info(f"选择以太网接口: {selected_interface} (描述: {iface.description})")
                        break
                
                # 如果没有找到合适的接口，选择第一个物理接口
                if not selected_interface:
                    for iface in interfaces_list:
                        iface_name = iface.name.lower()
                        # 跳过虚拟接口和Loopback
                        if any(x in iface_name for x in ['miniport', 'loopback', 'virtual', 'adapter', '本地连接']):
                            continue
                        selected_interface = iface.name
                        logger.info(f"未找到WLAN或以太网接口，使用第一个物理接口: {selected_interface} (描述: {iface.description})")
                        break
                
                # 如果仍然没有找到，使用第一个接口但给出警告
                if not selected_interface and interface_names:
                    selected_interface = interface_names[0]
                    logger.warning(f"未找到合适的物理接口，使用第一个接口: {selected_interface}")
                
                # 记录进程的端口使用历史
                process_ports = set()
                last_update_time = 0
                update_interval = 1  # 每秒更新一次进程连接信息
                
                # 获取进程的网络连接
                def get_process_connections():
                    """获取进程的网络连接"""
                    nonlocal last_update_time
                    nonlocal process_ports
                    
                    current_time = time.time()
                    # 定期更新进程连接信息
                    if current_time - last_update_time >= update_interval:
                        last_update_time = current_time
                        try:
                            # 使用psutil.net_connections()获取所有连接，然后过滤到目标进程
                            all_connections = psutil.net_connections(kind='inet')
                            
                            # 过滤出属于目标进程的连接，以及具有相同名称的其他进程的连接
                            # 这样可以捕获浏览器等多进程应用的所有连接
                            connections = []
                            for conn in all_connections:
                                if conn.pid == pid:
                                    connections.append(conn)
                                else:
                                    # 检查是否是具有相同名称的其他进程
                                    try:
                                        other_process = psutil.Process(conn.pid)
                                        if other_process.name() == process_name:
                                            connections.append(conn)
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        pass
                            
                            # 更新端口历史
                            for conn in connections:
                                if conn.laddr:
                                    process_ports.add(conn.laddr.port)
                                if conn.raddr:
                                    process_ports.add(conn.raddr.port)
                            
                            logger.debug(f"更新进程 {pid} 及其同名进程的连接: {len(connections)} 个连接, 端口: {process_ports}")
                            return connections
                        except Exception as e:
                            logger.error(f"获取进程连接失败: {e}")
                            return []
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
                    if not self.is_packet_from_process(packet, connections, process_ports):
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
                    
                    # 非致命错误，尝试重试
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"尝试重试抓包，第 {retry_count} 次")
                        self.queue.put(("update", f"抓包出现错误，正在重试... (第 {retry_count} 次)"))
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    else:
                        logger.error("达到最大重试次数，停止抓包")
                        self.queue.put(("error", "抓包出现错误，已达到最大重试次数"))
                        return
                
                # 正常结束，退出循环
                break
                
            except ImportError as e:
                logger.error(f"导入scapy失败: {e}")
                self.queue.put(("error", f"导入scapy失败: {e}"))
                return
            except PermissionError as e:
                logger.error(f"权限错误: {e}")
                self.queue.put(("error", "抓包需要管理员权限，请以管理员身份运行本程序！"))
                return
            except Exception as e:
                logger.error(f"抓包过程中发生错误：{type(e).__name__}: {str(e)}")
                import traceback
                logger.debug(f"错误详情: {traceback.format_exc()}")
                
                # 非致命错误，尝试重试
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"尝试重试抓包，第 {retry_count} 次")
                    self.queue.put(("update", f"抓包出现错误，正在重试... (第 {retry_count} 次)"))
                    time.sleep(2)  # 等待2秒后重试
                    continue
                else:
                    logger.error("达到最大重试次数，停止抓包")
                    self.queue.put(("error", f"抓包过程中发生错误：{type(e).__name__}: {str(e)}"))
                    return
    
    def is_packet_from_process(self, packet, connections, process_ports=None):
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
                if (conn.laddr and conn.laddr.ip == src_ip and conn.laddr.port == src_port) or \
                   (conn.raddr and conn.raddr.ip == src_ip and conn.raddr.port == src_port):
                    return True
                # 检查远程地址和端口
                if (conn.laddr and conn.laddr.ip == dst_ip and conn.laddr.port == dst_port) or \
                   (conn.raddr and conn.raddr.ip == dst_ip and conn.raddr.port == dst_port):
                    return True
            
            # 检查是否与进程的端口使用历史匹配（减少漏包）
            if process_ports:
                if src_port in process_ports or dst_port in process_ports:
                    logger.debug(f"数据包端口匹配: {src_port} 或 {dst_port} 在进程端口集合中")
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
            
            # 应用层信息和内容
            content = {}
            if packet.haslayer('HTTPRequest'):
                http_layer = packet['HTTPRequest']
                method = http_layer.Method.decode('utf-8', errors='ignore')
                path = http_layer.Path.decode('utf-8', errors='ignore')
                version = http_layer.Http_Version.decode('utf-8', errors='ignore')
                info += f"HTTP {method} {path}"
                
                # 提取HTTP请求内容
                content['type'] = 'HTTP Request'
                content['method'] = method
                content['path'] = path
                content['version'] = version
                
                # 提取HTTP头部
                headers = {}
                for key, value in http_layer.fields.items():
                    if key not in ['Method', 'Path', 'Http_Version']:
                        headers[key] = value.decode('utf-8', errors='ignore') if isinstance(value, bytes) else str(value)
                content['headers'] = headers
                
                # 提取HTTP载荷
                if packet.haslayer('Raw'):
                    raw = packet['Raw'].load
                    try:
                        content['body'] = raw.decode('utf-8', errors='ignore')
                    except:
                        content['body'] = f"Binary data ({len(raw)} bytes)"
            
            elif packet.haslayer('HTTPResponse'):
                http_layer = packet['HTTPResponse']
                version = http_layer.Http_Version.decode('utf-8', errors='ignore')
                status = http_layer.Status_Code.decode('utf-8', errors='ignore')
                reason = http_layer.Reason_Phrase.decode('utf-8', errors='ignore')
                info += f"HTTP Response {status} {reason}"
                
                # 提取HTTP响应内容
                content['type'] = 'HTTP Response'
                content['version'] = version
                content['status'] = status
                content['reason'] = reason
                
                # 提取HTTP头部
                headers = {}
                for key, value in http_layer.fields.items():
                    if key not in ['Http_Version', 'Status_Code', 'Reason_Phrase']:
                        headers[key] = value.decode('utf-8', errors='ignore') if isinstance(value, bytes) else str(value)
                content['headers'] = headers
                
                # 提取HTTP载荷
                if packet.haslayer('Raw'):
                    raw = packet['Raw'].load
                    try:
                        content['body'] = raw.decode('utf-8', errors='ignore')
                    except:
                        content['body'] = f"Binary data ({len(raw)} bytes)"
            
            elif packet.haslayer('DNS'):
                dns_layer = packet['DNS']
                if dns_layer.qr == 0:  # 查询
                    if dns_layer.haslayer('DNSQR'):
                        qr = dns_layer['DNSQR']
                        qname = qr.qname.decode('utf-8', errors='ignore')
                        qtype = qr.qtype
                        qclass = qr.qclass
                        info += f"DNS Query {qname}"
                        
                        # 提取DNS查询内容
                        content['type'] = 'DNS Query'
                        content['qname'] = qname
                        content['qtype'] = qtype
                        content['qclass'] = qclass
                else:  # 响应
                    info += f"DNS Response"
                    
                    # 提取DNS响应内容
                    content['type'] = 'DNS Response'
                    content['qr'] = dns_layer.qr
                    content['opcode'] = dns_layer.opcode
                    content['aa'] = dns_layer.aa
                    content['tc'] = dns_layer.tc
                    content['rd'] = dns_layer.rd
                    content['ra'] = dns_layer.ra
                    content['z'] = dns_layer.z
                    content['rcode'] = dns_layer.rcode
                    content['qdcount'] = dns_layer.qdcount
                    content['ancount'] = dns_layer.ancount
                    content['nscount'] = dns_layer.nscount
                    content['arcount'] = dns_layer.arcount
            
            # 提取TCP/UDP载荷（只有在没有应用层信息时）
            elif packet.haslayer('Raw'):
                raw = packet['Raw'].load
                try:
                    payload = raw.decode('utf-8', errors='ignore')
                    info += f"Data: {payload[:50]}..."
                    content['type'] = 'Raw Data'
                    content['payload'] = payload
                except:
                    info += f"Binary data ({len(raw)} bytes)"
                    content['type'] = 'Binary Data'
                    content['length'] = len(raw)
            
            # 如果没有应用层信息，添加基本信息
            if not content:
                content['type'] = 'Basic Packet'
                content['protocol'] = proto
                content['src_port'] = src_port
                content['dst_port'] = dst_port
            
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
                'raw': str(packet),
                'content': content  # 新增：详细内容解析
            }
            
            # 将数据包添加到队列
            self.queue.put(packet_info)
            
            return packet_info
        except Exception as e:
            logging.error(f"解析数据包失败: {str(e)}")
            return None