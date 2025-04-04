# 转发 url

此工具适合简单地通过特定的 proxy 转发特定 url 请求.

## 使用

启动脚本 `forwardurlproxy` 或者 `gforwardurlproxy` 后,
访问网址:

```text
http://localhost:40211?url=<quoted_url>&proxy=<proxy_url>
```

即可使用代理访问网址, 其中:
- `<quoted_url>`: 百分号编码之后的 url.
- `<proxy_url>`: 百分号编码之后的代理的地址, 比如 `http://localhost:7890` 或者 `socks5://localhost:7890` 进行百分号编码.

## 启动参数

- `--port`: 调整监听端口号.
