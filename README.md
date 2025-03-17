# Windows 脚本小工具

这里存放着我自制或仿制的在 windows 操作系统下的辅助脚本,
用于解决一些 windows 日常使用中的一些痛点.

> 默认测试环境为 Win 11 - 系统语言中文.

使用方法(uv):

```shell
git clone https://github.com/azazo1/windows_gadgets.git
cd windows_gadgets
uv tool install .
# 有些工具需要填写配置文件, 如果希望配置文件就在仓库克隆下来的文件夹路径, 请使用: uv tool install -e .
```

然后可以直接使用命令行启动对应的工具, 见 [pyproject.toml](pyproject.toml), 其中 g 开头的是不带命令行窗口的.

卸载方法:

```shell
uv tool uninstall windows_gadgets
```
