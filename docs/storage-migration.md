# microSD 卡顿诊断与 NVMe 全系统迁移

session_id: 2026-10-18-sd-nvme-migration
状态：部分验证；已有两轮短时资源快照，连续取证待Jetson验收，根因未定、迁移未执行。
适用：Jetson Orin Nano 开发套件；历史环境 JetPack 7.2.1 / L4T R39.2.1。先核实实际设备和版本。

## 先判断卡在哪里

桌面菜单暂时无响应只能证明交互被阻塞，不能独自证明 SD 卡故障。

| 观察与证据 | 优先调查 | 判断边界 |
| --- | --- | --- |
| 多个应用同时卡；复现时块设备等待、I/O pressure 与 SD 延迟一起升高 | 存储等待或后台读写 | 单个 wa 或 %util 数字不能独立定性；需要识别具体块设备 |
| 可用内存接近耗尽，memory pressure 上升，出现回收或 OOM | CPU/GPU 共用内存压力 | 没有 swap 也可能因回收文件页而卡顿；更快 SSD 不增加 RAM |
| 仅一个 Qt 应用在推理/打开文件时不响应，其他桌面正常 | 主线程同步工作或应用等待 | 核对实际运行源码；不能用仓库整理版推定现场实现 |
| CPU 个别核心长期满载，I/O 与内存压力低 | CPU/软件热点 | 全机平均 CPU 低也不能排除单线程热点 |
| 内核有 mmc 超时、CRC、I/O 或 EXT4 错误 | 卡、卡槽/供电链路或文件系统 | 先保护可读数据；不能只按正常性能瓶颈处理 |
| 温度与降频、桌面图形错误相关 | 散热/电源/图形栈 | SSD 不能保证修复这些问题 |

先在原有负载下复现，不先运行写盘压测或升级软件。通过 SSH 观察可减少桌面卡顿对采样的影响。

第一组只读状态：

```bash
findmnt -no SOURCE,FSTYPE /
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
df -h /
free -h
swapon --show
vmstat -w -t 1 20
```

运行最后一行的约 20 秒内重复发生卡顿的操作；第一条 vmstat CPU/I/O 报告是自启动以来的平均值，判断以后续区间报告为主。wa 是 CPU 等待 I/O 的时间比例，b 是等待 I/O 的阻塞任务数；两者均不能定位具体磁盘。

需要时补充：

```bash
head -n 2 /proc/pressure/io /proc/pressure/memory
sudo journalctl -k -b -p warning --no-pager -n 80
```

若已有 sysstat，另一轮复现时使用 iostat -xz -y 1 20，关注 SD 设备的 r_await/w_await、队列与读写量；缺包时先登记，不为第一轮诊断改环境。短卡顿可能被平均值稀释；低全局 wa 不能排除一个应用被 I/O 卡住。没有 swap 时 si/so 为 0 也不能排除内存压力。PSI 不可用时不作为硬件异常。

对照实验：记录原负载，然后正常退出不需要的 LLM、YOLO、编译或后台下载，再操作相同菜单。保存工作后可安排一次重启后的空闲对照，不强杀不明进程。若只影响 Qt，应检查文件读取、解码、模型加载和推理是否在 GUI 主线程执行，必要时使用工作线程和有界队列。

## 硬件准备

原厂载板提供 M.2 Key M 2280（PCIe 3.0 x4）和 2230（PCIe 3.0 x2）；Key E 的无线模块插槽不能当作同一种存储槽。

容量按项目数据和预算选择：500GB 可作为起点，1TB 更便于模型、容器和视频积累。优先确认机械尺寸、NVMe 协议、功耗、散热和外壳空间；M.2 SATA 盘不能代替 NVMe。安装前关机断电，不热插拔。

全盘块克隆还需目标实际字节数不少于源盘，且逻辑扇区大小匹配。先核实 SSD 是否已有需要保留的数据；迁移写入会覆盖目标相应内容。

