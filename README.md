# 星露谷物语 Switch 1.6.15.3 便携 Mod 合集

<!-- github-download-links -->
**下载：[v1.0.1-preview 预览版安装包](https://github.com/lih377036-tech/-switch-mod-Stardew-Valley-mod-for-the-Switch-version/releases/tag/v1.0.1-preview)**

[新手图文安装教程](新手安装指南.md) · [完整源码](source/) · [构建说明](BUILDING.md)


包含跳过钓鱼小游戏、自动捕获本竿原版随机宝箱，以及 UI 信息套件原生移植版。
合集版本 **1.0.1-preview**；UI 为 **0.1.5 修复候选版**。不绑定 SD 卡、读卡器序列号、盘符或主机身份。
本包沿用原有三个安装文件，没有重新修改游戏逻辑。

**第一次安装：在 GitHub 阅读 [新手图文指南](新手安装指南.md)；下载并解压后，也可以双击 [先看这里-安装指南.html](先看这里-安装指南.html) 离线阅读。**

**公开测试状态：**钓鱼与普通随机宝箱已收到一台续航版 Switch 的成功反馈；UI 0.1.5 已完成本地验证，尚无修复后的真机复测反馈。其他机型、固件、大气层版本和联机没有逐项验证，不应宣传为全机型稳定版。

## 对应游戏

| 项目 | 要求 |
| --- | --- |
| 平台 | 能正常使用 Atmosphère 游戏覆盖与 IPS32 补丁功能的 Switch 环境 |
| 游戏 | Switch《星露谷物语》1.6.15.3 |
| Title ID | `0100E65002BB8000` |
| main Build ID | `A5C617C14A7F3F6620B3BC8136965A4822D32B9C000000000000000000000000` |
| 常见工具显示的前 16 位 | `A5C617C14A7F3F66` |

“便携”指不绑定设备；仍只适配上述游戏构建。换 SD 卡或大气层不会自行改变游戏 Build ID。
钓鱼 IPS 由 Atmosphère 按完整 Build ID 选择；UI 启动前检查 18 个挂钩入口及额外代码特征，**UI 没有实现完整的内存 Build ID 读取器**。
安装器不能从加密的 SD 游戏目录直接确认游戏 Build ID；未提供导出的 `main` 时，会明确记录“未核对”。
编号不符时请等待适配，修改 IPS 文件名无法完成适配。

## 功能

- 钓鱼：手动抛竿、等待咬钩并提竿后，跳过绿色条小游戏，使用原版收鱼流程。不会自动抛下一竿，不强制 Perfect 或最高品质。
- 宝箱：这一竿原版生成宝箱时，和鱼一起捕获；出现概率、内容与开箱领取界面保留原版。没有宝箱的一竿不会额外生成宝箱。金色宝箱的标志保留，但尚未收到单独真机验收。
- UI：物品售价与收集提示、作物/设备信息、作用范围、运势/生日等每日提示、技能经验、动物状态、地图人物与好感信息。是原生 C++ 改写，不是完整 SMAPI，也不能直接加载电脑版 Mod。

UI 设置入口：**先打开背包所在的游戏菜单，按住 ZL 和 ZR，再按十字键 ↑**。
菜单里显示的小锤子尚有手柄无法选中的已知问题，请使用上述组合键。R3 保留原版聊天功能。
文字使用游戏字体原生 1 倍、整数像素位置和单层阴影；不会替换整套游戏字体。
UI 设置按存档身份保存在 `SD:/config/uiinfosuite2/`，移卡时可另外迁移这个目录；本包不会覆盖现有设置。

## Windows 安装器（推荐）

1. 完全退出游戏并关闭主机，将 SD 卡接到电脑；把**整个压缩包解压到电脑目录**。电脑目录可以包含中文和空格。
2. 确认实际盘符，例如 `E:`。目标应已有 `atmosphere` 文件夹。安装器不格式化 SD 卡，也不安装大气层。
3. 在解压目录打开 PowerShell，先只读检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install.ps1 -SdRoot "E:\" -CheckOnly
```

4. 检查通过后安装全部功能：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install.ps1 -SdRoot "E:\"
```

`E:` 只是示例。脚本支持 Windows PowerShell 5.1 和 PowerShell 7，不要求卷标、USB 类型、FAT32 或固定硬件序列号。
脚本核对包内三个文件的 SHA-256，检查程序覆盖、原生模块和同构建补丁冲突；遇到未知同名文件会停止。
安装前备份所选同名文件，复制后逐项读回核对，复制失败时尝试恢复旧文件。只备份本包涉及的文件，**不导出当前游戏存档或备份整张 SD 卡**。
备份默认保存在解压目录的 `outputs/backups/`；可用 `-BackupRoot "其他电脑目录"` 指定位置。备份必须在 SD 卡目标之外。

只装钓鱼与宝箱，或只装 UI：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install.ps1 -SdRoot "E:\" -Components Fishing
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install.ps1 -SdRoot "E:\" -Components UI
```

可选：加入 `-GameMain "导出的ExeFS目录\main"`，核对完整 NSO Build ID。这个选项只读取导出文件；不会破解或导出游戏。
未提供该文件也能安装，但安装报告会保留未核对状态。更深入的段摘要和指令核对见 [BUILDING.md](BUILDING.md)。

安装完成后安全弹出 SD 卡，插回关机状态的 Switch，再启动游戏。

## 手动安装（任何可复制文件的电脑系统）

先核对构建，检查其他 Mod 冲突，并备份下面三个同名文件；原来不存在的文件也要记下。
把本包根目录的 **`atmosphere` 文件夹合并复制到 SD 卡根目录**，不要把文档、源码、整个压缩包复制到 `contents` 里面。

实际运行文件只有：

```text
atmosphere/contents/0100E65002BB8000/exefs/subsdk9
atmosphere/contents/0100E65002BB8000/exefs/main.npdm
atmosphere/exefs_patches/StardewInstantCatch/
  A5C617C14A7F3F6620B3BC8136965A4822D32B9C000000000000000000000000.ips
```

前两个是配套的 UI 文件；最后一个同时包含钓鱼与宝箱功能。不要直接覆盖其他 Mod 的 `subsdk9`、`main.npdm` 或 `exefs.nsp`。
安装器对其他同构建 IPS 采用保守冲突判断，即使部分补丁实际可以共存，也需要先人工核对；不会自动合并未知 Mod。
本包不会迁移 emuMMC、游戏安装或主机存档；换机器时，游戏与存档需按各自方式准备。

## 回退与关闭

自动安装后，可用报告里的备份目录回退：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Restore.ps1 -SdRoot "E:\" -BackupDirectory "实际备份目录" -CheckOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Restore.ps1 -SdRoot "E:\" -BackupDirectory "实际备份目录"
```

回退恢复旧文件；原来不存在的安装文件会被移除。若文件在安装后又被别人修改，脚本会停止，避免覆盖后续修改。
手动安装时，恢复自己的同名备份；没有旧文件时，仅移除本包增加的文件即可。
可以单独移除配套的 UI 两文件而保留钓鱼 IPS；也可以移除钓鱼 IPS 而保留 UI。
**只改 IPS 外层文件夹名字不会关闭补丁**；应删除该 IPS 或改成不以 `.ips` 结尾的文件名。

## 已知限制与反馈

UI 0.1.5 针对生日提醒遍历建筑内部地点时读取非法人物集合的两次已定位崩溃增加了指针、内存映射、集合类型与数量检查，并用于地图人物扫描。
未知类型会被跳过，可能漏显示信息；这不表示所有潜在崩溃已消除。底层通用集合解包逻辑尚未全面重写。
小锤子导航问题保留，组合键入口在前版已由真机确认；0.1.5 沿用相同输入实现。
UI 0.1.5 的长期稳定性、SDK 读写、手柄与画面、不同主机以及联机需要公开测试反馈。

反馈时请说明游戏版本、完整 Build ID、大气层/固件版本、发生操作、是否装了其他 Mod，以及对应崩溃日志。
日志上传前请自行检查私人信息。本发布包未包含个人存档、崩溃照片、原始崩溃日志、聊天记录或设备序列号。

## 源码与转载

本压缩包包含对应运行源码、构建脚本、权限描述文件来源和验证记录，详见 [BUILDING.md](BUILDING.md)、[CREDITS.md](CREDITS.md) 与 [evidence](evidence/)。
项目采用 **GPL-2.0-only**；第三方文件保留各自许可。向 GitHub 或网盘转载时，请保留源码、许可证、来源和测试版说明，建议直接分享完整发布 ZIP。
GitHub 仓库可直接使用此解压目录中的公开文件；不要上传以后生成的 `work/`、`outputs/backups/` 或个人日志。
本包不包含游戏本体、更新包、主机密钥或固件；`main.npdm` 是无签名的自制权限描述文件，可从随附配置重建。

加载机制参考：[Atmosphère loader 官方文档](https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/components/modules/loader.md)。
