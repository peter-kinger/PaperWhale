"""
AI文献阅读工具 - PDF读取模块
从PDF文件中提取文本、元数据等信息
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


@dataclass
class PaperInfo:
    """论文基本信息"""
    title: str = ""
    authors: str = ""
    year: str = ""
    abstract: str = ""
    filename: str = ""
    filepath: str = ""


class PDFReader:
    """PDF文件读取器"""

    def __init__(self):
        self.use_pdfplumber = PDFPLUMBER_AVAILABLE
        self.use_pypdf2 = PYPDF2_AVAILABLE

        if not PDFPLUMBER_AVAILABLE and not PYPDF2_AVAILABLE:
            print("警告: 未安装pdfplumber或PyPDF2，PDF读取功能可能受限")
            print("请运行: pip install pdfplumber")

    def read_pdf(self, pdf_path: str) -> Tuple[str, PaperInfo]:
        """
        读取PDF文件内容

        Args:
            pdf_path: PDF文件路径

        Returns:
            Tuple[str, PaperInfo]: (文本内容, 论文信息)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        paper_info = self._extract_metadata(pdf_path)
        paper_info.filepath = pdf_path
        paper_info.filename = os.path.basename(pdf_path)

        if self.use_pdfplumber:
            text = self._read_with_pdfplumber(pdf_path)
        elif self.use_pypdf2:
            text = self._read_with_pypdf2(pdf_path)
        else:
            raise RuntimeError("无可用的PDF读取库，请安装pdfplumber")

        # 提取标题和作者（如果之前没提取到）
        if not paper_info.title:
            paper_info.title = self._extract_title_from_text(text)
        if not paper_info.authors:
            paper_info.authors = self._extract_authors_from_text(text)

        return text, paper_info

    def _read_with_pdfplumber(self, pdf_path: str) -> str:
        """使用pdfplumber读取PDF"""
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def _read_with_pypdf2(self, pdf_path: str) -> str:
        """使用PyPDF2读取PDF"""
        text_parts = []
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def _extract_metadata(self, pdf_path: str) -> PaperInfo:
        """从PDF元数据提取论文信息"""
        info = PaperInfo()

        if self.use_pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    if pdf.metadata:
                        info.title = pdf.metadata.get('Title', '')
                        info.authors = pdf.metadata.get('Author', '')
                        # 尝试从标题提取年份
                        year_match = re.search(r'\b(19|20)\d{2}\b', info.title)
                        if year_match:
                            info.year = year_match.group()
            except Exception:
                pass

        return info

    def _extract_title_from_text(self, text: str) -> str:
        """从文本内容提取标题（通常在开头几行）"""
        lines = text.strip().split('\n')[:10]
        for line in lines:
            line = line.strip()
            # 过滤掉太短或太长的行
            if 10 < len(line) < 200:
                # 过滤掉明显的元数据行
                if not any(kw in line.lower() for kw in ['abstract', 'introduction', 'doi', 'http']):
                    return line
        return "未知标题"

    def _extract_authors_from_text(self, text: str) -> str:
        """从文本内容提取作者信息"""
        # 常见模式
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s*,?\s*(?:and|&)\s*)?)+',
            r'作者[：:]\s*([^\n]+)',
            r'Authors?[：:]\s*([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:2000])
            if match:
                return match.group(1).strip()

        return "未知作者"

    def extract_figures_and_tables(self, text: str) -> Dict[str, List[str]]:
        """
        尝试从文本中提取图表描述

        Args:
            text: 论文文本内容

        Returns:
            Dict: 包含'figures'和'tables'两个列表的字典
        """
        result = {
            'figures': [],
            'tables': []
        }

        # 提取Figure描述
        figure_pattern = r'[Ff]igure\s+\d+[.:]\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\n|[Ff]igure|\n\s*[Tt]able)'
        figures = re.findall(figure_pattern, text)
        result['figures'] = [f.strip()[:500] for f in figures[:10]]  # 限制数量和长度

        # 提取Table描述
        table_pattern = r'[Tt]able\s+\d+[.:]\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\n|[Tt]able|\n\s*[Ff]igure)'
        tables = re.findall(table_pattern, text)
        result['tables'] = [t.strip()[:500] for t in tables[:10]]

        return result

    def read_folder(self, folder_path: str) -> List[Tuple[str, PaperInfo]]:
        """
        读取文件夹中所有PDF文件

        Args:
            folder_path: 文件夹路径

        Returns:
            List[Tuple[str, PaperInfo]]: 每个PDF的(文本内容, 论文信息)列表
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")

        pdf_files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(folder_path, filename))

        pdf_files.sort()  # 按文件名排序

        results = []
        for pdf_path in pdf_files:
            try:
                print(f"  读取: {os.path.basename(pdf_path)}")
                text, info = self.read_pdf(pdf_path)
                results.append((text, info))
            except Exception as e:
                print(f"  ⚠️ 读取失败 {os.path.basename(pdf_path)}: {str(e)}")

        return results

    def extract_images_from_pdf(self, pdf_path: str, output_dir: str = None,
                                 max_images: int = 20) -> List[Dict]:
        """
        从PDF中提取所有图片

        Args:
            pdf_path: PDF文件路径
            output_dir: 图片输出目录（默认为 PDF所在目录下的 images/ 文件夹）
            max_images: 最大提取图片数量

        Returns:
            List[Dict]: 图片信息列表，每项包含 {
                'page': 页码(1-based),
                'index': 图片序号,
                'path': 保存路径,
                'size': (width, height),
                'b64': base64编码字符串,
                'hash': 图片内容hash
            }
        """
        if not PYMUPDF_AVAILABLE:
            print("  [提示] 未安装 PyMuPDF，无法提取图片（运行: pip install pymupdf）")
            return []

        if output_dir is None:
            pdf_dir = os.path.dirname(pdf_path)
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_dir = os.path.join(pdf_dir, f"{pdf_name}_images")
        os.makedirs(output_dir, exist_ok=True)

        images_info = []
        image_hashes = set()  # 用于去重

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            img_count = 0
            for page_num, page in enumerate(doc, start=1):
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image_width = base_image["width"]
                    image_height = base_image["height"]

                    # 过滤太小的图片（通常是图标或水印）
                    if image_width < 100 or image_height < 100:
                        continue

                    # 生成hash去重
                    img_hash = hashlib.md5(image_bytes).hexdigest()
                    if img_hash in image_hashes:
                        continue
                    image_hashes.add(img_hash)

                    # 保存图片文件
                    img_filename = f"page{page_num:03d}_img{img_index+1:02d}.{image_ext}"
                    img_path = os.path.join(output_dir, img_filename)

                    with open(img_path, "wb") as f:
                        f.write(image_bytes)

                    # 转为 base64
                    b64_str = base64.b64encode(image_bytes).decode("utf-8")

                    images_info.append({
                        'page': page_num,
                        'index': img_index + 1,
                        'path': img_path,
                        'size': (image_width, image_height),
                        'b64': b64_str,
                        'hash': img_hash
                    })

                    img_count += 1
                    if img_count >= max_images:
                        break

                if img_count >= max_images:
                    break

            doc.close()

        except Exception as e:
            print(f"  [警告] 图片提取失败: {str(e)}")

        return images_info

    def read_pdf_with_images(self, pdf_path: str,
                              output_dir: str = None,
                              max_images: int = 20) -> Tuple[str, PaperInfo, List[Dict]]:
        """
        读取PDF，同时提取文本和图片

        Args:
            pdf_path: PDF文件路径
            output_dir: 图片输出目录
            max_images: 最大提取图片数量

        Returns:
            Tuple[str, PaperInfo, List[Dict]]: (文本内容, 论文信息, 图片信息列表)
        """
        text, paper_info = self.read_pdf(pdf_path)
        images = self.extract_images_from_pdf(pdf_path, output_dir, max_images)
        return text, paper_info, images


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        str: 清理后的文件名
    """
    # 替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    clean_name = re.sub(illegal_chars, '_', filename)
    # 限制长度
    if len(clean_name) > 200:
        clean_name = clean_name[:200]
    return clean_name


