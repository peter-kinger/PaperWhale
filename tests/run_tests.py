"""
测试运行脚本 - 简化测试执行
运行方式:
  python tests/run_tests.py              # 运行所有测试
  python tests/run_tests.py pdf_reader    # 只运行PDF模块测试
  python tests/run_tests.py api_client    # 只运行API模块测试
  python tests/run_tests.py doc_generator # 只运行文档生成测试
"""

import os
import sys
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"


def run_tests(module=None, verbose=True):
    """运行测试

    Args:
        module: 指定模块名（pdf_reader/api_client/doc_generator），None表示全部
        verbose: 是否详细输出
    """
    # 确保在正确目录
    os.chdir(PROJECT_ROOT)

    # 切换到项目根目录
    print(f"当前目录: {os.getcwd()}")
    print(f"项目目录: {PROJECT_ROOT}")
    print("-" * 60)

    # 准备测试文件列表
    if module:
        test_file = TESTS_DIR / f"test_{module}.py"
        if not test_file.exists():
            print(f"错误: 测试文件 {test_file} 不存在")
            return False
        test_files = [str(test_file)]
    else:
        test_files = [
            str(TESTS_DIR / "test_pdf_reader.py"),
            str(TESTS_DIR / "test_api_client.py"),
            str(TESTS_DIR / "test_doc_generator.py"),
        ]

    # 构建命令
    cmd = [sys.executable, "-m", "unittest", "discover"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-s", str(TESTS_DIR)])
    cmd.append("-p" if not module else f"test_{module}.py")

    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 60)

    # 执行
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )
        return result.returncode == 0
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False


def run_with_pytest(module=None):
    """使用pytest运行测试（如果可用）"""
    try:
        import pytest
    except ImportError:
        print("提示: pytest 未安装，将使用 unittest")
        return run_tests(module)

    os.chdir(PROJECT_ROOT)

    if module:
        args = ["-v", str(TESTS_DIR / f"test_{module}.py")]
    else:
        args = ["-v", str(TESTS_DIR)]

    print(f"运行pytest: {' '.join(args)}")
    return pytest.main(args) == 0


if __name__ == "__main__":
    # 解析参数
    module = None
    if len(sys.argv) > 1:
        module = sys.argv[1]

    print("=" * 60)
    print("AI文献阅读工具 - 测试运行器")
    print("=" * 60)

    # 运行测试
    success = run_tests(module)

    print("\n" + "=" * 60)
    if success:
        print("测试全部通过!")
    else:
        print("部分测试失败，请检查上述输出。")
    print("=" * 60)

    sys.exit(0 if success else 1)