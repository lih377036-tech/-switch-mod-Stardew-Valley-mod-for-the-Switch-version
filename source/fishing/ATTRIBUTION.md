# 来源与许可证

本项目的 ARM64 补丁、构建、检查和测试代码以 GPL-2.0-only 提供，随附 LICENSE。

tools/nso_reference.py 是以下项目 tools/analyze_nso.py 的未作功能修改副本（仅改文件名）：

- 作者标识：zmzhang2022-ai；项目许可证 GPL-2.0-only。
- 仓库：https://github.com/zmzhang2022-ai/Switch-StardewValley-Mod
- 固定提交：1fde8404aa129941d37d0f76853015b462152d11。
- 用途：读取 NSO 头、LZ4 解压和 NSO 段信息。

版本地址和原版结算语义通过该项目文档，以及用户本机已有整合包的分析记录核对。
本交付不包含完整游戏函数反汇编、游戏二进制、其他整合模组、PC SMAPI 模组或主机密钥。

参考技能 switch-homebrew：

- https://github.com/Lili679280/switch-homebrew
- 提交：21b2a43caa05e9836f08e08fc1fcac70d391bc56。
- 用于开发参考，没有作为运行时依赖或安装进 Switch。

LLVM、Unicorn、Capstone 仅作为本地构建/验证工具，未打入交付包。验证工具依赖的版本记录在 VALIDATION.json。
