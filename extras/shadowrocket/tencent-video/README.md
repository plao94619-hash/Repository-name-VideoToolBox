# 腾讯视频广告拦截（Shadowrocket）

版本 **1.3.0**，更新日期 2026-10-03。此版保留开屏、首页弹窗、GDT/IACC 与个人中心视频路径规则，并新增日志中与个人中心广告卡片同一时段仍按 `qq.com` 的 `DIRECT` 规则放行的 `c2.l.qq.com`、`p2.l.qq.com`、`livep2.l.qq.com` 精确拦截；没有封锁整个 `l.qq.com` 或 `qq.com`。

## Safari 一键安装

请在已安装 Shadowrocket 的 iPhone 或 iPad 上用 Safari 打开：

[🚀 一键跳转 Shadowrocket 并安装](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Ftencent-video%2FTencent-Video-AdBlock-2026.module)

系统询问是否打开 Shadowrocket 时选择“打开”，然后确认安装或更新并启用模块。此模块沿用上一版的原始文件地址，可重复打开同一链接更新。

手动导入：[模块原始文件](https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/tencent-video/Tencent-Video-AdBlock-2026.module)

## 规则覆盖范围

| 截图位置 | 过滤目标 | 命中方式 |
| --- | --- | --- |
| 启动页开屏广告 | `splashqqlive.gtimg.com/website/<编号>` | 精确 URL 路径，并有单独的开屏域名策略 |
| 进入首页后的弹窗 | `news.l.qq.com/app?`、`wa.gtimg.com/adxcdn/*.jpg` 与 `adsmind.gdtimg.com` | 广告接口和素材路径 |
| 个人中心视频广告卡片 | `video.dispatch.tc.qq.com/*.mp4`、`vmind.qqvideo.tc.qq.com/*.mp4` | 仅拦截对应 MP4 路径 |
| 腾讯 GDT 广告接口 | `c3.gdt.qq.com`、`v3.gdt.qq.com`、`xs.gdt.qq.com` | 精确主机匹配，默认 REJECT，可单独调整 |
| IACC 推荐接口 | `iacc.rec.qq.com` | 精确主机匹配，默认 REJECT，可单独调整 |
| 个人中心广告相关 L 域主机 | `c2.l.qq.com`、`p2.l.qq.com`、`livep2.l.qq.com` | 只拦截日志中出现的三个精确主机，默认 REJECT，可单独调整 |

路径写法参考了公开社区规则中的腾讯视频素材与页面过滤条目：[腾讯视频广告规则示例](https://github.com/bai1zi/shadowrocket-surge-loon-qx/blob/main/ADs.sgmodule#L2526-L2549)、[开屏资源规则示例](https://github.com/Masstone/Rules/blob/master/Dler%20Cloud#L2886-L2922)、[GDT 域规则示例](https://github.com/SukkaW/Clash-Rules/blob/master/clash_rules)。这些是社区维护的规则，不是腾讯官方接口文档；IACC 推荐接口项按本次流量记录精确添加。

## 日志确认的规则

此前提供的数据库在 10:40–10:42 这个筛选窗口内实际只记录到 **10:40:44**，共 64 条记录；其中 `iacc.qq.com` 出现 5 次，`pgdt.gtimg.cn` 出现 12 次。这两条精确域名继续默认拒绝。

另一份个人中心广告卡片显示时段的日志中，`c3.gdt.qq.com`、`v3.gdt.qq.com`、`xs.gdt.qq.com`、`iacc.rec.qq.com`、`c2.l.qq.com`、`p2.l.qq.com` 和 `livep2.l.qq.com` 都曾按通用 `DOMAIN-SUFFIX,qq.com,DIRECT` 规则直连。v1.2.1 已加入前四个精确主机；v1.3.0 再加入后三个精确主机。日志仅记录主机与路由结果，不能单凭它确认具体哪个主机承载了广告素材，因此保持精确拦截，不扩展为整个 `l.qq.com`。

这些流量记录早于 v1.2.1 发布，不能作为 v1.2.1 或 v1.3.0 的更新后命中验证。日志数据库和请求参数没有上传到仓库；要确认本次更新是否生效，需要在更新模块后重新打开个人中心并查看新日志。

## 启用 HTTPS 路径过滤

精确 URL 路径需要 Shadowrocket 解密相应 HTTPS 主机。模块的“启用精准HTTPS过滤”默认开启；请在你自己的 Shadowrocket 配置中开启 HTTPS 解密，并只安装、信任由该设备上的 Shadowrocket 生成的 CA 证书。

若不想使用 HTTPS 解密，或腾讯视频因此出现连接异常，可把“启用精准HTTPS过滤”改为 `false`。这样会停用路径级过滤，但 `[Rule]` 下全部精确主机规则仍按各自参数生效，包括 GDT、IACC 和本版新增的三条 L 域规则。

## 故障调整与范围

- 开屏、首页弹窗主机策略分别可改为 `DIRECT`。
- 如果个人中心卡片或正常视频播放异常，先把“启用精准HTTPS过滤”改为 `false`，再测试。
- 腾讯 GDT 规则只覆盖日志中出现的三个主机，IACC规则只覆盖 `iacc.rec.qq.com`；L 域规则只覆盖三个精确主机，未封锁整个 `qq.com`、`l.qq.com`、`gtimg.cn` 或 `gdtimg.com`。
- 腾讯视频可能改用其他广告接口或将广告与正片放在同一视频流中，因此不能保证去掉每一条广告；若广告仍出现，需要在广告展示的同一时段补充新的流量记录。
- 已加载的广告卡片和素材可能由客户端缓存；更新规则不会清除本地缓存。清理腾讯视频缓存、强制退出后再复测。

### 规则摘要

```ini
DOMAIN,iacc.qq.com,REJECT
DOMAIN,pgdt.gtimg.cn,REJECT
DOMAIN,splashqqlive.gtimg.com,REJECT
DOMAIN,adsmind.gdtimg.com,REJECT
DOMAIN,c3.gdt.qq.com,REJECT
DOMAIN,v3.gdt.qq.com,REJECT
DOMAIN,xs.gdt.qq.com,REJECT
DOMAIN,iacc.rec.qq.com,REJECT
DOMAIN,c2.l.qq.com,REJECT
DOMAIN,p2.l.qq.com,REJECT
DOMAIN,livep2.l.qq.com,REJECT
```
