# TikTok 网络隐私防护模块

面向 Shadowrocket 的增强隐私规则，采用“域名级遥测拦截 + HTTPS 解密 + 请求字段清理 + 全量代理路由”的分层方案。

## Safari 一键安装

> 请使用已安装 Shadowrocket 的 iPhone 或 iPad，并在 Safari 中打开本页面。

### [🚀 一键打开 Shadowrocket 并安装模块](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2FTikTok-Network-Privacy.module)

点击后，Safari 会通过 HTTPS 跳转页唤起 Shadowrocket。若系统询问是否在 Shadowrocket 中打开，请选择“打开”，然后确认安装或更新模块。

对应的 Shadowrocket URL Scheme：

```text
shadowrocket://install?module=https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/TikTok-Network-Privacy.module
```

## 本次增强内容

### 1. 网络出口保护

TikTok、TikTok CDN 与 ByteDance 国际版常用域名统一使用当前选定的 `PROXY` 策略，减少出口 IP 与节点地区不一致的情况。

### 2. 遥测端点拦截

模块拒绝一组明确的 `log`、`xlog`、`mon` 和 `rtlog` 域名。规则使用精确域名，没有直接封锁 `mssdk`、登录、验证码、视频、消息或风控服务，以降低功能损坏概率。

### 3. HTTPS 请求字段清理

模块对下列域名启用有限范围 MITM：

- `*.tiktok.com`
- `*.tiktokv.com`
- `*.byteoversea.com`
- `*.byteintlapi.com`

远程脚本会处理可安全修改的未签名文本请求，删除明确的：

- SIM、运营商、MCC/MNC、网络运营商及蜂窝地区字段
- IDFA、Advertising ID 等广告标识字段
- 经纬度等精确位置字段
- 客户端主动添加的 `X-Forwarded-For`、`X-Real-IP` 等 IP 转发头

为了保持 TikTok 可用性，脚本会主动跳过：

- 带 `X-Gorgon`、`X-Argus`、`X-Ladon` 等已知签名头的请求
- protobuf、图片、视频及其他二进制正文
- multipart 上传
- gzip、br、deflate 等压缩正文
- 超过模块正文读取上限的请求

脚本不会删除登录 Cookie、鉴权 Token、`device_id` 或 `install_id`，因为强行修改这些字段通常会造成登录失效、反复验证码或接口拒绝。

脚本固定引用经过测试的提交版本：

```text
https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/7ada97d08d939a5e6c754f99e500258a26636f80/extras/shadowrocket/scripts/tiktok-privacy-request.js
```

## 必须完成：安装并信任自己的 CA

只导入模块还不足以解密 HTTPS。请使用 **Shadowrocket 在你自己设备上生成的 CA**，不要安装别人发来的证书。

1. 在 Shadowrocket 中选择当前正在使用的配置。
2. 点击配置右侧的 `ⓘ`，进入“HTTPS 解密”。
3. 在“证书”中生成新的 CA 证书并选择安装。
4. 打开 iOS“设置”，安装刚下载的描述文件。
5. 前往“设置 → 通用 → 关于本机 → 证书信任设置”。
6. 为刚才由 Shadowrocket 生成的根证书开启完全信任。
7. 返回 Shadowrocket，确认当前配置的“HTTPS 解密”已经开启。
8. 打开模块的“编辑参数”，确认“启用HTTPS解密”为 `true`。
9. 将全局路由设为“配置”，重新连接 Shadowrocket，再彻底退出并重新打开 TikTok。

如果日志中的 TikTok HTTPS 请求显示 `MITM`，说明解密链路已经生效。部分 TikTok 请求可能使用证书固定或其他保护机制，不能保证全部流量都能被解密。

## 重要限制

本模块无法阻止 TikTok 在本机调用 iOS Core Telephony 或其他系统接口读取运营商信息。它能做的是：

- 减少常见遥测连接
- 清理能够被 Shadowrocket 解密、读取且安全修改的请求
- 避免明显的 SIM、运营商、广告标识和精确位置字段直接出现在这些请求中

它不能保证覆盖加密后的应用层数据、protobuf、带签名请求、新增域名、证书固定流量或服务器根据 IP、账号、时区、语言推断出的信息。因此这是一层网络隐私加固，不是“让 SIM 对 TikTok 完全不可见”。

如果需要设备层面更可靠的隔离，应使用没有 SIM/eSIM 配置的 Wi-Fi 设备，或者改用 TikTok 网页版。

## 安全提醒

- 只信任自己设备中由 Shadowrocket 生成的 CA。
- 不要从仓库、网盘、聊天消息或陌生网站安装别人提供的 CA/P12 证书。
- MITM 使 Shadowrocket 能在本机解密所列域名的 HTTPS 流量；不需要时应关闭 HTTPS 解密并取消根证书信任。
- 模块脚本不会上传、保存或输出请求正文，也不会把敏感字段写入日志。
- 远程脚本使用固定 Git 提交地址，避免脚本内容在模块不变时被静默替换。

## 手动导入

如果一键安装没有响应，请复制原始模块地址：

```text
https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/TikTok-Network-Privacy.module
```

进入 Shadowrocket 的“配置 → 模块”，点击右上角加号，粘贴地址并启用。

如果你的策略组不叫 `PROXY`，请将模块里的 `PROXY` 替换为自己的策略组名称。

## 故障排查

### TikTok 提示网络异常或无法登录

1. 在模块“编辑参数”中把“启用HTTPS解密”改为 `false`。
2. 重新连接 Shadowrocket 并重启 TikTok。
3. 如果恢复正常，说明该版本 TikTok 的部分连接不接受 MITM；可继续保留域名拦截和代理规则。
4. 如果仍然异常，再逐条停用模块顶部的 `REJECT` 规则排查。

### 模块已启用，但脚本没有生效

检查：

- 当前全局路由是否为“配置”
- 当前配置是否真的开启 HTTPS 解密
- CA 描述文件是否已经安装
- “证书信任设置”中是否开启完全信任
- 代理日志中目标请求是否显示 `MITM`
- 脚本 URL 是否成功下载

### 登录、验证码或播放异常

先关闭 MITM 参数，不要立即删除整个模块。这样仍能保留代理路由和遥测域名拦截。

## 文件校验

```text
TikTok-Network-Privacy.module
SHA-256: 4b3fb324096b9bf9529941c2fc555c993b0e6af300a0c434666b0d6bacbbf376

scripts/tiktok-privacy-request.js
SHA-256: d323f330326fd0e6977381e3e4bdb963e6f3c1dcc007409979769a623ffaafe0
```

TikTok 可能随版本调整域名、请求签名和参数结构，模块需要结合 Shadowrocket 请求日志定期维护。
