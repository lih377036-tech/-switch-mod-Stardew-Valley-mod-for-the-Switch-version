# 来源与许可

本项目的钓鱼 ARM64 补丁、UI 改写、便携安装器和发布工具以 GPL-2.0-only 提供，完整文本见 LICENSE。未替原作者或发布者虚构署名。

- Switch 原生基础：**zmzhang2022-ai/Switch-StardewValley-Mod**，固定提交 `1fde8404aa129941d37d0f76853015b462152d11`，GPL-2.0-only。https://github.com/zmzhang2022-ai/Switch-StardewValley-Mod
- 功能参考：**Annosz/UIInfoSuite2** v2.3.7，固定提交 `9f536012602fcd2d9456c02376127c9dcbdc443f`。https://github.com/Annosz/UIInfoSuite2 。本包为独立原生改写，不包含 PC SMAPI DLL 或其图片资源，也不是上游官方 Switch 发行版。
- 原生框架沿用 exlaunch、Atmosphère/libnx 相关代码，保留源码内现有版权和许可声明。运行时完整源码位于 `source/ui/runtime/`。
- **Thog** 的 rtld，保留 `source/ui/runtime/source/rtld/LICENSE.txt`（ISC 许可）。
- **Rprop / And64InlineHook**，保留 `source/ui/runtime/source/lib/hook/nx64/hook_impl.cpp` 文件内 MIT 许可。https://github.com/Rprop/And64InlineHook
- `source/fishing/tools/nso_reference.py` 来自上述原生仓库的 `tools/analyze_nso.py`，仅改文件名，保留对应 GPL 许可和来源说明。
- 开发时参考 switch-homebrew 技能，提交 `21b2a43caa05e9836f08e08fc1fcac70d391bc56`，不作为运行时依赖。https://github.com/Lili679280/switch-homebrew

便携发行改动：将三个既有运行文件合并；重写与设备无关的安装/回退工具；增加自包含的权限描述文件重建、可配置构建路径、公开文档、摘要和安装器回归验证。UI 与钓鱼的运行文件逐字节保持原组件版本。

编译使用 LLVM/Clang 23.1.3 和 devkitPro devkitA64；它们不随包分发。段读取/LZ4 和 ELF 转 NSO 工具源码随包提供。
游戏绘制使用设备上原游戏已有的字体和素材；不随包分发游戏素材。

转载时请保留本文件、LICENSE、源码内第三方声明，以及 UI 尚待真机复测的测试版状态。
