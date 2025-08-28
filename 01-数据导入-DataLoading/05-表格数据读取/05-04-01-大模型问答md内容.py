import os
from openai import OpenAI
import json
from datetime import datetime

# ==================== 配置区域 ====================
# 在这里设置你要分析的markdown文件路径
MARKDOWN_FILE_PATH = "output/document_structure_unified_20250827_163611.md"

# 在这里设置千问模型名称
QWEN_MODEL = "qwen-plus"

# =================================================

def load_markdown_file(file_path):
    """加载指定的markdown文件"""
    if not os.path.exists(file_path):
        print(f"❌ 错误: 文件不存在: {file_path}")
        return None
    
    if not file_path.endswith('.md'):
        print(f"❌ 错误: 文件不是markdown格式: {file_path}")
        return None
    
    print(f"📖 加载markdown文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ 成功加载文件，大小: {len(content)} 字符")
        return content
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None

def ask_qwen_about_document(document_content, question, model=QWEN_MODEL):
    """使用千问大模型回答关于文档的问题"""
    try:
        # 检查API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("❌ 错误: 未设置DASHSCOPE_API_KEY环境变量")
            print("请设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
            print("或者在代码中设置: os.environ['DASHSCOPE_API_KEY'] = 'your-api-key'")
            return None
        
        print(f"🤖 正在调用千问大模型 ({model})...")
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 构建系统提示词
        system_prompt = """你是一个专业的文档分析助手。用户会给你一个PDF文档的内容，你需要根据文档内容准确回答用户的问题。

请遵循以下原则：
1. 只基于提供的文档内容回答问题，不要添加文档中没有的信息
2. 如果文档中没有相关信息，请明确说明
3. 回答要准确、简洁、有条理
4. 如果涉及数据，请引用具体的数字
5. 如果涉及表格，请准确描述表格内容

文档内容如下：
"""
        
        # 构建用户消息
        user_message = f"{question}\n\n请基于以上文档内容回答我的问题。"
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt + document_content},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,  # 降低随机性，提高准确性
            max_tokens=2000,  # 限制回答长度
        )
        
        answer = completion.choices[0].message.content
        print(f"✅ 千问大模型回答完成")
        return answer
        
    except Exception as e:
        print(f"❌ 调用千问大模型时出错: {e}")
        print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
        return None

def main():
    print("🚀 千问大模型PDF文档问答系统 (简化版)")
    print("=" * 50)
    
    # 显示配置信息
    print(f"📁 要分析的文件: {MARKDOWN_FILE_PATH}")
    print(f"🤖 使用的模型: {QWEN_MODEL}")
    print(f"🔑 API密钥: {'已设置' if os.getenv('DASHSCOPE_API_KEY') else '未设置'}")
    print("=" * 50)
    
    # 1. 加载指定的markdown文档
    document_content = load_markdown_file(MARKDOWN_FILE_PATH)
    if not document_content:
        return
    
    print(f"\n📋 文档内容预览 (前200字符):")
    print("-" * 50)
    print(document_content[:200] + "..." if len(document_content) > 200 else document_content)
    print("-" * 50)
    
    # 2. 获取用户问题
    print(f"\n❓ 请输入你的问题 (或按回车使用默认问题):")
    user_question = "谁是2022年的第二有钱的？来自哪个国家？ta的USD是多少，财富来源自哪里？"
    
    if not user_question:
        # 使用默认问题
        user_question = "请总结一下这个文档的主要内容，包括各个年份的富豪排名情况。"
        print(f"使用默认问题: {user_question}")
    
    print(f"\n🔍 问题: {user_question}")
    
    # 3. 调用千问大模型
    answer = ask_qwen_about_document(document_content, user_question)
    
    if answer:
        print(f"\n🤖 千问大模型回答:")
        print("=" * 50)
        print(answer)
        print("=" * 50)
        
              
    else:
        print("❌ 无法获取千问大模型的回答")

if __name__ == "__main__":
    main()
