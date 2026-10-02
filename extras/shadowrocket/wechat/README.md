# 微信广告拦截合集（含谱慧云） · Shadowrocket

合集版本：1.2.0 · 主响应脚本：1.0.0 · 维护日期：2026-10-02

本合集将原微信广告模块与谱慧云开屏资源规则合并到 [WeChat-AdBlock-2026.module](WeChat-AdBlock-2026.module)。默认包含公众号、部分通用小程序、企迈、美团点餐及谱慧云广告规则，安装一个模块即可使用这些功能。原微信模块地址保持不变，已安装用户可以直接更新。

2026-10-02 是本次制作、检索与维护日期，不表示已经在所有当年微信版本上实机验证。谱慧云部分已有用户反馈拦截见效；广告容器和 5 秒倒计时是否一起消失尚未确认。

## Safari 一键安装合集

[点击或复制链接：打开 Shadowrocket 并安装微信广告拦截合集](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Fwechat%2FWeChat-AdBlock-2026.module)

在已安装 Shadowrocket 的 iPhone / iPad 上，复制该 HTTPS 链接，粘贴到 Safari 地址栏访问。页面会尝试自动唤起 Shadowrocket；系统提示“在 Shadowrocket 中打开”时选择“打开”，再确认模块导入或更新。如果系统阻止自动唤起，可点击页面上的“点击一键安装”。

安装或更新后：

1. 在当前配置的模块列表启用“微信广告拦截合集（含谱慧云）”。
2. 停用旧的“谱慧云开屏广告（实验）”独立模块；如果旧微信模块另有重复条目，也停用重复条目。这组微信广告功能只需启用合集。
3. 全局路由选择“配置”，重新连接 Shadowrocket，彻底退出微信后重新打开谱慧云。
4. 合集“编辑参数”中的“谱慧云资源策略”保持默认 `REJECT`，沿用此前已获用户见效反馈的三条资源拦截策略。

直接唤起地址：

```text
shadowrocket://install?module=https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/wechat/WeChat-AdBlock-2026.module
```

手动添加模块的原始地址：

```text
https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/wechat/WeChat-AdBlock-2026.module
```

手动路径：Shadowrocket → 配置 → 模块 → 右上角“＋”，粘贴原始地址。它是模块地址，应添加到“模块”。HTTPS 跳转页复用本仓库已有模块使用的 LOWERTOP 页面；模块和响应脚本由本仓库提供。

## 覆盖范围

| 场景 | 合集的行为 | 范围与限制 |
| --- | --- | --- |
| 公众号文章广告 | 清空 `getappmsgad` 响应中的已知广告数组与数量；拦截 `advertisement` 和 `ad_` 专用接口 | 保留 appid、阅读数、评论及其他字段；不保证去除作者自行写入正文的推广 |
| 通用微信小程序广告 | 拦截 `wapad/getaddata?action=getad` 及曝光上报；拦截已知广告视频资源域名 | 覆盖仍使用这些接口且流量经过 Shadowrocket 的广告，不代表全部小程序 |
| 企迈系点餐小程序 | 拦截专用画布广告接口；过滤专用广告接口内已知 `detailInfo` 结构 | 上游列举挪瓦咖啡、LINLEE、霸王茶姬、陈香贵等；具体小程序的当前接口仍需实机确认 |
| 美团系点餐小程序 | 过滤 `queryPortalInfo` 中 `advType === true` 的模块及 `float-window` | 保留其他菜单、导航、商品和未知结构 |
| 谱慧云开屏广告 | 默认拒绝 `wxa.wxs.qq.com`、`wximg.wxs.qq.com`、`wxsmw.wxs.qq.com` 的资源连接；用户已反馈这组规则拦截见效 | 共享域名规则作用于整个微信，可能影响其他图片；页面与倒计时的变化尚待确认 |
| 朋友圈信息流广告 | **不支持可靠过滤 MMTLS 中的朋友圈广告** | 没有实现 MMTLS 解密；共享资源拦截不能等同于删除朋友圈广告条目 |

有些旧规则把公众号的 `getappmsgad` 脚本命名为“朋友圈去广告”。它处理的实际地址属于公众号接口，不能据此宣称支持朋友圈信息流过滤。协议依据、公开规则及用户反馈见 [SOURCES.md](SOURCES.md)。

## 参数与局部停用

在 Shadowrocket → 配置 → 模块 → 点击合集 → 编辑参数，按需调整：

| 参数 | 默认值 | 用途 |
| --- | --- | --- |
| `启用HTTPS解密` | `true` | 开启公众号、企迈、美团等 HTTPS 重写和脚本所需的解密；需要信任自己的 CA |
| `谱慧云资源策略` | `REJECT` | 拦截三个共享资源域名；改为 `DIRECT` 可单独取消这部分拦截并让其直连 |

谱慧云三条域名规则不依赖 HTTPS 解密。关闭 HTTPS 解密后，这三条规则仍按资源策略执行；HTTPS URL 重写与响应脚本无法处理未解密的 HTTPS 流量。

如果正常图片或其他小程序资源加载异常，把“谱慧云资源策略”从 `REJECT` 改成 `DIRECT`，保存后重新连接。这样保留公众号及其他广告规则，取消这三个域名的拒绝策略。请先停用旧谱慧云独立模块，否则其中的静态 `REJECT` 规则仍可能拦截资源。

