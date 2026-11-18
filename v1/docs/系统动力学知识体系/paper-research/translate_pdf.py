#!/usr/bin/env python3
"""
PDF文本翻译工具
用法: python translate_pdf.py <输入txt文件> <输出txt文件>
"""

import sys
from googletrans import Translator

def translate_text(input_file, output_file, chunk_size=3000):
    translator = Translator()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 分块翻译（避免超时）
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []
    
    for i, chunk in enumerate(chunks):
        print(f"正在翻译第 {i+1}/{len(chunks)} 块...")
        try:
            result = translator.translate(chunk, src='en', dest='zh-cn')
            translated_chunks.append(result.text)
        except Exception as e:
            print(f"翻译第 {i+1} 块时出错: {e}")
            translated_chunks.append(chunk)  # 失败时保留原文
    
    translated_text = ''.join(translated_chunks)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(translated_text)
    
    print(f"翻译完成，结果保存到 {output_file}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python translate_pdf.py <输入txt文件> <输出txt文件>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    translate_text(input_file, output_file)
