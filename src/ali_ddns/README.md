# 阿里云 DDNS 脚本

启动之后会在脚本运行目录产生文件 `ali-ddns-config.toml`, 请按照文件内的注释填写配置.

第二次运行脚本即可更新域名解析.

> 如果 ali-ddns-config.toml 中的 ROUTINE 值设置为 python int 值且大于 0,
> 那么脚本会每 ROUTINE 秒请求一次更新域名解析.
> 其他情况下, 脚本只会请求一次更新域名解析然后退出.

参考文章: [实现阿里云域名的DDNS](https://developer.aliyun.com/article/1328033)