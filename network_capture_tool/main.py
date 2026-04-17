import tkinter as tk
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 默认日志级别为INFO
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',  # 添加文件名和行号
    handlers=[
        logging.FileHandler('capture_tool.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建日志记录器
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

from core.dependency_manager import DependencyManager
from ui.main_window import NetworkCaptureTool

def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Network Capture Tool')
    parser.add_argument('--cli', action='store_true', help='Run in command line mode')
    parser.add_argument('--pid', type=int, help='Process ID to capture')
    parser.add_argument('--interface', type=str, help='Network interface to use')
    parser.add_argument('--duration', type=int, default=60, help='Capture duration in seconds')
    args = parser.parse_args()
    
    print("程序启动中...")
    logger.debug("程序启动中...")
    logger.info("程序启动中...")
    
    try:
        # 检查依赖
        print("开始检查依赖项...")
        logger.debug("开始检查依赖项...")
        logger.info("检查依赖项...")
        dependency_manager = DependencyManager()
        if not dependency_manager.install_dependencies():
            print("依赖安装失败，程序退出")
            logger.error("依赖安装失败，程序退出")
            sys.exit(1)
        print("依赖检查完成")
        logger.debug("依赖检查完成")
        
        # 检查是否有图形界面
        try:
            import tkinter
            has_gui = True
        except ImportError:
            has_gui = False
        
        # 如果指定了--cli参数，或者没有图形界面，运行命令行模式
        if args.cli or not has_gui:
            run_cli_mode(args)
        else:
            # 初始化GUI
            print("开始初始化GUI...")
            logger.debug("开始初始化GUI...")
            logger.info("初始化GUI...")
            root = tk.Tk()
            print(f"创建根窗口: {root}")
            logger.debug(f"创建根窗口: {root}")
            
            try:
                app = NetworkCaptureTool(root)
                print(f"创建应用实例: {app}")
                logger.debug(f"创建应用实例: {app}")
                print("GUI初始化完成，进入主循环")
                logger.info("GUI初始化完成，进入主循环")
                root.mainloop()
            except Exception as e:
                print(f"GUI运行出错: {str(e)}")
                logger.error(f"GUI运行出错: {str(e)}")
                import traceback
                traceback.print_exc()
                logger.debug(f"错误详情: {traceback.format_exc()}")
                # 显示错误信息给用户
                import tkinter.messagebox
                tkinter.messagebox.showerror("错误", f"程序运行出错: {str(e)}")
    except KeyboardInterrupt:
        print("用户中断了程序")
        logger.info("用户中断了程序")
    except Exception as e:
        print(f"程序启动出错: {str(e)}")
        logger.error(f"程序启动出错: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.debug(f"错误详情: {traceback.format_exc()}")
    finally:
        print("程序退出")
        logger.info("程序退出")

def run_cli_mode(args):
    """命令行模式"""
    print("运行命令行模式...")
    logger.info("运行命令行模式...")
    
    if not args.pid:
        print("错误：请使用 --pid 参数指定要捕获的进程ID")
        logger.error("错误：请使用 --pid 参数指定要捕获的进程ID")
        return
    
    # 导入抓包引擎
    from core.capture_engine import CaptureEngine
    
    # 创建队列
    import queue
    packet_queue = queue.Queue()
    
    # 创建抓包引擎
    engine = CaptureEngine(packet_queue)
    
    # 开始抓包
    print(f"开始捕获进程 {args.pid} 的网络数据包...")
    logger.info(f"开始捕获进程 {args.pid} 的网络数据包...")
    engine.start_capture(args.pid)
    
    # 捕获指定时间
    import time
    start_time = time.time()
    packet_count = 0
    
    try:
        while time.time() - start_time < args.duration:
            try:
                # 尝试从队列中获取数据包
                packet = packet_queue.get(timeout=1)
                if isinstance(packet, dict):
                    # 处理数据包
                    packet_count += 1
                    print(f"[{packet['time']}] {packet['src']}:{packet['src_port']} -> {packet['dst']}:{packet['dst_port']} {packet['proto']} {packet['length']} bytes")
                    logger.info(f"[{packet['time']}] {packet['src']}:{packet['src_port']} -> {packet['dst']}:{packet['dst_port']} {packet['proto']} {packet['length']} bytes")
                elif isinstance(packet, tuple) and packet[0] == "error":
                    # 处理错误
                    print(f"错误: {packet[1]}")
                    logger.error(f"错误: {packet[1]}")
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        print("用户中断抓包")
        logger.info("用户中断抓包")
    finally:
        # 停止抓包
        print("停止抓包...")
        logger.info("停止抓包...")
        engine.stop_capture()
        print(f"抓包完成，共捕获 {packet_count} 个数据包")
        logger.info(f"抓包完成，共捕获 {packet_count} 个数据包")

if __name__ == "__main__":
    main()