## 全系统保留范围

目标保留系统包与包数据库、用户与原绝对路径、隐藏配置、系统服务、CUDA/TensorRT 等依赖、项目、venv、llama.cpp、模型、桌面入口，以及实际存在的 Docker/containerd 数据和卷。只复制 home 或 pip freeze 都不是全系统迁移。

需要记录 root、ESP/EFI、独立 boot、其他持久挂载和引导项。/proc、/sys、/dev、/run 属于运行时接口，不按普通静态文件复制。开发板 QSPI 固件与磁盘文件系统分开；存储迁移默认保持当前兼容固件，不附带跨版本升级。

## 迁移路线选择

推荐目标是同版本、全系统、可回退迁移；具体复制方法由当前分区布局、逻辑扇区和可用维护环境决定。

### A：离线全盘克隆，优先评估保留环境

适合有 Linux 电脑/通用维护系统、SD 读卡器及 SSD 接入方式的情况。电脑可运行 Linux Live 环境；块复制不要求电脑和 Jetson 同为 ARM。此路径是工程迁移方案，不宣称 NVIDIA 提供一键跨介质克隆保证。

1. 采集设备、挂载、分区布局、实际扇区大小和引导链；校验重要源码与模型。
2. 系统正常关机，使源卡不再作为活动根文件系统；在维护环境下保持源卡未挂载或只读，制作可校验的全盘备份。完整 128GB 卡的原始镜像约需相应容量，不能用约 39GB 的文件占用估算镜像空间。
3. 经型号/容量与设备路径双重核对后，把镜像恢复到 NVMe，包含现有分区与 ESP；保留 SD 原件。
4. 按实际布局修复目标盘 GPT 备份表位置，并核对引导是否硬编码 SD 设备名。块克隆会复制 UUID/PARTUUID；首次验证取出原卡，避免重复标识产生歧义。若要长期同时连接两盘，另行重建目标标识并同步修正所有引用。
5. 核对 UEFI 启动项、根参数、fstab、ESP 与当前实际使用的 GRUB 或 extlinux；按实际引导链修复。不能只替换某个 extlinux.conf 就宣称适配所有 JetPack 版本。
6. 关机后仅保留 NVMe，选择相应启动项，验证根和 ESP 都来自目标盘，再验证原业务。
7. 通过后再安排扩容。源卡可能在 APP 后还有 EFI/其他小分区，不能假设根分区后面的空间连续可用，也不能盲目执行 growpart。必要时调整布局或选择文件级方案。

### B：官方同版 NVMe 安装骨架 + 一致性完整系统还原

当块布局/扩容不适合，或缺少直接离线克隆条件时，使用 JetPack 7.2.1 Jetson ISO 写到 16GB 以上 U 盘，从 U 盘启动，将同版 BSP 安装到 NVMe。安装会清空选定目标盘；移除源 SD 以免选错。此步只建立可启动的目标盘，不会自动带回已有软件。

完整状态还原另行进行：使用可访问两份文件系统的可信维护环境，对静止源进行文件级还原，保留数字 UID/GID、权限、ACL、xattrs、硬链接、符号链接和稀疏文件；单独处理跨挂载的持久数据与 EFI。内核、模块、initramfs 作为配套集合处理。保留或重新生成目标磁盘标识后，修正 fstab、根启动参数和实际引导配置；不能把源盘 EFI/标识无差别覆盖回去。

NVIDIA 说明 ISO 安装 U 盘是最小安装环境，不是完整 Live 桌面系统，不能预设其自带任意迁移工具。若无法获得一致性恢复环境，则选择显式记录的应用级重建路径，并承认它不等同于完整克隆，不冒称全部软件自动保留。

有兼容 Linux 主机时，也可按该版本 Linux_for_Tegra 的 initrd 克隆/恢复工具执行；必须使用对应设备与发行版参数，避免照搬旧版教程。