def generate_paper_filename(paper_info: PaperInfo) -> str:
    """
    根据论文信息生成标准化的文件名

    格式: 作者年份-标题.md

    Args:
        paper_info: 论文信息

    Returns:
        str: 生成的文件名
    """
    # 提取作者姓氏
    authors = paper_info.authors
    if not authors or authors == "未知作者":
        authors = "Unknown"
    else:
        # 取第一个作者
        first_author = authors.split(',')[0].split(';')[0].split(' and ')[0].strip()
        # 取姓氏
        name_parts = first_author.split()
        if name_parts:
            authors = name_parts[-1]  # 取最后一个词作为姓氏

    # 提取年份
    year = paper_info.year
    if not year:
        # 尝试从标题中提取
        year_match = re.search(r'\b(19|20)\d{2}\b', paper_info.title)
        if year_match:
            year = year_match.group()
        else:
            year = "0000"

    # 清理标题
    title = paper_info.title
    if not title or title == "未知标题":
        title = "Unknown_Title"

    # 简化标题
    title = sanitize_filename(title)
    # 移除多余空格
    title = re.sub(r'\s+', '_', title)
    # 限制标题长度
    if len(title) > 100:
        title = title[:100]

    return f"{authors}{year}-{title}.md"


def test_pdf_reader():
    """测试PDF读取功能"""
    print("=" * 60)
    print("AI文献阅读工具 - PDF读取测试")
    print("=" * 60)

    reader = PDFReader()
    print(f"\npdfplumber可用: {reader.use_pdfplumber}")
    print(f"PyPDF2可用: {reader.use_pypdf2}")

    # 测试单个文件
    test_file = input("\n请输入测试PDF文件路径（或直接回车跳过）: ").strip()
    if test_file and os.path.exists(test_file):
        print(f"\n正在读取: {test_file}")
        text, info = reader.read_pdf(test_file)
        print(f"\n提取的信息:")
        print(f"  标题: {info.title}")
        print(f"  作者: {info.authors}")
        print(f"  年份: {info.year}")
        print(f"  文件名: {info.filename}")
        print(f"\n文本长度: {len(text)} 字符")
        print(f"\n前500字符预览:")
        print("-" * 40)
        print(text[:500])
        print("-" * 40)

        # 测试文件名生成
        filename = generate_paper_filename(info)
        print(f"\n生成的文件名: {filename}")
    else:
        print("\n跳过文件测试")


if __name__ == "__main__":
    test_pdf_reader()