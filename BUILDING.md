# 源码、构建与验证

`source/ui/runtime/` 是 UI 0.1.5 模块对应的完整原生源码及链接脚本，运行源码的逐文件摘要见 `evidence/UI_SOURCE_AND_BUILD.json`。
`source/fishing/source/` 是钓鱼与宝箱补丁的 ARM64 汇编；`source/permissions/` 可重建配套的无签名 NPDM。
本发布未修改三个运行文件；`manifest.json` 记录运行文件摘要。

## UI 模块

准备 Python 3.11+、LLVM/Clang 23.1.3、LLD，以及 devkitPro devkitA64 的 `aarch64-none-elf` 头文件、C++ 头和 `lib/pic/libsysbase.a`。
本地验证工具链：LLVM MinGW `20261006-ucrt-x86_64`；devkitPro `devkita64` OCI 20260219。工具链需要自行安装，不包含在本包。
`--devkitpro` 应指向包含 `devkitA64/` 的目录；`--llvm-bin` 指向编译器所在的 `bin/` 目录。无需原作者电脑路径。

```powershell
python -B source/ui/tools/build.py --llvm-bin "工具链/LLVM/bin" --devkitpro "工具链/devkitpro"
```

编译会先运行 8 组 ARM64 编译期回归，然后编译 40 个单元，输出 `source/ui/work/build/subsdk9`、ELF、map 和构建报告。
源码路径、编译器或库不同可能改变模块 Build ID/文件摘要；不要把重新编译的文件自动当作原发布文件。
运行时改动来自此前原生移植与生日扫描防护；本次仅将构建工具改为参数路径，未改运行源码。

## 钓鱼与宝箱 IPS32

```powershell
python -B source/fishing/tools/build.py --llvm "工具链/LLVM根目录"
```

该脚本目前使用 LLVM MinGW 的 Windows 可执行文件名。仅用随包汇编即可构建 77 字节 IPS32，无需原始游戏或外部分析包。
输出到 `source/fishing/outputs/`；应与 manifest 中钓鱼文件摘要一致。
历史 `validate_candidate.py` 的完整函数指令模拟另需开发者自备参考分析包及 Unicorn/Capstone，不是安装或重建补丁的依赖，参考分析包不在此分发。
已有验证结论见 `evidence/FISHING_BUILD.json`，不把历史模拟当成新一轮真机测试。

## 配套权限文件

```powershell
python -B source/permissions/build_npdm.py --output work/main.npdm
```

输入 `source/permissions/npdm.json` 包含无签名自制权限描述文件的元数据、服务列表和内核能力配置。重建结果应为 1544 字节，SHA-256 与 manifest 一致。
这不是游戏原始 main，也不包含主机密钥；NPDM 的签名/公钥区域均为零。

## 实际游戏检查（可选）

安装器 `-GameMain` 核对 NSO 头和完整 Build ID。对自行导出的实际 `main`，可以进一步验证三个段摘要及钓鱼原指令：

```powershell
python -B source/fishing/tools/verify_game.py "导出的main文件" --manifest evidence/FISHING_BUILD.json
```

这些工具只读用户提供的文件。仓库和发布 ZIP 均不包含原游戏 main、游戏更新、固件或密钥。

## 发行检查与打包

```powershell
python -B tests/test_installer.py
python -B tools/verify_release.py
python -B tools/package_release.py
```

安装器测试只在本项目 `work/` 创建的隔离目录中模拟 SD 卡；不写真实 SD 卡。包括不同路径、只读检查、备份回退、分组件、冲突、损坏包、错误 Build ID 和失败回滚。
发行检查核对运行文件、NSO 段摘要、对应源码摘要、IPS32 记录、权限文件重建、公开内容清单与私人数据排除；不会启动 Switch 游戏。
输出 ZIP 包含源码、文档、工具、证据和 3 个运行文件，排除 work、缓存、个人安装备份和原始日志。
