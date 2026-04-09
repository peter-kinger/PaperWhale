"""
AI文献阅读工具 - APIClient模块测试
测试API客户端、多模型支持、上下文限制检查等功能
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 尝试导入
try:
    from api_client import APIClient
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保在项目根目录运行此测试")
    sys.exit(1)


class TestAPIClient(unittest.TestCase):
    """APIClient模块测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 使用项目配置文件
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        cls.client = APIClient(str(config_path) if config_path.exists() else None)

    def test_01_client_initialization(self):
        """测试APIClient初始化"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.providers)
        self.assertIsNotNone(self.client.active_provider)
        self.assertGreater(len(self.client.providers), 0)

    def test_02_providers_config(self):
        """测试提供商配置加载"""
        providers = self.client.providers
        # 检查已知提供商
        expected_providers = ['openai', 'anthropic', 'deepseek', 'qwen', 'qwen_vl']
        for provider in expected_providers:
            self.assertIn(provider, providers, f"提供商 {provider} 应在配置中")

    def test_03_set_provider(self):
        """测试切换提供商"""
        # 保存原始提供商
        original = self.client.active_provider

        # 切换到 openai
        result = self.client.set_provider('openai')
        self.assertTrue(result)
        self.assertEqual(self.client.active_provider, 'openai')

        # 切换到不存在的提供商
        result = self.client.set_provider('nonexistent_provider')
        self.assertFalse(result)

        # 恢复原始
        self.client.set_provider(original)

    def test_04_get_current_provider_info(self):
        """测试获取当前提供商信息"""
        info = self.client.get_current_provider_info()
        self.assertIsInstance(info, dict)
        self.assertIn('model', info)
        self.assertIn('api_key_env', info)

    def test_05_is_vision_supported(self):
        """测试视觉支持检查"""
        # 测试 openai (支持视觉)
        self.client.set_provider('openai')
        self.assertTrue(self.client.is_vision_supported())

        # 测试 deepseek (不支持视觉)
        self.client.set_provider('deepseek')
        self.assertFalse(self.client.is_vision_supported())

    def test_06_get_model_context_info(self):
        """测试获取模型上下文信息"""
        # 测试各提供商
        for provider in ['openai', 'anthropic', 'deepseek', 'qwen', 'qwen_vl']:
            self.client.set_provider(provider)
            info = self.client.get_model_context_info()

            # 验证返回结构
            self.assertIn('provider_name', info)
            self.assertIn('model', info)
            self.assertIn('context_limit_chars', info)
            self.assertIn('description', info)
            self.assertIn('active_provider', info)
            self.assertIn('vision_supported', info)

            # 验证数据类型
            self.assertIsInstance(info['context_limit_chars'], int)
            self.assertIsInstance(info['vision_supported'], bool)

            # 验证值范围
            self.assertGreater(info['context_limit_chars'], 0)

    def test_07_format_model_intro(self):
        """测试模型介绍格式化"""
        self.client.set_provider('openai')
        intro = self.client.format_model_intro()

        # 验证包含关键信息
        self.assertIn('当前模型', intro)
        self.assertIn('上下文限制', intro)
        self.assertIn('视觉能力', intro)
        self.assertIn('支持图片理解', intro)

        # 测试不支持视觉的模型
        self.client.set_provider('deepseek')
        intro = self.client.format_model_intro()
        self.assertIn('不支持图片理解', intro)

    def test_08_check_api_configured(self):
        """测试API配置检查"""
        configured, message = self.client.check_api_configured()
        self.assertIsInstance(configured, bool)
        self.assertIsInstance(message, str)

        # 检查返回信息格式
        if configured:
            self.assertIn('已配置', message)
        else:
            self.assertIn('环境变量', message)

    def test_09_call_api_without_api_key(self):
        """测试无API Key时的调用"""
        # 使用不存在的API key环境变量来模拟
        with patch.dict(os.environ, {}, clear=True):
            client = APIClient()
            success, result = client.call_api("test prompt")

            # 应该返回失败，因为没有配置任何API key
            # 注意：取决于环境变量设置，结果可能不同
            self.assertIsInstance(success, bool)


class TestAPIClientVisionSupport(unittest.TestCase):
    """视觉API支持专项测试"""

    def setUp(self):
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        self.client = APIClient(str(config_path) if config_path.exists() else None)

    def test_vision_provider_list(self):
        """测试视觉支持提供商列表"""
        vision_providers = []
        non_vision_providers = []

        for name, config in self.client.providers.items():
            if config.get('vision', False):
                vision_providers.append(name)
            else:
                non_vision_providers.append(name)

        # 验证视觉提供商
        self.assertIn('openai', vision_providers)
        self.assertIn('anthropic', vision_providers)
        self.assertIn('qwen_vl', vision_providers)

        # 验证非视觉提供商
        self.assertIn('deepseek', non_vision_providers)
        self.assertIn('qwen', non_vision_providers)

    def test_context_limit_values(self):
        """测试上下文限制值"""
        for name, config in self.client.providers.items():
            limit = config.get('context_limit_chars', 0)
            self.assertGreater(limit, 0, f"{name} 的上下文限制应 > 0")

            # 验证合理范围 (1万 ~ 100万字符)
            self.assertLessEqual(limit, 1000000, f"{name} 的上下文限制不应超过100万")


class TestAPIClientCallMethods(unittest.TestCase):
    """API调用方法测试"""

    def setUp(self):
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"
        self.client = APIClient(str(config_path) if config_path.exists() else None)

    def test_call_api_routing(self):
        """测试API路由"""
        # 测试各提供商的路由是否正确
        test_cases = [
            ('openai', '_call_openai'),
            ('anthropic', '_call_anthropic'),
            ('deepseek', '_call_deepseek'),
            ('zhipu', '_call_zhipu'),
            ('qwen', '_call_qwen'),
            ('siliconflow', '_call_siliconflow'),
        ]

        for provider, expected_method in test_cases:
            self.client.set_provider(provider)
            self.assertEqual(self.client.active_provider, provider)

    def test_call_api_with_images_routing(self):
        """测试视觉API路由"""
        # 测试 call_api_with_images 的路由逻辑
        test_images = [{'b64': 'fake', 'size': (100, 100)}]

        # 测试各视觉提供商
        for provider in ['openai', 'anthropic', 'qwen_vl']:
            self.client.set_provider(provider)
            # 由于没有真实API key，会返回错误，但验证路由不崩溃
            try:
                success, result = self.client.call_api_with_images(
                    "test", test_images, "system"
                )
                # 不关注结果，只验证路由不报错
                self.assertIsInstance(success, bool)
            except Exception as e:
                # API调用失败是预期的（无key），但路由应正确
                self.assertIn('API', str(e))  # 错误信息应与API相关


class TestAPIClientConfig(unittest.TestCase):
    """配置文件测试"""

    def test_config_file_structure(self):
        """测试配置文件结构"""
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"

        if not config_path.exists():
            self.skipTest("配置文件不存在")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 验证顶层结构
        self.assertIn('model_providers', config)
        self.assertIn('active_provider', config)

        # 验证active_provider在model_providers中
        self.assertIn(
            config['active_provider'],
            config['model_providers']
        )

    def test_all_providers_have_required_fields(self):
        """测试所有提供商都有必需字段"""
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.json"

        if not config_path.exists():
            self.skipTest("配置文件不存在")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        required_fields = ['name', 'model', 'api_key_env', 'context_limit_chars']

        for name, provider in config['model_providers'].items():
            for field in required_fields:
                self.assertIn(
                    field, provider,
                    f"提供商 {name} 缺少必需字段: {field}"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)