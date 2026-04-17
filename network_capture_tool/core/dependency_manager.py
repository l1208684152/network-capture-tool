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
        
        print("所有依赖安装成功")
        logger.info("所有依赖安装成功")
        logger.debug("依赖安装完成")
        return True