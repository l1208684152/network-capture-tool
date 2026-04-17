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
        logger.debug(f"开始抓包，PID: {pid}")
        self.running = True
        self.paused = False
        self.capture_thread = threading.Thread(target=self.capture_packets, args=(pid,), daemon=True)
        logger.debug(f"创建抓包线程: {self.capture_thread}")
        self.capture_thread.start()
        logger.info(f"抓包线程已启动")
        logger.debug(f"抓包线程已启动")
    
    def pause_capture(self, paused):
        """暂停/继续抓包"""
        logger.info(f"{'暂停' if paused else '继续'}抓包")
        logger.debug(f"{'暂停' if paused else '继续'}抓包")
        self.paused = paused
    
    def stop_capture(self):
        """停止抓包"""
        logger.info("停止抓包")
        logger.debug("停止抓包")
        self.running = False
        if self.capture:
            try:
                self.capture.close()
                logger.info("已关闭LiveCapture对象")
                logger.debug("已关闭LiveCapture对象")
            except Exception as e:
                logger.error(f"关闭LiveCapture对象时出错: {e}")
                logger.debug(f"关闭LiveCapture对象时出错: {e}")
        if self.capture_thread:
            logger.info(f"等待抓包线程结束: {self.capture_thread}")
            logger.debug(f"等待抓包线程结束: {self.capture_thread}")
            self.capture_thread.join(timeout=1)
            logger.info("抓包线程已结束")
            logger.debug("抓包线程已结束")
    
    def capture_packets(self, pid):
        """抓包线程"""
        logger.info(f"进入抓包线程，PID: {pid}")
        logger.debug(f"进入抓包线程，PID: {pid}")
        try:
            # 导入必要的模块
            import asyncio
            import os
            logger.info("导入必要模块成功")
            logger.debug("导入必要模块成功")
            
            # 在新线程中创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.debug(f"创建事件循环: {loop}")
            
            # 添加Wireshark路径到系统PATH
            wireshark_path = r"F:\Wireshark"
            if wireshark_path not in os.environ['PATH']:
                os.environ['PATH'] += ';' + wireshark_path
                logger.info(f"已将Wireshark路径添加到系统PATH: {wireshark_path}")
            
            # 设置pyshark的tshark路径
            tshark_path = os.path.join(wireshark_path, 'tshark.exe')
            os.environ['TSHARK_PATH'] = tshark_path
            logger.info(f"已设置TSHARK_PATH: {os.environ['TSHARK_PATH']}")
            
            # 检查tshark是否存在
            if not os.path.exists(tshark_path):
                logger.error(f"tshark不存在于路径: {tshark_path}")
                self.queue.put(("error", f"tshark不存在于路径: {tshark_path}"))
                return
            
            # 使用pyshark进行抓包，通过进程PID过滤
            # 注意：Windows上pyshark的进程过滤可能需要管理员权限
            # 这里使用通用过滤，捕获所有TCP/UDP流量
            self.queue.put(("update", f"正在初始化抓包..."))
            logger.debug("正在初始化抓包...")
            
            # 根据不同平台设置适当的参数
            system = platform.system()
            logger.debug(f"当前平台: {system}")
            
            # 导入pyshark
            import pyshark
            logger.debug("导入pyshark成功")
            
            # 获取可用网络接口
            logger.debug("获取可用网络接口...")
            # 直接使用tshark命令获取接口，避免事件循环问题
            import subprocess
            try:
                result = subprocess.run(
                    [tshark_path, '-D'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=10
                )
                if result.returncode == 0:
                    interfaces = result.stdout.strip().split('\n')
                    logger.info(f"通过tshark命令获取的接口: {interfaces}")
                else:
                    logger.error(f"获取接口失败: {result.stderr}")
                    self.queue.put(("error", f"获取网络接口失败: {result.stderr}"))
                    return
            except Exception as e:
                logger.error(f"获取接口时发生错误: {e}")
                self.queue.put(("error", f"获取网络接口时发生错误: {e}"))
                return
            
            # 选择网络接口
            if not interfaces:
                logger.error("没有可用的网络接口")
                self.queue.put(("error", "没有可用的网络接口"))
                return
            
            # 尝试找到WLAN接口
            wlan_interface = None
            ethernet_interface = None
            
            for iface in interfaces:
                if 'wlan' in iface.lower() or '无线' in iface.lower() or 'wifi' in iface.lower():
                    wlan_interface = iface
                    logger.info(f"找到WLAN接口: {wlan_interface}")
                elif 'ethernet' in iface.lower() or '以太网' in iface.lower():
                    ethernet_interface = iface
                    logger.info(f"找到以太网接口: {ethernet_interface}")
            
            # 优先使用WLAN接口，然后是以太网接口，最后是第一个接口
            if wlan_interface:
                interface = wlan_interface
                logger.info("优先使用WLAN接口")
            elif ethernet_interface:
                interface = ethernet_interface
                logger.info("优先使用以太网接口")
            else:
                interface = interfaces[0]
                logger.info(f"未找到WLAN或以太网接口，使用第一个接口: {interface}")
            
            # 使用指定接口进行抓包
            logger.debug(f"创建LiveCapture，interface: {interface}, tshark_path: {tshark_path}")
            # 提取接口名称（去掉编号和描述）
            import re
            interface_match = re.search(r'\\d+\\.\\s+(\\S+)', interface)
            if interface_match:
                interface_name = interface_match.group(1)
                logger.debug(f"提取的接口名称: {interface_name}")
            else:
                interface_name = interface
                logger.debug(f"使用完整接口名称: {interface_name}")
            
            # 创建LiveCapture对象，指定事件循环
            self.capture = pyshark.LiveCapture(
                interface=interface_name,
                display_filter=f"tcp or udp",
                output_file=None,
                use_json=True,
                tshark_path=tshark_path,
                eventloop=loop
            )
            logger.debug(f"创建LiveCapture成功: {self.capture}")
            
            self.queue.put(("update", f"抓包初始化完成，开始捕获数据包..."))
            logger.info("抓包初始化完成，开始捕获数据包...")
            
            packet_no = 0
            logger.debug("开始捕获数据包")
            
            # 尝试获取几个数据包来验证抓包是否正常
            test_packets = 0
            max_test_packets = 10
            
            try:
                for packet in self.capture.sniff_continuously():
                    if not self.running:
                        logger.debug("抓包已停止，退出循环")
                        break
                    
                    if self.paused:
                        logger.debug("抓包已暂停")
                        time.sleep(0.1)
                        continue
                    
                    packet_no += 1
                    test_packets += 1
                    
                    logger.debug(f"捕获到数据包 {packet_no}: {packet}")
                    
                    # 解析数据包
                    packet_info = self.parse_packet(packet, packet_no)
                    if packet_info:
                        # 数据包已经在parse_packet中添加到队列
                        # 这里只需要记录日志
                        if packet_no % 100 == 0:
                            logger.info(f"已捕获 {packet_no} 个数据包")
                            logger.debug(f"已捕获 {packet_no} 个数据包")
                    
                    # 测试阶段，只捕获几个数据包就记录一次状态
                    if test_packets <= max_test_packets:
                        logger.info(f"测试阶段：已捕获 {test_packets} 个数据包")
            except Exception as e:
                logger.error(f"抓包循环中发生错误: {e}")
                import traceback
                logger.debug(f"错误详情: {traceback.format_exc()}")
                    
        except FileNotFoundError as e:
            logger.error(f"未找到tshark.exe: {e}")
            self.queue.put(("error", "未找到tshark.exe，请确保Wireshark已正确安装且添加到系统PATH中！"))
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            self.queue.put(("error", "抓包需要管理员权限，请以管理员身份运行本程序！"))
        except Exception as e:
            logger.error(f"抓包过程中发生错误：{type(e).__name__}: {str(e)}")
            import traceback
            logger.debug(f"错误详情: {traceback.format_exc()}")
            self.queue.put(("error", f"抓包过程中发生错误：{type(e).__name__}: {str(e)}"))
        finally:
            # 清理事件循环
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.close()
                logger.debug("事件循环已关闭")
            except Exception as e:
                logger.debug(f"清理事件循环时出错: {e}")
                pass
            logger.debug("抓包线程结束")
    
    def parse_packet(self, packet, packet_no):
        """解析数据包信息"""
        try:
            # 基本信息
            import datetime
            if isinstance(packet.sniff_time, str):
                # 如果sniff_time是字符串，尝试转换为datetime对象
                try:
                    # 处理ISO格式的时间字符串
                    if 'T' in packet.sniff_time:
                        # 移除毫秒部分（如果有）
                        if '.' in packet.sniff_time:
                            packet.sniff_time = packet.sniff_time.split('.')[0]
                        # 转换为datetime对象
                        sniff_time = datetime.datetime.strptime(packet.sniff_time, '%Y-%m-%dT%H:%M:%S')
                    else:
                        # 其他格式的时间字符串
                        sniff_time = datetime.datetime.strptime(packet.sniff_time, '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    # 如果转换失败，使用当前时间
                    logging.warning(f"时间戳解析失败: {e}，使用当前时间")
                    sniff_time = datetime.datetime.now()
            else:
                # 如果sniff_time已经是datetime对象，直接使用
                sniff_time = packet.sniff_time
            
            # 格式化时间戳
            packet_time = sniff_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 协议信息
            proto = packet.transport_layer if hasattr(packet, 'transport_layer') else 'Unknown'
            
            # IP信息
            src_ip = dst_ip = src_port = dst_port = 'N/A'
            if hasattr(packet, 'ip'):
                src_ip = packet.ip.src
                dst_ip = packet.ip.dst
            elif hasattr(packet, 'ipv6'):
                src_ip = packet.ipv6.src
                dst_ip = packet.ipv6.dst
            
            # 端口信息
            if proto == 'TCP':
                src_port = packet.tcp.srcport
                dst_port = packet.tcp.dstport
            elif proto == 'UDP':
                src_port = packet.udp.srcport
                dst_port = packet.udp.dstport
            
            # 长度信息
            try:
                if isinstance(packet.length, str):
                    # 如果length是字符串，尝试转换为整数
                    length = int(packet.length)
                else:
                    # 如果length已经是数值，直接使用
                    length = int(packet.length)
            except Exception as e:
                # 如果转换失败，使用默认值
                logging.warning(f"长度解析失败: {e}，使用默认值 0")
                length = 0
            
            # 详细信息
            info = ''
            if proto == 'TCP':
                flags = []
                if hasattr(packet.tcp, 'flags_syn') and packet.tcp.flags_syn == '1':
                    flags.append('SYN')
                if hasattr(packet.tcp, 'flags_ack') and packet.tcp.flags_ack == '1':
                    flags.append('ACK')
                if hasattr(packet.tcp, 'flags_fin') and packet.tcp.flags_fin == '1':
                    flags.append('FIN')
                if hasattr(packet.tcp, 'flags_rst') and packet.tcp.flags_rst == '1':
                    flags.append('RST')
                if hasattr(packet.tcp, 'flags_psh') and packet.tcp.flags_psh == '1':
                    flags.append('PSH')
                if hasattr(packet.tcp, 'flags_urg') and packet.tcp.flags_urg == '1':
                    flags.append('URG')
                info = f"TCP {','.join(flags)} "
            elif proto == 'UDP':
                info = f"UDP "
            
            # 应用层信息
            if hasattr(packet, 'http'):
                info += f"HTTP {packet.http.request_method if hasattr(packet.http, 'request_method') else 'Response'}"
            elif hasattr(packet, 'dns'):
                info += f"DNS {packet.dns.qry_name if hasattr(packet.dns, 'qry_name') else 'Response'}"
            
            # 注意：不保存原始packet对象，避免事件循环问题
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
                # 移除packet_obj，避免事件循环问题
            }
            
            # 将数据包添加到队列
            self.queue.put(packet_info)
            
            return packet_info
        except Exception as e:
            logging.error(f"解析数据包失败: {str(e)}")
            return None