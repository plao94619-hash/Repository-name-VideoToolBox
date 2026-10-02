# 接口来源与验证范围

核查日期：2026-10-02

本目录的 JavaScript 为原始实现，沿用仓库 MIT License。下面的公开项目用于核实接口地址、字段名和配置方式，没有复制其整份模块或脚本，也没有运行上游远程脚本。

## 公众号接口

- [NobyDa / Script：Wechat.js](https://github.com/NobyDa/Script/blob/master/QuantumultX/File/Wechat.js)
  - 文件说明明确为“去除公众号文章底部广告”。
  - 核实 `mp.weixin.qq.com/mp/getappmsgad` 及 `advertisement_num`、`advertisement_info` 字段。
  - 本模块保留 `appid`，并添加格式、错误状态与体积检查。
- [zirawell / R-Store：微信模块](https://github.com/zirawell/R-Store/blob/dea5018c844e3486df872d6fb2207e3652e3d82b/Rule/Surge/Adblock/App/W/%E5%BE%AE%E4%BF%A1/wechat.sgmodule)
  - 本次核查的 main 提交为 `dea5018c844e3486df872d6fb2207e3652e3d82b`，该仓库最近提交时间为 2026-09-30；微信模块中标注日期为 2026-05-09。
  - 文件 blob：`376e201ee429c44d179dc59b5bd8763b89eb8e31`。
  - 核实专用 `/mp/advertisement` 与 `/mp/ad_` 接口。
  - 没有采用该上游封锁整个 `wxs.qq.com` 的规则，也没有引入解除微信安全跳转等其他功能。

## 小程序接口

- [R-Store：微信小程序通用模块](https://github.com/zirawell/R-Store/blob/dea5018c844e3486df872d6fb2207e3652e3d82b/Rule/Surge/Adblock/Applet/Wechat/%23/%E9%80%9A%E7%94%A8%E7%B1%BB/wechatAppletGeneral.sgmodule)
  - 文件 blob：`f48bbb0bccc55b7c0c706c289ff3dfd82455ba51`。
  - GitHub 返回的最近文件提交日期为 2026-04-21，提交 `59386d70ab42a79d6b8cff500256facbee9cf545`。
  - 核实 `wxsmsdy.video.qq.com` 广告视频域名、`/wapad/getaddata?action=getad`、`/wapad/reportaddata?action=exposure_report`。
  - 核实企迈 `marketing/canvas/advert`、`advertising/ad/advertiseInfo` 接口和美团 `queryPortalInfo` 的模块结构。
- [R-Store：qmai.js](https://github.com/zirawell/R-Store/blob/dea5018c844e3486df872d6fb2207e3652e3d82b/Res/Scripts/AntiAd/qmai.js)
  - 核实广告列表在 `data` 数组中，广告项包含 `detailInfo`。
  - 本实现仅在该专用接口中过滤识别到的广告项，保留未知项与响应的其他字段。

以上是维护中公开规则的接口依据，不是来自用户设备的抓包记录。接口沿用旧日期不等于失效，也不能凭公开规则就确认其在所有最新微信版本中仍可触发。

## 谱慧云开屏广告：实验补充模块

- 用户在本次对话上传谱慧云的全屏广告截图，以及 Shadowrocket 导出的连接日志。
  - 本地只读解析得到 573 条记录，时间范围为 2026-10-02 18:21:27 至 18:28:34（设备记录时间）。
  - `wxa.wxs.qq.com`、`wximg.wxs.qq.com`、`wxsmw.wxs.qq.com` 分别出现 1、13、6 条记录，原策略均为 `DIRECT`。19 条是 `域名:443` 连接，另 1 条是 HTTP 资源请求。
  - 日志表没有请求或响应正文，也没有小程序 appid，不能确认这 20 条均属于谱慧云广告，不能据此虚构谱慧云广告 API 或 JSON 字段。
  - 仓库只保存上述汇总、规则与说明，原始数据库、截图和含个人参数的完整 URL 没有发布。
- [AWAvenue-Ads-Rule：固定提交中的规则文件](https://github.com/TG-Twilight/AWAvenue-Ads-Rule/blob/99b020c21853cbed56b90456399dad6bde842309/AWAvenue-Ads-Rule.txt)
  - 本次读取的 main 提交为 `99b020c21853cbed56b90456399dad6bde842309`，提交日期 2026-09-21；文件标记版本 1.7.8-release，更新时间 2026-09-21 21:56:59 UTC+8。
  - 文件 blob：`8dc3bd72d74c3f925b09b37c778a818566ed072b`。
  - 核实三个域名均被列入该公开广告过滤规则。这里只将公开域名事实与本次日志交叉核对，没有引入整个第三方规则集。
- [217heidai/adblockfilters：微信图片不能正常加载，Issue #178](https://github.com/217heidai/adblockfilters/issues/178)
  - 直接用户反馈要求放行 `wximg.wxs.qq.com`，说明公开黑名单不能证明该域名只承载广告。
  - 因此本方案作为可单独启停的实验补充模块发布，不默认合并到微信主模块，不承诺正常图片完全不受影响。

实验模块使用精确 `DOMAIN` 规则，作用于整个微信，无法按谱慧云 appid 区分共享资源。没有启用额外 MITM，没有对 `wxs.qq.com` 整个后缀、微信 MMTLS 通道、登录或支付接口添加拒绝规则。离线回放命中 20 条候选连接，其余 553 条不匹配，其中 165 条 MMTLS 请求全部不匹配。尚未验证广告容器和倒计时是否消失，以及谱慧云的登录、余额、充值与用水功能。

## 朋友圈协议限制

- [Citizen Lab：Privacy in the WeChat Ecosystem，2023](https://citizenlab.ca/research/privacy-in-the-wechat-ecosystem-full-report/)
  - 研究指出，聊天、查看朋友圈及部分小程序通信使用专用 MMTLS 协议。
- [Citizen Lab：MMTLS 研究 FAQ，2024](https://citizenlab.ca/research/should-we-chat-too-security-analysis-of-wechats-mmtls-encryption-protocol/should-we-chat-too-faq/)
  - 研究说明，常规 TLS 网络分析工具不能直接处理 MMTLS，而且它包含独立的业务加密层。

据此，本模块没有把标准 HTTPS MITM 能力表述为 MMTLS 解密能力，没有添加假想的朋友圈 JSON 过滤接口。没有实现或验证 2026 年微信朋友圈的专用协议解密，因此不宣称支持朋友圈信息流广告。

## Shadowrocket 与安装链接

- [LOWERTOP / Shadowrocket 使用手册](https://github.com/LOWERTOP/Shadowrocket/wiki)
  - 本次访问的手册显示于 2026-09-11 更新。
  - 核查 `http-response`、`engine=jsc`、`%APPEND%`、`h2=true`、HTTP/2 MITM 的版本门槛及 `shadowrocket://install?module=`。
  - 这是维护者的社区手册；软件内具体功能仍以实际版本为准。
- [LOWERTOP / Shadowrocket-First：redirect.html](https://github.com/LOWERTOP/Shadowrocket-First/blob/main/redirect.html)
  - 本次读取源码确认：HTTPS 页面解析 url 参数后尝试自动跳转，并提供手动唤起按钮。
  - 复用此仓库现有 Shadowrocket 模块的安装跳转方式。iOS 可能要求确认“打开”；模块导入不能自动完成证书信任。

## 本次验证

- 46 项 Node.js 自动测试通过；样例为合成数据。
- 在无 Node 全局 API 的隔离上下文执行脚本，验证成功与异常路径都只调用一次 `$done`。
- 验证正常文章、支付、订单、核心微信与 MMTLS 地址不被 URL/脚本规则匹配。
- 发布前会将模块脚本地址固定到本仓库的已验证提交，并核对公开文件内容。
- **没有 iPhone、微信或 Shadowrocket 实机测试**，没有针对某个微信构建号的全面适配承诺。
