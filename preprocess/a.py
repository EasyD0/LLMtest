"""预处理工具和git差异工具集。

包含：
- changed_lines_between_commits(repo_path, file_path, old_commit, new_commit)

"""
from git import Repo
import difflib
from typing import List


def changed_lines_between_commits(repo_path: str, file_path: str, old_commit: str, new_commit: str) -> List[int]:
    """
    返回指定文件在 old_commit -> new_commit 之间在 new_commit 中被新增或修改的行号（基于 new_commit 的行号，1-based）。

    参数:
        repo_path: 仓库根目录路径（工作树所在目录）。
        file_path: 仓库内相对路径，例如 'src/main.c' 或 'main.c'。
        old_commit: 旧的提交 hash 或引用（例如 'HEAD~1'）。
        new_commit: 新的提交 hash 或引用（例如 'HEAD'）。

    返回:
        整数列表，按升序排列的变更行号（new_commit 中的行号）。
    """


    repo = Repo(repo_path)
    # 解析提交对象
    old = repo.commit(old_commit)
    new = repo.commit(new_commit)

    # 读取文件在两个提交中的内容为行列表（若文件不存在则为空）
    try:
        old_blob = old.tree / file_path
        old_source = old_blob.data_stream.read().decode('utf-8', errors='ignore').splitlines()
    except Exception:
        old_source = []

    try:
        new_blob = new.tree / file_path
        new_source = new_blob.data_stream.read().decode('utf-8', errors='ignore').splitlines()
    except Exception:
        new_source = []

    # 使用 SequenceMatcher 获取 opcode 区间
    sm = difflib.SequenceMatcher(a=old_source, b=new_source)
    changed = set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        # tag: 'replace','delete','insert','equal'
        if tag == 'equal':
            continue
        if tag in ('replace', 'insert'):
            # new 中受影响的行索引为 j1..j2-1（0-based）
            for j in range(j1, j2):
                changed.add(j + 1)  # 转为1-based
        # delete 表示 old 中被删除，new 中没有对应行，不加入结果

    return sorted(changed)

def get_changed_lines(repo_path, file_path, commit_hash1, commit_hash2):
    # 打开指定的 Git 仓库
    repo = git.Repo(repo_path)
    
    # 获取两个提交对象
    commit1 = repo.commit(commit_hash1)
    commit2 = repo.commit(commit_hash2)
    
    # 获取文件在两个提交之间的差异
    diff = commit2.diff(commit1, paths=file_path)
    
    changed_lines = []
    
    for change in diff:
        # 只处理修改的文件
        if change.a_blob and change.b_blob:
            # 获取修改的行号
            for line in change.diff.decode('utf-8').splitlines():
                if line.startswith('+') and not line.startswith('+++'):
                    # 计算行号
                    line_number = change.b_blob.size - change.b_blob.data.count(b'\n', 0, change.b_blob.size) + 1
                    changed_lines.append(line_number)
    
    return changed_lines



'''
if __name__ == '__main__':
    # 简单命令行测试示例（在仓库根目录运行此脚本）
    import sys
    if len(sys.argv) == 5:
        _, repo_root, target_file, oldc, newc = sys.argv
        lines = changed_lines_between_commits(repo_root, target_file, oldc, newc)
        print(lines)
    else:
        print('用法: python a.py <repo_root> <file_path> <old_commit> <new_commit>')
'''
