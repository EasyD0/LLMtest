import subprocess
## 单元1

def write_all_include_paths_rsp(root_dir: str, rsp_file: str):
	"""
	递归获取root_dir下所有子目录（含自身），以 -I"路径" 格式写入rsp响应文件。
	"""
	import os
	with open(rsp_file, 'w', encoding='utf-8') as f:
		for dirpath, dirnames, filenames in os.walk(root_dir):
			f.write(f'-I"{os.path.abspath(dirpath)}"\n')

def run_gcc_with_rsp(c_file: str, rsp_file: str, output: str = "a.exe"):
	"""
	使用响应文件和.c文件路径自动执行gcc编译命令。
	c_file: 要编译的C文件路径
	rsp_file: 响应文件路径
	output: 输出文件名，默认为a.exe
	"""
	cmd = ["gcc", "-E", f"@{rsp_file}", c_file, "-o", output]
	print("运行命令:", " ".join(cmd))
	result = subprocess.run(cmd, capture_output=True, text=True)
	print("stdout:\n", result.stdout)
	print("stderr:\n", result.stderr)
	return result.returncode



if __name__ == "__main__":
	# 示例用法
	root = "./include"  # 你要递归查找的根目录
	rsp = "include.rsp" # 响应文件名
	write_all_include_paths_rsp(root, rsp)
	print(f"已写入所有包含路径到 {rsp}")
	print(f"gcc 使用示例: gcc @include.rsp main.c -o main.exe")

## 单元2

