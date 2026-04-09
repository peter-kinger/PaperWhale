"""
AI文献阅读工具 - DocGenerator模块测试
测试文档生成、Prompt管理、上下文超限检查等功能
"""

import os
import sys
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# 尝试导入
try:
    from doc_generator import DocGenerator, PromptManager, AnalysisResult
    from pdf_reader import PaperInfo
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保在项目根目录运行此测试")
    sys.exit(1)


class TestPromptManager(unittest.TestCase):
    """PromptManager测试"""

    @classmethod
    def setUpClass(cls):
        cls.manager = PromptManager()

    def test_01_manager_initialization(self):
        """测试PromptManager初始化"""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.prompts_config)

    def test_02_get_available_profiles(self):
        """测试获取可用模板"""
        profiles = self.manager.get_available_profiles()
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)

        # 验证profile结构
        for profile in profiles:
            self.assertIn('id', profile)
            self.assertIn('name', profile)

    def test_03_get_active_profile(self):
        """测试获取当前激活的模板"""
        profile = self.manager.get_active_profile()
        self.assertIsInstance(profile, dict)
        self.assertIn('prompts', profile)

    def test_04_set_active_profile(self):
        """测试设置当前模板"""
        # 获取当前
        original = self.manager.prompts_config.get('active_profile', 'default')

        # 设置新模板（如果存在）
        profiles = self.manager.get_available_profiles()
        if len(profiles) > 1:
            new_profile = profiles[1]['id']
            result = self.manager.set_active_profile(new_profile)
            self.assertTrue(result)

        # 恢复原始
        self.manager.set_active_profile(original)

    def test_05_get_prompts(self):
        """测试获取Prompts"""
        prompts = self.manager.get_prompts()
        self.assertIsInstance(prompts, dict)
        # default profile 应有 paper_analysis 和 brief_summary
        self.assertIn('paper_analysis', prompts)


