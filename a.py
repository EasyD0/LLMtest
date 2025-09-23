import os
import re
import subprocess
import json
import tempfile
import shutil
from bs4 import BeautifulSoup

# --- 1. 爬虫部分：解析HTML报告 ---
def parse_html_report(html_file_path):
    """
    使用BeautifulSoup解析HTML测试报告，提取错误信息。
    
    参数:
    html_file_path (str): HTML报告文件的路径。
    
    返回:
    dict: 包含错误信息的字典，如果找不到则返回None。
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # 使用CSS选择器定位第一个错误区域
        error_section = soup.select_one('div.error-section')
        if not error_section:
            print("错误: 未在HTML报告中找到 '.error-section' 区域。")
            return None
        
        # 在错误区域内提取具体信息
        file_path_tag = error_section.select_one('p.file-path')
        line_number_tag = error_section.select_one('p.line-number')
        error_code_tag = error_section.select_one('p.error-code')

        if not all([file_path_tag, line_number_tag, error_code_tag]):
            print("错误: 报告中缺少关键信息（文件路径、行号或错误代号）。")
            return None

        file_path = file_path_tag.text.strip()
        line_number = int(line_number_tag.text.strip())
        error_code = error_code_tag.text.strip()
        
        return {
            'file_path': file_path,
            'line_number': line_number,
            'error_code': error_code
        }
    except Exception as e:
        print(f"解析HTML报告时出错: {e}")
        return None

# --- 2. AST部分：使用Clang AST提取函数代码 ---
def find_function_in_ast(ast_node, original_file_path, target_line):
    """
    递归遍历AST节点，寻找包含目标行号的函数定义节点。
    
    参数:
    ast_node (dict): 当前要检查的AST节点。
    original_file_path (str): 原始C文件路径。
    target_line (int): 错误所在的行号。
    
    返回:
    dict: 如果找到，返回FunctionDecl节点，否则返回None。
    """
    if 'kind' in ast_node and ast_node['kind'] == 'FunctionDecl':
        location = ast_node['loc']
        start_line = location['line']
        end_line = location.get('end', {}).get('line') or start_line
        
        if start_line <= target_line <= end_line:
            file_path = location.get('file', '')
            if os.path.normpath(file_path) == os.path.normpath(original_file_path):
                return ast_node
    
    if 'inner' in ast_node:
        for child_node in ast_node['inner']:
            result = find_function_in_ast(child_node, original_file_path, target_line)
            if result:
                return result
    
    return None

def extract_function_with_clang_ast(original_file_path, target_line):
    """
    使用clang AST来提取包含错误行的整个函数代码。
    
    参数:
    original_file_path (str): 原始C文件路径。
    target_line (int): 错误所在的行号。
    
    返回:
    str: 提取出的整个函数代码片段，如果找不到则返回None。
    """
    try:
        command = [
            'clang', 
            '-Xclang', '-ast-dump=json', 
            '-fsyntax-only', 
            original_file_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        json_output = re.search(r'^\s*\{.*\}\s*$', result.stdout, re.DOTALL).group(0)
        ast = json.loads(json_output)
        
        function_node = find_function_in_ast(ast, original_file_path, target_line)
        
        if function_node:
            location = function_node['loc']
            start_line = location['line']
            end_line = location.get('end', {}).get('line') or start_line
            
            with open(original_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            function_code = "".join(lines[start_line - 1: end_line])
            return function_code
        else:
            print(f"Error: Could not find function containing line {target_line} in AST.")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error calling clang: {e.stderr}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- 3. 评论部分：在原始文件插入注释 ---
def insert_comment_into_file(file_path, line_number, comment):
    """
    在指定文件的指定行末尾插入注释。

    参数:
    file_path (str): C源文件路径。
    line_number (int): 需要插入注释的行号。
    comment (str): 要插入的注释文本（例如：错误代号）。

    返回:
    bool: 成功返回True，否则返回False。
    """
    try:
        with open(file_path, 'r+', encoding='utf-8') as f:
            lines = f.readlines()
        
        if 1 <= line_number <= len(lines):
            target_line = lines[line_number - 1].rstrip('\n')
            comment_text = f" // {comment}"
            new_line = target_line + comment_text + '\n'
            
            lines[line_number - 1] = new_line
            
            f.seek(0)
            f.writelines(lines)
            f.truncate()
            
            print(f"成功在 {file_path}:{line_number} 处插入注释: '{comment}'")
            return True
        else:
            print(f"错误: 行号 {line_number} 无效。")
            return False
            
    except Exception as e:
        print(f"插入注释时出错: {e}")
        return False

# --- 主程序逻辑 ---
def main():
    # 模拟HTML报告文件
    mock_html_content = """
    <html>
      <body>
        <div class="error-section">
          <p class="file-path">./test.c</p>
          <p class="line-number">13</p>
          <p class="error-code">D12</p>
        </div>
      </body>
    </html>
    """
    html_file_path = "mock_report.html"
    with open(html_file_path, "w", encoding='utf-8') as f:
        f.write(mock_html_content)

    # 模拟C源文件
    test_file_content = """#include <stdio.h>
#define A 1
#define myMacro_impl(x,y) x##y = 1
#define myMacro(x,y) myMacro_impl(x,y)
#define Loop(x,n) \\
for(int i = 0; i < n; i++) {\\
    x+=i;\\
}

int main(){
    int myMacro(x,A);
    Loop(x1,5);
    printf("%d\\n", x1);
    return 0;
}
"""
    test_file_path = "CFile/test.c"
    with open(test_file_path, "w") as f:
        f.write(test_file_content)

    print("--- 1. 解析HTML报告并提取错误信息 ---")
    error_info = parse_html_report(html_file_path)
    if not error_info:
        return
        
    print("提取到的错误信息:")
    print(error_info)
    
    print("\n--- 2. 使用Clang AST提取函数代码 ---")
    function_code = extract_function_with_clang_ast(error_info['file_path'], error_info['line_number'])
    
    if function_code:
        print("\n成功提取的函数代码:")
        print("-------------------------")
        print(function_code)
        print("-------------------------")
        
        # 在成功提取函数代码后，才在原始文件插入注释
        print(f"\n--- 3. 在原始文件中插入注释: {error_info['error_code']} ---")
        insert_comment_into_file(error_info['file_path'], error_info['line_number'], error_info['error_code'])


if __name__ == "__main__":
    main()