## 验收与回退

验收分层：

- 磁盘：关机取出 SD 后启动；findmnt / 与 /boot/efi、lsblk、实际引导项均指向预期 NVMe；检查持续读写与内核错误。
- 系统：用户/权限/网络/服务与迁移前对照，无新增失败单元或挂载超时；保留当前系统版本。
- 软件：原绝对路径的 venv、TensorRT/PyTorch 导入与实际 CUDA 数值任务通过；原 YOLO 引擎、图片与视频界面、LLM/API，以及实际存在的容器分别验收。
- 数据：关键源码、模型和配置哈希/清单一致；记录预期因启动更新而变化的日志。
- 性能：相同应用、素材、负载、电源模式下重复原菜单操作；区分冷启动/热缓存，记录延迟与 I/O、内存压力，不预报改善倍数。

失败时关机断电，隔离 NVMe，装回原 SD，通过 UEFI 选择原盘启动。若方案涉及固件变更，必须另有兼容性与恢复安排，不能仅把旧 SD 当作完整固件回退保证。保留原卡至稳定运行与备份验证完成。

SSD 可改善加载与存储等待，不增加内存，也不会自动修复界面线程。迁移后依据新采样再评估 zram 或 SSD swap；不把给 SD 增加大 swap 当本次通用修复。

## 下一步证据

尚需：卡顿影响范围、上述只读输出、复现时资源采样、当前完整分区/引导配置、SSD 型号/容量/逻辑扇区与是否为空盘，以及可用维护电脑/读卡器。未收到这些证据前，只交付路线，不生成绑定真实磁盘的破坏性命令。

## 官方依据（2026-10-18 检索）

- [NVIDIA Quick Start：JetPack 7.2.1、ISO 与安装目标](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html)
- [NVIDIA Hardware Layout：NVMe 槽位](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/hardware_layout.html)
- [NVIDIA R39.2.1 Flashing Support](https://docs.nvidia.com/jetson/archives/r39.2.1/DeveloperGuide/SD/FlashingSupport.html)
- [NVIDIA UEFI：启动顺序与多种引导方式](https://docs.nvidia.com/jetson/archives/r39.2.1/DeveloperGuide/SD/Bootloader/UEFI.html)
- [Ubuntu vmstat 字段说明](https://manpages.ubuntu.com/manpages/noble/man8/vmstat.8.html)
- [Linux PSI](https://www.kernel.org/doc/html/latest/accounting/psi.html)
- [Qt：耗时工作与 GUI 线程](https://doc.qt.io/qt-6/threads-qobject.html)

## 追加：短时采样与连续取证
同一session追加，未实施迁移，SD瓶颈未证实。
- 卡顿主要报告于Chrome、CherryStudio窗口与部分设置菜单；一次更新无响应后更新已经完成，缺少应用错误日志。
- 两轮短采样均b=0，wa分别0与0%～1%；第一轮CPU空闲约91%～96%，第二轮前可用内存1.8GiB、swap=0。是否与实际卡顿严格同步尚未确认。
- 已提供的内核片段未见mmc超时、I/O或EXT4错误。PSI接口不可用、缺少iostat。以上不能证明持续磁盘拥堵，也不能排除瞬时等待。
- 已保存复盘报告交付jetson_watch.py与工具包，支持连续采样、现场标记、受限临时文件I/O、轮转、摘要和导出；报告18项逻辑检查及通用Linux流程通过。这是历史来源报告，本次未复跑，Jetson未验收。
- 当前可读取来源未包含完整工具源码或VALIDATION.md；只登记待收集，仓库不生成替代脚本，不宣称已收录工具代码。

## 下一步验收
先收回实际源码及验证记录，在Jetson原负载下持续记录卡顿与恢复并导出可读日志。监控与I/O测试分开；PSI缺失正常降级，临时文件测试不触碰原数据且遵守写入预算。之后再决定是否迁移及进行同负载对照。
