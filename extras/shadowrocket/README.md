# TikTok 网络隐私防护模块

适用于 Shadowrocket 的无 MITM 网络层隐私规则。

## Safari 一键安装

> 请使用已安装 Shadowrocket 的 iPhone 或 iPad，并在 Safari 中打开本页面。

### [🚀 一键打开 Shadowrocket 并安装模块](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2FTikTok-Network-Privacy.module)

点击后，Safari 会通过 HTTPS 跳转页唤起 Shadowrocket。若系统弹出“在 Shadowrocket 中打开”，请选择“打开”；进入 Shadowrocket 后确认安装模块。

对应的 Shadowrocket URL Scheme：

```text
shadowrocket://install?module=https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/TikTok-Network-Privacy.module
```

## 功能

- 强制 TikTok 与 ByteDance 国际版常用域名通过当前选定代理节点访问。
- 拒绝部分常见日志和监控端点。
- 使用 TikTok / Musical.ly User-Agent 规则补充匹配。
- 不安装 HTTPS 解密证书，不读取或修改请求正文。

## 重要限制

Shadowrocket 只能控制网络请求。本模块不能阻止 TikTok 在设备本机通过 iOS API 读取 SIM、运营商、MCC/MNC 等信息，也不能保证阻止这些信息通过未覆盖的新域名或主要业务接口上传。

如果需要从设备层面避免 SIM 信息可用，应使用没有 SIM/eSIM 配置的 Wi-Fi 设备，或改用网页版。不要相信宣称仅靠代理规则即可“100% 屏蔽 SIM 读取”的配置。

## 手动导入

如果一键安装没有响应，请复制下面的原始模块地址：

```text
https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/TikTok-Network-Privacy.module
```

然后进入 Shadowrocket 的“配置 → 模块”，点击右上角加号，粘贴地址并启用。最后将全局路由设为“配置”，并选择需要使用的代理节点。

如果配置中的策略组不叫 `PROXY`，请将模块中的 `PROXY` 替换为自己的策略组名称。

## 故障排查

如果出现登录、验证码、上传或播放异常：

1. 暂时停用模块，确认问题是否由规则造成。
2. 依次移除文件顶部的 `REJECT` 规则。
3. 保留 `PROXY` 域名规则，重新启动 TikTok 测试。

TikTok 可能调整服务域名，规则需要根据 Shadowrocket 请求日志定期维护。
