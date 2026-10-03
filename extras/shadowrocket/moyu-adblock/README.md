# 墨鱼去广告：规则来源目录

## Shadowrocket 一键安装

- [Safari 一键安装「墨鱼去广告」](https://lowertop.github.io/Shadowrocket-First/redirect.html?url=shadowrocket%3A%2F%2Finstall%3Fmodule%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2Fplao94619-hash%2FRepository-name-VideoToolBox%2Fmain%2Fextras%2Fshadowrocket%2Fmoyu-adblock%2FMoyu-AdBlock.module)
- [查看 Shadowrocket 模块源文件](https://raw.githubusercontent.com/plao94619-hash/Repository-name-VideoToolBox/main/extras/shadowrocket/moyu-adblock/Moyu-AdBlock.module)

在 iPhone Safari 打开安装链接，按提示跳转到 Shadowrocket 并确认安装。模块文件位于 `extras/shadowrocket/moyu-adblock/Moyu-AdBlock.module`。

## 模块覆盖范围与使用要求

- 当前版本包含 **148 条 `[URL Rewrite]` 规则**（147 条请求拦截 + 1 条 YouTube 302 重写）、**22 条 `[Rule]` 域名/IP 拒绝规则**，以及 **53 条 JSON jq 正文规则**。
- `[Body Rewrite]` 另含 3 条正则替换规则（共 9 组替换）：微信图文广告响应、部分小程序响应和掌上公交响应。微信读书保留 1 条 Shadowrocket `[Script]` 响应脚本规则，脚本由上游地址远程加载。
- 本次覆盖 21 个 `AdBlock` 配置文件，以及知乎、贴吧、起点、微信读书和滴滴等 5 个补充配置。QX 的 `jsonjq-response-body`、URL 302、域名和 IP 拒绝语法已转换为 Shadowrocket 对应格式。
- 这不是主页 42 项功能的完整移植。依赖 Quantumult X 专用 JavaScript API 的脚本规则、完整「墨鱼去开屏 2.0」及失效条目仍未并入；小程序脚本中一个空字符串替换也未转换。WeRead 脚本保留了上游 `.sgmodule` 格式，但尚未在设备上验证。
- Shadowrocket 全局路由设为“配置”模式；在当前配置启用 HTTPS 解密，并安装、信任 Shadowrocket CA 证书。正文重写和脚本规则需要 HTTPS 解密；模块使用 `%APPEND%` 追加主机名。应用证书固定或版本变化可能令个别规则失效，详见 [Shadowrocket 使用手册](https://lowertop.github.io/Shadowrocket/)。

上游仓库没有统一开源许可证；主页另声明禁止公众号/自媒体转载或发布其内容。模块按组保留来源链接，但规则语法转换不等于取得再分发授权；公开推广或二次发布前请核对对应源文件说明并取得必要许可。

本目录按 [ddgksf2013 的 GitHub 主页](https://github.com/ddgksf2013/ddgksf2013)「广告屏蔽」栏目整理，共 42 项。每条链接都指向原作者或页面所列的上游来源；本文件只保存名称、来源、贡献者与页面状态，不复制或托管上游规则源码。



## 上游页面列出的 42 项

| # | 页面名称 | 上游文件 / 页面 | 页面注明的贡献者或状态 |
|---:|---|---|---|
| 1 | 微信小程序去广告 | [Applet.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/Applet.conf) | ddgksf2013；脚本配置 |
| 2 | 墨鱼去开屏 2.0 | [StartUpAds.conf](https://ddgksf2013.top/rewrite/StartUpAds.conf) | ddgksf2013 |
| 3 | YouTube 广告屏蔽 | [YoutubeAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/YoutubeAds.conf) | divineEngine、Maasea；页面还注明画中画与后台播放 |
| 4 | 公众号图文去广告 | [WeChat.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/WeChat.conf) | 页面已划除，并注明无法去除朋友圈广告 |
| 5 | 知乎去广告 | [zheye.snippet](https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/script/zheye/zheye.snippet) | blackmatrix7 |
| 6 | 百度贴吧去广告 | [tieba-qx.conf](https://github.com/app2smile/rules/raw/master/module/tieba-qx.conf) | app2smile |
| 7 | 百度网盘去广告 | [bdpan.ads.js](https://ddgksf2013.top/scripts/bdpan.ads.js) | ddgksf2013；JavaScript |
| 8 | 喜马拉雅去广告 | [Ximalaya.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/Ximalaya.conf) | ddgksf2013 |
| 9 | 小红书去水印 | [XiaoHongShuAds.conf](https://ddgksf2013.top/rewrite/XiaoHongShuAds.conf) | ddgksf2013；去水印，不是单纯广告过滤 |
| 10 | Keep 超级净化 | [KeepAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/KeepAds.conf) | ddgksf2013 |
| 11 | Pixiv 去广告 | [pixivAds.js](https://github.com/ddgksf2013/Scripts/raw/master/pixivAds.js) | ddgksf2013；JavaScript |
| 12 | 酷安去广告 | [coolapk.js](https://github.com/ddgksf2013/Scripts/raw/master/coolapk.js) | ddgksf2013；JavaScript |
| 13 | 12306 去广告 | [12306.js](https://github.com/ddgksf2013/Scripts/raw/master/12306.js) | ddgksf2013；JavaScript |
| 14 | 多多视频去广告 | [rrtv_json.js](https://raw.githubusercontent.com/ddgksf2013/Scripts/master/rrtv_json.js) | 页面标注未适配新版并划除 |
| 15 | 微博轻享版去广告 | [WeiboAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/WeiboAds.conf) | ddgksf2013 |
| 16 | 高德地图去广告 | [AmapAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/AmapAds.conf) | ddgksf2013；页面注明卸载重装 |
| 17 | 网易云去广告 | [NeteaseAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/NeteaseAds.conf) | ddgksf2013 |
| 18 | 菜鸟裹裹去广告 | [CainiaoAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/CainiaoAds.conf) | ddgksf2013 |
| 19 | 起点去广告 | [qidian.conf](https://raw.githubusercontent.com/app2smile/rules/master/module/qidian.conf) | app2smile；页面注明卸载重装 |
| 20 | 随手记去广告 | [suishouji.ads.js](https://ddgksf2013.top/scripts/suishouji.ads.js) | ddgksf2013；JavaScript |
| 21 | Bing 首页简化 | [BingSimplify.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/BingSimplify.conf) | ddgksf2013；页面归入广告屏蔽栏目 |
| 22 | 优酷净化 | [youku.adblock.js](https://gist.githubusercontent.com/ddgksf2013/5b431857f8b88acbc7ac2453a21e676a/raw/youku.adblock.js) | 页面标注新版失效并划除 |
| 23 | 百度地图净化 | [bdmap.ads.js](https://ddgksf2013.top/scripts/bdmap.ads.js) | 页面已划除 |
| 24 | 皮皮虾净化及去水印 | [pipixia.adblock.js](https://gist.githubusercontent.com/ddgksf2013/bb1dadbd32f67c68772caebcc70b0a33/raw/pipixia.adblock.js) | 页面注明 Liquor030 |
| 25 | 什么值得买 | [SmzdmAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/SmzdmAds.conf) | blackmatrix7、ddgksf2013 |
| 26 | 微信阅读精简 | [WeRead.sgmodule](https://raw.githubusercontent.com/Maasea/sgmodule/master/WeRead.sgmodule) | Maasea |
| 27 | 滴滴出行 | [Didichuxing.snippet](https://raw.githubusercontent.com/ZenmoFeiShi/Qx/main/Didichuxing.snippet) | ZenmoFeiShi |
| 28 | 黑木耳去广告 | [cmsAdblock.js](https://gist.githubusercontent.com/ddgksf2013/d3a5059645378a05861d6ba18e2fda4c/raw/cmsAdblock.js) | Yswag、ddgksf2013；JavaScript |
| 29 | 彩云天气净化 | [CaiYunAds.conf](https://github.com/ddgksf2013/Rewrite/raw/master/AdBlock/CaiYunAds.conf) | ddgksf2013 |
| 30 | 知乎去广告（墨鱼自用版） | [zhihu.ads.js](https://ddgksf2013.top/scripts/zhihu.ads.js) | ddgksf2013、blackmatrix7；JavaScript |
| 31 | 贴吧去广告（JQ 版） | [TieBaAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/TieBaAds.conf) | ddgksf2013、app2smile |
| 32 | Reddit 去广告 | [RedditAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/RedditAds.conf) | ddgksf2013 |
| 33 | 网易邮箱大师净化（JQ 版） | [NeteaseMailAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/NeteaseMailAds.conf) | ddgksf2013 |
| 34 | 闲鱼净化（JQ 版） | [GoofishAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/GoofishAds.conf) | ddgksf2013 |
| 35 | 汽水音乐净化（JQ 版） | [QiShuiMusicAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/QiShuiMusicAds.conf) | ddgksf2013；页面注明卸载重装 |
| 36 | 小宇宙 FM 去广告 | [XiaoYuZhouAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/XiaoYuZhouAds.conf) | ddgksf2013 |
| 37 | 车来了净化 | [CheLaiLeAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/CheLaiLeAds.conf) | ddgksf2013 |
| 38 | 墨迹天气去广告 | [MoJiWeatherAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/MoJiWeatherAds.conf) | ddgksf2013 |
| 39 | 搜图神器净化 | [soutushenqi.vip.js](https://ddgksf2013.top/scripts/soutushenqi.vip.js) | ddgksf2013；JavaScript |
| 40 | 淘票票净化 | [TaoPiaoPiaoAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/TaoPiaoPiaoAds.conf) | ddgksf2013 |
| 41 | 中国联通去广告 | [ChinaUnicomAds.conf](https://raw.githubusercontent.com/ddgksf2013/Rewrite/refs/heads/master/AdBlock/ChinaUnicomAds.conf) | ddgksf2013 |
| 42 | 更多应用去广告 | [ddgksf2013.top](https://ddgksf2013.top) | 页面索引，没有指向单个规则文件 |

## 页面与使用说明

- 上游目录：[ddgksf2013 主页](https://github.com/ddgksf2013/ddgksf2013)、[Rewrite](https://github.com/ddgksf2013/Rewrite)、[Scripts](https://github.com/ddgksf2013/Scripts)、[Filter](https://github.com/ddgksf2013/Filter)。
- 页面将第 4、14、22、23 项划除或标注失效；其他条目也可能随应用版本变化，请以原始来源的最新说明为准。
- 这份目录只用于查找与核对来源，不能在 Shadowrocket 中作为去广告模块安装。Shadowrocket 使用手册说明，RULE-SET 需要匹配符合其规则格式的规则集；脚本和客户端专用重写文件需单独适配。
- 此目录不会修改原有的腾讯视频、微信或谱慧云模块，也不替换此前的 Safari 一键安装链接。

参考：[Shadowrocket 使用手册](https://lowertop.github.io/Shadowrocket/)。
