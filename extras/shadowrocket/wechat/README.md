# 微信广告拦截 · Shadowrocket

目录版本：1.1.1 · 主响应脚本：1.0.0 · 维护日期：2026-10-02

按本次能核实到的公开接口，为 Shadowrocket 编写的微信广告模块。2026-10-02 是本模块的制作、检索和维护日期，不表示已经在所有 2026 年微信版本上实机验证。

## 谱慧云开屏广告：实验补充模块

新增 [Puhuiyun-AdBlock-Experimental.module](Puhuiyun-AdBlock-Experimental.module)，根据用户上传的全屏广告截图、代理日志以及公开规则，尝试阻止三个候选微信广告资源域名的加载。它可以与下面的微信主模块同时启用，也可以单独停用。

**已有用户实机反馈：2026-10-02，用户确认谱慧云广告拦截“确实起效果了”。** 这确认了用户当前设备和配置下观察到拦截效果；尚未确认广告容器及 5 秒倒计时是否消失，也没有开关对照测试或后续抓包。本方案仍作为实验补充模块提供。

这三个域名由微信共享，规则会影响整个微信，无法按小程序名称或 appid 限定作用范围。`wximg.wxs.qq.com` 有公开的普通图片无法加载反馈，故该方案没有默认并入主模块；安装本补充模块才启用。

[Safari 一键安装谱慧云开屏广告实验补充模块](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Fwechat%2FPuhuiyun-AdBlock-Experimental.module)

直接唤起地址：

```text
shadowrocket://install?module=https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/wechat/Puhuiyun-AdBlock-Experimental.module
```

[手动导入地址](https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/wechat/Puhuiyun-AdBlock-Experimental.module)。本补充模块仅包含精确 `DOMAIN` 拒绝规则，**不需要安装 CA 或开启 HTTPS 解密**；主模块的 HTTPS 过滤仍有下文的证书要求。

| 候选资源域名 | 上传日志中的连接记录数 | 实验处理 |
| --- | ---: | --- |
| `wxa.wxs.qq.com` | 1 | 精确域名拒绝 |
| `wximg.wxs.qq.com` | 13 | 精确域名拒绝；可能影响其他图片 |
| `wxsmw.wxs.qq.com` | 6 | 精确域名拒绝 |

日志共 573 条，覆盖 2026-10-02 18:21:27 至 18:28:34（设备记录时间）。这 20 条记录在原配置中均为 `DIRECT`。这些数字是候选资源连接数，不是已经确认的广告条数；19 条仅显示 `域名:443`，没有 HTTP 路径或正文。日志表仅记录 URL、UA、规则、策略及时间，无法核实具体广告响应结构。

使用和验证：

1. 在 Safari 打开上面的实验补充模块链接，确认导入；保留已安装的微信主模块。
2. 在当前配置的模块列表启用“谱慧云开屏广告（实验）”，全局路由选择“配置”，重新连接 Shadowrocket。
3. 彻底退出微信后重新进入谱慧云，观察广告素材、整个广告页面、倒计时三个部分是否分别消失。
4. 查看新增连接日志，确认上述域名命中 `DOMAIN,<域名>,REJECT`。已缓存素材、已有连接、未经过 Shadowrocket 的流量以及其他广告域名不受这三条规则覆盖。
5. 如果正常图片、小程序资源加载异常，或激励广告功能不可用，单独关闭该实验补充模块并重新连接。主模块可以继续使用。

拦截资源后，广告页可能直接跳过，也可能保留空白、下载按钮或 5 秒倒计时；本次用户反馈尚未区分这些表现。本补充模块没有读取 MMTLS、修改原生界面或模拟点击“跳过”。它没有添加谱慧云登录、余额、充值、用水接口的过滤规则，也没有对这些功能做实机验证。

离线回放上传日志时，新增规则会命中上述 20 条候选连接，其他 553 条不匹配，其中 165 条 `/mmtls/` 请求均不匹配。回放本身只验证规则匹配范围，实际见效的证据来自上述用户反馈；广告页面及倒计时的变化仍待确认。原始数据库、截图及含个人参数的 URL 没有加入本仓库。

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
| 谱慧云开屏广告 | 可选实验补充模块拒绝 3 个候选微信资源域名；用户已反馈拦截见效 | 按域名影响整个微信，可能影响其他图片；页面与倒计时的变化尚待确认 |
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

在 Shadowrocket 的模块列表中更新相应远程模块即可。原微信主模块地址保持不变，谱慧云实验补充模块有独立地址。脚本 URL 固定引用本仓库经过本次测试的提交，以防脚本在模块未更新时发生变化；本次响应脚本内容未变更。

## 开发验证

```bash
node --test extras/shadowrocket/wechat/tests/wechat-ad-filter.test.cjs
```

已通过 **46 项自动测试**：响应字段保留、异常输入放行、广告与正常接口的匹配边界、查询参数顺序、未知结构保留、请求不被修改，以及不依赖 Node API 的脚本执行上下文。

这 46 项自动测试使用合成样例。谱慧云补充模块另有用户反馈，确认其当前设备和配置下拦截见效；没有作者直接操作 iPhone 或在独立设备上的重复实测。因此不承诺所有小程序广告或全部当前微信版本的拦截效果。
