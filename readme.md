## 导出环境
```shell
conda env export > environment.yml
```

## 使用yml部署环境
```shell
conda env create -f environment.yml
```

## 更新环境
```shell
conda env update -f environment.yml
```

## 安装clang python的方法
```
conda install python-clang libclang
```
