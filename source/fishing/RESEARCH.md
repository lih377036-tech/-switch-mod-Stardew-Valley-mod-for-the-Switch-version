# 调研与适配记录

## 钓鱼流程

星露谷 Wiki 的 Fishing 页面描述了抛竿、等待咬钩、提竿进入控条小游戏、捕获及领取的顺序。
本次只跳过 BobberBar 控条阶段，保留前后的手动操作。

- https://wiki.stardewvalley.net/Fishing

## PC 模组与 Switch 差异

官方 SMAPI 提供的平台为 Linux、macOS、Windows/Steam Deck，不能把 PC SMAPI DLL 直接当作本机 Switch 模组。
公开的 FishingAssistant2 源码可用于理解“跳过小游戏后进入 pullFishFromWater”的设计，但其 C# 调用不能直接作为 Switch ARM64 地址。

- https://smapi.io/
- https://github.com/GhostUnderBlanket/Stardew-SMAPI-Mods/blob/main/FishingAssistant2/Frameworks/Assistant.cs

## Switch 版本证据

公开 Switch-StardewValley-Mod 提供了 1.6.15.3 的函数地址和指纹。
开发时另参考了 `fast-animations-singleplayer-merged-v13-1-1.zip` 中该版本 `BobberBar.update` 的反汇编分析和构建信息；该参考包及完整函数反汇编不随此包分发。
本项目从这个记录核对字段、跳转、参数和普通成功的尺寸处理，再生成独立补丁，没有安装该整合包，也没有包含它的其他游戏功能。
证据仍属于历史包的分析记录；未据此宣称已核对当前真机的游戏文件。

- https://github.com/zmzhang2022-ai/Switch-StardewValley-Mod
- https://github.com/zmzhang2022-ai/Switch-StardewValley-Mod/blob/main/docs/AUTO_FISHING_SWITCH.md

## 加载方式

Atmosphère 官方 loader 文档规定按 NSO 的完整 Build ID 查找 IPS/IPS32。
核对 1.9.5 的 loader 和 patcher 实现后，确认本补丁要使用 IPS32，并在文件地址中加 NSO 头的 0x100 偏移。

- https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/components/modules/loader.md
- https://github.com/Atmosphere-NX/Atmosphere/blob/1.9.5/stratosphere/loader/source/ldr_patcher.cpp
- https://github.com/Atmosphere-NX/Atmosphere/blob/1.9.5/libraries/libstratosphere/source/patcher/patcher_api.cpp

## 技能检索

开发时参考了 `Lili679280/switch-homebrew` 技能的 API 查证和工具链指导。
最终使用无外部运行库的 ARM64 汇编补丁，不需要照搬独立 NRO 应用的主循环或安装 SMAPI。
该技能不是安装或运行此 Mod 的依赖。

- https://github.com/Lili679280/switch-homebrew

## 后续真机验证

0.1.0 跳过小游戏版已收到真机运行反馈；随后 0.2.0 的普通随机宝箱、开箱和领取也收到成功反馈，限一台续航版主机，详见根目录的 evidence/HARDWARE_STATUS.json。
新增 0.2.0 的依据是同一原版函数 `0x167FFE0` 对 `BobberBar+0xC2` 的读取及随后传给 pullFishFromWater 的 w5 参数。
新版只把该读取改为 `+0xC1`（原版本竿有宝箱），不写入生成标志；保留旧版 52 字节记录。
PC FishingAssistant2 对生成标志、捕获标志和收鱼参数的分离提供语义对照：

- https://github.com/GhostUnderBlanket/Stardew-SMAPI-Mods/blob/main/FishingAssistant2/Frameworks/SBobberBar.cs
- https://github.com/GhostUnderBlanket/Stardew-SMAPI-Mods/blob/main/FishingAssistant2/Frameworks/Assistant.cs

金色宝箱和其他主机仍需测试；历史模拟只核对指令流、参数、对象字段和随机数调用。

Build ID 匹配由 Atmosphère 加载器限定；推荐进一步导出实际 main，用 verify_game.py 检查字节和三段摘要。
开发时曾查阅 nxdumptool rewrite 的 ExeFS 导出能力；导出工具不随此包分发。实际游戏文件需由使用者自行准备。

- https://github.com/DarkMatterCore/nxdumptool/releases/tag/rewrite-prerelease
