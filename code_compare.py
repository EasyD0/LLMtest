from pathlib import Path
import os
import subprocess

def gitCloneCode(git_addr:str, git_hash1:str, git_hash2:str, git_version : str = "master", dest_dir1: str | Path= './version1', dest_dir2: str | Path= './version2')->bool:
	"""
	从git仓库克隆代码并切换到指定版本.
	"""	
	Dest_Dir1 = Path(dest_dir1)
	Dest_Dir2 = Path(dest_dir2)

	if not Dest_Dir1.exists():
		Dest_Dir1.mkdir(parents=True, exist_ok=True)

	if not Dest_Dir2.exists():
		Dest_Dir2.mkdir(parents=True, exist_ok=True)

	# 克隆代码到dest_dir1
	cmd_clone1 = ["git", "clone", "-b", git_version, git_addr, str(Dest_Dir1)]
	print("运行命令:", " ".join(cmd_clone1))
	result1 = subprocess.run(cmd_clone1, capture_output=True, text=True)
	if result1.returncode != 0:
		print("Git 克隆命令失败:", result1.stderr)
		return False
	
	
	# 切换到指定的hash1
	cmd_checkout1 = ["git", "-C", str(Dest_Dir1), "checkout", git_hash1]
	print("运行命令:", " ".join(cmd_checkout1))
	result_checkout1 = subprocess.run(cmd_checkout1, capture_output=True, text=True)
	if result_checkout1.returncode != 0:
		print("Git checkout 命令失败:", result_checkout1.stderr)
		return False
	
	# 克隆代码到dest_dir2
	cmd_clone2 = ["git", "clone", "-b", git_version, git_addr,
		str(Dest_Dir2)]
	print("运行命令:", " ".join(cmd_clone2))
	result2 = subprocess.run(cmd_clone2, capture_output=True, text=True)
	if result2.returncode != 0:
		print("Git 克隆命令失败:", result2.stderr)
		return False
	# 切换到指定的hash2
	cmd_checkout2 = ["git", "-C", str(Dest_Dir2), "checkout", git_hash2]
	print("运行命令:", " ".join(cmd_checkout2))	
	result_checkout2 = subprocess.run(cmd_checkout2, capture_output=True, text=True)
	if result_checkout2.returncode != 0:
		print("Git checkout 命令失败:", result_checkout2.stderr)
		return False
	return True




def gitDiff(projectpath:str|Path, git_hash1:str, git_hash2:str)->list[str]:
	"""
	这两个路径是
	比较两个路径下的代码差异，返回差异文件列表.
	"""
	diff_files = []
	if not os.path.exists(projectpath):
		print(f"路径 {projectpath} 不存在.")
		return diff_files
	cmd = ["git", "-C", str(projectpath), "diff", "--name-only", git_hash1, git_hash2]
	result = subprocess.run(cmd, capture_output=True, text=True)
	if result.returncode != 0:
		print("Git diff 命令失败:", result.stderr)
		return diff_files
	diff_files = result.stdout.strip().split('\n')
	return [f for f in diff_files if f]  # 过滤掉空字符串

def filterCFiles(file_list:list[str])->list[str]:
	"""
	过滤出C源文件.
	"""
	c_files = [f for f in file_list if f.endswith('.c')]
	return c_files

