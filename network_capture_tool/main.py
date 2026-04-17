import tkinter as tk
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 提高日志级别到DEBUG
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',  # 添加文件名和行号
    handlers=[
        logging.FileHandler('capture_tool.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建日志记录器
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('..'))

from core.dependency_manager import DependencyManager
from ui.main_window import NetworkCaptureTool

def main():
    """主函数"""
    logger.debug("程序启动中...")
    logger.info("程序启动中...")
    
    # 检查依赖
    logger.debug("开始检查依赖项...")
    logger.info("检查依赖项...")
    dependency_manager = DependencyManager()
    if not dependency_manager.install_dependencies():
        logger.error("依赖安装失败，程序退出")
        sys.exit(1)
    logger.debug("依赖检查完成")
    
    # 初始化GUI
    logger.debug("开始初始化GUI...")
    logger.info("初始化GUI...")
    root = tk.Tk()
    logger.debug(f"创建根窗口: {root}")
    
    try:
        app = NetworkCaptureTool(root)
        logger.debug(f"创建应用实例: {app}")
        logger.info("GUI初始化完成，进入主循环")
        root.mainloop()
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.debug(f"错误详情: {traceback.format_exc()}")
    finally:
        logger.info("程序退出")

if __name__ == "__main__":
    main()