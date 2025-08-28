# 扫描图片型 PDF，使用 pdf2image + 千问视觉模型


from openai import OpenAI
import pdf2image
import os
import base64


client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def encode_image_to_base64(image_path):
    """将图片编码为base64格式"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def call_qwen_vision_model(image_paths, question):
    """调用千问视觉模型"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    base64_images = []
    for image_path in image_paths:
        # 将图片编码为base64
        base64_image = encode_image_to_base64(image_path)
        base64_images.append(base64_image)

    
    contents = [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}} for base64_image in base64_images]
    contents.append({"type": "text", "text": question})
    
    
    try:
        completion = client.chat.completions.create(
            model="qwen-vl-max-latest",
            messages=[
                {
                    "role": "system",
                    "content": [{"type":"text","text": "You are a helpful assistant."}]
                 },
                {
                    "role": "user",
                    "content": contents
                }

            ]
        )
        return completion.choices[0].message.content
    
    except Exception as e:
        print(f"调用千问视觉模型时出错: {e}")
        return None

def main():
    # 创建 output 目录
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # PDF文件路径
    pdf_path = '替换为实际的pdf路径'
    
    # 将 PDF 转换为图片并保存
    print("正在将PDF转换为图片...")
    images = pdf2image.convert_from_path(pdf_path)
    
    image_paths = []
    for i, image in enumerate(images):
        image_path = f'{output_dir}/page_{i+1}.png'
        image.save(image_path)
        image_paths.append(image_path)
        print(f'已保存: {image_path}')
    
    print(f"\n共转换了 {len(image_paths)} 页")
    
    question = "谁是2023年的首富？来自哪个国家？ta的USD是多少，财富来源自哪里？"
            
    if not question:
        question = "这张图片展示了什么内容？请详细描述。"
    
    print(f"问题: {question}")
    
    answer = call_qwen_vision_model(image_paths, question)
    if answer:
        print(f"\n千问视觉模型回答:")
        print(answer)
    else:
        print("获取回答失败，请检查API密钥和网络连接")

if __name__ == "__main__":
    main() 