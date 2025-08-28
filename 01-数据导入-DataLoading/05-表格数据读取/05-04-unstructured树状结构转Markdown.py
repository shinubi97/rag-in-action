from unstructured.partition.pdf import partition_pdf
import os
import json
from datetime import datetime
import re

def is_header_or_footer(text):
    """判断是否为页眉页脚或页数信息"""
    if not text:
        return False
    
    text = text.strip().lower()
    
    # 页眉页脚常见模式
    header_footer_patterns = [
        r'^\d+/\d+$',  # 页码格式如 "1/33"
        r'^\d{1,2}:\d{2}\s+[ap]m$',  # 时间格式如 "7:31 PM"
        r'^\d{1,2}/\d{1,2}/\d{2},\s+\d{1,2}:\d{2}\s+[ap]m$',  # 日期+时间格式如 "7/1/23, 11:31 PM"
        r'^\d{1,2}/\d{1,2}/\d{2}$',  # 日期格式如 "7/1/23"
        r'^the world\'s billionaires - wikipedia$',  # 重复的标题
        r'^wikipedia$',  # 重复的标题
        r'^the free encyclopedia$',  # 重复的标题
        r'^https?://',  # URL链接
        r'^\*https?://',  # 带星号的URL
        r'^a$',  # 单个字母
        r'^\*net worth\*$',  # 带星号的标题
        r'^\d{1,2}:\d{2}$',  # 纯时间格式如 "11:31"
        r'^page\s+\d+$',  # 页码格式如 "Page 1"
        r'^\d+\s+of\s+\d+$',  # 页码格式如 "1 of 33"
        # 注意：移除了 r'^\d+$' 模式，避免过滤掉年份标题如 "2023", "2022" 等
    ]
    
    for pattern in header_footer_patterns:
        if re.match(pattern, text):
            return True
    
    return False

def build_element_tree(elements):
    """构建元素的树状结构"""
    # 创建元素ID到元素的映射
    element_map = {element.id: element for element in elements if hasattr(element, 'id')}
    
    # 构建树状结构
    tree = []
    
    # First pass: create all element_info dicts and link parents
    element_info_map = {}
    for element in elements:
        if not hasattr(element, 'id'):
            continue
        
        element_info = {
            'id': element.id,
            'category': element.category,
            'text': element.text if hasattr(element, 'text') else "",
            'metadata': {
                'page_number': getattr(element.metadata, 'page_number', None),
                'detection_confidence': getattr(element.metadata, 'detection_class_prob', None),
                'parent_id': getattr(element.metadata, 'parent_id', None),
                'coordinates': str(getattr(element.metadata, 'coordinates', None))
            },
            'children': [],
            'parent': None # Will be filled in the second pass
        }
        element_info_map[element.id] = element_info
    
    # Second pass: establish parent-child relationships
    for element_id, element_info in element_info_map.items():
        parent_id = element_info['metadata']['parent_id']
        if parent_id and parent_id in element_info_map:
            parent_element_info = element_info_map[parent_id]
            parent_element_info['children'].append(element_info)
            element_info['parent'] = {
                'id': parent_element_info['id'],
                'category': parent_element_info['category'],
                'text': parent_element_info['text']
            }
        else:
            # Elements without a recognized parent are root elements
            tree.append(element_info)
    
    return tree

def convert_table_to_markdown(table_text):
    """将表格文本转换为markdown表格格式"""
    if not table_text:
        return ""
    
    # 按行分割
    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return f"```\n{table_text}\n```\n"
    
    # 尝试按空格分割第一行作为标题
    headers = lines[0].split()
    if len(headers) < 2:
        return f"```\n{table_text}\n```\n"
    
    # 创建markdown表格
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    # 处理数据行
    for line in lines[1:]:
        if line.strip():
            cells = line.split()
            if len(cells) >= len(headers):
                markdown_table += "| " + " | ".join(cells[:len(headers)]) + " |\n"
            else:
                # 如果列数不匹配，用空格填充
                padded_cells = cells + [""] * (len(headers) - len(cells))
                markdown_table += "| " + " | ".join(padded_cells) + " |\n"
    
    return markdown_table + "\n"

