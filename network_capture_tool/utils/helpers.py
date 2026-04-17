import platform
import os
import sys
import tempfile

def get_platform_info():
    """
    获取当前平台信息
    
    Returns:
        dict: 包含平台信息的字典
    """
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'python_version': platform.python_version()
    }

def get_temp_dir():
    """
    获取临时目录
    
    Returns:
        str: 临时目录路径
    """
    return tempfile.gettempdir()

def ensure_directory(path):
    """
    确保目录存在
    
    Args:
        path: 目录路径
    """
    if not os.path.exists(path):
        os.makedirs(path)

def get_app_data_dir():
    """
    获取应用数据目录
    
    Returns:
        str: 应用数据目录路径
    """
    system = platform.system()
    if system == 'Windows':
        return os.path.join(os.environ.get('APPDATA', ''), 'NetworkCaptureTool')
    elif system == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'NetworkCaptureTool')
    else:  # Linux
        return os.path.join(os.path.expanduser('~'), '.network_capture_tool')

def is_admin():
    """
    检查是否以管理员权限运行
    
    Returns:
        bool: 是否以管理员权限运行
    """
    try:
        if platform.system() == 'Windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False

def get_python_executable():
    """
    获取Python可执行文件路径
    
    Returns:
        str: Python可执行文件路径
    """
    return sys.executable

def format_bytes(bytes_value):
    """
    格式化字节大小
    
    Args:
        bytes_value: 字节数
    
    Returns:
        str: 格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"