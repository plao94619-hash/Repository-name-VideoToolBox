# 微信广告拦截 · Shadowrocket

版本：1.0.0 · 维护日期：2026-10-02

按本次能核实到的公开接口，为 Shadowrocket 编写的微信广告模块。2026-10-02 是本模块的制作、检索和维护日期，不表示已经在所有 2026 年微信版本上实机验证。

## Safari 一键安装

[点击打开 Shadowrocket 并导入模块](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Fwechat%2FWeChat-AdBlock-2026.module)

复制上面的 HTTPS 链接，粘贴到 iPhone / iPad 的 Safari 地址栏并访问。页面会尝试自动唤起 Shadowrocket；如果 Safari 提示“在 Shadowrocket 中打开”，请选择“打开”，再确认模块导入。系统若阻止页面自动唤起，可点击页面上的“点击一键安装”。

直接唤起地址：

```text
shadowrocket://install?module=https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/wechat/WeChat-AdBlock-2026.module
```

手动添加模块的原始地址：

```text
https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/wechat/WeChat-AdBlock-2026.module
```

手动路径：Shadowrocket → 配置 → 模块 → 右上角“＋”，粘贴原始地址。它是模块地址，应添加到“模块”，不是服务器订阅。

HTTPS 跳转页复用此仓库现有模块使用的 LOWERTOP 页面。模块和响应脚本由本仓库提供；直接唤起地址不需要该跳转页。

## 实际覆盖范围

| 场景 | 本模块的行为 | 范围与限制 |
| --- | --- | --- |
| 公众号文章广告 | 清空 `getappmsgad` 响应中的已知广告数组与数量；拦截 `advertisement` 和 `ad_` 专用接口 | 保留 appid、阅读数、评论及其他字段；不保证去除正文中作者自行写入的推广 |
| 通用微信小程序广告 | 拦截 `wapad/getaddata?action=getad` 及曝光上报；拦截已知广告视频资源域名 | 只覆盖仍使用这些接口、且流量经过 Shadowrocket 的广告；不代表全部小程序 |
| 企迈系点餐小程序 | 拦截专用画布广告接口；过滤专用广告接口内已知 `detailInfo` 结构 | 上游列举挪瓦咖啡、LINLEE 林里柠檬茶、霸王茶姬、陈香贵等，具体小程序是否继续使用该接口需要实机确认 |
| 美团系点餐小程序 | 过滤 `queryPortalInfo` 中 `advType === true` 的模块及 `float-window` | 保留其他菜单、导航、商品和未知结构 |
| 朋友圈信息流广告 | **不支持可靠过滤 MMTLS 中的朋友圈广告** | 普通 HTTPS MITM / JSON 脚本无法读取这种协议的内容，本模块未实现 MMTLS 解密 |

有些旧规则将公众号的 `getappmsgad` 脚本命名为“朋友圈去广告”。它处理的实际地址属于公众号接口，不能据此宣称已经过滤朋友圈信息流。协议依据与上游接口来源见 [SOURCES.md](SOURCES.md)。

## 首次使用：开启 HTTPS 解密

建议使用最新 Shadowrocket；HTTP/2 MITM 至少需要 2.2.81。手机上已经安装并信任自己的 Shadowrocket CA 时，可以直接复用它。

1. 打开 Shadowrocket 的“配置”，确认当前选中的配置。
2. 点击该配置右侧的“ⓘ” → “HTTPS 解密” → “证书”。
3. 如果还没有可信任的 CA，生成新的 CA 并安装到本机。
4. 在 iOS“设置” → “通用” → “VPN 与设备管理”安装对应描述文件。
5. 在“设置” → “通用” → “关于本机” → “证书信任设置”，开启对应 Shadowrocket CA 的完全信任。
6. 回到 Shadowrocket，确认当前配置启用 HTTPS 解密，以及通过 HTTP/2 解密。
7. 确认本模块已经启用；“编辑参数”中的“启用HTTPS解密”保持 `true`。
8. 将“全局路由”设为“配置”，重新连接 Shadowrocket，再彻底退出并重新打开微信。

Safari 唤起导入模块无法替代 iOS 的证书安装与信任步骤。证书由你自己的设备生成；模块不附带任何 CA、私钥或共享证书。

MITM 主机名只追加：

- `mp.weixin.qq.com`
- `webapi.qmai.cn`
- `miniapp.qmai.cn`
- `rms.meituan.com`

该模块用 `%APPEND%` 保留已有解密主机名。没有封锁整个 `wxs.qq.com`、`weixin.qq.com` 或 `qq.com`，没有改写聊天、支付、登录或订单接口。响应脚本不发起额外联网请求，不读取账号、不上传数据。

## 验证效果与排查

- 用新打开的公众号文章或重新进入的小程序观察效果，已缓存的广告可能继续显示。
- 在 Shadowrocket“数据” → “代理”开启日志，检查匹配接口是否显示 `MITM`、URL 重写或对应脚本。
- 如果看不到该接口，可能是缓存、接口改版、MMTLS，或当前配置绕过了该流量；不能仅靠增加宽泛封锁域名解决。
- 如果启用模块后某个小程序出现功能异常，先禁用本模块并重新连接，对比是否恢复。
- 微信和小程序接口会变化。对没有识别到的响应、HTML、JSONP、错误响应、二进制正文或超出读取上限的正文，脚本原样放行。
- 不需要更换当前节点。本模块不添加代理节点，也不指定微信必须走哪个地区的出口。

## 更新

在 Shadowrocket 的模块列表中更新此远程模块即可。模块地址保持不变，脚本 URL 固定引用本仓库经过本次测试的提交，以防脚本在模块未更新时发生变化。

## 开发验证

```bash
node --test extras/shadowrocket/wechat/tests/wechat-ad-filter.test.cjs
```

已通过 **46 项自动测试**：响应字段保留、异常输入放行、广告与正常接口的匹配边界、查询参数顺序、未知结构保留、请求不被修改，以及不依赖 Node API 的脚本执行上下文。

这些测试使用合成样例；本次没有访问你的 iPhone，也没有在真实微信或 Shadowrocket 上实机测试。因此不承诺所有小程序广告或全部当前微信版本的拦截效果。
