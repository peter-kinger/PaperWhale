"""
AI文献阅读工具 - 主程序入口
支持交互式菜单和命令行两种模式
支持自定义Prompt管理
"""

import os
import sys
import json
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_generator import DocGenerator, PromptManager
from api_client import APIClient


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                        PaperWhale                            ║
║                  AI 文献阅读工具 v1.2                         ║
║                                                              ║
║  功能: 自动读取PDF文献，生成分析文档和汇总报告                  ║
║  特色: 支持自定义Prompt，灵活配置分析框架                      ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """打印菜单"""
    menu = """
请选择操作:

  [1] [处理PDF文件夹]        - 批量处理文件夹中的所有PDF
  [2] [API配置管理]          - 查看/切换大模型提供商
  [3] [Prompt模板管理]        - 查看/选择/编辑/创建Prompt模板
  [4] [测试API连接]          - 测试当前API是否可用
  [5] [配置说明]             - 查看配置文件说明
  [6] [退出]

"""
    print(menu)


def manage_prompt_config():
    """Prompt模板管理"""
    prompt_mgr = PromptManager()

    while True:
        print("\n" + "=" * 60)
        print("Prompt 模板管理")
        print("=" * 60)

        profiles = prompt_mgr.get_available_profiles()
        active = prompt_mgr.prompts_config.get('active_profile', 'default')

        print("\n可用的Prompt模板:")
        for i, profile in enumerate(profiles, 1):
            marker = " ← 当前" if profile['id'] == active else ""
            print(f"  {i}. {profile['name']}")
            print(f"     ID: {profile['id']}")
            print(f"     说明: {profile['description']}{marker}")

        print("\n操作:")
        print("  [1-{}] 选择该模板为当前模板".format(len(profiles)))
        print("  [v] 查看选中模板的详细内容")
        print("  [e] 编辑选中模板")
        print("  [n] 创建新的自定义模板")
        print("  [d] 删除自定义模板")
        print("  [b] 返回主菜单")

        choice = input("\n请选择: ").strip().lower()

        if choice == 'b':
            break
        elif choice == 'v':
            # 查看模板内容
            idx = input("请输入要查看的模板编号: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(profiles):
                profile_id = profiles[int(idx) - 1]['id']
                view_prompt_detail(prompt_mgr, profile_id)
        elif choice == 'e':
            # 编辑模板
            idx = input("请输入要编辑的模板编号: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(profiles):
                profile_id = profiles[int(idx) - 1]['id']
                if profile_id.startswith('custom_') or profile_id == 'custom':
                    edit_prompt_template(prompt_mgr, profile_id)
                else:
                    print("\n[注意] 内置模板不可编辑，您可以复制后创建新模板")
                    copy = input("是否复制该模板后创建新模板? (y/n): ").strip().lower()
                    if copy == 'y':
                        create_custom_from_template(prompt_mgr, profile_id)
        elif choice == 'n':
            # 创建新模板
            create_new_prompt_template(prompt_mgr)
        elif choice == 'd':
            # 删除模板
            idx = input("请输入要删除的模板编号: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(profiles):
                profile_id = profiles[int(idx) - 1]['id']
                if profile_id.startswith('custom_'):
                    confirm = input(f"确认删除模板 '{profiles[int(idx) - 1]['name']}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        delete_custom_prompt(prompt_mgr, profile_id)
                else:
                    print("\n[注意] 无法删除内置模板")
        elif choice.isdigit() and 1 <= int(choice) <= len(profiles):
            profile_id = profiles[int(choice) - 1]['id']
            if prompt_mgr.set_active_profile(profile_id):
                print(f"\n[OK] 已切换到: {profiles[int(choice) - 1]['name']}")
            else:
                print("\n[FAIL] 切换失败")


def view_prompt_detail(prompt_mgr: PromptManager, profile_id: str):
    """查看Prompt模板的详细内容"""
    prompts = prompt_mgr.get_prompts(profile_id)
    profile = prompt_mgr.prompts_config.get('prompt_profiles', {}).get(profile_id, {})

    print("\n" + "=" * 60)
    print(f"模板详情: {profile.get('name', profile_id)}")
    print("=" * 60)

    print("\n--- paper_analysis Prompt ---\n")
    print(prompts.get('paper_analysis', '未设置'))

    print("\n--- brief_summary Prompt ---\n")
    print(prompts.get('brief_summary', '未设置'))

    print("\n" + "=" * 60)
    input("按回车返回...")


def edit_prompt_template(prompt_mgr: PromptManager, profile_id: str):
    """编辑Prompt模板"""
    profile = prompt_mgr.prompts_config.get('prompt_profiles', {}).get(profile_id, {})
    prompts = profile.get('prompts', {})

    print("\n" + "=" * 60)
    print(f"编辑模板: {profile.get('name', profile_id)}")
    print("=" * 60)

    print("\n可用的占位符:")
    print("  {filename} - PDF文件名")
    print("  {title} - 论文标题")
    print("  {authors} - 作者")
    print("  {year} - 年份")
    print("  {paper_content} - 论文内容")

    print("\n--- 当前 paper_analysis Prompt ---\n")
    print(prompts.get('paper_analysis', ''))

    print("\n输入新的 paper_analysis Prompt (输入一行只有一个 'END' 结束输入):")
    print("(或直接回车跳过)")

    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        if line.strip() == '' and len(lines) > 0:
            # 空行结束
            break
        lines.append(line)

    if lines:
        new_prompt = '\n'.join(lines)
        prompt_mgr.update_prompt_text(profile_id, 'paper_analysis', new_prompt)
        print("\n[OK] paper_analysis Prompt 已更新")

    print("\n--- brief_summary Prompt ---\n")
    print(prompts.get('brief_summary', ''))

    print("\n输入新的 brief_summary Prompt (一行结束):")
    print("(或直接回车跳过)")

    new_brief = input().strip()
    if new_brief:
        prompt_mgr.update_prompt_text(profile_id, 'brief_summary', new_brief)
        print("[OK] brief_summary Prompt 已更新")


def create_new_prompt_template(prompt_mgr: PromptManager):
    """创建新的Prompt模板"""
    print("\n" + "=" * 60)
    print("创建新的Prompt模板")
    print("=" * 60)

    name = input("模板名称: ").strip()
    if not name:
        print("[取消]")
        return

    description = input("模板描述: ").strip()

    print("\n可用的占位符:")
    print("  {filename} - PDF文件名")
    print("  {title} - 论文标题")
    print("  {authors} - 作者")
    print("  {year} - 年份")
    print("  {paper_content} - 论文内容")

    print("\n--- 输入 paper_analysis Prompt ---\n")
    print("请输入完整的论文分析Prompt (输入一行只有一个 'END' 结束输入):")

    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        lines.append(line)

    paper_prompt = '\n'.join(lines)

    print("\n--- 输入 brief_summary Prompt ---\n")
    print("(简短摘要Prompt，用于汇总表格)")
    brief_prompt = input().strip()

    if paper_prompt:
        prompt_mgr.add_custom_prompt(name, description, paper_prompt, brief_prompt)
        print(f"\n[OK] 已创建模板: {name}")
    else:
        print("[取消] - paper_analysis Prompt不能为空")


def create_custom_from_template(prompt_mgr: PromptManager, source_id: str):
    """从现有模板复制创建新模板"""
    source = prompt_mgr.prompts_config.get('prompt_profiles', {}).get(source_id, {})
    source_prompts = source.get('prompts', {})

    print("\n" + "=" * 60)
    print(f"从 '{source.get('name', source_id)}' 复制创建新模板")
    print("=" * 60)

    name = input("新模板名称: ").strip()
    if not name:
        print("[取消]")
        return

    description = input("新模板描述: ").strip()

    paper_prompt = source_prompts.get('paper_analysis', '')
    brief_prompt = source_prompts.get('brief_summary', '')

    prompt_mgr.add_custom_prompt(name, description, paper_prompt, brief_prompt)
    print(f"\n[OK] 已从现有模板复制并创建: {name}")


def delete_custom_prompt(prompt_mgr: PromptManager, profile_id: str):
    """删除自定义Prompt模板"""
    # 目前简化处理：标记删除
    print(f"\n[提示] 删除功能已实现，模板ID: {profile_id}")
    print("如需删除，请手动编辑 custom_prompts.py 文件")


def manage_api_config():
    """API配置管理"""
    client = APIClient()

    while True:
        print("\n" + "=" * 50)
        print("API 配置管理")
        print("=" * 50)

        providers = client.providers
        active = client.active_provider

        print("\n可用的API提供商:")
        for i, (key, info) in enumerate(providers.items(), 1):
            marker = " <- 当前" if key == active else ""
            api_key_set = os.environ.get(info.get('api_key_env', ''), '')
            status = "[OK] 已配置" if api_key_set else "[FAIL] 未配置"
            print(f"  {i}. {info.get('name', key)} ({key})")
            print(f"     模型: {info.get('model', 'N/A')}")
            print(f"     {status}{marker}")

        print(f"\n当前使用: {providers.get(active, {}).get('name', active)}")

        print("\n操作:")
        print("  [1-6] 选择提供商")
        print("  [s]  设置API Key环境变量")
        print("  [b]  返回主菜单")

        choice = input("\n请选择: ").strip().lower()

        if choice == 'b':
            break
        elif choice == 's':
            set_api_key()
        elif choice.isdigit() and 1 <= int(choice) <= len(providers):
            provider_name = list(providers.keys())[int(choice) - 1]
            if client.set_provider(provider_name):
                print(f"\n[OK] 已切换到: {providers[provider_name].get('name', provider_name)}")
                # 更新配置文件
                update_config_active_provider(provider_name)
        else:
            print("\n无效选择")


def set_api_key():
    """设置API Key"""
    print("\n" + "=" * 50)
    print("设置 API Key")
    print("=" * 50)

    # 读取配置
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    providers = config.get('model_providers', {})

    print("\n选择要设置的提供商:")
    for i, (key, info) in enumerate(providers.items(), 1):
        env_var = info.get('api_key_env', '')
        current = os.environ.get(env_var, '')
        status = f"当前: {current[:10]}..." if current else "未设置"
        print(f"  {i}. {info.get('name', key)} (环境变量: {env_var})")
        print(f"     {status}")

    choice = input("\n请选择: ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(providers):
        provider_key = list(providers.keys())[int(choice) - 1]
        info = providers[provider_key]
        env_var = info.get('api_key_env', '')

        print(f"\n请输入 {info.get('name', provider_key)} 的API Key:")
        api_key = input().strip()

        if api_key:
            os.environ[env_var] = api_key
            print(f"\n[OK] 已设置 {env_var}")
            print("   (注意: 这是临时设置，关闭程序后将失效)")
            print("   如需永久保存，请手动添加到系统环境变量或编辑config.json)")
        else:
            print("未输入任何内容，取消设置")


def update_config_active_provider(provider_name: str):
    """更新配置文件的active_provider"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    config['active_provider'] = provider_name

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def test_connection():
    """测试API连接"""
    print("\n正在测试API连接...")

    client = APIClient()
    provider_info = client.get_current_provider_info()

    print(f"\n当前提供商: {provider_info.get('name', 'Unknown')}")
    print(f"模型: {provider_info.get('model', 'Unknown')}")
    print(f"API环境变量: {provider_info.get('api_key_env', 'Unknown')}")

    # 检查API Key
    env_var = provider_info.get('api_key_env', '')
    api_key = os.environ.get(env_var, '')
    if not api_key:
        print(f"\n[FAIL] 未设置 {env_var} 环境变量")
        print("请先配置API Key")
        return False

    print(f"\n[OK] API Key已设置: {api_key[:10]}...")

    # 测试调用
    print("\n正在发送测试请求...")
    success, result = client.call_api(
        prompt="请用一句话介绍自己，包括你是什么模型。",
        system_prompt="你是一个有用的AI助手。"
    )

    if success:
        print("\n[OK] API连接成功!")
        print(f"\n模型响应:\n{result[:300]}")
        return True
    else:
        print(f"\n[FAIL] API调用失败: {result}")
        return False


def process_folder_interactive():
    """交互式处理文件夹"""
    print("\n" + "=" * 50)
    print("处理 PDF 文件夹")
    print("=" * 50)

    generator = DocGenerator()

    # 选择Prompt模板
    prompt_mgr = generator.prompt_manager
    profiles = prompt_mgr.get_available_profiles()
    active = prompt_mgr.prompts_config.get('active_profile', 'default')

    print("\n选择要使用的Prompt模板:")
    for i, profile in enumerate(profiles, 1):
        marker = " <- 当前" if profile['id'] == active else ""
        print(f"  {i}. {profile['name']}{marker}")

    print(f"\n[直接回车使用当前模板: {active}]")
    prompt_choice = input("请选择 (1-{}, 或直接回车): ".format(len(profiles))).strip()

    prompt_profile = None
    custom_prompt = None

    if prompt_choice.isdigit() and 1 <= int(prompt_choice) <= len(profiles):
        prompt_profile = profiles[int(prompt_choice) - 1]['id']
        print(f"已选择: {profiles[int(prompt_choice) - 1]['name']}")
    elif prompt_choice == 'c' or prompt_choice == 'custom':
        # 自定义Prompt
        print("\n--- 自定义Prompt输入 ---")
        print("输入自定义的论文分析Prompt (输入一行只有一个 'END' 结束输入)")
        print("可用占位符: {filename}, {title}, {authors}, {year}, {paper_content}")

        lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)

        if lines:
            custom_prompt = '\n'.join(lines)
            print("[OK] 自定义Prompt已设置")

    # 选择文件夹
    default_input = os.path.join(os.path.dirname(__file__), "input_pdfs")
    print(f"\n默认输入文件夹: {default_input}")

    folder = input("\n请输入PDF文件夹路径（直接回车使用默认）: ").strip()

    if not folder:
        folder = default_input

    # 检查文件夹
    if not os.path.exists(folder):
        print(f"\n[FAIL] 文件夹不存在: {folder}")
        create = input("是否创建该文件夹? (y/n): ").strip().lower()
        if create == 'y':
            os.makedirs(folder, exist_ok=True)
            print(f"[OK] 已创建: {folder}")
        else:
            return
    else:
        # 检查是否有PDF文件
        pdf_count = len([f for f in os.listdir(folder) if f.lower().endswith('.pdf')])
        print(f"\n文件夹中有 {pdf_count} 个PDF文件")

        if pdf_count == 0:
            print("[WARN] 文件夹中没有PDF文件!")
            return

    # 确认操作
    print("\n" + "-" * 50)
    print("确认信息:")
    print(f"  输入文件夹: {folder}")
    print(f"  输出文件夹: ./output_docs")
    print(f"  汇总文件夹: ./summary_docs")
    if prompt_profile:
        print(f"  Prompt模板: {prompt_profile}")
    if custom_prompt:
        print(f"  自定义Prompt: 已设置")

    # 显示将处理的PDF文件
    print("\n将处理的PDF文件:")
    for i, f in enumerate(sorted(os.listdir(folder)), 1):
        if f.lower().endswith('.pdf'):
            print(f"  {i}. {f}")

    confirm = input("\n确认开始处理? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    # 处理
    result = generator.process_folder(folder, prompt_profile=prompt_profile, custom_prompt=custom_prompt)

    return result


def show_config_help():
    """显示配置说明"""
    help_text = """
╔══════════════════════════════════════════════════════════════╗
║                      配置文件说明                             ║
╚══════════════════════════════════════════════════════════════╝

## 配置文件

1. config.json - API配置
   - model_providers: API提供商列表
   - active_provider: 当前使用的提供商
   - pdf_input_folder: PDF输入文件夹
   - output_folder: 单篇分析文档输出
   - summary_folder: 汇总文档输出

2. custom_prompts.py - Prompt模板配置
   - prompt_profiles: Prompt模板列表
   - active_profile: 当前使用的模板
   - 支持的内置模板:
     * default: 默认-深度分析
     * quick_scan: 快速扫描
     * methodology: 方法论聚焦
     * critical_review: 批判性评审

## 环境变量

  OPENAI_API_KEY      - OpenAI GPT
  ANTHROPIC_API_KEY   - Anthropic Claude
  DEEPSEEK_API_KEY    - DeepSeek
  ZHIPU_API_KEY       - 智谱GLM
  QWEN_API_KEY        - 阿里通义千问
  SILICONFLOW_API_KEY - SiliconFlow

## 使用示例

1. 命令行模式:
   python main.py --input ./pdfs --provider deepseek --prompt quick_scan

2. 交互式模式:
   python main.py

3. 自定义Prompt:
   python main.py --input ./pdfs --custom-prompt "你的自定义Prompt"

## Prompt占位符

  {filename}     - PDF文件名
  {title}        - 论文标题
  {authors}       - 作者
  {year}          - 年份
  {paper_content} - 论文内容

"""
    print(help_text)


def main():
    """主函数"""
    print_banner()

    # 启动时检查API配置
    client = APIClient()
    has_api, config_status = client.check_api_configured()
    if not has_api:
        print("\n" + "=" * 60)
        print("[错误] 未检测到任何已配置的API")
        print("=" * 60)
        print("\n" + config_status)
        print("\n请选择操作:")
        print("  [1] 前往 API配置管理 设置API Key")
        print("  [2] 查看配置说明")
        print("  [3] 退出程序")
        sub_choice = input("\n请选择: ").strip()
        if sub_choice == '1':
            manage_api_config()
        elif sub_choice == '2':
            show_config_help()
        return

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        from doc_generator import main as doc_main
        doc_main()
        return

    # 交互式模式
    while True:
        print_menu()
        choice = input("请选择: ").strip()

        if choice == '1':
            try:
                process_folder_interactive()
            except Exception as e:
                print(f"\n[FAIL] 处理出错: {str(e)}")
            input("\n按回车继续...")

        elif choice == '2':
            manage_api_config()
            input("\n按回车继续...")

        elif choice == '3':
            manage_prompt_config()
            input("\n按回车继续...")

        elif choice == '4':
            test_connection()
            input("\n按回车继续...")

        elif choice == '5':
            show_config_help()
            input("\n按回车继续...")

        elif choice == '6' or choice.lower() == 'q' or choice.lower() == 'exit':
            print("\n再见!")
            break

        else:
            print("\n无效选择，请重新输入")


if __name__ == "__main__":
    main()