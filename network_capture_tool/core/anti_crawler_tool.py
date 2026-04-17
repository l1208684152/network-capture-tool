import random
import logging
import requests

class AntiCrawlerTool:
    """反爬虫工具类"""
    
    def __init__(self):
        self.common_ua = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/119.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 14; Mobile; rv:119.0) Gecko/119.0 Firefox/119.0',
            'Mozilla/5.0 (Android 14; Mobile; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        self.ua_history = []
        self.proxy_history = []
        self.request_timestamps = {}
        self.cookies = {}
    
    def generate_random_ua(self):
        """生成随机User-Agent"""
        browsers = ['Chrome', 'Firefox', 'Edge', 'Safari']
        
        # 操作系统和对应的系统字符串
        os_list = [
            ('Windows', 'Windows NT 10.0; Win64; x64'),
            ('macOS', 'Macintosh; Intel Mac OS X 14_2'),
            ('Linux', 'X11; Linux x86_64')
        ]
        
        browser = random.choice(browsers)
        os_name, os_string = random.choice(os_list)
        
        if browser == 'Chrome':
            version = f'{random.randint(110, 120)}.0.0.0'
            ua = f'Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'
        elif browser == 'Firefox':
            version = f'{random.randint(115, 120)}.0'
            # Firefox的UA格式略有不同
            if os_name == 'Windows':
                ua = f'Mozilla/5.0 ({os_string}; rv:{version}) Gecko/{version} Firefox/{version}'
            elif os_name == 'macOS':
                ua = f'Mozilla/5.0 ({os_string}) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/{version}'
            else:  # Linux
                ua = f'Mozilla/5.0 ({os_string}; rv:{version}) Gecko/{version} Firefox/{version}'
        elif browser == 'Edge':
            version = f'{random.randint(110, 120)}.0.0.0'
            ua = f'Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Edge/{version}'
        else:  # Safari
            version = f'{random.randint(16, 17)}.{random.randint(0, 2)}'
            # Safari主要用于macOS和iOS
            if os_name == 'macOS':
                ua = f'Mozilla/5.0 ({os_string}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15'
            elif os_name == 'Windows':
                # Windows上的Safari
                ua = f'Mozilla/5.0 ({os_string}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15'
            else:  # Linux
                # Linux上的Safari
                ua = f'Mozilla/5.0 ({os_string}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15'
        
        return ua
    
    def generate_browser_fingerprint(self, user_agent):
        """生成浏览器指纹"""
        # 生成浏览器指纹
        fingerprint = {
            'user_agent': user_agent,
            'browser': random.choice(['Chrome', 'Firefox', 'Edge', 'Safari']),
            'browser_version': f'{random.randint(90, 120)}.0.{random.randint(0, 9999)}.{random.randint(0, 999)}',
            'os': random.choice(['Windows', 'macOS', 'Linux']),
            'os_version': random.choice(['10', '11', '14', '15', '20.04', '22.04']),
            'screen_resolution': f'{random.randint(1366, 3840)}x{random.randint(768, 2160)}',
            'color_depth': random.choice(['24', '32']),
            'language': random.choice(['zh-CN', 'en-US', 'ja-JP', 'ko-KR']),
            'timezone': random.choice(['Asia/Shanghai', 'America/New_York', 'Europe/London', 'Asia/Tokyo']),
            'canvas_hash': f'{random.randint(1000000, 9999999)}',
            'webgl_hash': f'{random.randint(1000000, 9999999)}',
            'fonts': random.sample(['Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Microsoft YaHei', 'SimSun'], 3),
            'plugins': random.sample(['Flash', 'Java', 'QuickTime', 'Silverlight'], 2),
            'do_not_track': random.choice(['1', '0', 'null']),
            'touch_support': random.choice(['true', 'false']),
            'device_memory': str(random.randint(4, 16)),
            'hardware_concurrency': str(random.randint(2, 16))
        }
        
        # 保存到ua_history
        self.ua_history.append(fingerprint)
        
        return fingerprint
    
    def generate_request_headers(self, user_agent):
        """生成请求头模板"""
        # 生成请求头
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(['zh-CN,zh;q=0.9,en;q=0.8', 'en-US,en;q=0.9,zh-CN;q=0.8']),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': str(random.randint(0, 1)),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Chromium";v="120", "Not=A?Brand";v="8", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Referer': 'https://www.google.com/'
        }
        
        return headers
    
    def test_proxy(self, proxy):
        """测试代理是否可用"""
        try:
            # 使用HTTPS地址测试代理，这样可以测试HTTPS代理是否可用
            response = requests.get('https://www.baidu.com', proxies={'http': proxy, 'https': proxy}, timeout=5)
            if response.status_code == 200:
                return True, f"代理 {proxy} 可用！"
            else:
                return False, f"代理 {proxy} 不可用，状态码：{response.status_code}"
        except Exception as e:
            return False, f"代理 {proxy} 不可用：{str(e)}"
    
    def analyze_anti_crawler(self, packet):
        """分析数据包的反爬虫特征"""
        analysis = []
        packet_str = str(packet)
        
        # 检查是否有反爬虫相关的请求头
        anti_crawler_headers = [
            'User-Agent', 'Referer', 'Cookie', 'X-Requested-With', 
            'Authorization', 'Origin', 'DNT', 'Accept-Language',
            'Accept-Encoding', 'Cache-Control', 'Pragma'
        ]
        
        analysis.append("=== 反爬虫分析结果 ===")
        analysis.append(f"数据包时间: {packet.sniff_time}")
        analysis.append(f"协议: {packet.transport_layer if hasattr(packet, 'transport_layer') else 'Unknown'}")
        
        # 检查HTTP请求
        if packet.haslayer('HTTPRequest'):
            analysis.append("\n--- HTTP请求分析 ---")
            http_layer = packet['HTTPRequest']
            
            # 检查请求方法
            if hasattr(http_layer, 'Method'):
                analysis.append(f"请求方法: {http_layer.Method.decode('utf-8', errors='ignore')}")
            
            # 检查请求路径
            if hasattr(http_layer, 'Path'):
                analysis.append(f"请求路径: {http_layer.Path.decode('utf-8', errors='ignore')}")
            
            # 检查请求头
            for header in anti_crawler_headers:
                if hasattr(http_layer, header):
                    header_value = getattr(http_layer, header)
                    if isinstance(header_value, bytes):
                        header_value = header_value.decode('utf-8', errors='ignore')
                    analysis.append(f"{header}: {header_value}")
            
            # 检查Cookie
            if hasattr(http_layer, 'Cookie'):
                cookies = http_layer.Cookie
                if isinstance(cookies, bytes):
                    cookies = cookies.decode('utf-8', errors='ignore')
                cookie_count = len(cookies.split(';')) if cookies else 0
                analysis.append(f"Cookie数量: {cookie_count}")
            
            # 检查是否有Referer
            if hasattr(http_layer, 'Referer'):
                analysis.append("包含Referer头")
            else:
                analysis.append("警告：缺少Referer头，可能被识别为爬虫")
            
            # 检查User-Agent
            if hasattr(http_layer, 'User_Agent'):
                ua = http_layer.User_Agent
                if isinstance(ua, bytes):
                    ua = ua.decode('utf-8', errors='ignore')
                if 'bot' in ua.lower() or 'spider' in ua.lower():
                    analysis.append("警告：User-Agent包含爬虫特征")
                else:
                    analysis.append("User-Agent看起来正常")
            else:
                analysis.append("警告：缺少User-Agent头，可能被识别为爬虫")
        
        # 检查HTTP响应
        if packet.haslayer('HTTPResponse'):
            http_layer = packet['HTTPResponse']
            # 检查响应状态码
            if hasattr(http_layer, 'Status_Code'):
                status_code = http_layer.Status_Code
                if isinstance(status_code, bytes):
                    status_code = status_code.decode('utf-8', errors='ignore')
                analysis.append(f"\n响应状态码: {status_code}")
                if status_code == '403':
                    analysis.append("警告：收到403 Forbidden，可能被反爬虫机制拦截")
                elif status_code == '429':
                    analysis.append("警告：收到429 Too Many Requests，请求频率过高")
                elif status_code == '503':
                    analysis.append("警告：收到503 Service Unavailable，可能被限流")
        
        # 检查是否有JavaScript挑战
        if 'javascript' in packet_str.lower() or 'challenge' in packet_str.lower():
            analysis.append("\n发现JavaScript相关内容，可能包含反爬虫挑战")
        
        # 检查是否有验证码相关内容
        if 'captcha' in packet_str.lower() or 'verify' in packet_str.lower():
            analysis.append("\n发现验证码相关内容，可能需要验证码验证")
        
        return '\n'.join(analysis)