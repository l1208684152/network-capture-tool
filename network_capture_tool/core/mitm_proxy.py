import socket
import ssl
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import os

# 尝试导入OpenSSL
try:
    import OpenSSL
    OPENSSL_AVAILABLE = True
except ImportError:
    OPENSSL_AVAILABLE = False

class MITMProxy:
    """MITM代理，用于解密HTTPS流量"""
    
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.cert_dir = os.path.join(os.path.dirname(__file__), 'certs')
        self.ca_cert = os.path.join(self.cert_dir, 'ca.crt')
        self.ca_key = os.path.join(self.cert_dir, 'ca.key')
        self.is_running = False
        
        # 创建证书目录
        if not os.path.exists(self.cert_dir):
            os.makedirs(self.cert_dir)
        
        # 检测并处理预设的CA私钥
        self._check_preset_ca_cert()
        
        # 生成CA证书
        self._generate_ca_cert()
    
    def _check_preset_ca_cert(self):
        """检测预设的CA私钥并提示用户"""
        if os.path.exists(self.ca_key):
            try:
                # 读取私钥文件大小
                key_size = os.path.getsize(self.ca_key)
                # 检查私钥文件是否存在且大小合理
                if key_size > 0:
                    # 提示用户删除预设的CA私钥
                    logging.warning("检测到预设的CA私钥文件，可能存在安全风险！")
                    logging.warning("建议删除现有的CA私钥文件并重新生成，以确保安全性。")
                    
                    # 询问用户是否删除并重新生成
                    import tkinter as tk
                    from tkinter import messagebox
                    
                    # 创建一个临时的tk根窗口
                    root = tk.Tk()
                    root.withdraw()  # 隐藏窗口
                    
                    response = messagebox.askyesno(
                        "安全警告",
                        "检测到预设的CA私钥文件，可能存在安全风险！\n\n"+
                        "为了确保安全性，建议删除现有的CA私钥并重新生成。\n\n"+
                        "是否删除现有CA私钥并重新生成？"
                    )
                    
                    root.destroy()
                    
                    if response:
                        # 删除现有的CA证书和私钥
                        if os.path.exists(self.ca_cert):
                            os.remove(self.ca_cert)
                        if os.path.exists(self.ca_key):
                            os.remove(self.ca_key)
                        logging.info("已删除预设的CA私钥文件，将重新生成")
            except Exception as e:
                logging.error(f"检测CA私钥时出错: {str(e)}")
    
    def _generate_ca_cert(self):
        """生成CA证书"""
        if not OPENSSL_AVAILABLE:
            raise ImportError("OpenSSL库未安装，请安装pyOpenSSL: pip install pyOpenSSL")
        
        if not os.path.exists(self.ca_cert) or not os.path.exists(self.ca_key):
            logging.info("生成CA证书...")
            
            # 创建私钥
            key = OpenSSL.crypto.PKey()
            key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
            
            # 创建证书
            cert = OpenSSL.crypto.X509()
            cert.get_subject().C = "CN"
            cert.get_subject().ST = "Beijing"
            cert.get_subject().L = "Beijing"
            cert.get_subject().O = "Network Capture Tool"
            cert.get_subject().OU = "MITM Proxy"
            cert.get_subject().CN = "Network Capture Tool CA"
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1年
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            cert.sign(key, 'sha256')
            
            # 保存证书
            with open(self.ca_key, 'wb') as f:
                f.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
            
            with open(self.ca_cert, 'wb') as f:
                f.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
            
            logging.info("CA证书生成完成")
    
    def _generate_cert(self, hostname):
        """为指定域名生成证书"""
        if not OPENSSL_AVAILABLE:
            raise ImportError("OpenSSL库未安装，请安装pyOpenSSL: pip install pyOpenSSL")
        
        cert_file = os.path.join(self.cert_dir, f'{hostname}.crt')
        key_file = os.path.join(self.cert_dir, f'{hostname}.key')
        
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            # 加载CA证书
            with open(self.ca_cert, 'rb') as f:
                ca_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, f.read())
            
            with open(self.ca_key, 'rb') as f:
                ca_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, f.read())
            
            # 创建证书
            key = OpenSSL.crypto.PKey()
            key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
            
            cert = OpenSSL.crypto.X509()
            cert.get_subject().C = "CN"
            cert.get_subject().ST = "Beijing"
            cert.get_subject().L = "Beijing"
            cert.get_subject().O = "Network Capture Tool"
            cert.get_subject().OU = "MITM Proxy"
            cert.get_subject().CN = hostname
            cert.set_serial_number(1001)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
            cert.set_issuer(ca_cert.get_subject())
            cert.set_pubkey(key)
            
            # 添加主题备用名称（SAN）
            san = f"DNS:{hostname}"
            cert.add_extensions([
                OpenSSL.crypto.X509Extension(
                    b"subjectAltName",
                    False,
                    san.encode('utf-8')
                )
            ])
            
            cert.sign(ca_key, 'sha256')
            
            # 保存证书
            with open(key_file, 'wb') as f:
                f.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
            
            with open(cert_file, 'wb') as f:
                f.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
        
        return cert_file, key_file
    
    def start(self):
        """启动代理服务器"""
        if not OPENSSL_AVAILABLE:
            raise ImportError("OpenSSL库未安装，请安装pyOpenSSL: pip install pyOpenSSL")
        
        logging.info(f"启动MITM代理服务器: {self.host}:{self.port}")
        
        # 保存对MITMProxy实例的引用
        proxy_instance = self
        
        class ProxyHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle_request()
            
            def do_POST(self):
                self._handle_request()
            
            def do_CONNECT(self):
                """处理HTTPS CONNECT请求"""
                try:
                    # 获取目标主机和端口
                    host, port = self.path.split(':')
                    port = int(port)
                    
                    # 发送200 OK响应
                    self.send_response(200, 'Connection Established')
                    self.end_headers()
                    
                    # 为目标主机生成证书
                    cert_file, key_file = proxy_instance._generate_cert(host)
                    
                    # 使用生成的证书包装连接
                    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    context.load_cert_chain(cert_file, key_file)
                    secure_socket = context.wrap_socket(self.connection, server_side=True)
                    
                    # 连接目标服务器
                    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    target_socket.settimeout(10)
                    target_socket.connect((host, port))
                    
                    # 开始双向数据传输
                    def forward_data(source, destination):
                        """从源读取数据并发送到目标"""
                        try:
                            while True:
                                data = source.recv(4096)
                                if not data:
                                    break
                                destination.sendall(data)
                        except Exception as e:
                            pass
                    
                    # 启动两个线程进行双向数据传输
                    client_to_server = threading.Thread(target=forward_data, args=(secure_socket, target_socket))
                    server_to_client = threading.Thread(target=forward_data, args=(target_socket, secure_socket))
                    
                    client_to_server.daemon = True
                    server_to_client.daemon = True
                    
                    client_to_server.start()
                    server_to_client.start()
                    
                    # 等待线程完成
                    client_to_server.join()
                    server_to_client.join()
                    
                    secure_socket.close()
                    target_socket.close()
                    
                except Exception as e:
                    logging.error(f"CONNECT请求失败: {str(e)}")
                    try:
                        self.send_error(500, f"Proxy Error: {str(e)}")
                    except:
                        pass
            
            def _handle_request(self):
                try:
                    # 解析URL
                    url = urlparse(self.path)
                    if not url.netloc:
                        # 处理相对路径
                        url = urlparse(f'http://{self.headers["Host"]}{self.path}')
                    
                    hostname = url.netloc.split(':')[0]
                    port = url.port or 80
                    
                    # 读取请求数据
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length) if content_length else b''
                    
                    # 构建请求
                    request_lines = [f"{self.command} {url.path}{url.query} HTTP/1.1"]
                    for key, value in self.headers.items():
                        if key.lower() != 'host':
                            request_lines.append(f"{key}: {value}")
                    request_lines.append(f"Host: {url.netloc}")
                    request_lines.append("")
                    request_data = '\r\n'.join(request_lines).encode('utf-8')
                    if post_data:
                        request_data += post_data
                    
                    # 连接目标服务器
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    sock.connect((hostname, port))
                    sock.sendall(request_data)
                    
                    # 接收响应
                    response = b''
                    while True:
                        data = sock.recv(4096)
                        if not data:
                            break
                        response += data
                    sock.close()
                    
                    # 解析响应
                    response_lines = response.split(b'\r\n')
                    status_line = response_lines[0]
                    
                    # 发送响应给客户端
                    self.send_response(int(status_line.split(b' ')[1]))
                    
                    # 发送响应头
                    for i in range(1, len(response_lines)):
                        line = response_lines[i]
                        if not line:
                            break
                        if b':' in line:
                            key, value = line.split(b':', 1)
                            self.send_header(key.decode('utf-8'), value.strip().decode('utf-8'))
                    
                    self.end_headers()
                    
                    # 发送响应体
                    body_start = response.find(b'\r\n\r\n') + 4
                    if body_start > 4:
                        self.wfile.write(response[body_start:])
                    
                except Exception as e:
                    logging.error(f"代理请求失败: {str(e)}")
                    try:
                        self.send_error(500, f"Proxy Error: {str(e)}")
                    except:
                        pass
        
        # 创建HTTP服务器
        self.server = HTTPServer((self.host, self.port), ProxyHandler)
        
        # 启动服务器线程
        self.is_running = True
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logging.info(f"MITM代理服务器已启动: http://{self.host}:{self.port}")
    
    def stop(self):
        """停止代理服务器"""
        if self.server:
            logging.info("停止MITM代理服务器...")
            self.is_running = False
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=5)
            logging.info("MITM代理服务器已停止")
    
    def get_proxy_url(self):
        """获取代理URL"""
        return f"http://{self.host}:{self.port}"
    
    def get_ca_cert_path(self):
        """获取CA证书路径"""
        return self.ca_cert
    
    def set_system_proxy(self, enable=True):
        """设置系统代理"""
        import platform
        system = platform.system()
        
        if system == 'Windows':
            return self._set_windows_proxy(enable)
        elif system == 'Darwin':
            return self._set_mac_proxy(enable)
        elif system == 'Linux':
            return self._set_linux_proxy(enable)
        return False
    
    def _set_windows_proxy(self, enable):
        """设置Windows系统代理"""
        try:
            import winreg
            
            # 打开注册表
            reg_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings'
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
            
            if enable:
                # 启用代理
                winreg.SetValueEx(reg_key, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(reg_key, 'ProxyServer', 0, winreg.REG_SZ, f'http=127.0.0.1:{self.port};https=127.0.0.1:{self.port}')
                winreg.SetValueEx(reg_key, 'ProxyOverride', 0, winreg.REG_SZ, '<local>')
            else:
                # 禁用代理
                winreg.SetValueEx(reg_key, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
            
            winreg.CloseKey(reg_key)
            return True
        except Exception as e:
            logging.error(f"设置Windows代理失败: {str(e)}")
            return False
    
    def _set_mac_proxy(self, enable):
        """设置macOS系统代理"""
        try:
            import subprocess
            
            if enable:
                # 启用代理
                subprocess.run(['networksetup', '-setwebproxy', 'Wi-Fi', '127.0.0.1', str(self.port)], check=True)
                subprocess.run(['networksetup', '-setsecurewebproxy', 'Wi-Fi', '127.0.0.1', str(self.port)], check=True)
            else:
                # 禁用代理
                subprocess.run(['networksetup', '-setwebproxystate', 'Wi-Fi', 'off'], check=True)
                subprocess.run(['networksetup', '-setsecurewebproxystate', 'Wi-Fi', 'off'], check=True)
            
            return True
        except Exception as e:
            logging.error(f"设置macOS代理失败: {str(e)}")
            return False
    
    def _set_linux_proxy(self, enable):
        """设置Linux系统代理"""
        try:
            # 这里可以根据不同的Linux桌面环境实现
            # 暂时返回False，需要用户手动设置
            return False
        except Exception as e:
            logging.error(f"设置Linux代理失败: {str(e)}")
            return False
    
    def install_certificate(self):
        """自动安装CA证书"""
        import platform
        system = platform.system()
        
        if system == 'Windows':
            return self._install_windows_certificate()
        elif system == 'Darwin':
            return self._install_mac_certificate()
        elif system == 'Linux':
            return self._install_linux_certificate()
        return False
    
    def _install_windows_certificate(self):
        """在Windows上安装CA证书"""
        try:
            import subprocess
            # 使用certutil命令安装证书
            result = subprocess.run(
                ['certutil', '-addstore', '-f', 'Root', self.ca_cert],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"安装Windows证书失败: {str(e)}")
            return False
    
    def _install_mac_certificate(self):
        """在macOS上安装CA证书"""
        try:
            import subprocess
            # 使用security命令安装证书
            result = subprocess.run(
                ['security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k', '/Library/Keychains/System.keychain', self.ca_cert],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"安装macOS证书失败: {str(e)}")
            return False
    
    def _install_linux_certificate(self):
        """在Linux上安装CA证书"""
        try:
            # 这里可以根据不同的Linux发行版实现
            # 暂时返回False，需要用户手动安装
            return False
        except Exception as e:
            logging.error(f"安装Linux证书失败: {str(e)}")
            return False
    
    def check_proxy_status(self):
        """检查代理状态"""
        import platform
        system = platform.system()
        
        if system == 'Windows':
            return self._check_windows_proxy()
        elif system == 'Darwin':
            return self._check_mac_proxy()
        elif system == 'Linux':
            return self._check_linux_proxy()
        return False
    
    def _check_windows_proxy(self):
        """检查Windows代理状态"""
        try:
            import winreg
            
            # 打开注册表
            reg_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings'
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
            
            # 读取代理设置
            proxy_enable, _ = winreg.QueryValueEx(reg_key, 'ProxyEnable')
            proxy_server, _ = winreg.QueryValueEx(reg_key, 'ProxyServer')
            
            winreg.CloseKey(reg_key)
            
            return proxy_enable == 1 and f'127.0.0.1:{self.port}' in proxy_server
        except Exception as e:
            logging.error(f"检查Windows代理失败: {str(e)}")
            return False
    
    def _check_mac_proxy(self):
        """检查macOS代理状态"""
        try:
            import subprocess
            
            # 检查Web代理设置
            result = subprocess.run(
                ['networksetup', '-getwebproxy', 'Wi-Fi'],
                capture_output=True,
                text=True
            )
            
            return f'Server: 127.0.0.1' in result.stdout and f'Port: {self.port}' in result.stdout
        except Exception as e:
            logging.error(f"检查macOS代理失败: {str(e)}")
            return False
    
    def _check_linux_proxy(self):
        """检查Linux代理状态"""
        try:
            # 检查环境变量
            import os
            http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
            https_proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
            
            expected_proxy = f'http://127.0.0.1:{self.port}'
            return http_proxy == expected_proxy and https_proxy == expected_proxy
        except Exception as e:
            logging.error(f"检查Linux代理失败: {str(e)}")
            return False