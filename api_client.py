"""
AI文献阅读工具 - API客户端模块
支持多种大模型API配置
"""

import json
import os
import requests
from typing import Dict, List, Optional, Tuple


class APIClient:
    """统一API客户端，支持多种大模型提供商"""

    def __init__(self, config_path: str = None):
        """
        初始化API客户端

        Args:
            config_path: 配置文件路径，默认为config.json
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.providers = self.config.get('model_providers', {})
        self.active_provider = self.config.get('active_provider', 'openai')
        self.max_tokens = self.config.get('max_tokens', 4096)
        self.temperature = self.config.get('temperature', 0.7)

    def set_provider(self, provider_name: str) -> bool:
        """
        切换API提供商

        Args:
            provider_name: 提供商名称（如'openai', 'anthropic', 'deepseek'等）

        Returns:
            bool: 切换是否成功
        """
        if provider_name in self.providers:
            self.active_provider = provider_name
            return True
        return False

    def get_current_provider_info(self) -> Dict:
        """获取当前提供商信息"""
        return self.providers.get(self.active_provider, {})

    def is_vision_supported(self) -> bool:
        """检查当前模型是否支持视觉（图片理解）"""
        provider = self.providers.get(self.active_provider, {})
        return provider.get('vision', False)

    def get_model_context_info(self) -> Dict:
        """
        获取当前模型的上下文限制信息

        Returns:
            Dict: 包含模型名称、上下文限制字符数、描述
        """
        provider = self.providers.get(self.active_provider, {})
        context_limit = provider.get('context_limit_chars', 15000)
        model_name = provider.get('model', 'unknown')
        description = provider.get('description', '未知限制')
        vision = provider.get('vision', False)

        return {
            'provider_name': provider.get('name', self.active_provider),
            'model': model_name,
            'context_limit_chars': context_limit,
            'description': description,
            'active_provider': self.active_provider,
            'vision_supported': vision
        }

    def format_model_intro(self) -> str:
        """
        格式化的模型介绍字符串，用于在API调用前展示

        Returns:
            str: 包含模型信息和上下文字符限制的字符串
        """
        info = self.get_model_context_info()
        vision_str = "✓ 支持图片理解" if info['vision_supported'] else "✗ 不支持图片理解"
        return (f"当前模型: {info['provider_name']} ({info['model']})\n"
                f"上下文限制: 约 {info['context_limit_chars']:,} 字符 ({info['description']})\n"
                f"视觉能力: {vision_str}")

    def _get_api_key(self, provider_name: str) -> Optional[str]:
        """从环境变量获取API Key"""
        provider = self.providers.get(provider_name, {})
        env_var = provider.get('api_key_env', '')
        if env_var:
            return os.environ.get(env_var, '')
        return None

    def check_api_configured(self) -> Tuple[bool, str]:
        """
        检查是否有任何API已配置

        Returns:
            Tuple[bool, str]: (是否至少有一个API可用, 状态信息)
        """
        configured = []
        missing = []

        for name, provider in self.providers.items():
            env_var = provider.get('api_key_env', '')
            if env_var:
                api_key = os.environ.get(env_var, '')
                if api_key:
                    configured.append(f"{provider.get('name', name)} ({env_var})")
                else:
                    missing.append(f"{provider.get('name', name)} - 需要设置 {env_var}")
            else:
                missing.append(f"{provider.get('name', name)} - 无环境变量配置")

        if configured:
            return True, f"已配置: {', '.join(configured)}"
        else:
            missing_info = '\n  - '.join(missing) if missing else '无可用提供商'
            return False, f"没有任何API已配置！\n  请设置以下环境变量之一：\n  - {missing_info}"

    def call_api(self, prompt: str, system_prompt: str = None) -> Tuple[bool, str]:
        """
        调用当前配置的API

        Args:
            prompt: 用户输入的prompt
            system_prompt: 系统提示（可选）

        Returns:
            Tuple[bool, str]: (是否成功, 返回内容或错误信息)
        """
        provider = self.providers.get(self.active_provider, {})

        if self.active_provider == 'openai':
            return self._call_openai(prompt, system_prompt, provider)
        elif self.active_provider == 'anthropic':
            return self._call_anthropic(prompt, system_prompt, provider)
        elif self.active_provider == 'deepseek':
            return self._call_deepseek(prompt, system_prompt, provider)
        elif self.active_provider == 'zhipu':
            return self._call_zhipu(prompt, system_prompt, provider)
        elif self.active_provider == 'qwen' or self.active_provider == 'qwen_vl':
            return self._call_qwen(prompt, system_prompt, provider)
        elif self.active_provider == 'siliconflow':
            return self._call_siliconflow(prompt, system_prompt, provider)
        else:
            return False, f"不支持的提供商: {self.active_provider}"

    def is_vision_supported(self) -> bool:
        """检查当前模型是否支持视觉（图片理解）"""
        provider = self.providers.get(self.active_provider, {})
        return provider.get('vision', False)

    def get_model_context_info(self) -> Dict:
        """
        获取当前模型的上下文限制信息

        Returns:
            Dict: 包含模型名称、上下文限制字符数、描述
        """
        provider = self.providers.get(self.active_provider, {})
        context_limit = provider.get('context_limit_chars', 15000)
        model_name = provider.get('model', 'unknown')
        description = provider.get('description', '未知限制')
        vision = provider.get('vision', False)

        return {
            'provider_name': provider.get('name', self.active_provider),
            'model': model_name,
            'context_limit_chars': context_limit,
            'description': description,
            'active_provider': self.active_provider,
            'vision_supported': vision
        }

    def format_model_intro(self) -> str:
        """
        格式化的模型介绍字符串，用于在API调用前展示

        Returns:
            str: 包含模型信息和上下文字符限制的字符串
        """
        info = self.get_model_context_info()
        vision_str = "✓ 支持图片理解" if info['vision_supported'] else "✗ 不支持图片理解"
        return (f"当前模型: {info['provider_name']} ({info['model']})\n"
                f"上下文限制: 约 {info['context_limit_chars']:,} 字符 ({info['description']})\n"
                f"视觉能力: {vision_str}")

    def _call_openai(self, prompt: str, system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """调用OpenAI API"""
        api_key = self._get_api_key('openai')
        if not api_key:
            return False, "未设置OPENAI_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://api.openai.com/v1')
        model = provider.get('model', 'gpt-4o')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return True, result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_anthropic(self, prompt: str, system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """调用Anthropic Claude API"""
        api_key = self._get_api_key('anthropic')
        if not api_key:
            return False, "未设置ANTHROPIC_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://api.anthropic.com/v1')
        model = provider.get('model', 'claude-3-5-sonnet-20241022')

        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }

        messages = []
        if system_prompt:
            messages.append({'role': 'user', 'content': system_prompt + '\n\n' + prompt})
        else:
            messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/messages',
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return True, result['content'][0]['text']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_deepseek(self, prompt: str, system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """调用DeepSeek API"""
        api_key = self._get_api_key('deepseek')
        if not api_key:
            return False, "未设置DEEPSEEK_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://api.deepseek.com/v1')
        model = provider.get('model', 'deepseek-chat')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return True, result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_zhipu(self, prompt: str, system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """调用智谱GLM API"""
        api_key = self._get_api_key('zhipu')
        if not api_key:
            return False, "未设置ZHIPU_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://open.bigmodel.cn/api/paas/v4')
        model = provider.get('model', 'glm-4')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return True, result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_qwen(self, prompt: str, system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """调用阿里通义千问API"""
        api_key = self._get_api_key('qwen')
        if not api_key:
            return False, "未设置QWEN_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        model = provider.get('model', 'qwen-max')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return True, result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_siliconflow(self, prompt: str, system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """调用SiliconFlow API"""
        api_key = self._get_api_key('siliconflow')
        if not api_key:
            return False, "未设置SILICONFLOW_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://api.siliconflow.cn/v1')
        model = provider.get('model', 'deepseek-ai/DeepSeek-V3')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return True, result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_openai_vision(self, text: str, images: List[Dict],
                             system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """
        调用OpenAI GPT-4o 视觉API

        Args:
            text: 文本内容
            images: 图片信息列表，每项包含 'b64' (base64) 和 'size'
            system_prompt: 系统提示
            provider: 提供商配置

        Returns:
            Tuple[bool, str]: (是否成功, 返回内容)
        """
        api_key = self._get_api_key('openai')
        if not api_key:
            return False, "未设置OPENAI_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://api.openai.com/v1')
        model = provider.get('model', 'gpt-4o')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # 构建多模态内容
        content_parts = []
        for img in images:
            w, h = img.get('size', (0, 0))
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img['b64']}",
                    "detail": "high"
                }
            })
        content_parts.append({"type": "text", "text": text})

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': content_parts})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            return True, result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_anthropic_vision(self, text: str, images: List[Dict],
                                system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """
        调用Anthropic Claude 视觉API

        Args:
            text: 文本内容
            images: 图片信息列表，每项包含 'b64' (base64) 和 'size'
            system_prompt: 系统提示
            provider: 提供商配置

        Returns:
            Tuple[bool, str]: (是否成功, 返回内容)
        """
        api_key = self._get_api_key('anthropic')
        if not api_key:
            return False, "未设置ANTHROPIC_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://api.anthropic.com/v1')
        model = provider.get('model', 'claude-3-5-sonnet-20241022')

        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }

        # Anthropic：图片+文字在 user 消息的 content 中，system 单独传
        msg_content = []
        for img in images:
            msg_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img['b64']
                }
            })
        msg_content.append({"type": "text", "text": text})

        messages = [{'role': 'user', 'content': msg_content}]

        data = {
            'model': model,
            'messages': messages,
            'system': system_prompt if system_prompt else "",
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/messages',
                headers=headers,
                json=data,
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            return True, result['content'][0]['text']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def _call_qwen_vision(self, text: str, images: List[Dict],
                          system_prompt: str, provider: Dict) -> Tuple[bool, str]:
        """
        调用阿里通义千问VL视觉API

        Args:
            text: 文本内容
            images: 图片信息列表，每项包含 'b64' (base64) 和 'size'
            system_prompt: 系统提示
            provider: 提供商配置

        Returns:
            Tuple[bool, str]: (是否成功, 返回内容)
        """
        api_key = self._get_api_key('qwen')
        if not api_key:
            return False, "未设置QWEN_API_KEY环境变量"

        api_base = provider.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        model = provider.get('model', 'qwen-vl-plus')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # 构建多模态消息
        content_parts = []
        for img in images:
            content_parts.append({
                "image": f"data:image/png;base64,{img['b64']}"
            })
        content_parts.append({"text": text})

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': content_parts})

        data = {
            'model': model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        try:
            response = requests.post(
                f'{api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            return True, result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return False, f"API调用失败: {str(e)}"

    def call_api_with_images(self, text: str, images: List[Dict],
                              system_prompt: str = None) -> Tuple[bool, str]:
        """
        调用支持图片的API（优先使用视觉能力）

        Args:
            text: 文本内容
            images: 图片信息列表，每项包含 'b64' 和 'size'
            system_prompt: 系统提示

        Returns:
            Tuple[bool, str]: (是否成功, 返回内容或错误信息)
        """
        if not images:
            # 没有图片，直接用普通文本API
            return self.call_api(text, system_prompt)

        provider = self.providers.get(self.active_provider, {})

        if self.active_provider == 'openai':
            return self._call_openai_vision(text, images, system_prompt, provider)
        elif self.active_provider == 'anthropic':
            return self._call_anthropic_vision(text, images, system_prompt, provider)
        elif self.active_provider == 'qwen_vl':
            return self._call_qwen_vision(text, images, system_prompt, provider)
        else:
            # 模型不支持视觉，降级到纯文本
            return self.call_api(text, system_prompt)


def test_api_client():
    """测试API客户端"""
    print("=" * 60)
    print("PaperWhale - API配置测试")
    print("=" * 60)

    client = APIClient()

    # 显示当前配置
    provider_info = client.get_current_provider_info()
    print(f"\n当前提供商: {provider_info.get('name', 'Unknown')}")
    print(f"模型: {provider_info.get('model', 'Unknown')}")
    print(f"API环境变量: {provider_info.get('api_key_env', 'Unknown')}")

    # 测试API调用
    print("\n正在测试API连接...")
    success, result = client.call_api(
        prompt="请用一句话介绍自己，包括你是什么模型。",
        system_prompt="你是一个有用的AI助手。"
    )

    if success:
        print("\n[OK] API测试成功！")
        print(f"模型响应: {result[:200]}...")
    else:
        print(f"\n[FAIL] API测试失败: {result}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_api_client()