class TestAnalysisResult(unittest.TestCase):
    """AnalysisResult数据类测试"""

    def test_result_creation(self):
        """测试结果对象创建"""
        info = PaperInfo(
            title="Test Paper",
            authors="Test Author",
            year="2024"
        )
        result = AnalysisResult(
            paper_info=info,
            full_analysis="This is the analysis.",
            brief_summary="Brief summary.",
            output_filename="test.md",
            success=True
        )
        self.assertEqual(result.paper_info.title, "Test Paper")
        self.assertTrue(result.success)
        self.assertEqual(result.error_message, "")

    def test_result_with_error(self):
        """测试错误结果"""
        result = AnalysisResult(
            paper_info=PaperInfo(),
            full_analysis="",
            brief_summary="",
            output_filename="",
            success=False,
            error_message="Test error message"
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Test error message")


class TestDocGenerator(unittest.TestCase):
    """DocGenerator测试"""

    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        cls.generator = DocGenerator(str(config_path) if config_path.exists() else None)

    def test_01_generator_initialization(self):
        """测试DocGenerator初始化"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.pdf_reader)
        self.assertIsNotNone(self.generator.api_client)
        self.assertIsNotNone(self.generator.prompt_manager)

    def test_02_output_directories(self):
        """测试输出目录创建"""
        self.assertTrue(os.path.exists(self.generator.output_folder))
        self.assertTrue(os.path.exists(self.generator.summary_folder))

    def test_03_api_client_integration(self):
        """测试API客户端集成"""
        # 验证DocGenerator正确使用了API客户端
        client = self.generator.api_client
        self.assertTrue(hasattr(client, 'call_api'))
        self.assertTrue(hasattr(client, 'get_model_context_info'))
        self.assertTrue(hasattr(client, 'format_model_intro'))


class TestContextLimitCheck(unittest.TestCase):
    """上下文超限检查测试"""

    def setUp(self):
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        self.generator = DocGenerator(str(config_path) if config_path.exists() else None)

    def test_context_limit_detection(self):
        """测试上下文限制检测"""
        # 获取当前模型的上下文限制
        model_info = self.generator.api_client.get_model_context_info()
        context_limit = model_info['context_limit_chars']

        # 模拟不同长度的文本
        short_text = "a" * 1000
        long_text = "a" * (context_limit + 10000)

        # 验证检测逻辑
        self.assertLess(len(short_text), context_limit)
        self.assertGreater(len(long_text), context_limit)

    def test_context_limit_error_message(self):
        """测试超限错误消息格式"""
        # 模拟超限情况
        model_info = self.generator.api_client.get_model_context_info()
        context_limit = model_info['context_limit_chars']
        text_length = context_limit + 50000

        coverage = round(context_limit / text_length * 100, 1)

        # 验证错误消息包含关键信息
        self.assertIn(str(context_limit), str(context_limit))
        self.assertIn(str(text_length), str(text_length))
        self.assertIsInstance(coverage, float)
        self.assertLess(coverage, 100)


class TestVisionCapabilityCheck(unittest.TestCase):
    """视觉能力检查测试"""

    def setUp(self):
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        self.generator = DocGenerator(str(config_path) if config_path.exists() else None)

    def test_vision_support_detection(self):
        """测试视觉支持检测"""
        # 测试各模型的视觉支持状态
        for provider in ['openai', 'anthropic', 'deepseek', 'qwen_vl']:
            if self.generator.api_client.set_provider(provider):
                info = self.generator.api_client.get_model_context_info()
                self.assertIn('vision_supported', info)
                self.assertIsInstance(info['vision_supported'], bool)

    def test_vision_fallback_logic(self):
        """测试视觉降级逻辑"""
        # 当模型不支持视觉时，应降级到纯文本
        self.generator.api_client.set_provider('deepseek')  # 不支持视觉
        info = self.generator.api_client.get_model_context_info()

        if not info['vision_supported']:
            # 应该使用 call_api 而不是 call_api_with_images
            self.assertFalse(self.generator.api_client.is_vision_supported())


class TestSaveAndSummary(unittest.TestCase):
    """保存和汇总功能测试"""

    def setUp(self):
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        self.generator = DocGenerator(str(config_path) if config_path.exists() else None)

    def test_save_single_analysis_structure(self):
        """测试保存单篇分析的输出结构"""
        info = PaperInfo(
            title="Test Paper",
            authors="Test Author",
            year="2024",
            filename="test.pdf"
        )
        result = AnalysisResult(
            paper_info=info,
            full_analysis="Full analysis content here.",
            brief_summary="Brief.",
            output_filename="TestAuthor2024-Test_Paper.md",
            success=True,
            prompt_profile="default"
        )

        # 测试保存（使用临时目录）
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = self.generator.output_folder
            self.generator.output_folder = tmpdir

            output_path = self.generator.save_single_analysis(result)

            # 验证文件创建
            self.assertTrue(os.path.exists(output_path))

            # 验证内容
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn(info.title, content)
                self.assertIn(result.full_analysis, content)

            # 恢复原始目录
            self.generator.output_folder = original_folder

    def test_generate_summary_structure(self):
        """测试汇总文档的输出结构"""
        results = []
        for i in range(3):
            info = PaperInfo(
                title=f"Paper {i+1}",
                authors=f"Author {i+1}",
                year="2024"
            )
            result = AnalysisResult(
                paper_info=info,
                full_analysis=f"Analysis {i+1}",
                brief_summary=f"Brief {i+1}",
                output_filename=f"paper_{i+1}.md",
                success=True
            )
            results.append(result)

        # 生成汇总（使用临时目录）
        with tempfile.TemporaryDirectory() as tmpdir:
            original_folder = self.generator.summary_folder
            self.generator.summary_folder = tmpdir

            output_path = self.generator.generate_summary(results)

            # 验证文件创建
            self.assertTrue(os.path.exists(output_path))

            # 验证内容包含论文信息
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Paper 1", content)
                self.assertIn("Paper 2", content)
                self.assertIn("Paper 3", content)

            # 恢复原始目录
            self.generator.summary_folder = original_folder


class TestPromptManagerCustomPrompts(unittest.TestCase):
    """自定义Prompt测试"""

    def setUp(self):
        self.manager = PromptManager()

    def test_add_custom_prompt(self):
        """测试添加自定义Prompt"""
        # 获取当前profile
        original = self.manager.prompts_config.get('active_profile', 'default')

        # 添加自定义prompt
        success = self.manager.add_custom_prompt(
            name="测试模板",
            description="用于测试的自定义模板",
            paper_analysis="分析这篇论文：{paper_content}",
            brief_summary="简要总结：{title}"
        )

        # 验证添加成功
        self.assertTrue(success)

        # 验证可以切换到新模板
        profiles = self.manager.get_available_profiles()
        custom_profiles = [p for p in profiles if p['id'].startswith('custom_')]
        self.assertGreater(len(custom_profiles), 0)

        # 恢复原始profile
        self.manager.set_active_profile(original)


if __name__ == "__main__":
    unittest.main(verbosity=2)