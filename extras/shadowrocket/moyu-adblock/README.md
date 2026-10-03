# 墨鱼去广告：规则来源目录

本目录按 [ddgksf2013 的 GitHub 主页](https://github.com/ddgksf2013/ddgksf2013)「广告屏蔽」栏目整理，共 42 项。每条链接都指向原作者或页面所列的上游来源；本文件只保存名称、来源、贡献者与页面状态，不复制或托管上游规则源码。

## 先看兼容性

这份目录不是可直接安装的 Shadowrocket 模块。上游条目混有 Quantumult X 配置、脚本响应规则、JavaScript、snippet、Shadowrocket/Surge 模块，以及第三方来源。Shadowrocket 的 RULE-SET 需要对应格式的规则集，不能把这些不同格式的文件当作同一个列表直接导入。将其做成一个真正可执行的模块，需要逐条转换并按对应应用测试；部分脚本还依赖 HTTPS 解密和客户端专用 API。

GitHub 仓库元数据没有为 ddgksf2013、Rewrite、Filter、Profile 声明统一的开源许可证；因此这里保留上游链接和页面注明的作者，不镜像规则内容。具体使用与再分发请遵循每个源文件自己的许可和说明。

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
