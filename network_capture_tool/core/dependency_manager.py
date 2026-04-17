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
    def check_tshark():
        """检查tshark是否安装（pyshark的必要依赖）"""
        logger.debug("开始检查tshark...")
        # 尝试直接运行tshark命令
        try:
            logger.debug("尝试直接运行tshark命令...")
            result = subprocess.run(['tshark', '--version'], capture_output=True, text=True, check=True)
            logger.info(f"tshark版本: {result.stdout.strip()}")
            logger.debug("tshark检查成功")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"直接运行tshark失败: {e}")
            # 尝试使用用户指定的路径
            custom_path = "F:\\Wireshark\\tshark.exe"
            logger.debug(f"尝试使用自定义路径: {custom_path}")
            try:
                result = subprocess.run([custom_path, '--version'], capture_output=True, text=True, check=True)
                logger.info(f"tshark版本: {result.stdout.strip()}")
                # 将Wireshark路径添加到系统PATH
                wireshark_dir = "F:\\Wireshark"
                if wireshark_dir not in os.environ['PATH']:
                    os.environ['PATH'] += ';' + wireshark_dir
                    logger.info(f"已将Wireshark路径添加到系统PATH: {wireshark_dir}")
                logger.debug("tshark检查成功（使用自定义路径）")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"未检测到tshark，请安装Wireshark: {e}")
                return False
    
    @staticmethod
    def install_wireshark():
        """自动安装Wireshark"""
        system = platform.system()
        
        if system == 'Windows':
            try:
                # Wireshark下载地址（64位Windows）
                wireshark_url = "https://2.na.dl.wireshark.org/win64/Wireshark-win64-latest.exe"
                
                # 创建临时文件
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, "Wireshark-installer.exe")
                
                # 下载安装程序
                with urllib.request.urlopen(wireshark_url) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded_size = 0
                    
                    with open(installer_path, 'wb') as f:
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            progress = (downloaded_size / total_size) * 100
                            logging.info(f"Wireshark下载进度: {progress:.1f}%")
                
                # 运行安装程序（静默安装）
                subprocess.run([installer_path, "/S"], check=True)
                
                # 添加Wireshark到系统PATH
                wireshark_path = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Wireshark')
                if os.path.exists(wireshark_path):
                    os.environ['PATH'] += ';' + wireshark_path
                    logging.info(f"已将Wireshark路径添加到系统PATH: {wireshark_path}")
                
                return True
                
            except Exception as e:
                logging.error(f"Wireshark安装失败: {str(e)}")
                return False
        elif system == 'Darwin':  # macOS
            logging.info("macOS平台，请手动安装Wireshark")
            return False
        elif system == 'Linux':
            logging.info("Linux平台，请使用包管理器安装Wireshark")
            return False
        else:
            logging.warning(f"不支持的操作系统: {system}")
            return False
    
    @staticmethod
    def install_dependencies():
        """安装所需依赖"""
        logger.debug("开始安装依赖...")
        required_packages = ['psutil', 'pandas', 'requests']
        missing_packages = []
        
        # 检查Python包
        logger.debug(f"检查Python包: {required_packages}")
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"{package} 已安装")
                logger.debug(f"{package} 导入成功")
            except ImportError as e:
                missing_packages.append(package)
                logger.warning(f"{package} 未安装: {e}")
        
        # 安装缺失的Python包
        if missing_packages:
            logger.info(f"正在安装缺失的依赖包: {', '.join(missing_packages)}")
            logger.debug(f"安装命令: {[sys.executable, '-m', 'pip', 'install', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'] + missing_packages}")
            try:
                result = subprocess.check_output(
                    [sys.executable, '-m', 'pip', 'install', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'] + missing_packages,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                logger.debug(f"安装输出: {result}")
                logger.info("Python依赖包安装成功")
            except subprocess.CalledProcessError as e:
                logger.error(f"依赖安装失败: {e.output}")
                return False
        
        # 检查tshark
        logger.debug("检查tshark...")
        if not DependencyManager.check_tshark():
            # 询问用户是否自动安装Wireshark
            user_input = input("未检测到tshark（Wireshark的组件），是否自动安装Wireshark？(y/n): ")
            logger.debug(f"用户输入: {user_input}")
            if user_input.lower() == 'y':
                logger.debug("用户选择自动安装Wireshark")
                if DependencyManager.install_wireshark():
                    # 重新检查tshark
                    logger.debug("重新检查tshark...")
                    if DependencyManager.check_tshark():
                        logger.info("Wireshark安装成功，tshark已就绪")
                    else:
                        logger.error("Wireshark安装后仍未检测到tshark")
                        return False
                else:
                    logger.debug("Wireshark安装失败")
                    return False
            else:
                logger.error("未检测到tshark，请先安装Wireshark（包含tshark）！")
                return False
        
        # 安装pyshark
        logger.debug("检查pyshark...")
        try:
            __import__('pyshark')
            logger.info("pyshark 已安装")
            logger.debug("pyshark 导入成功")
        except ImportError:
            logger.info("正在安装pyshark...")
            logger.debug(f"安装命令: {[sys.executable, '-m', 'pip', 'install', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple', 'pyshark']}")
            try:
                result = subprocess.check_output(
                    [sys.executable, '-m', 'pip', 'install', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple', 'pyshark'],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                logger.debug(f"安装输出: {result}")
                logger.info("pyshark安装成功")
            except subprocess.CalledProcessError as e:
                logger.error(f"pyshark安装失败: {e.output}")
                return False
        
        logger.info("所有依赖安装成功")
        logger.debug("依赖安装完成")
        return True