def convert_tree_to_markdown(tree, level=0):
    """将树状结构转换为markdown格式"""
    markdown_content = []
    
    for element in tree:
        # 过滤掉页眉页脚等无意义内容
        if is_header_or_footer(element['text']):
            continue
            
        category = element['category']
        text = element['text']
        
        if not text.strip():
            continue
        
        # 根据元素类型添加相应的markdown格式
        if category == "Title":
            markdown_content.append(f"{'#' * (level + 3)} {text}\n\n")
        elif category == "Header":
            markdown_content.append(f"{'#' * (level + 4)} {text}\n\n")
        elif category == "NarrativeText":
            markdown_content.append(f"{text}\n\n")
        elif category == "Table":
            # 表格直接转换为markdown表格语法
            markdown_content.append("**表格内容**:\n\n")
            markdown_table = convert_table_to_markdown(text)
            markdown_content.append(markdown_table)
            
            # 添加表格元数据
            confidence = element['metadata']['detection_confidence']
            if confidence:
                markdown_content.append(f"*表格识别置信度: {confidence:.3f}*\n\n")
        elif category == "UncategorizedText":
            markdown_content.append(f"*{text}*\n\n")
        elif category == "Footer":
            # 跳过页脚
            continue
        else:
            markdown_content.append(f"{text}\n\n")
        
        # 递归处理子元素
        if element['children']:
            markdown_content.extend(convert_tree_to_markdown(element['children'], level + 1))
    
    return markdown_content

def convert_to_markdown_unified(elements):
    """统一转换为markdown格式，不按页分组"""
    markdown_content = []
    
    # 添加文档头部
    markdown_content.append("# PDF文档结构提取报告\n")
    markdown_content.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    markdown_content.append(f"**总元素数**: {len(elements)}\n\n")
    markdown_content.append("---\n\n")
    
    # 过滤掉页眉页脚
    filtered_elements = []
    for element in elements:
        text = element.text if hasattr(element, 'text') else ""
        if not is_header_or_footer(text):
            filtered_elements.append(element)
    
    # 构建树状结构
    tree = build_element_tree(filtered_elements)
    
    # 转换为markdown
    markdown_content.extend(convert_tree_to_markdown(tree))
    
    return "".join(markdown_content)

def main():
    # 创建output目录
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    print(f"创建输出目录: {output_dir}")
    
    # 解析 PDF 结构
    file_path = "/Users/litingguo/project_station/ai/rag-in-action/90-文档-Data/复杂PDF/billionaires_page-1-5.pdf"
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return
    
    try:
        print("正在解析PDF文件...")
        print("使用高精度策略 (strategy='hi_res')...")
        
        # 使用高精度策略解析PDF
        elements = partition_pdf(
            file_path,
            strategy="hi_res",
        )
        
        print(f"成功解析PDF，共找到 {len(elements)} 个元素")
        
        # 统计各类型元素数量
        category_counts = {}
        for element in elements:
            category = element.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\n元素类型统计:")
        for category, count in category_counts.items():
            print(f"  {category}: {count}")
        
        # 构建树状结构
        print("\n正在构建元素树状结构...")
        tree = build_element_tree(elements)
        print(f"构建了 {len(tree)} 个根级元素")
        
        # 转换为markdown（不按页分组）
        print("正在转换为Markdown格式...")
        markdown_content = convert_to_markdown_unified(elements)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存文件
        markdown_file = os.path.join(output_dir, f"document_structure_unified_{timestamp}.md")
        json_file = os.path.join(output_dir, f"document_structure_unified_{timestamp}.json")
        
        print(f"\n正在保存文件...")
        
        # 保存markdown文件
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✅ Markdown文件已保存到: {markdown_file}")
        
        # 保存树状结构JSON文件
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        print(f"✅ 树状结构数据已保存到: {json_file}")
        
        print(f"\n🎉 文档结构提取完成！")
        print(f"📁 输出目录: {os.path.abspath(output_dir)}")
        
        # 显示文件大小信息
        for file_path in [markdown_file, json_file]:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"📄 {os.path.basename(file_path)}: {size} bytes")
        
        # 显示markdown预览
        print(f"\n📝 Markdown文件预览 (前500字符):")
        print("-" * 50)
        print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)
        print("-" * 50)
        
    except Exception as e:
        print(f"处理PDF时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
