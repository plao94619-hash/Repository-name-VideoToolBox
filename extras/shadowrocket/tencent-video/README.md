# 腾讯视频广告拦截（Shadowrocket）

版本 **1.3.3**，更新日期 2026-10-03。保留既有广告过滤，并新增个人中心广告点击落地域名 `jump01.gw62.cn` 的精确 `REJECT` 规则。它会阻止打开该广告落地页；单凭点击链接无法确认或隐藏广告卡片本身。

## Safari 一键安装

请在已安装 Shadowrocket 的 iPhone 或 iPad 上用 Safari 打开：

[🚀 一键跳转 Shadowrocket 并安装](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Ftencent-video%2FTencent-Video-AdBlock-2026.module)

系统询问是否打开 Shadowrocket 时选择“打开”，然后确认安装或更新并启用模块。此模块沿用上一版的原始文件地址，可重复打开同一链接更新。

手动导入：[模块原始文件](https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/tencent-video/Tencent-Video-AdBlock-2026.module)

## 规则覆盖范围

| 截图位置 | 过滤目标 | 命中方式 |
| --- | --- | --- |
| 启动页开屏广告 | `mi.gdt.qq.com`、`splashqqlive.gtimg.com/website/<编号>` | 精确广告请求主机与开屏素材路径；新加主机待本次开屏日志验证 |
| 进入首页后的弹窗 | `news.l.qq.com/app?`、`wa.gtimg.com/adxcdn/*.jpg` 与 `adsmind.gdtimg.com` | 广告接口和素材路径 |
| 个人中心视频广告与点击跳转 | `video.dispatch.tc.qq.com/*.mp4`、`vmind.qqvideo.tc.qq.com/*.mp4`、`jump01.gw62.cn` | MP4素材路径过滤；精确域名拦截给定落地页访问，只阻止点击跳转，卡片仍需定位实际广告数据请求 |
| 腾讯 GDT 广告接口 | `mi.gdt.qq.com`、`c3.gdt.qq.com`、`v3.gdt.qq.com`、`xs.gdt.qq.com` | 精确主机匹配，默认 REJECT，可单独调整 |
| IACC 推荐接口 | `iacc.rec.qq.com` | 精确主机匹配，默认 REJECT，可单独调整 |
| 个人中心广告相关 L 域主机 | `c2.l.qq.com`、`p2.l.qq.com`、`livep2.l.qq.com` | 三个精确主机固定 `REJECT`，避免 TCP 流量被策略组转发 |

现有素材路径参考公开社区规则：[腾讯视频广告规则示例](https://github.com/bai1zi/shadowrocket-surge-loon-qx/blob/main/ADs.sgmodule#L2526-L2549)、[开屏资源规则示例](https://github.com/Masstone/Rules/blob/master/Dler%20Cloud#L2886-L2922)。腾讯广告官方[广告请求接口文档](https://developers.adnet.qq.com/doc/api/guide)将 `http://mi.gdt.qq.com/api/v3` 列为广告请求地址，并说明开屏广告位实时请求广告。此文档支持新增 `mi.gdt.qq.com` 规则，但这张截图对应的请求尚无新日志验证；IACC 与 L 域规则按你提供的流量记录精确添加。

## 日志确认的规则

你最新上传的数据库覆盖 11:27:52–13:18:25，共 10,149 条记录。`jump01.gw62.cn` 出现 3 次，均按现有 `DOMAIN-SUFFIX,cn,DIRECT` 规则直连，因此 v1.3.3 新增了该主机的精确 `REJECT`。完整落地链接包含点击跟踪参数，仓库只保存域名，不保存完整 URL 或参数。

同一日志的近段时间内，`xs.gdt.qq.com`、`pgdt.gtimg.cn`、`adsmind.gdtimg.com`、`c3.gdt.qq.com`、`v3.gdt.qq.com` 等请求已出现 `REJECT` 结果。`vr.gdt.qq.com` 也有直连记录；腾讯官方文档将该主机用于视频播放信息上报，因此不能仅凭域名出现在日志中就认定它提供了个人中心广告素材，本版不封它。参见[腾讯广告接口文档](https://developers.adnet.qq.com/doc/api/guide)。

Shadowrocket 这份数据库只记录主机、端口和路由结果，不含 HTTPS 请求路径、响应内容或广告素材 URL。新增规则可以阻止点击 `jump01.gw62.cn` 后打开广告落地页，但不等于隐藏已渲染的广告卡片。卡片仍显示，说明广告可能通过其他接口或缓存内容加载；需要在打开个人中心、卡片出现的同一时段捕获完整请求 URL，才能继续精确定位。日志数据库和点击参数没有上传到仓库。

## 启用 HTTPS 路径过滤

精确 URL 路径需要 Shadowrocket 解密相应 HTTPS 主机。模块的“启用精准HTTPS过滤”默认开启；请在你自己的 Shadowrocket 配置中开启 HTTPS 解密，并只安装、信任由该设备上的 Shadowrocket 生成的 CA 证书。

若不想使用 HTTPS 解密，或腾讯视频因此出现连接异常，可把“启用精准HTTPS过滤”改为 `false`。这样会停用路径级过滤，但 `[Rule]` 下全部精确主机规则仍按各自参数生效，包括 GDT、IACC 和本版新增的三条 L 域规则。

## 故障调整与范围

- 开屏、首页弹窗主机策略分别可改为 `DIRECT`。
- v1.3.3 的 `jump01.gw62.cn` 规则只阻止点击跳转。若个人中心卡片仍显示，需要抓取卡片显示时的广告请求，不要把此落地域名误当作素材请求。
- 若正常页面或播放异常，可临时删除对应的三条 L 域规则排查。
- 腾讯 GDT 规则只覆盖日志中的 `c3/v3/xs.gdt.qq.com` 和官方文档列出的 `mi.gdt.qq.com` 精确主机；IACC规则只覆盖 `iacc.rec.qq.com`；L 域规则只覆盖三个精确主机，未封锁整个 `qq.com`、`l.qq.com`、`gtimg.cn` 或 `gdtimg.com`。
- 腾讯视频可能改用其他广告接口或将广告与正片放在同一视频流中，因此不能保证去掉每一条广告；若广告仍出现，需要在广告展示的同一时段补充新的流量记录。

### 规则摘要

```ini
DOMAIN,iacc.qq.com,REJECT
DOMAIN,pgdt.gtimg.cn,REJECT
DOMAIN,splashqqlive.gtimg.com,REJECT
DOMAIN,mi.gdt.qq.com,REJECT
DOMAIN,adsmind.gdtimg.com,REJECT
DOMAIN,c3.gdt.qq.com,REJECT
DOMAIN,v3.gdt.qq.com,REJECT
DOMAIN,xs.gdt.qq.com,REJECT
DOMAIN,iacc.rec.qq.com,REJECT
DOMAIN,c2.l.qq.com,REJECT
DOMAIN,p2.l.qq.com,REJECT
DOMAIN,livep2.l.qq.com,REJECT
DOMAIN,jump01.gw62.cn,REJECT
```
