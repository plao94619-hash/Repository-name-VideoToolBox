# 腾讯视频广告拦截（Shadowrocket）

版本 1.0.0，依据你提供的 2026-10-03 流量记录制作。日志筛选窗口为 10:40–10:42；数据库中实际记录到 **10:40:44**，窗口内共 64 条记录。日志没有提交到仓库。

## Safari 一键安装

请在已安装 Shadowrocket 的 iPhone 或 iPad 上用 Safari 打开：

[🚀 一键跳转 Shadowrocket 并安装](${install})

系统询问是否打开 Shadowrocket 时选择“打开”，再确认安装并启用模块。

手动导入：[模块原始文件](${raw})

## 规则范围

| 精确域名 | 默认策略 | 依据 |
| --- | --- | --- |
| `iacc.qq.com` | `REJECT` | 该时间段记录到 5 次请求；腾讯视频客户端流量中出现。 |
| `pgdt.gtimg.cn` | `REJECT` | 该时间段记录到 12 次请求；腾讯视频客户端流量中出现。 |

这两个精确域名也出现在公开的社区广告规则集合中；该资料是社区维护的规则，不是腾讯官方接口说明。参考：[Hackl0us 国内网站广告追踪屏蔽规则](https://github.com/Hackl0us/SS-Rule-Snippet/blob/master/%E8%A7%84%E5%88%99%E7%89%87%E6%AE%B5%E9%9B%86/%E8%87%AA%E9%80%89%E8%A7%84%E5%88%99%E9%9B%86/%E5%9B%BD%E5%86%85%E7%BD%91%E7%AB%99%E5%B9%BF%E5%91%8A%E8%BF%BD%E8%B8%AA%E5%B1%8F%E8%94%BD.txt)；另见 [TencentVideo 分流规则](https://clashios.app/rule/tencentvideo)。

## 调整与限制

模块只拒绝上表中的两个主机，不匹配整个 `qq.com` 或 `gtimg.cn`，也不加入播放器、视频 CDN、会员或支付域名。由于 Shadowrocket 的这类规则按主机名匹配，`pgdt.gtimg.cn` 也可能被其他腾讯应用使用。

如果腾讯视频启动、播放或图片加载异常，在 Shadowrocket 中编辑模块参数，将对应的“腾讯广告接口策略”或“腾讯广告素材策略”改为 `DIRECT`，然后重新测试。广告也可能由视频播放接口或其他共享域名返回，所以不能保证移除所有开屏、贴片或信息流广告；若广告仍出现，应根据新的广告时段日志再添加经确认的精确域名。

### 当前规则

```ini
DOMAIN,iacc.qq.com,REJECT
DOMAIN,pgdt.gtimg.cn,REJECT
```
