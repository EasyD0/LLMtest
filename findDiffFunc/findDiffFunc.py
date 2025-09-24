import clang.cindex
import os
from pathlib import Path
import hashlib
import json


# 确保 clang.cindex 可以找到 libclang 库
# 如果你在 Windows 上，可能需要手动设置这个路径
# 例如: clang.cindex.Config.set_library_path("C:/Program Files/LLVM/bin")
# 或者如果你使用 brew 安装在 macOS 上: clang.cindex.Config.set_library_file('/usr/local/opt/llvm/lib/libclang.dylib')


def _getCodeByLine(
    file_path: str | Path, start_line: int = None, end_line: int = None
) -> str:
    result_lines = []
    current_line_number = 1

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if current_line_number >= start_line:
                result_lines.append(line)

            # 当达到结束行时，停止读取以提高效率
            if current_line_number == end_line:
                break

            current_line_number += 1

    return "".join(result_lines)


# 待测试
def getFuncInfoInFile(
    prep_file: str, only_hash: bool = False, contain_filename: bool = True
) -> dict[str, dict]:
    """
    解析一个C文件, 并得到所有的函数名和函数体
    only_hash 是否只保留函数体的hash值
    结果的键值对是 函数名 : 函数信息, 其中函数信息也是一个字典
    """

    # 检查文件是否存在
    if not os.path.exists(prep_file):
        print(f"Error: File not found at {prep_file}")
        return []

    file_name = (os.path.basename(str(prep_file)) + "/") if contain_filename else ""

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
                    function_name = file_name + node.spelling
                    start_line = node.extent.start.line
                    end_line = node.extent.end.line
                    function_body = _getCodeByLine(prep_file, start_line, end_line)
                    function_hash = hashlib.sha1(
                        function_body.encode("utf-8")
                    ).hexdigest()

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
        print(f"getFuncInfoInFile, LibClang 库出错: {e}")
        return []
    except Exception as e:
        print(f"getFuncInfoInFile, 解析 C 文件时出错: {e}")
        return []


# 待测试
def getDiffFuncName(
    file_path1: str | Path,
    file_path2: str | Path,
    need_hash: bool = True,
    contain_filename: bool = True,
) -> dict[str, list[str]]:
    """
    直接比较两个C文件, 找到不同的函数名 (不利用git变更行号)
    need_hash 是否需要返回函数体的hash值
    contain_filename 函数名字前是否含有文件名
    """
    dict1 = getFuncInfoInFile(file_path1, only_hash=True)
    result = dict()
    file_name = (os.path.basename(str(file_path1)) + "/") if contain_filename else ""
    try:
        index = clang.cindex.Index.create()
        tu = index.parse(file_path2)

        for node in tu.cursor.walk_preorder():
            if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                if node.location.file and node.location.file.name == file_path2:
                    function_name = file_name + node.spelling

                    if function_name in dict1:
                        hash1 = dict1[function_name]["func_hash"]

                        start_line = node.extent.start.line
                        end_line = node.extent.end.line
                        hash2 = hashlib.sha1(
                            _getCodeByLine(file_path2, start_line, end_line).encode(
                                "utf-8"
                            )
                        ).hexdigest()
                        if hash1 != hash2:
                            if not need_hash:
                                result.update({function_name: [""]})
                            else:
                                result.update({function_name: [hash1, hash2]})
        return result

    except clang.cindex.LibclangError as e:
        print(f"getDiffFuncName: LibClang 库出错: {e}")
        return result
    except Exception as e:
        print(f"getDiffFuncName: 解析 C 文件时出错: {e}")
        return result


# 已测试
def dictToJson(mydict: dict[str, list[str]], json_file: str | Path) -> None:
    # TODO 这里增加一个, 当文件夹不存在时, 自动创建文件夹

    with open(json_file, "w") as f:
        # TODO这里存在问题, 该格式的字典不能直接用json.dump写入json文件, 会报错
        json.dump(mydict, f, ensure_ascii=False, indent=4)


# 已测试
def updateDiffFuncCollection(
    json_file: str | Path, mydict: dict[str, list[str]]
) -> None:
    with open(json_file, "r") as f:
        data = json.load(f)

    for func_name, hash_list in mydict.items():
        if func_name in data:
            data[func_name] = list(set(data[func_name]).union(hash_list))
        else:
            data.update({func_name: hash_list})

    dictToJson(data, json_file)


if __name__ == "__main__":
    dict = getFuncInfoInFile("a.c")
    for func_name, func_info in dict.items():
        print(func_name)
        print(func_info["func_body"])
        print(func_info["func_hash"])
