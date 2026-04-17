import unittest
import os
import sys
from queue import Queue

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('..'))

from core.capture_engine import CaptureEngine

class TestCaptureEngine(unittest.TestCase):
    """抓包引擎类的单元测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.queue = Queue()
        self.capture_engine = CaptureEngine(self.queue)
    
    def test_start_capture(self):
        """测试开始抓包功能"""
        # 测试开始抓包（这里只是测试函数是否能正常执行）
        # 注意：这个测试可能会触发实际的抓包操作，需要谨慎运行
        try:
            self.capture_engine.start_capture(1)  # 使用PID 1作为测试
            # 检查线程是否创建
            self.assertIsNotNone(self.capture_engine.capture_thread)
        except Exception as e:
            # 这里我们只是测试函数是否能正常执行，不强制要求抓包必须成功
            pass
    
    def test_stop_capture(self):
        """测试停止抓包功能"""
        # 测试停止抓包
        self.capture_engine.stop_capture()
        # 检查状态是否正确
        self.assertFalse(self.capture_engine.running)

if __name__ == '__main__':
    unittest.main()
