import clang.cindex
import os
from pathlib import Path
import hashlib


# 确保 clang.cindex 可以找到 libclang 库
# 如果你在 Windows 上，可能需要手动设置这个路径
# 例如: clang.cindex.Config.set_library_path("C:/Program Files/LLVM/bin")
# 或者如果你使用 brew 安装在 macOS 上: clang.cindex.Config.set_library_file('/usr/local/opt/llvm/lib/libclang.dylib')


def _getCodeByLine(file_path: str | Path, start: int = None, end: int = None) -> str:
    return ""


def getFuncInfoInFile(prep_file: str, only_hash: bool = False) -> dict[str, dict]:
    """
    解析一个C文件, 并得到所有的函数名和函数体
    only_hash 是否只保留函数体的hash值
    结果的键值对是 函数名 : 函数信息, 其中函数信息也是一个字典
    """

    # 检查文件是否存在
    if not os.path.exists(prep_file):
        print(f"Error: File not found at {prep_file}")
        return []

    try:
        # 创建索引，这是解析的第一步
        index = clang.cindex.Index.create()
        # 解析文件并生成 AST。
        # 'translation_unit' 是 AST 的根节点。
        tu = index.parse(prep_file)

        result = dict()
        # 遍历 AST 中的所有节点
        for node in tu.cursor.walk_preorder():
            # 查找 'FUNCTION_DECL' 类型的节点，它代表一个函数声明或定义
            if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                # 检查这个节点是否在当前文件内（而非头文件）
                if node.location.file and node.location.file.name == prep_file:
                    function_name = node.spelling
                    start_line = node.extent.start.line
                    end_line = node.extent.end.line
                    function_body = _getCodeByLine(prep_file, start_line, end_line)
                    function_hash = hashlib.sha1(function_body).hexdigest()

                    if not only_hash:
                        result.update(
                            {
                                function_name: {
                                    "func_body": function_body,
                                    "func_hash": function_hash,
                                }
                            }
                        )
                    else:
                        result.update({function_name: {"func_hash": function_hash}})
        return result

    except clang.cindex.LibclangError as e:
        print(f"LibClang 库出错: {e}")
        return []
    except Exception as e:
        print(f"解析 C 文件时出错: {e}")
        return []


def getDiffFuncName(file1: str | Path, file2: str | Path) -> list[str]:
    dict1 = getFuncInfoInFile(file1, only_hash=True)
    result = []
    try:
        index = clang.cindex.Index.create()
        tu = index.parse(file1)

        for node in tu.cursor.walk_preorder():
            if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                if node.location.file and node.location.file.name == file2:

                    function_name = node.spelling
                    if function_name in dict1:
                        hash1 = dict1[function_name]["func_hash"]
                        # TODO 这里可以用另一种方法提取函数体? 需要测试一下和根据行号的方法比较
                        hash2 = hashlib.sha1(node.extent.body.content).hexdigest()
                        if hash1 != hash2:
                            result.append(function_name)

    except clang.cindex.LibclangError as e:
        print(f"LibClang 库出错: {e}")
        return []
    except Exception as e:
        print(f"解析 C 文件时出错: {e}")
        return []
    return result


if __name__ == "__main__":
    # 创建一个临时的 C 文件用于测试
    test_c_code = """
#include <stdio.h>

void my_first_function(int a, int b) {
    printf("Sum: %d\\n", a + b);
}

int main(void) {
    int x = 10, y = 20;
    my_first_function(x, y);
    return 0;
}

static void another_function() {
    // This is a static function
}

int final_function(void) {
    return 1;
}
    """

    c_file_path = "temp_test.c"
    with open(c_file_path, "w") as f:
        f.write(test_c_code)

    print(f"Parsing C file: {c_file_path}")
    function_list = getFuncInfoInFile(c_file_path)

    if function_list:
        print("Found the following functions:")
        for func in function_list:
            print(
                f"  - 函数名: {func['函数名']}, 起始行: {func['起始行']}, 结束行: {func['结束行']}"
            )
    else:
        print("No functions found or an error occurred.")

    # 清理临时文件
    os.remove(c_file_path)
