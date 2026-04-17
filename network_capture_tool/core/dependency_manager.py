import subprocess
import platform
import tempfile
import urllib.request
import os
import sys
import logging

# 创建日志记录器
logger = logging.getLogger(__name__)

class DependencyManager:
    """依赖管理类"""
    
    @staticmethod
    def check_system_dependencies():
        """检查系统级依赖"""
        print("开始检查系统级依赖...")
        logger.debug("开始检查系统级依赖...")
        
        system = platform.system()
        
        # 检查权限
        if not DependencyManager.check_privileges():
            print("权限不足，请以管理员/root身份运行程序")
            logger.error("权限不足，请以管理员/root身份运行程序")
            return False
        
        # 检查系统依赖
        if system == 'Windows':
            # Windows下检查Npcap/WinPcap
            try:
                # 尝试导入winpcap模块（scapy的依赖）
                from scapy.all import conf
                # 尝试获取接口列表，这会触发底层依赖检查
                interfaces = conf.ifaces.values()
                print("Windows系统依赖检查通过")
                logger.info("Windows系统依赖检查通过")
            except Exception as e:
                print(f"Windows系统依赖检查失败: {e}")
                print("请安装Npcap或WinPcap")
                logger.error(f"Windows系统依赖检查失败: {e}")
                return False
        elif system == 'Linux':
            # Linux下检查libpcap
            try:
                # 尝试运行tcpdump -h来检查libpcap
                result = subprocess.run(['tcpdump', '-h'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Linux系统依赖检查通过")
                    logger.info("Linux系统依赖检查通过")
                else:
                    print("Linux系统依赖检查失败: 未找到tcpdump")
                    print("请安装libpcap和tcpdump")
                    logger.error("Linux系统依赖检查失败: 未找到tcpdump")
                    return False
            except FileNotFoundError:
                print("Linux系统依赖检查失败: 未找到tcpdump")
                print("请安装libpcap和tcpdump")
                logger.error("Linux系统依赖检查失败: 未找到tcpdump")
                return False
        elif system == 'Darwin':
            # macOS下检查libpcap
            try:
                # 尝试运行tcpdump -h来检查libpcap
                result = subprocess.run(['tcpdump', '-h'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("macOS系统依赖检查通过")
                    logger.info("macOS系统依赖检查通过")
                else:
                    print("macOS系统依赖检查失败: 未找到tcpdump")
                    print("请安装libpcap")
                    logger.error("macOS系统依赖检查失败: 未找到tcpdump")
                    return False
            except FileNotFoundError:
                print("macOS系统依赖检查失败: 未找到tcpdump")
                print("请安装libpcap")
                logger.error("macOS系统依赖检查失败: 未找到tcpdump")
                return False
        
        print("系统级依赖检查成功")
        logger.info("系统级依赖检查成功")
        return True
    
    @staticmethod
    def check_privileges():
        """检查是否有足够的权限"""
        system = platform.system()
        
        if system == 'Windows':
            # Windows下检查是否以管理员身份运行
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception:
                return False
        elif system in ['Linux', 'Darwin']:
            # Linux/macOS下检查是否为root用户
            return os.geteuid() == 0
        
        return True
    
    @staticmethod
    def install_dependencies():
        """安装所需依赖"""
        print("开始安装依赖...")
        logger.debug("开始安装依赖...")
        required_packages = ['psutil', 'pandas', 'requests', 'scapy']
        missing_packages = []
        
        # 检查Python包
        print(f"检查Python包: {required_packages}")
        logger.debug(f"检查Python包: {required_packages}")
        for package in required_packages:
            try:
                __import__(package)
                print(f"{package} 已安装")
                logger.info(f"{package} 已安装")
                logger.debug(f"{package} 导入成功")
            except ImportError as e:
                missing_packages.append(package)
                print(f"{package} 未安装: {e}")
                logger.warning(f"{package} 未安装: {e}")
        
        # 安装缺失的Python包
        if missing_packages:
            print(f"正在安装缺失的依赖包: {', '.join(missing_packages)}")
            logger.info(f"正在安装缺失的依赖包: {', '.join(missing_packages)}")
            logger.debug(f"安装命令: {[sys.executable, '-m', 'pip', 'install', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'] + missing_packages}")
            try:
                result = subprocess.check_output(
                    [sys.executable, '-m', 'pip', 'install', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'] + missing_packages,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                print(f"安装输出: {result}")
                logger.debug(f"安装输出: {result}")
                print("Python依赖包安装成功")
                logger.info("Python依赖包安装成功")
            except subprocess.CalledProcessError as e:
                print(f"依赖安装失败: {e.output}")
                logger.error(f"依赖安装失败: {e.output}")
                return False
        
        # 检查系统级依赖
        if not DependencyManager.check_system_dependencies():
            return False
        
        print("所有依赖安装成功")
        logger.info("所有依赖安装成功")
        logger.debug("依赖安装完成")
        return True