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
        
        # 生成CA证书
        self._generate_ca_cert()
    
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
        
        class ProxyHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle_request()
            
            def do_POST(self):
                self._handle_request()
            
            def _handle_request(self):
                try:
                    # 解析URL
                    url = urlparse(self.path)
                    if not url.netloc:
                        # 处理相对路径
                        url = urlparse(f'http://{self.headers["Host"]}{self.path}')
                    
                    hostname = url.netloc.split(':')[0]
                    port = url.port or (443 if url.scheme == 'https' else 80)
                    
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
                    
                    if url.scheme == 'https':
                        # HTTPS连接
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        sock = context.wrap_socket(sock, server_hostname=hostname)
                    
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
                    self.send_error(500, f"Proxy Error: {str(e)}")
        
        # 创建HTTP服务器
        self.server = HTTPServer((self.host, self.port), ProxyHandler)
        
        # 包装为HTTPS服务器
        cert_file, key_file = self._generate_cert(self.host)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_file, key_file)
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        
        # 启动服务器线程
        self.is_running = True
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logging.info(f"MITM代理服务器已启动: https://{self.host}:{self.port}")
    
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
        return f"https://{self.host}:{self.port}"
    
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
                winreg.SetValueEx(reg_key, 'ProxyServer', 0, winreg.REG_SZ, f'127.0.0.1:{self.port}')
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