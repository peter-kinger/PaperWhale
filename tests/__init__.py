"""
AI文献阅读工具 - 测试套件
运行所有测试: python -m pytest tests/ -v
或直接运行: python tests/test_all.py
"""

import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


if __name__ == "__main__":
    # 直接运行此文件时，执行所有测试
    from tests.test_pdf_reader import TestPDFReader
    from tests.test_api_client import TestAPIClient
    from tests.test_doc_generator import TestDocGenerator

    print("=" * 60)
    print("AI文献阅读工具 - 测试套件")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestPDFReader))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIClient))
    suite.addTests(loader.loadTestsFromTestCase(TestDocGenerator))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出总结
    print("\n" + "=" * 60)
    print(f"测试完成: {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    if result.failures:
        print(f"失败: {len(result.failures)}")
    if result.errors:
        print(f"错误: {len(result.errors)}")
    print("=" * 60)

    # 以退出码形式反映结果
    sys.exit(0 if result.wasSuccessful() else 1)