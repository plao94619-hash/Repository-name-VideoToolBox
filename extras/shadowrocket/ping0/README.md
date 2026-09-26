# Ping0 Route Helper for Shadowrocket

此模块将 Ping0 流量经由 Shadowrocket 当前选中的 `PROXY` 策略，并默认仅对 `ping0.cc` 及其子域名启用 HTTPS 解密（MITM）。它与 TikTok 模块彼此独立。

> **隐私提示：**启用 MITM 后，Shadowrocket 可在本机解密匹配域名的 HTTPS 流量。Ping0 仍会看到所选代理出口的公网 IP；解密不会隐藏 IP，也不会让 Ping0 的服务端检测消失。仓库不包含 CA 证书，模块没有脚本或内容改写规则。

## Safari 一键安装

在装有 Shadowrocket 的 iPhone 或 iPad 上用 Safari 打开并点击：

[🚀 Safari 一键跳转 Shadowrocket 并安装 Ping0 模块](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Fping0%2FPing0.module)

iOS 会跳转到 Shadowrocket，并要求你确认导入。若模块已安装，可在模块页更新到新版本。

原始模块地址：

`https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/ping0/Ping0.module`

## 模块行为

模块仅增加以下路由规则：

```ini
DOMAIN-SUFFIX,ping0.cc,PROXY
```

它将 `ping0.cc` 及其子域名（包括 `ip.ping0.cc`）路由到 `PROXY`。如果你的代理策略组使用其他名称，请在模块中将 `PROXY` 改成该名称。

MITM 主机范围通过 `hostname = %APPEND%` 追加为 `ping0.cc` 和 `*.ping0.cc`，不会覆盖当前配置的其他解密主机。模块不读取、记录或修改请求内容，也不启用其他域名的解密。Shadowrocket 的本地请求日志可能显示解密后的请求信息；只在你信任 Ping0 服务和自己的证书时启用。

## 启用 HTTPS 解密

1. 在 Shadowrocket 中打开正在使用的配置，进入配置详情的 **HTTPS 解密**。
2. 在“证书”处生成你自己的 CA，并选择安装。不要安装仓库、网盘或他人发送的证书。
3. 按 iOS 提示安装描述文件，然后前往 **设置 → 通用 → 关于本机 → 证书信任设置**，对刚生成的 Shadowrocket CA 开启完全信任。
4. 返回 Shadowrocket，确认当前配置启用了 HTTPS 解密。
5. 打开本模块的 **编辑参数**，确认“启用HTTPS解密”为 `true`。该参数默认开启，主机列表仍限制在 Ping0 域名。
6. 保持全局路由为“配置”，重新连接 Shadowrocket 后访问 Ping0。

HTTPS 解密只对当前已开启解密的配置生效。更换配置后，需确认新配置也启用了 HTTPS 解密。部分客户端或连接可能使用证书固定等机制，无法保证都能解密。

### 关闭 MITM

如果不想解密 Ping0 流量，或访问时出现证书错误，在模块 **编辑参数** 中将“启用HTTPS解密”设为 `false`。Ping0 域名仍会按 `PROXY` 规则路由。

## Ping0 服务能力边界

本模块不会复制 Ping0 的 IP 风险数据库、全球探测节点或浏览器环境检测。它只负责 Shadowrocket 路由与所列主机的 HTTPS 解密；IP 查询、Ping、Trace、环境检测等服务仍由 [ping0.cc](https://ping0.cc/) 提供。
