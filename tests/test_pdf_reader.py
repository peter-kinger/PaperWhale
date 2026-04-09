"""
AI文献阅读工具 - PDFReader模块测试
测试PDF读取、图片提取、元数据提取等功能
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 尝试导入，失败时提供有意义的错误信息
try:
    from pdf_reader import (
        PDFReader, PaperInfo, generate_paper_filename, sanitize_filename
    )
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保在项目根目录运行此测试")
    sys.exit(1)


class TestPDFReader(unittest.TestCase):
    """PDFReader模块测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.reader = PDFReader()
        cls.project_root = Path(__file__).parent.parent
        cls.test_pdfs_dir = cls.project_root / "input_pdfs"

        # 查找测试用PDF文件
        if cls.test_pdfs_dir.exists():
            pdf_files = list(cls.test_pdfs_dir.glob("*.pdf"))
            cls.test_pdf = pdf_files[0] if pdf_files else None
        else:
            cls.test_pdf = None

    def test_01_pdfreader_initialization(self):
        """测试PDFReader初始化"""
        reader = PDFReader()
        self.assertIsNotNone(reader)
        # 检查库可用性
        self.assertIn(reader.use_pdfplumber, [True, False])
        self.assertIn(reader.use_pypdf2, [True, False])

    def test_02_paper_info_dataclass(self):
        """测试PaperInfo数据类"""
        info = PaperInfo(
            title="测试标题",
            authors="张三, 李四",
            year="2024",
            abstract="测试摘要",
            filename="test.pdf",
            filepath="/path/to/test.pdf"
        )
        self.assertEqual(info.title, "测试标题")
        self.assertEqual(info.authors, "张三, 李四")
        self.assertEqual(info.year, "2024")
        self.assertEqual(info.abstract, "测试摘要")

    def test_03_sanitize_filename(self):
        """测试文件名清理"""
        # 测试非法字符替换
        self.assertEqual(sanitize_filename("正常文件名.pdf"), "正常文件名.pdf")
        self.assertEqual(sanitize_filename("file<>:\"/\\|?*.pdf"), "file_________.pdf")
        # 测试长度限制
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 200)

    def test_04_generate_paper_filename(self):
        """测试论文文件名生成"""
        # 测试标准情况 - authors="Zhang San" → 取最后一个词 "San" 作为姓氏
        info = PaperInfo(
            title="Deep Learning for Climate Prediction",
            authors="Zhang San, Li Si",
            year="2024",
            filename="test.pdf",
            filepath="/path/test.pdf"
        )
        filename = generate_paper_filename(info)
        self.assertIn("San", filename)  # 取最后一个词作为姓氏
        self.assertIn("2024", filename)
        self.assertTrue(filename.endswith(".md"))

        # 测试无作者情况
        info_no_author = PaperInfo(title="Unknown Title", year="2024")
        filename = generate_paper_filename(info_no_author)
        self.assertIn("Unknown", filename)

        # 测试无年份情况
        info_no_year = PaperInfo(title="Test Title", year="")
        filename = generate_paper_filename(info_no_year)
        self.assertIn("0000", filename)

    def test_05_extract_figures_and_tables(self):
        """测试图表提取"""
        text = """
        Figure 1: This is a description of Figure 1.
        Some content here.

        Figure 2: Description of Figure 2.
        More content.

        Table 1: Summary of results.
        More table content.
        """
        result = self.reader.extract_figures_and_tables(text)
        self.assertIn('figures', result)
        self.assertIn('tables', result)
        self.assertIsInstance(result['figures'], list)
        self.assertIsInstance(result['tables'], list)

    @unittest.skipUnless(
        Path(__file__).parent.parent.joinpath("input_pdfs").exists(),
        "input_pdfs目录不存在，跳过实际PDF测试"
    )
    def test_06_read_pdf_with_real_file(self):
        """测试读取真实PDF文件"""
        if not self.test_pdf:
            self.skipTest("没有找到测试PDF文件")

        text, info = self.reader.read_pdf(str(self.test_pdf))
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0, "PDF文本不应为空")
        self.assertIsInstance(info, PaperInfo)
        self.assertIn(info.filename, str(self.test_pdf))

    @unittest.skipUnless(
        Path(__file__).parent.parent.joinpath("input_pdfs").exists(),
        "input_pdfs目录不存在，跳过实际PDF测试"
    )
    def test_07_read_pdf_with_images(self):
        """测试PDF+图片提取"""
        if not self.test_pdf:
            self.skipTest("没有找到测试PDF文件")

        text, info, images = self.reader.read_pdf_with_images(
            str(self.test_pdf),
            max_images=5
        )
        self.assertIsInstance(text, str)
        self.assertIsInstance(images, list)
        # images中每个元素应包含必要字段
        for img in images:
            self.assertIn('page', img)
            self.assertIn('index', img)
            self.assertIn('path', img)
            self.assertIn('size', img)
            self.assertIn('b64', img)
            self.assertIn('hash', img)

    def test_08_extract_images_from_pdf_mock(self):
        """测试图片提取（模拟）"""
        with patch('pdf_reader.PYMUPDF_AVAILABLE', False):
            reader = PDFReader()
            result = reader.extract_images_from_pdf("/fake/path.pdf")
            self.assertEqual(result, [])  # 无PyMuPDF时应返回空列表

    def test_09_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.reader.read_pdf("/nonexistent/path/to/file.pdf")

    def test_10_read_folder_mock(self):
        """测试读取文件夹（模拟）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建空目录（无PDF文件）
            result = self.reader.read_folder(tmpdir)
            self.assertEqual(result, [])


class TestPDFReaderImageExtraction(unittest.TestCase):
    """图片提取专项测试"""

    def setUp(self):
        self.reader = PDFReader()

    def test_image_filter_size(self):
        """测试图片大小过滤逻辑"""
        # 模拟图片尺寸检查
        test_cases = [
            ((50, 50), False),   # 太小，应过滤
            ((99, 100), False),  # 宽度<100，应过滤
            ((100, 100), True),  # 刚好100，可以通过
            ((1920, 1080), True),  # 正常尺寸
        ]
        for size, expected_pass in test_cases:
            width, height = size
            passed = width >= 100 and height >= 100
            self.assertEqual(passed, expected_pass,
                           f"图片尺寸 {size} 应{'通过' if expected_pass else '过滤'}")

    def test_image_hash_deduplication(self):
        """测试图片hash去重逻辑"""
        hashes = set()
        test_hashes = ["abc123", "def456", "abc123", "ghi789"]
        expected_unique = 3

        for h in test_hashes:
            if h not in hashes:
                hashes.add(h)

        self.assertEqual(len(hashes), expected_unique)


class TestPaperInfoEdgeCases(unittest.TestCase):
    """PaperInfo边缘情况测试"""

    def test_empty_paper_info(self):
        """测试空PaperInfo"""
        info = PaperInfo()
        self.assertEqual(info.title, "")
        self.assertEqual(info.authors, "")
        self.assertEqual(info.year, "")
        self.assertEqual(info.abstract, "")

    def test_paper_info_with_special_chars(self):
        """测试含特殊字符的PaperInfo"""
        info = PaperInfo(
            title="论文标题 with <特殊> & \"字符\"",
            authors="作者, 另一个<作者>",
            year="2024"
        )
        self.assertIn("论文标题", info.title)
        filename = generate_paper_filename(info)
        # 文件名中不应包含非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        import re
        self.assertIsNone(re.search(illegal_chars, filename))


if __name__ == "__main__":
    unittest.main(verbosity=2)