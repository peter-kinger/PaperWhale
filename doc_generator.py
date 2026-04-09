"""
AI文献阅读工具 - 文档生成模块
生成单篇分析文档和汇总文档
支持自定义Prompt配置
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from pdf_reader import PDFReader, PaperInfo, generate_paper_filename
from api_client import APIClient


@dataclass
class AnalysisResult:
    """单篇论文分析结果"""
    paper_info: PaperInfo
    full_analysis: str
    brief_summary: str
    output_filename: str
    prompt_profile: str = "default"
    success: bool = True
    error_message: str = ""


class PromptManager:
    """Prompt管理器 - 支持自定义Prompt配置"""

    def __init__(self, prompts_file: str = None):
        """
        初始化Prompt管理器

        Args:
            prompts_file: Prompt配置文件路径
        """
        if prompts_file is None:
            prompts_file = os.path.join(os.path.dirname(__file__), "custom_prompts.py")

        self.prompts_file = prompts_file
        self.prompts_config = self._load_prompts()

    def _load_prompts(self) -> Dict:
        """加载Prompt配置"""
        # 从custom_prompts.py读取配置
        prompts_path = os.path.join(os.path.dirname(__file__), "custom_prompts.py")
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取JSON部分（去掉Python字典声明和注释）
                json_str = content.strip()
                if json_str.startswith('{'):
                    return json.loads(json_str)
                # 如果有Python dict格式的内容，手动处理
                return self._parse_python_dict(content)
        except Exception as e:
            print(f"加载Prompt配置失败: {e}")
            return self._get_default_config()

    def _parse_python_dict(self, content: str) -> Dict:
        """解析Python字典格式的配置"""
        # 简化处理：直接返回默认配置
        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "prompt_profiles": {
                "default": {
                    "name": "默认-深度分析",
                    "description": "完整的学术论文分析",
                    "type": "full_analysis",
                    "prompts": {
                        "paper_analysis": "分析这篇论文：{paper_content}",
                        "brief_summary": "简要总结：{title}"
                    }
                }
            },
            "active_profile": "default",
            "custom_prompts_storage": []
        }

    def get_available_profiles(self) -> List[Dict]:
        """获取所有可用的Prompt模板"""
        profiles = []
        for key, profile in self.prompts_config.get("prompt_profiles", {}).items():
            profiles.append({
                "id": key,
                "name": profile.get("name", key),
                "description": profile.get("description", ""),
                "type": profile.get("type", "")
            })
        return profiles

    def get_active_profile(self) -> Dict:
        """获取当前激活的Prompt模板"""
        active = self.prompts_config.get("active_profile", "default")
        profiles = self.prompts_config.get("prompt_profiles", {})
        return profiles.get(active, profiles.get("default", {}))

    def set_active_profile(self, profile_id: str) -> bool:
        """设置当前激活的Prompt模板"""
        if profile_id in self.prompts_config.get("prompt_profiles", {}):
            self.prompts_config["active_profile"] = profile_id
            self._save_prompts()
            return True
        return False

    def get_prompts(self, profile_id: str = None) -> Dict:
        """获取指定Profile的Prompts"""
        if profile_id is None:
            profile_id = self.prompts_config.get("active_profile", "default")

        profile = self.prompts_config.get("prompt_profiles", {}).get(profile_id, {})
        return profile.get("prompts", {})

    def add_custom_prompt(self, name: str, description: str, paper_analysis: str,
                          brief_summary: str = "") -> bool:
        """
        添加新的自定义Prompt模板

        Args:
            name: 模板名称
            description: 模板描述
            paper_analysis: 论文分析Prompt
            brief_summary: 简短摘要Prompt

        Returns:
            bool: 是否成功
        """
        custom_id = f"custom_{len(self.prompts_config.get('custom_prompts_storage', [])) + 1}"

        new_profile = {
            "name": name,
            "description": description,
            "type": "custom",
            "prompts": {
                "paper_analysis": paper_analysis,
                "brief_summary": brief_summary or f"简要总结：{name}"
            }
        }

        self.prompts_config["prompt_profiles"][custom_id] = new_profile
        self.prompts_config.setdefault("custom_prompts_storage", []).append({
            "id": custom_id,
            "name": name,
            "description": description
        })

        self._save_prompts()
        return True

    def update_prompt_text(self, profile_id: str, prompt_type: str, new_text: str) -> bool:
        """
        更新指定Profile的Prompt内容

        Args:
            profile_id: Profile ID
            prompt_type: prompt类型（paper_analysis/brief_summary）
            new_text: 新的Prompt文本

        Returns:
            bool: 是否成功
        """
        if profile_id not in self.prompts_config.get("prompt_profiles", {}):
            return False

        prompts = self.prompts_config["prompt_profiles"][profile_id].get("prompts", {})
        prompts[prompt_type] = new_text

        self._save_prompts()
        return True

    def _save_prompts(self):
        """保存Prompt配置到文件"""
        try:
            prompts_path = os.path.join(os.path.dirname(__file__), "custom_prompts.py")
            with open(prompts_path, 'w', encoding='utf-8') as f:
                json.dump(self.prompts_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存Prompt配置失败: {e}")


class DocGenerator:
    """文档生成器"""

    def __init__(self, config_path: str = None):
        """
        初始化文档生成器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.api_client = APIClient(config_path)
        self.pdf_reader = PDFReader()
        self.prompt_manager = PromptManager()

        # 加载配置
        if config_path:
            config_full_path = config_path
        else:
            config_full_path = os.path.join(os.path.dirname(__file__), "config.json")

        with open(config_full_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.output_folder = self.config.get('output_folder', './output_docs')
        self.summary_folder = self.config.get('summary_folder', './summary_docs')

        # 创建输出目录
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.summary_folder, exist_ok=True)

        # 从配置文件加载汇总Prompt
        self.summary_prompt = self._load_summary_prompt()

    def _load_summary_prompt(self) -> str:
        """加载汇总文档的Prompt"""
        prompts_path = os.path.join(os.path.dirname(__file__), "prompts.py")
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取SUMMARY_PROMPT
                import re
                match = re.search(r'SUMMARY_PROMPT\s*=\s*"""(.*?)"""', content, re.DOTALL)
                if match:
                    return match.group(1)
        except Exception:
            pass

        # 默认汇总Prompt
        return """你是一位学术研究助手，请对以下多篇论文进行综合分析，生成一份结构化的总结报告。

论文列表：
{paper_list}

各论文内容摘要：
---
{paper_summaries}
---

请生成一份综合总结文档，包含表格总结和文字总结两部分。"""

    def analyze_single_paper(self, pdf_path: str, max_content_length: int = 15000,
                            custom_prompt: str = None) -> AnalysisResult:
        """
        分析单篇论文

        Args:
            pdf_path: PDF文件路径
            max_content_length: 最大内容长度（仅作为兜底，已废弃，请参考模型实际上下文限制）
            custom_prompt: 自定义Prompt（如果提供，将覆盖配置）

        Returns:
            AnalysisResult: 分析结果
        """
        result = AnalysisResult(
            paper_info=PaperInfo(),
            full_analysis="",
            brief_summary="",
            output_filename=""
        )

        try:
            # 读取PDF（含图片提取）
            print(f"  正在读取PDF（文本+图片）...")
            text, paper_info, images = self.pdf_reader.read_pdf_with_images(pdf_path)
            original_length = len(text)

            # 获取当前模型上下文限制和视觉支持
            model_info = self.api_client.get_model_context_info()
            context_limit = model_info['context_limit_chars']
            vision_supported = model_info['vision_supported']

            # 调用API前，先展示模型信息
            print(f"\n  {'='*50}")
            print(f"  模型信息:")
            print(f"  {self.api_client.format_model_intro()}")
            print(f"  {'='*50}")
            print(f"  论文文本长度: {original_length:,} 字符")
            print(f"  检测到图片数量: {len(images)} 张")
            if images:
                print(f"  图片列表:")
                for i, img in enumerate(images[:5], 1):
                    w, h = img['size']
                    print(f"    {i}. 第{img['page']}页 - {w}x{h}px")
                if len(images) > 5:
                    print(f"    ... 还有 {len(images)-5} 张")
            if images and not vision_supported:
                print(f"\n  [注意] 检测到 {len(images)} 张图片，但当前模型不支持图片理解！")
                print(f"         图片将不会被分析。")
                print(f"         如需分析图片，请切换到支持视觉的模型:")
                print(f"           - OpenAI GPT-4o (vision)")
                print(f"           - Anthropic Claude (vision)")
                print(f"           - 通义千问VL (vision)")

            # 检查内容是否超出模型上下文限制
            if original_length > context_limit:
                coverage = round(context_limit / original_length * 100, 1)
                error_msg = (
                    f"\n"
                    f"  {'='*50}\n"
                    f"  [错误] 论文文本过长，超出当前模型上下文限制！\n"
                    f"  {'='*50}\n"
                    f"  论文文本长度:   {original_length:,} 字符\n"
                    f"  模型上下文限制: {context_limit:,} 字符\n"
                    f"  覆盖率:         仅 {coverage}%\n"
                    f"\n"
                    f"  【解决方案】请选择以下方式之一:\n"
                    f"  1. [切换模型] 使用支持更大上下文的模型:\n"
                    f"     - OpenAI GPT-4o (约10万字符)\n"
                    f"     - Anthropic Claude (约10万字符)\n"
                    f"     - SiliconFlow DeepSeek-V3 (约3万字符)\n"
                    f"\n"
                    f"  2. [拆分PDF] 将论文拆分为多个小文件后分别处理\n"
                    f"     - 建议每份控制在 {context_limit * 8 // 10:,} 字符以内\n"
                    f"     - 或按章节/页数拆分\n"
                    f"\n"
                    f"  3. [手动压缩] 使用外部工具提取关键章节后处理\n"
                    f"     - 建议保留摘要、引言、方法、结论部分\n"
                    f"  {'='*50}\n"
                )
                print(error_msg)
                result.success = False
                result.error_message = (
                    f"文本长度{original_length:,}字符超出模型上下文限制{context_limit:,}字符。"
                    f"请切换至更大上下文的模型（GPT-4o/Claude约10万字符），"
                    f"或拆分PDF后重试。"
                )
                result.full_analysis = f"处理失败: {result.error_message}"
                return result

            result.paper_info = paper_info

            # 生成文件名
            output_filename = generate_paper_filename(paper_info)
            result.output_filename = output_filename

            # 获取当前使用的Prompt
            active_profile = self.prompt_manager.get_active_profile()
            prompts = active_profile.get("prompts", {})

            # 确定要使用的paper_analysis prompt
            if custom_prompt:
                paper_analysis_prompt = custom_prompt
            else:
                # 如果有图片且模型支持视觉，优先使用视觉专用prompt
                if images and vision_supported:
                    from prompts import PAPER_ANALYSIS_VISION_PROMPT
                    paper_analysis_prompt = PAPER_ANALYSIS_VISION_PROMPT
                else:
                    paper_analysis_prompt = prompts.get("paper_analysis", "")

            # 构建Prompt
            # 替换占位符（文本部分）
            prompt = paper_analysis_prompt.format(
                filename=paper_info.filename,
                title=paper_info.title,
                authors=paper_info.authors,
                year=paper_info.year or "未知",
                paper_content=text
            )

            # 构建系统提示
            system_prompt = "你是一位专业的学术论文审稿人，请仔细阅读以下论文内容和图片，进行全面深入的分析。"

            # 根据是否支持视觉选择调用方式
            if images and vision_supported:
                print(f"\n  正在调用AI分析（含{len(images)}张图片）...")
                success, analysis = self.api_client.call_api_with_images(
                    text=prompt,
                    images=images,
                    system_prompt=system_prompt
                )
            else:
                print(f"\n  正在调用AI分析...")
                success, analysis = self.api_client.call_api(prompt)

            if success:
                result.full_analysis = analysis
                result.success = True
                result.prompt_profile = self.prompt_manager.prompts_config.get("active_profile", "default")

                # 生成简短摘要
                brief_prompt_template = prompts.get("brief_summary", "")
                if brief_prompt_template:
                    brief_prompt = brief_prompt_template.format(
                        title=paper_info.title,
                        content=text[:5000]
                    )
                    _, brief = self.api_client.call_api(brief_prompt)
                    result.brief_summary = brief if brief else ""
            else:
                result.success = False
                result.error_message = analysis
                result.full_analysis = f"分析失败: {analysis}"

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.full_analysis = f"处理出错: {str(e)}"

        return result

    def analyze_single_paper_with_prompt_profile(self, pdf_path: str,
                                                profile_id: str,
                                                max_content_length: int = 15000) -> AnalysisResult:
        """
        使用指定Prompt Profile分析单篇论文

        Args:
            pdf_path: PDF文件路径
            profile_id: Prompt Profile ID
            max_content_length: 已废弃参数，请使用模型的上下文限制

        Returns:
            AnalysisResult: 分析结果
        """
        # 临时切换到指定Profile
        original_profile = self.prompt_manager.prompts_config.get("active_profile", "default")
        self.prompt_manager.set_active_profile(profile_id)

        result = self.analyze_single_paper(pdf_path, max_content_length=max_content_length)

        # 恢复原Profile
        self.prompt_manager.set_active_profile(original_profile)

        return result

    def save_single_analysis(self, result: AnalysisResult) -> str:
        """
        保存单篇分析文档

        Args:
            result: 分析结果

        Returns:
            str: 保存的文件路径
        """
        output_path = os.path.join(self.output_folder, result.output_filename)

        # 添加文件头信息
        content = f"---\n"
        content += f"title: {result.paper_info.title}\n"
        content += f"authors: {result.paper_info.authors}\n"
        content += f"year: {result.paper_info.year}\n"
        content += f"source: {result.paper_info.filename}\n"
        content += f"prompt_profile: {result.prompt_profile}\n"
        content += f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"model: {self.api_client.get_current_provider_info().get('name', 'Unknown')}\n"
        content += f"---\n\n"
        content += result.full_analysis

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def generate_summary(self, results: List[AnalysisResult], output_name: str = None) -> str:
        """
        生成汇总文档

        Args:
            results: 所有论文的分析结果列表
            output_name: 输出文件名（不含路径）

        Returns:
            str: 保存的文件路径
        """
        if not output_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_name = f"文献综述汇总_{timestamp}.md"

        output_path = os.path.join(self.summary_folder, output_name)

        # 构建论文列表
        paper_list = []
        paper_summaries = []

        for i, result in enumerate(results):
            paper_list.append(f"{i+1}. {result.paper_info.title} ({result.paper_info.authors}, {result.paper_info.year})")
            paper_summaries.append(
                f"=== 论文{i+1}: {result.paper_info.title} ===\n"
                f"作者: {result.paper_info.authors}\n"
                f"年份: {result.paper_info.year}\n"
                f"Prompt模板: {result.prompt_profile}\n"
                f"简短摘要: {result.brief_summary}\n\n"
                f"详细分析:\n{result.full_analysis[:3000]}"
            )

        # 构建Prompt
        prompt = self.summary_prompt.format(
            paper_list="\n".join(paper_list),
            paper_summaries="\n\n".join(paper_summaries)
        )

        # 调用API生成汇总
        print("  正在生成汇总文档...")
        success, summary = self.api_client.call_api(prompt)

        if not success:
            summary = f"汇总生成失败: {summary}"

        # 添加文件头
        content = f"---\n"
        content += f"title: 文献综述汇总\n"
        content += f"papers_count: {len(results)}\n"
        content += f"papers:\n"
        for result in results:
            content += f"  - {result.paper_info.title}\n"
        content += f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"model: {self.api_client.get_current_provider_info().get('name', 'Unknown')}\n"
        content += f"---\n\n"
        content += summary

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def process_folder(self, folder_path: str = None, generate_summary: bool = True,
                      prompt_profile: str = None, custom_prompt: str = None) -> Dict:
        """
        处理整个文件夹的PDF文件

        Args:
            folder_path: PDF文件夹路径
            generate_summary: 是否生成汇总文档
            prompt_profile: 使用的Prompt模板ID
            custom_prompt: 自定义Prompt（临时覆盖）

        Returns:
            Dict: 处理结果统计
        """
        if folder_path is None:
            folder_path = self.config.get('pdf_input_folder', './input_pdfs')

        # 切换Prompt Profile
        if prompt_profile:
            self.prompt_manager.set_active_profile(prompt_profile)

        active_profile = self.prompt_manager.get_active_profile()

        print("=" * 60)
        print("AI文献阅读工具 - 开始处理")
        print("=" * 60)
        print(f"输入文件夹: {folder_path}")
        print(f"输出文件夹: {self.output_folder}")
        print(f"汇总文件夹: {self.summary_folder}")
        print(f"当前模型: {self.api_client.get_current_provider_info().get('name', 'Unknown')}")
        print(f"当前Prompt: {active_profile.get('name', 'default')}")
        if custom_prompt:
            print(f"自定义Prompt: 已启用")
        print("=" * 60)

        # 读取所有PDF
        print("\n[1/3] 读取PDF文件...")
        papers = self.pdf_reader.read_folder(folder_path)
        print(f"共找到 {len(papers)} 个PDF文件")

        if not papers:
            print("未找到PDF文件！")
            return {'success': 0, 'failed': 0, 'results': []}

        # 分析每篇论文
        print("\n[2/3] 分析论文内容...")
        results = []
        for i, (text, paper_info) in enumerate(papers):
            print(f"\n处理 [{i+1}/{len(papers)}]: {paper_info.title[:50]}...")
            result = self.analyze_single_paper(paper_info.filepath, custom_prompt=custom_prompt)

            if result.success:
                output_path = self.save_single_analysis(result)
                print(f"  [OK] 已保存: {result.output_filename}")
            else:
                print(f"  [FAIL] 失败: {result.error_message}")

            results.append(result)

        # 生成汇总
        if generate_summary and results:
            print("\n[3/3] 生成汇总文档...")
            summary_path = self.generate_summary(results)
            print(f"  [OK] 汇总文档已保存: {os.path.basename(summary_path)}")

        # 统计结果
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count

        print("\n" + "=" * 60)
        print("处理完成!")
        print(f"成功: {success_count} 篇")
        print(f"失败: {failed_count} 篇")
        print(f"输出文件夹: {self.output_folder}")
        print(f"汇总文件夹: {self.summary_folder}")
        print("=" * 60)

        return {
            'success': success_count,
            'failed': failed_count,
            'results': results
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='AI文献阅读工具')
    parser.add_argument('--input', '-i', type=str, help='输入PDF文件夹路径')
    parser.add_argument('--output', '-o', type=str, help='输出文档文件夹路径')
    parser.add_argument('--summary', '-s', type=str, help='汇总文档文件夹路径')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--provider', '-p', type=str, help='指定API提供商')
    parser.add_argument('--prompt', '-pm', type=str, help='指定Prompt模板 (default/quick_scan/methodology/critical_review)')
    parser.add_argument('--custom-prompt', '-cp', type=str, help='自定义Prompt内容（会覆盖模板）')
    parser.add_argument('--no-summary', action='store_true', help='不生成汇总文档')
    parser.add_argument('--list-prompts', action='store_true', help='列出所有可用的Prompt模板')

    args = parser.parse_args()

    # 创建生成器
    generator = DocGenerator(args.config)

    # 列出Prompt模板
    if args.list_prompts:
        print("\n可用的Prompt模板:")
        for profile in generator.prompt_manager.get_available_profiles():
            print(f"  {profile['id']}: {profile['name']} - {profile['description']}")
        return

    # 切换API提供商
    if args.provider:
        if generator.api_client.set_provider(args.provider):
            print(f"已切换到: {args.provider}")
        else:
            print(f"未知的提供商: {args.provider}")
            return

    # 覆盖配置路径
    if args.output:
        generator.output_folder = args.output
        os.makedirs(generator.output_folder, exist_ok=True)
    if args.summary:
        generator.summary_folder = args.summary
        os.makedirs(generator.summary_folder, exist_ok=True)

    # 处理文件夹
    generator.process_folder(
        args.input,
        not args.no_summary,
        prompt_profile=args.prompt,
        custom_prompt=args.custom_prompt
    )


if __name__ == "__main__":
    main()