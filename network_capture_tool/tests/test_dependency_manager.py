import unittest
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('..'))

from core.dependency_manager import DependencyManager

class TestDependencyManager(unittest.TestCase):
    """依赖管理类的单元测试"""
    
    def test_check_tshark(self):
        """测试tshark检查功能"""
        # 测试tshark检查
        result = DependencyManager.check_tshark()
        # 这里我们只是测试函数是否能正常执行，不强制要求tshark必须安装
        self.assertIsInstance(result, bool)
    
    def test_install_dependencies(self):
        """测试依赖安装功能"""
        # 测试依赖安装（这里只是测试函数是否能正常执行）
        # 注意：这个测试可能会触发依赖安装，需要谨慎运行
        result = DependencyManager.install_dependencies()
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()
