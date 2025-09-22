from typing import List, Tuple
from git import Repo, Diff
import os
import re

def changed_line_numbers(repo_path: str, file_path: str, commit_a: str, commit_b: str) -> List[int]:
    """
    返回文件在 commit_a 和 commit_b 之间变更的行号列表（基于 commit_b 的行号）。
    - repo_path: 仓库根目录路径
    - file_path: 仓库内文件路径（相对路径，如 "src/module/example.py"）
    - commit_a, commit_b: 提交 hash（可以为完整或简短 hash）
    返回值：commit_b 版本下被修改或新增行的行号列表（升序，不重复）
    """
    repo = Repo(repo_path)
    # 确保路径统一
    file_path = os.path.normpath(file_path)

    # 获取 commit 对象
    ca = repo.commit(commit_a)
    cb = repo.commit(commit_b)

    # 获取两个提交之间的 diff，限制到特定文件
    diffs = cb.diff(ca, paths=file_path, create_patch=True)

    if not diffs:
        return []

    # 只处理第一个匹配的 diff（paths 限定应只返回一个）
    diff = diffs[0]
    patch_text = diff.diff.decode('utf-8', errors='replace')

    # 解析 unified diff 的 hunk header，示例： @@ -start_a,count_a +start_b,count_b @@
    changed_lines = set()
    for hunk in re.finditer(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', patch_text):
        start_a = int(hunk.group(1))
        cnt_a = int(hunk.group(2)) if hunk.group(2) else 1
        start_b = int(hunk.group(3))
        cnt_b = int(hunk.group(4)) if hunk.group(4) else 1

        # 获取该 hunk 的文本（从当前 match 位置到下一个 @@ 或文件结尾）
        hunk_start = hunk.end()
        next_hunk = re.search(r'@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@', patch_text[hunk_start:])
        hunk_text = patch_text[hunk_start:hunk_start + next_hunk.start()] if next_hunk else patch_text[hunk_start:]

        # 遍历 hunk_text 行，计算基于 commit_b 的行号
        line_b = start_b
        for line in hunk_text.splitlines():
            if not line:
                # 空行在 diff 中仍有前缀（' ', '+', '-'），但 splitlines() 去掉了换行符，
                # 这里空字符串通常不会出现，但留作稳健处理
                continue
            prefix = line[0]
            if prefix == ' ':
                # 上下文行，行号在 both
                line_b += 1
            elif prefix == '+':
                # 新增行：属于 commit_b 的行，记录行号并增加
                changed_lines.add(line_b)
                line_b += 1
            elif prefix == '-':
                # 删除行：不占据 commit_b 的行号，但视为影响相邻行。
                # 为简单起见，将删除行映射到下一 commit_b 的行号（若存在），或到 start_b if none.
                # 这里我们将标记下一行（即当前 line_b）作为受影响行（如果该行在 commit_b 中存在）。
                # 不增加 line_b（删除不会推进 commit_b 行号)
                # 若需要以 commit_a 的行号为准，请调整此逻辑。
                changed_lines.add(line_b)  # 可能为下一个 commit_b 行号
            else:
                # 忽略其他前缀（例如 \ No newline at end of file）
                pass

    return sorted(changed_lines)

if __name__ == '__main__':
    oldhash = "80036b3c09c6673f020607074016e8523b994914"
    newhash = "36079d22971fdd8ca2f372edef906b489df6366e"
    print(changed_line_numbers("./","preprocess/a.py",oldhash, newhash))
    print(changed_line_numbers("./","preprocess/a.py",newhash, oldhash))
