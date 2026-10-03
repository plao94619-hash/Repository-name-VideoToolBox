# 腾讯视频广告拦截（Shadowrocket）

版本 **1.3.2**，更新日期 2026-10-03。保留个人中心三条固定 `REJECT` 主机，并新增 `mi.gdt.qq.com` 精确规则，用于覆盖腾讯广告官方文档列出的广告请求接口，作为启动页开屏广告候选项。

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
| 个人中心视频广告卡片 | `video.dispatch.tc.qq.com/*.mp4`、`vmind.qqvideo.tc.qq.com/*.mp4` | 仅拦截对应 MP4 路径 |
| 腾讯 GDT 广告接口 | `mi.gdt.qq.com`、`c3.gdt.qq.com`、`v3.gdt.qq.com`、`xs.gdt.qq.com` | 精确主机匹配，默认 REJECT，可单独调整 |
| IACC 推荐接口 | `iacc.rec.qq.com` | 精确主机匹配，默认 REJECT，可单独调整 |
| 个人中心广告相关 L 域主机 | `c2.l.qq.com`、`p2.l.qq.com`、`livep2.l.qq.com` | 三个精确主机固定 `REJECT`，避免 TCP 流量被策略组转发 |

现有素材路径参考公开社区规则：[腾讯视频广告规则示例](https://github.com/bai1zi/shadowrocket-surge-loon-qx/blob/main/ADs.sgmodule#L2526-L2549)、[开屏资源规则示例](https://github.com/Masstone/Rules/blob/master/Dler%20Cloud#L2886-L2922)。腾讯广告官方[广告请求接口文档](https://developers.adnet.qq.com/doc/api/guide)将 `http://mi.gdt.qq.com/api/v3` 列为广告请求地址，并说明开屏广告位实时请求广告。此文档支持新增 `mi.gdt.qq.com` 规则，但这张截图对应的请求尚无新日志验证；IACC 与 L 域规则按你提供的流量记录精确添加。

## 日志确认的规则

最新数据库显示，个人中心相关的 GDT/IACC 请求已命中 `REJECT`；三个 L 域主机也已命中规则，但 `p2.l.qq.com` 的部分 TCP 请求仍经 `PROXY`，因此 v1.3.1 将这三条规则固定为 `REJECT`。

这份数据库截至 12:55:26，早于本次开屏截图；其中没有 `splashqqlive.gtimg.com` 或 `mi.gdt.qq.com` 的对应请求。v1.3.2 按腾讯广告官方文档增加 `mi.gdt.qq.com` 精确规则作为候选项，是否命中这次开屏仍需新日志确认。

数据库只记录主机名、端口和路由结果，不含 HTTPS 请求路径、响应内容或广告素材 URL。`rdelivery.qq.com`、`pbaccess.video.qq.com`、`vv6.video.qq.com` 等其他主机仍有直连记录，但可能承担视频或页面功能；缺少请求路径时，不把它们直接列为广告拦截域名。日志数据库和请求参数没有上传到仓库。

## 启用 HTTPS 路径过滤

精确 URL 路径需要 Shadowrocket 解密相应 HTTPS 主机。模块的“启用精准HTTPS过滤”默认开启；请在你自己的 Shadowrocket 配置中开启 HTTPS 解密，并只安装、信任由该设备上的 Shadowrocket 生成的 CA 证书。

若不想使用 HTTPS 解密，或腾讯视频因此出现连接异常，可把“启用精准HTTPS过滤”改为 `false`。这样会停用路径级过滤，但 `[Rule]` 下全部精确主机规则仍按各自参数生效，包括 GDT、IACC 和本版新增的三条 L 域规则。

## 故障调整与范围

- 开屏、首页弹窗主机策略分别可改为 `DIRECT`。
- v1.3.1 后若卡片仍在，先清除腾讯视频缓存并完全退出再复测；若正常页面或播放异常，可临时删除对应的三条 L 域规则排查。
- 腾讯 GDT 规则只覆盖日志中出现的三个主机，IACC规则只覆盖 `iacc.rec.qq.com`；L 域规则只覆盖三个精确主机，未封锁整个 `qq.com`、`l.qq.com`、`gtimg.cn` 或 `gdtimg.com`。
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
```