这三个域名由微信共享，无法按小程序名称或 appid 限定作用范围。`wximg.wxs.qq.com` 有公开的普通图片加载异常反馈；参数为 `REJECT` 时也可能影响其他图片、小程序资源或广告激励。合并到合集是按本次用户要求完成的，作用范围没有扩大到整个 `wxs.qq.com`、`weixin.qq.com` 或 `qq.com`。

## 首次使用 HTTPS 过滤：信任自己的 CA

谱慧云资源拦截不需要证书。公众号等 HTTPS 过滤需要 Shadowrocket 的可信任 CA；已经安装并信任的自己的 CA 可以继续复用。

建议使用最新 Shadowrocket；HTTP/2 MITM 至少需要 2.2.81。

1. 打开 Shadowrocket 的“配置”，确认当前选中的配置。
2. 点击该配置右侧的“ⓘ” → “HTTPS 解密” → “证书”。
3. 如果还没有可信任的 CA，生成新的 CA 并安装到本机。
4. 在 iOS“设置” → “通用” → “VPN 与设备管理”安装对应描述文件。
5. 在“设置” → “通用” → “关于本机” → “证书信任设置”，开启对应 Shadowrocket CA 的完全信任。
6. 回到 Shadowrocket，确认当前配置启用 HTTPS 解密及通过 HTTP/2 解密。
7. 合集“编辑参数”中的“启用HTTPS解密”保持 `true`。
8. 将全局路由设为“配置”，重新连接 Shadowrocket，再彻底退出并重新打开微信。

Safari 唤起导入不能替代 iOS 的证书安装和信任步骤。证书由自己的设备生成，模块不附带 CA、私钥或共享证书。

MITM 仅使用 `%APPEND%` 追加以下主机名，保留已有解密主机：

- `mp.weixin.qq.com`
- `webapi.qmai.cn`
- `miniapp.qmai.cn`
- `rms.meituan.com`

谱慧云资源域名没有加入 MITM。响应脚本不发起额外联网请求，不读取账号、不上传数据，不改写聊天、登录、支付或订单请求。

## 谱慧云规则的证据和限制

用户上传的日志共 573 条，覆盖 2026-10-02 18:21:27 至 18:28:34（设备记录时间）。其中 `wxa.wxs.qq.com`、`wximg.wxs.qq.com`、`wxsmw.wxs.qq.com` 分别有 1、13、6 条连接记录，原策略均为 `DIRECT`。19 条只显示 `域名:443`，另 1 条是 HTTP 资源请求；日志没有响应正文或小程序 appid。

公开广告规则也列出了这三个域名。用户在安装旧独立模块后反馈谱慧云广告拦截“确实起效果了”。该反馈说明用户当时的设备和配置下观察到效果；尚未区分素材、整个页面和 5 秒倒计时是否分别消失，也没有开关对照测试、后续抓包或登录、余额、充值、用水功能验证。

合集默认参数下沿用同样的三条拒绝策略。离线回放命中上述 20 条候选资源连接，其余 553 条不匹配这组规则，包括全部 165 条 `/mmtls/` 请求。这些是连接数，不是已确认的广告条数；回放本身只验证匹配范围。原始数据库、截图及含个人参数的 URL 没有发布到仓库。

## 旧独立模块兼容

[Puhuiyun-AdBlock-Experimental.module](Puhuiyun-AdBlock-Experimental.module) 保留原文件及地址，供已有用户继续使用。新安装或迁移到合集时，只需安装上方合集并停用旧独立模块。只想使用三个资源域名拦截规则的用户，也可以继续单独使用旧文件。

## 验证与更新

- 重新进入小程序或打开新文章观察效果；缓存素材或已有连接可能暂时继续显示。
- 在 Shadowrocket“数据” → “代理”开启日志，谱慧云资源域名默认应命中 `REJECT`；HTTPS 脚本接口应显示解密及对应处理。
- 看不到某个接口可能是缓存、改版、MMTLS 或流量没有经过当前配置。脚本对未知结构、HTML、JSONP、错误响应、二进制或超出上限的正文原样放行。
- 如果出现正常图片异常，先将谱慧云资源策略改为 `DIRECT` 并重新连接；其他问题可禁用合集对比。
- 不需要更换当前节点。合集不添加代理节点，也不指定微信必须走某个地区的出口。
- 更新模块列表中的本远程模块即可；原模块及安装链接地址保持不变。更新后检查自定义参数，已有参数可能保留。
- 响应脚本继续固定引用本仓库已验证提交。本次只合并资源规则并增加资源策略参数，响应脚本内容未变更。

开发验证：

```bash
node --test extras/shadowrocket/wechat/tests/wechat-ad-filter.test.cjs
```

原有 **46 项自动测试**覆盖响应字段保留、异常输入放行、URL 与脚本的匹配边界、查询参数顺序、未知结构保留、请求不被修改及 JSC 脚本上下文。合集另外检查默认参数与 `DIRECT` 参数展开、原独立模块规则等价性，以及日志回放范围。

自动测试使用合成样例；谱慧云实际见效证据来自用户对旧独立模块的反馈。没有作者直接操作 iPhone 或对新合集的独立实机重复测试，不承诺所有小程序广告或全部微信版本的拦截效果。
