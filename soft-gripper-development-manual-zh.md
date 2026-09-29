# 前言

[English](soft-gripper-development-manual.md) | [简体中文](soft-gripper-development-manual-zh.md)

LiteGrip 是 NEXFORM ROBOTICS 面向科研教育、AI 机器人开发与轻量级工业自动化场景设计的自适应两指平动夹爪，有效行程 87.000 mm。夹爪通过 USB-CAN 适配器与上位机通信（经典 CAN，1 Mbps），配套 Python SDK 与完整协议文档，可用于抓取、搬运、上下料、分拣与算法验证等场景。

本文档面向**集成工程师**，说明 SDK 的安装、接口用法、参数与返回值、异常、每个接口的**前置条件**，以及底层 CAN 通信协议。产品规格数值（行程、速度、力矩、温度与电气参数等）见《产品手册》与《参数文档》；安全设计依据见《安全说明书》。

## 目录

- [硬件组成](#硬件组成)
- [单位说明](#单位说明)
- [安全须知](#安全须知)
- [SDK 使用指南](#sdk-使用指南)
  - [概述](#概述)
  - [库相关依赖](#库相关依赖)
  - [1. 安装 SDK](#1-安装-sdk)
  - [2. 配置 CAN 接口](#2-配置-can-接口)
  - [3. 接 24 V 驱动电源](#3-接-24-v-驱动电源)
  - [4. 加载标定](#4-加载标定)
  - [5. 跑起来：让夹爪动一下](#5-跑起来让夹爪动一下)
  - [6. 夹爪不动的时候](#6-夹爪不动的时候)
  - [使能、失能与故障处理](#使能失能与故障处理)
  - [运动控制（开合与位置）](#运动控制开合与位置)
  - [抓取与力控](#抓取与力控)
  - [读取状态](#读取状态)
  - [单位与换算](#单位与换算)
  - [手动示教（零重力）](#手动示教零重力)
  - [标定与零点](#标定与零点)
  - [配置对象](#配置对象)
  - [前置条件与调用约束](#前置条件与调用约束)
  - [异常与错误处理](#异常与错误处理)
  - [运动调参（MotionConfig）](#运动调参motionconfig)
  - [遥操作（主从）](#遥操作主从)
  - [直接驱动总线（litegrip.can）](#直接驱动总线litegripcan)
  - [核心 API 速查](#核心-api-速查)
- [二次开发](#二次开发)
  - [扩展 Python SDK](#扩展-python-sdk)
  - [C++ SDK](#c-sdk)
  - [ROS 2（ros2_control 与 MoveIt 2）](#ros-2ros2_control-与-moveit-2)
  - [仿真（MuJoCo、PyBullet、Isaac Sim）](#仿真mujocopybulletisaac-sim)
  - [上位机（litegrip-studio）](#上位机litegrip-studio)
  - [尚未就绪的部分](#尚未就绪的部分)
  - [报告与验证状态](#报告与验证状态)
  - [常见问题与技术支持](#常见问题与技术支持)
- [CAN 通信协议](#can-通信协议)
  - [物理层与节点](#物理层与节点)
  - [帧类型总览](#帧类型总览)
  - [MIT 控制帧](#mit-控制帧)
  - [命令帧](#命令帧)
  - [状态刷新帧](#状态刷新帧)
  - [参数帧与寄存器](#参数帧与寄存器)
  - [反馈帧与错误码](#反馈帧与错误码)
  - [通信时序](#通信时序)
  - [典型交互序列](#典型交互序列)
- [附录一 状态、错误码与异常](#附录一-状态错误码与异常)
  - [状态与错误字段](#状态与错误字段)
  - [Python 异常类型](#python-异常类型)
  - [错误处理建议](#错误处理建议)
- [附录二 通信与连接排查](#附录二-通信与连接排查)
  - [CAN 接口与端点信息](#can-接口与端点信息)
  - [CAN 接口配置](#can-接口配置)
  - [不经 SDK 的总线自检](#不经-sdk-的总线自检)
  - [连接排查](#连接排查)

## 硬件组成

| 序号 | 设备 | 说明 |
|------|------|------|
| 1 | LiteGrip 夹爪本体 | 自适应两指平动夹爪，含驱动电机 **DM-J4310-2EC**（电机内置 10:1 减速箱，无额外减速级） |
| 2 | 24 V 直流电源 | 必需外部设备。**未接通时电机不输出力矩** |
| 3 | USB-CAN 适配器 | 必需外部设备。通信由它独立供电 |
| 4 | CAN 终端电阻 | 必需外部设备，总线两端各一只 120 Ω |
| 5 | 上位机 | **Linux**，Python 3.8 或更高版本 |
| 6 | 本机标定文件 | 该台机器的实测标定数据，每台一套 |

## 单位说明

| 参数 | 单位 | 说明 |
|------|------|------|
| 开口 / 位置 | mm | 毫米 |
| 电机角度 | rad | 弧度 |
| 速度 | mm/s、rad/s | 毫米每秒、弧度每秒 |
| 力矩 | N·m | 牛米 |
| 夹持力 | N | 牛顿 |
| 温度 | °C | 摄氏度 |
| 电压 | V DC | 伏特（直流） |

**开口读数约定**：同一个物理开口有三套表示方式，**零点和方向都不一致**，混用是产生错误数字最常见的原因。

| 表示方式 | 完全闭合 | 完全张开 | 张开时数值 |
|---------|---------|---------|-----------|
| 电机角度 `r`（rad） | 标定值 `pos_closed_rad`（**见本机标定文件**） | 标定值 `pos_open_rad`（**见本机标定文件**） | **减小** |
| SDK 位置 `p`（mm） | 0 | **87.000**（= 有效行程） | 增大 |
| **实际开口**（mm） | 1.508 | **87.000** | 增大 |

> **本文档未特别说明时，"mm"一律指"实际开口"**（即两指内侧面之间的真实距离），因为那是可以用卡尺直接量到的量。
>
> **`get_position()` 与 `position_mm` 返回的是上表的 `p`，不是实际开口**，两者在闭合侧相差 1.508 mm 的闭合间隙：
>
> ```
> 实际开口 ≈ get_position() + 1.508
> ```
>
> 要得到卡尺读数必须做这一步加法。
>
> **注意这个口径差**：`p` 的跨度是 **87.000 mm**（0 → 87.000），而卡尺实际开口的跨度是 **85.492 mm**（1.508 → 87.000）。**"有效行程 87.000 mm"是 `p` 的口径**，比卡尺跨度大 1.8 %；上式的 `+ 1.508` 在闭合端精确、在张开端会高估 1.508 mm。要毫米级精确，请直接用卡尺标定 `rad_to_mm`（见 [标定与零点](#标定与零点)）。
>
> **电机角度与标定值因台而异。** rad 端点取自本机标定文件（`~/.litegrip/litegrip_calibration.json`），**每台机器的数值都不同**，所以本文档不写具体数字，请以自己那台的标定文件为准。
>
> **换算系数只影响"显示出来的毫米数与毫米目标"。** SDK 的位置钳制用的是 `pos_closed_rad` / `pos_open_rad` 两个 **rad** 值，与毫米换算系数无关 —— 系数写错只会让数字不对，不会改变端点位置。**但这也意味着 SDK 不替你做任何越界判断**：需要"越界就拒答"请自己实现（见 [运动控制（开合与位置）](#运动控制开合与位置)）。

## 安全须知

### 简介

本节介绍使用 LiteGrip 夹爪及系统时需要遵守的安全原则与规范。在安装、使用前，使用者必须认真阅读本文档及《安全说明书》，标有警示级别的内容需要掌握并严格遵守。夹爪系统运行中存在夹持、碰撞、坠落等潜在危险，使用人员应充分认识操作风险，并经过培训后使用 SDK 开发与调试。

### 警示级别

本文档其他章节的安全提示用如下标签标明其级别；对应的图形符号见产品随附标识：

- 危险：用于可能导致人员伤亡或设备严重损坏的危险情况。
- 警告：用于如不避免，可导致人员伤亡或设备严重损坏的危险情况。
- 高温：用于存在高温部件、接触可能造成灼烫伤害或设备损坏的危险情况。
- 注意：用于如不避免，可能导致人员伤害或设备损坏的一般警示。

### 安全注意事项（软件侧）

**保护体系由三层构成，软件只是其中一层：**

| 层级 | 由谁实现 | 保护什么 |
|------|---------|---------|
| 越界判断 | **集成方自行实现** | 命令不越界（SDK 本身不做任何越界判断） |
| 驱动器级保护 | 电机驱动器固件 | 过压 / 欠压 / 过流 / 过温 / 掉线 |
| 物理挡块与硬件急停 | **必须由集成方配置** | 机械不越界、真正断电停机 |

1. **SDK 不做越界判断。** 位置目标超出标定行程时会被**静默钳制**到端点（见 [运动控制（开合与位置）](#运动控制开合与位置)），既不报错也不告知；`kp` / `kd` / `tau` 越界会被**静默饱和**。"命令不越界"必须由集成方自己实现。
2. **必须配置硬件急停回路，且其动作不依赖 CAN 通信与上位机软件。** 进程卡死、CAN 掉线、Python 异常时软件侧无法停机。
3. **必须配置机械挡块**作为最后一道防线。标定端点不是硬限位。
4. **不要把软件停止当作安全功能使用。** `stop()` 只发零力矩帧、电机保持使能且可被反驱，并且不返回成功与否；`disable()` 的返回值也只表示命令已发出、未获证实（见 [使能、失能与故障处理](#使能失能与故障处理)）。二者都无法替代硬件急停。
5. **不要把返回值当作"命令已生效"的证据。** 运动接口的返回值只表示帧发出去了，只有反馈帧能证明实际状态。
6. **不要在力标定完成前使用任何力参数。** `force_n` 换算用的是名义系数 `0.1 N·m/N`，SDK 既不校验也不限幅（见 [抓取与力控](#抓取与力控)）。
7. 运行期间必须有周期性帧发送，否则驱动器在 0.4 s 后**自动退出使能**【待测·乙 回读 RID 9 核对】；**该超时保护可以关闭，关闭后掉线时电机将保持最后一条力矩指令**，请勿在未经评估时关闭。
8. 调试与标定**必须有人在场监护**，且硬件急停可用。
9. 发现异常（异响、卡顿、异常温升、位置读数跳变）应**立即停机并切断 24 V**，再排查。

### 责任及规范

夹爪可与其他设备组成完整系统，本文档不包含完整系统的全部设计、安装与操作内容。完整系统安装的安全性取决于集成方式，使用者需依据所在国家/地区法律法规与安全规范，对完整系统进行设计与安装风险评估，并采取相应防护措施。

开始使用本夹爪即视为已阅读、理解并接受本文档及安全信息全部条款。使用者承诺对自身行为及后果负责，仅将夹爪用于正当目的。对违反使用要求或不可抗力导致的人身伤害、事故、财产损失等，我司不承担相应责任。使用者需履行但不限于：对完整系统做风险评估、编制操作规程、建立安全措施、确认系统设计安装无误、**不擅自修改或绕过安全措施**。

### 风险评估

从软件侧看，风险评估应特别考虑以下失效模式：

- 上位机进程卡死或崩溃，运动指令停止发送但机构仍带着最后一条力矩指令；
- CAN 掉线导致软件无法停机；
- 位置读数跳变或失效，导致闭环判断错误；
- 目标位置计算错误（尤其 mm 与 rad 混用、忘记 1.508 mm 间隙）导致机构撞向端点；
- 力参数计算错误导致夹持力过大；
- **误把"函数返回了"当成"动作完成了"**；
- 多进程或多个上位机同时向同一台夹爪发送指令。

| 失效模式 | 后果 | 缓解措施 |
|---------|------|---------|
| 进程卡死 | 机构保持最后指令 | 驱动器通信超时（0.4 s）+ 硬件急停 |
| CAN 掉线 | 软件停机失效 | 驱动器超时自动失能 + 硬件急停 |
| 读数失效 | 闭环误判 | 上位机自行校验读数 + 硬件急停 |
| 目标计算错误 | 撞向端点 | 上位机先行限幅 + **机械挡块** |
| 多主站并发 | 指令互相覆盖 | 保证**单主站**，软件层互斥 |

使用者须通过风险评估判断相关危险是否构成不可接受的风险并采取相应措施。夹爪不适合无专业人员指导且不具备完全民事行为能力的人士使用。

> **注意**：**本 SDK 不做安全判断。** 越界目标被**静默钳制**到标定端点、力参数**不做任何校验**、`kp` / `kd` / `tau` 越界被**静默饱和** —— 这三种情形都**不会报错**。各接口的前置条件也只有"已连接"与"已使能"两项，见 [前置条件与调用约束](#前置条件与调用约束)。**建议先读那一节，再读具体接口。**

# SDK 使用指南

## 概述

LiteGrip 的 Python SDK 是 `litegrip` 包。它封装达妙 **DM-J4310-2EC** 电机的 MIT 协议，提供连接、使能、运动、抓取、手动示教、标定、遥操作与状态读取的接口。

**SDK 只做两件事：把毫米换算成电机角度、把牛顿换算成前馈力矩，然后按固定周期把 MIT 帧发到总线上。** 它不做越界检查，不做故障锁存，也不校验力标定。

| 设计原则 | 在接口上的体现 |
|---------|--------------|
| **命令是单向的，反馈才是事实** | CAN 命令帧没有应答；只有电机回传的状态帧能证明命令真的生效 |
| **位置目标会被钳位到端点** | 超出标定行程的目标会被**静默钳位**到端点，既不报错也不拒绝（见 [运动控制](#运动控制开合与位置)） |
| **运动前必须先显式加载标定** | `connect()` **不会**自动加载标定文件；没加载时运动跑在占位系数上（见 [配置对象](#配置对象)） |
| **驱动保护不重复实现** | 过压 / 欠压 / 过流 / 过温 / 断线保护由 DM-J4310-2EC 驱动固件负责 |

> **注意**：**本 SDK 不实现"安全限位"。** 越界目标会被钳位；`kp` / `kd` / `tau` 超出编码范围会被静默饱和；力参数不做任何校验就下发。**防止夹伤工件或夹伤人的措施必须由集成方在软件或硬件上实现。**

**支持环境：**

| 项 | 要求 |
|------|------|
| 操作系统 | **仅 Linux**（内核需支持 SocketCAN）。Windows 与 macOS 未适配 |
| 架构 | x86_64 或 arm64 |
| Python | 3.8 及以上 |
| 运行时依赖 | **无。** 本包只用 Python 标准库加 Linux SocketCAN，不需要 `python-can`，也不需要 `damiao_socketcan` |
| 可选扩展 | `eclipse-zenoh>=1.0`，仅 zenoh 遥操作链路需要 |
| 硬件 | USB-CAN 适配器、24 V 电源、总线两端各 120 Ω 终端电阻 |

> **注意**：**本 SDK 只支持 Linux。** 在其它平台上请按 [CAN 通信协议](#can-通信协议) 自行实现协议。

**包内模块：**

| 模块 | 内容 |
|------|------|
| `litegrip.gripper` | `LiteGrip`，连接与运动入口 |
| `litegrip.actions` | `GripperActions` —— open/close/grasp/zero 引擎，以及 `MotionConfig` 与结果对象 |
| `litegrip.models` | `GripperState`、`GripperConfig`、`GripperInfo`、`GripperStatus`、`GripperMode`、`CalibrationData` |
| `litegrip.constants` | `GripperParams`、`UnitConversion`、`ErrorCode`、`DefaultParams`、`describe_error` |
| `litegrip.exceptions` | 六个异常类加基类 |
| `litegrip.teleop` | `GripperTeleop` 与各传输实现 |
| `litegrip.can` | 原始 SocketCAN 传输与达妙电机编解码，多电机机架用 |

## 库相关依赖

**本包不安装任何东西。** `pyproject.toml` 的 `dependencies` 是空列表：SDK 就是标准库加 Linux SocketCAN，因此它能在连不上软件源的裸控制器上跑起来。没有充分理由就不要加运行时依赖——这个性质本身就是设计目的。

| 依赖类别 | 项 | 说明 |
|------|------|------|
| 运行时 | *（无）* | 装 `litegrip` 不会顺带装任何东西 |
| 可选 | `eclipse-zenoh>=1.0` | 只有 zenoh 遥操作链路会 import 它；用 `pip install 'litegrip[zenoh]'` 安装 |
| 系统 | SocketCAN | Linux 内核自带；虚拟总线用 `modprobe vcan` |

> **注意**：**SDK 没有发布到 PyPI。** `pip install litegrip` 会失败。请按下一节从源码检出安装。

## 1. 安装 SDK

本包没有发布到 PyPI，因此安装从检出 SDK 仓库开始。

**第一步，克隆仓库：**

```bash
git clone https://github.com/nexform-tech/litegrip-python.git
cd litegrip-python
```

**第二步，安装：**

```bash
python3 -m pip install .
```

**第三步，确认能 import：**

```bash
python3 -c "import litegrip; print(litegrip.__version__)"
```

安装成功会打印所装版本号。从未安装过、直接跑源码的检出会打印 `0.0.0+source`，这是 SDK 标记"从散装文件导入、而非已安装发行版"的方式——它不是错误。

**另一种做法：不安装直接跑。** 如果不想装进解释器，把 `PYTHONPATH` 指向源码树即可：

```bash
PYTHONPATH=/path/to/litegrip-python/src python3 your_script.py
```

**卸载：**

```bash
python3 -m pip uninstall litegrip
```

> **注意**：**部署时不要用 `pip install -e .`。** 可编辑安装会把解释器指向你的工作副本，之后在该目录上执行一次 `git checkout`，机器人跑的东西就被悄悄换掉了。驱动机器的那台机器上用 `pip install .`，可编辑安装只留给开发机。

## 2. 配置 CAN 接口

SDK 能打开接口之前，接口必须存在、处于 up 状态且波特率正确。这需要 root 或 `CAP_NET_ADMIN` 能力。

**第一步，确认接口存在：**

```bash
ip -details link show can0
```

**第二步，拉起接口：**

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000 fd off
sudo ip link set can0 up
```

> **注意**：**`fd off` 不能省略。** 如果接口被配成 CAN FD 模式，即使波特率写对了也**完全无法通信**——而且这个现象看起来很像"24 V 没接"，很容易误判成硬件故障。

**没有硬件时**，先用虚拟总线验证软件环境：

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

> 虚拟总线上没有真实电机，所以**使能这一步会超时**（`enable()` 收不到任何反馈帧，重试耗尽后抛 `HardwareError`）。这是**预期行为**，不是故障。

## 3. 接 24 V 驱动电源

电机要出力、要转动，就需要 24 V。请在第一条运动命令之前接上。

> **CAN 通信由 USB-CAN 适配器独立供电**，所以不接 24 V 时你**仍能读状态和参数**，但电机会报欠压故障（`ERR = 0x9`）且不响应运动命令。排查"命令发了但不动"时，**先查 24 V**。

## 4. 加载标定

每一台的行程端点与毫米刻度都不同，所以 SDK 出厂带的是占位值，真实的要靠标定文件加载进来。

```python
gripper.connect()
gripper.load_calibration()      # 本通道的文件，再退到出厂标定
gripper.enable()
```

> **注意**：**`connect()` 不会加载标定文件。** 它只做两件事：打开总线、注册电机。标定必须由调用方**显式**加载。
>
> **注意**：**跳过这一步的后果，在 API 上是分成两半的。** 此时 `config` 里仍是 `GripperConfig()` 的默认值（`pos_closed_rad=1.14`、`pos_open_rad=0.0`、`rad_to_mm=105.26`），`config.calibrated` 为 `False`。
>
> | 层次 | 未标定时的行为 |
> |------|------|
> | `open()`、`close()`、`grasp()` | **拒绝执行**，抛 `CommandError`（"配置尚未标定…"）。动作层要经过 `limit_target()` / `press_target()`，这两个函数都会调标定检查 |
> | `goto()`、`goto_rad()`、`move_to()`、`move_at_speed()`、`move_at_speed_rad()`、`home()`、`send_mit_frame()` | **照常执行**，静默地跑在占位系数上 |
>
> 也就是说，*高层*动作会大声失败——这是好事，崩溃容易发现。*中层*接口则是安静地失败，这才是问题。**把这道检查当作一层的安全网，而不是"可以不调 `load_calibration()`"的理由。**

`load_calibration()` 可以不带参数、带 `path=`、或带 `template=`；不带参数时先找本通道自己的文件，再找旧的单文件路径，最后退到 SDK 内置的出厂标定。完整查找顺序见 [标定与零点](#标定与零点)。

## 5. 跑起来：让夹爪动一下

整个程序就是这样。它连接、加载标定、使能、张开、闭合，再以 20 N 抓取一次。

```python
from litegrip import LiteGrip

with LiteGrip(channel="can0", can_id=0x08) as gripper:
    gripper.load_calibration()   # 本通道的标定文件，再退到出厂标定
    gripper.enable()             # 重试到状态帧报 err == 1 为止

    gripper.open()                                     # 以 50 mm/s 顶到张开侧限位
    gripper.close()                                    # 以 50 mm/s 顶到闭合侧限位
    result = gripper.grasp(force_n=20.0, hold_s=3.0)   # 闭合到夹住，再保持 20 N
    print(result.reached, result.stalled, result.cycles)
```

存成 `first_move.py` 然后运行：

```bash
python3 first_move.py
```

**逐行说明：**

| 行 | 做了什么 |
|------|------|
| `with LiteGrip(...) as gripper:` | 打开 CAN 总线并注册电机。离开 with 块时调用 `disconnect()`，默认会先失能电机 |
| `gripper.load_calibration()` | 把本台的行程端点与毫米刻度读进 `config` |
| `gripper.enable()` | 先失能、切 MIT 模式、使能，然后**等一帧反馈**确认。返回 `EnableResult` |
| `gripper.open()` | 朝张开侧斜坡运动，直到机械限位结束这段运动。返回 `MoveResult` |
| `gripper.close()` | 在闭合侧做同样的事 |
| `gripper.grasp(force_n=20.0, hold_s=3.0)` | 闭合到位置不再变化，然后保持 20 N 前馈力矩 3 秒。返回 `GraspResult` |

**预期输出** —— `GraspResult` 的三个字段：

```text
False True 12
```

`stalled=True` 表示位置停止变化，也就是手指碰到物体的情形。`reached` 为 `False` 是因为夹口没到目标角度。`cycles` 是闭合阶段跑了多少个控制周期。

> **不要**指望抓住东西时 `reached=True`。抓取场景里 `stalled=True`、`reached=False` 才是成功。`open()` 和 `close()` 恰好相反：它们是靠顶住机械限位来成功的，所以 `ok=True` 总是伴随 `stalled=True`。

> **注意**：**这三段示例是按 SDK 源码及其 README 写的，本版手册没有在硬件上跑过。** 接口名、签名与默认值都已对照 SDK 核过，但打印出来的是示例数值——你的 `cycles` 计数和具体位置都会不同。见 [报告与验证状态](#报告与验证状态)。

## 6. 夹爪不动的时候

| 现象 | 可能原因 | 检查什么 |
|------|------|------|
| `enable()` 抛 `HardwareError`，没有任何反馈 | 没有 24 V；电机不应答 | 量 24 V 母线；没有 24 V 时错误码是 `0x9` |
| 虚拟总线上 `enable()` 抛 `HardwareError` | 预期行为——`vcan0` 上没有电机 | 无需处理；使能这一步要用真实硬件 |
| 什么都不动，也不报错 | 标定没加载，所有目标都钳到同一个值 | 调 `load_calibration()`，检查 `config.calibrated` |
| 什么都不动，`ERR = 0x9` | 欠压——驱动电源缺失或跌落 | 带载量 24 V 母线 |
| 什么都不动，`ERR = 0xA` | 过流——手指碰到障碍或硬限位 | 排除障碍后 `clear_fault()` |
| 什么都不动，`ERR = 0xB` / `0xC` | MOS 或线圈过温 | 等它降温；检查占空比 |
| 波特率对但通信失败 | 接口被拉成了 CAN FD 模式 | 按第二步加 `fd off` 重来 |
| 帧时断时续，总线报错 | 终端电阻缺失或不对 | 总线两端各接 120 Ω |
| `connect()` 抛 `ConnectError` | 接口没 up，或 `channel` 名写错 | `ip -details link show can0` |
| 运动发涩或手指嗡嗡响 | `kp` / `kd` 与负载不匹配 | 见 [运动调参（MotionConfig）](#运动调参motionconfig) |

**直接读错误码：**

```python
state = gripper.get_state()
print(f"0x{state.error_code:X}")
```

`is_error` 在错误码既不是 `0`（失能）也不是 `1`（使能）时为 `True`。完整错误码表见 [反馈帧与错误码](#反馈帧与错误码)；异常类见 [异常与错误处理](#异常与错误处理)。

## 使能、失能与故障处理

```python
gripper.enable()        # 使能，带完整初始化与反馈确认
gripper.disable()       # 失能
gripper.clear_fault()   # 清驱动故障
```

**`enable()` 的完整时序**：失能 → 切 MIT 模式 → 使能 → **等一帧反馈确认**。如果当前错误码不是 `0x0` / `0x1`，它会先自动调一次 `clear_fault()` 清故障。

**`enable()` 返回 `EnableResult`**，只有命令发出后收到了有效反馈帧（`ERR ∈ {0x0, 0x1}`），`ok` 才为 `True`；重试耗尽仍未确认则抛 `HardwareError`——它不会伪造成功。`tries` 报告用了几次尝试。

**本节接口只检查两件事：已连接、已使能。** 任一不满足即抛 `NotInitializedError`。

| 方法 | 签名 | 说明 |
|------|------|------|
| `enable()` | `enable(retries=None) -> EnableResult` | 使能并确认。`retries=None` 时取 `MotionConfig.enable_retries`（3） |
| `disable()` | `disable() -> bool` | 力矩归零，可反驱。成功与否没有反馈确认 |
| `clear_fault()` | `clear_fault() -> bool` | 失能 → 清故障（`0xFB`）→ 使能 → 确认，最多重试 `GripperParams.FAULT_CLEAR_RETRIES`（5）次 |
| `stop()` | `stop() -> None` | 急停：发一帧零力矩 MIT 帧。**不使能也不失能**，不锁存，无返回值 |

> **注意**：**`stop()` 不是安全级停止。** 它只发一帧零力矩就返回；电机保持使能，会接受下一条命令。真正的急停要用硬件开关切断 24 V——见《产品手册》安全章节。

## 运动控制（开合与位置）

**两层，而且两层对"标定"的态度不一致。**

| 层次 | 方法 | 前置条件 | 未标定时 |
|------|------|------|------|
| **高层动作** | `open`、`close`、`grasp`、`zero` | 已连接、已使能、**已标定** | 抛 `CommandError` |
| **中层接口** | `goto`、`goto_rad`、`move_to`、`move_at_speed*`、`home` | 已连接、已使能 | 跑在占位系数上 |

高层动作跑的是闭环引擎：带速度前馈的斜坡、堵转检测，并返回结果对象。中层接口按固定时长发 MIT 帧流，返回一个普通 `bool`。

> **本节接口整体只检查已连接与已使能**，任一不满足抛 `NotInitializedError`。标定**只有**高层动作会查，路径是 `limit_target()` / `press_target()`；**`goto` / `goto_rad` / `move_to` / `move_at_speed*` / `home` 从不检查标定**——没加载标定时它们不报错，继续用 `rad_to_mm = 105.26` 换算毫米。

| 方法 | 目标 | 说明 |
|------------------------|--------------------------------------------|--------------------------------|
| `open()` | 越过标定的张开端点 | 斜坡顶到张开侧机械限位，由限位结束运动；返回 `MoveResult` |
| `close()` | 越过标定的闭合端点 | 在闭合侧做同样的事；要出力抓取请用 `grasp()` |
| `grasp()` | 闭合到堵转，然后保持力 | 返回 `GraspResult`；见 [抓取与力控](#抓取与力控) |
| `zero()` | 依次到两端 | 完整标定；返回 `CalibrationData` |
| `home()` | `config.pos_closed_rad` | **用本实例标定出的闭合限位**，所以反装的机器会回到正确的那一端；返回 `bool` |
| `goto()` | 绝对位置（mm） | 内部换算成 rad 后走 `goto_rad()` |
| `goto_rad()` | 绝对位置（rad） | 唯一会做钳位的对外入口 |
| `move_to()` | 绝对位置（rad） | 它就是 `goto_rad()`，只是默认时长更长 |
| `move_at_speed()` | 定线速度运动 | 端点同样被钳位 |
| `move_at_speed_rad()` | 定角速度运动 | 端点同样被钳位 |
| `send_mit_frame()` | 直接发一帧 MIT | 专家接口，**不钳位、不查饱和** |

**通用参数**（`kp` / `kd` 省略时取 `config` 中的值）：

| 参数 | 默认值 | 说明 |
|------|------|------|
| `kp` / `kd` | 100.0 / 2.0 | 位置刚度 / 阻尼 |
| `duration` | 见签名 | 运动时长（秒） |
| `force_n` | `None` | 目标夹持力（N）；`None` = 不加前馈力矩 |
| `dq_target` | `0.0` | 目标速度前馈（rad/s），仅 `goto_rad` |
| `tau_feedforward` | `0.0` | 前馈力矩（N·m）；`goto_rad` / `move_to` 直接收它，`set_force` 收的是 `force_n` 换算来的值 |
| `speed_mm_s` | `MotionConfig.speed_mm_s`（50.0） | `open` / `close` 的开合速度 |
| `speed_mm_s` | 30.0[未实测] | `move_at_speed` 的线速度（mm/s） |
| `speed_rad_s` | 0.5[未实测] | `move_at_speed_rad` 的角速度（rad/s） |

> `duration` 的默认值写在下面的签名里：`home` / `move_to` 是 1.0 秒，`goto` / `goto_rad` 是 0.5 秒，`set_force` 是 0.3 秒。

**完整签名：**

```python
home() -> bool
open(speed_mm_s=None, *, progress=None) -> MoveResult
close(speed_mm_s=None, *, progress=None) -> MoveResult
goto(position_mm, kp=None, kd=None, duration=0.5) -> bool
goto_rad(position_rad, kp=None, kd=None,
         dq_target=0.0, tau_feedforward=0.0, duration=0.5) -> bool
move_to(target_rad, kp=None, kd=None,
        tau_feedforward=0.0, duration=1.0) -> bool
set_force(force_n, duration=0.3) -> bool
move_at_speed(target_mm, speed_mm_s=30.0, kp=None, kd=None) -> bool
move_at_speed_rad(target_rad, speed_rad_s=0.5, kp=None, kd=None) -> bool
send_mit_frame(q, kp, kd, dq=0.0, tau=0.0) -> bool
```

典型用法：

```python
with LiteGrip(channel="can0", mst_id=0x18) as gripper:
    gripper.load_calibration()      # 先加载标定
    gripper.enable()
    gripper.open()                  # 顶到标定的张开限位
    gripper.goto(60.0)              # 走到 60 mm
    gripper.close()                 # 顶到标定的闭合限位
```

> **注意**：**超出标定端点的目标会被静默钳位。** `goto_rad()` 内部是
> `position_rad = max(pos_open_rad, min(pos_closed_rad, position_rad))`，
> `move_at_speed_rad()` 同样把端点钳到 `[pos_open_rad, pos_closed_rad]`。
> **它不抛异常，也不告诉你钳过。** 需要"越界就拒绝"的语义，请在调用前自己判断。

> **注意**：**`open()` 与 `close()` 是故意越过标定限位的。** 由机械限位结束运动，所以成功的 `open()` 会报 `stalled=True`：夹口正以很小的压紧力矩抵在限位上。做全开或全闭时这是有意的，但这也意味着调用后的位置不是标定端点——需要真实停止位置就读 `result.state.position_mm`。想停在限位之前，请用 `goto()`。

> **注意**：**`send_mit_frame()` 完全不钳位、不查范围。** 它只检查"已连接、已使能"；越界的 `q` 原样发出；`kp` / `kd` / `tau` 超出编码范围时在编码阶段被静默饱和到 `[0, 500]` / `[0, 5]` / `[−10, 10]`。除非你要自己控制单帧时序，否则请用高层接口。

> **注意**：**速度是"时长分配"，不是"速度限制"。** `duration` 只决定这一串帧持续多久——帧以 200 Hz（5 ms 周期）发出，位置目标在整个时长内平滑过渡。要真正限制最大速度，请用 `move_at_speed()` / `move_at_speed_rad()`，它们按给定速度算出目标序列。

## 抓取与力控

```python
grasp(force_n=None, hold_s=0.0, *, progress=None) -> GraspResult
```

`force_n=None` 时取 `MotionConfig.force_n`（20.0 N）。`hold_s=0.0` 表示保持到出故障或你按 Ctrl+C。

**时序**：朝机械限位做斜坡闭合 → **每个周期比较位置** → 位置变化连续 `MotionConfig.stall_cycles` 个周期低于堵转判据即判定"已抓住"，随后以 `force_n × 0.1` N·m 的**前馈力矩**保持。

> **这里的"自适应"指位置堵转检测，不是力矩检测。** 判据是加窗位置变化低于 `MotionConfig.stall_delta`，与力矩读数无关。

| `GraspResult` 字段 | 含义 |
|------|------|
| `ok` | 保持阶段正常结束。`bool(result)` 返回的就是它 |
| `reached` | 夹口到达目标角度、没有堵转 |
| `stalled` | 位置停止变化——**夹住物体时的正常结果** |
| `state` | 保持结束时的 `GripperState` |
| `target_rad` / `force_n` | 目标角度与所保持的力 |
| `cycles` | 闭合阶段跑过的控制周期数 |

> **注意**：**成功的抓取报的是 `stalled=True`、`reached=False`。** 因为堵转判据是位置式的，夹住物体和走到行程端点对它来说是一样的——**光靠这两个标志分不出"夹到东西"和"空夹到限位"。** 请配合 `get_position()`：空夹会停在闭合端点，夹到物体则停在端点之前。

**不闭合、只加力：**

```python
set_force(force_n, duration=0.3) -> bool
```

以 `kp=150.0, kd=2.0` 保持当前位置，并叠加 `force_n × 0.1` N·m 的前馈，持续 `duration` 秒。

> **注意**：**力参数完全不做校验。** `force_n` 按标称系数 `UnitConversion.N_TO_NM = 0.1 N·m/N` 换算后原样下发，负值就按负力矩发。`force_n=20.0` 对应 `2.0 N·m` 前馈，是力矩编码上限 `10 N·m` 的五分之一。
>
> ```python
> gripper.grasp(force_n=0)      # 只按位置闭合：不加前馈力矩
> gripper.grasp()               # 取 MotionConfig.force_n（20 N）→ 2.0 N·m 前馈
> ```

> **注意**：**`force_n` 的物理含义没有标定过。** `0.1 N·m/N` 是标称换算系数；**在力标定完成之前，不要把它用于安全决策或负载设计**。

## 读取状态

```python
state = gripper.get_state(wait=True)
```

| `GripperState` 字段 | 类型 | 说明 |
|---------------------|------|-------------|
| `position_rad` | `float` | 位置（rad） |
| `position_mm` | `float` | 位置（mm，按换算系数折算） |
| `velocity_rad_s` | `float` | 速度（rad/s） |
| `torque_nm` | `float` | 力矩（N·m） |
| `force_n` | `float` | **估算**夹持力（N） |
| `temperature_mos` | `int` | MOS 温度（℃） |
| `temperature_coil` | `int` | 线圈温度（℃） |
| `error_code` | `int` | 电机错误码 |
| `timestamp` | `float` | 采样时间戳 |

`get_state(wait=True)` 最多等 50 ms 收一帧新反馈；`wait=False` 直接返回上一帧缓存，适合高频控制循环。

**派生属性：**

| 属性 | 说明 |
|------|------|
| `is_enabled` | 电机是否已使能（`error_code == 1`） |
| `is_error` | 是否处于故障（`error_code` 既非 0 也非 1） |
| `is_moving` | 速度是否超过小阈值（0.01） |
| `aperture_mm` | 开合读数（**单指位移**） |

> **注意**：**`force_n` 是估算值**，由 `torque_nm × UnitConversion.NM_TO_N` 折算，而 `NM_TO_N = 10.0` 是**标称换算系数**（源码注释标的是 `approximate`），不是标定值。**在力标定完成之前，请不要把 `force_n` 当作真实夹持力。**
>
> **总开口 = `aperture_mm` × 2**（该字段是单指位移）。单指行程 43.500 mm × 2 = 总行程 87.000 mm。

**便捷读取方法：**

| 方法 | 返回 |
|------|------|
| `get_position()` / `get_position_rad()` | 位置（mm / rad） |
| `get_force()` | 估算夹持力（N） |
| `get_torque()` | 力矩（N·m） |
| `get_error()` | 错误码 |
| `get_temperature()` | `(MOS 温度, 线圈温度)` |
| `get_info()` | `GripperInfo` —— 型号、电机型号、CAN ID、固件版本、序列号 |

**状态判定方法：**

| 方法 | 返回 |
|--------------------------------------|--------------------------------------------------------------|
| `is_moving()` | 夹爪是否在运动 |
| `is_grasped()` | `abs(torque_nm)` 是否超过 `config.grasp_torque_threshold`（默认 0.5 N·m）[待实测 · C，力标定完成前无法定值] |
| `wait_for_ready(timeout=5.0)` | 阻塞到已使能且静止；超时返回 `False` |

**轮询与专家接口：**

| 方法 | 说明 |
|------|------|
| `poll(timeout_s=0.0) -> bool` | 轮询一帧反馈并更新内部状态；未连接返回 `False` |
| `read_param(rid, timeout_s=0.5) -> float` | 按寄存器 ID 读驱动参数 |

> **注意**：**反馈是请求驱动的。** 驱动只在收到上位机的帧之后才回帧——**单纯监听总线永远收不到任何反馈**。

> **注意**：**`read_param` 的寄存器表见 [参数帧与寄存器](#参数帧与寄存器)。** 特别注意：`OC_Value` 是比例值不是安培；位置 / 速度 / 力矩的 MIT 量化范围不是保护阈值。

## 单位与换算

**SDK 没有暴露换算方法。** `mm ↔ rad` 的换算内联在两处：

```python
# goto()（gripper.py）
position_rad = config.pos_closed_rad - position_mm / config.rad_to_mm

# get_state()（gripper.py）
position_mm = (config.pos_closed_rad - position_rad) * config.rad_to_mm
```

也就是说，**`rad` 越小开口越大**；`pos_closed_rad` 是数值较大的一端，`pos_open_rad` 是数值较小的一端。

**换算系数 `rad_to_mm` 由标定过程写入**，等于"用于标定的行程（mm）÷ 实测角行程（rad）"。本机实测值为：

> **有效行程 87.000 mm ÷ 本机实测角行程（rad）= 本机 `rad_to_mm`**。分子是 `config.max_stroke_mm`，分母是标定过程中实测的 rad 跨度；**两个数都随机而异**。本机的取值见随机附带的标定文件与《产品手册》2.2 节。

> **注意**：**`rad_to_mm` 只影响"显示的毫米数与毫米目标"**；它不动任何边界，因为钳位用的 `pos_closed_rad` / `pos_open_rad` 本身就是 rad 值，不依赖 `rad_to_mm`。系数错了只是毫米数不对。
>
> **注意**：**`position_mm` 与卡尺量到的开口差 1.508 mm。** SDK 的 mm 零点在机械全闭处，而该处两指之间还有 1.508 mm 间隙。卡尺读数 ≈ `get_position() + 1.508`（该式在闭合端精确，在张开端高估约 1.5 mm；精确关系见 [单位说明](#单位说明)）。

## 手动示教（零重力）

```python
gripper.enter_zero_gravity()       # 夹爪变软，可以用手推动
input("摆好位置后按回车……")
gripper.exit_zero_gravity()        # 保持当前位置
```

**`enter_zero_gravity(duration=0.0)`** —— 进入零重力模式：电机保持使能，但持续发 `kp=0, kd=0, tau=0` 的帧，机构可以被自由推动。

| `duration` | 效果 |
|-----------|------|
| `> 0` | 阻塞这么久并持续发零力矩帧；到期后**只是停止发帧**，不会自动回到位置保持 |
| `0`（默认） | 只发**一帧**示教帧；**必须由调用方持续轮询或发帧**，否则驱动会因通信超时失能 |

> **注意**：**零重力模式下不保持位置。** 电机不出力，重力与摩擦力决定手指停在哪。要"松手即停在原处"，必须在松手后调 `exit_zero_gravity()`。
>
> **注意**：`duration > 0` 这种形式**不会自动退出零重力模式**；循环结束后不再发帧。需要位置保持就显式调 `exit_zero_gravity()`。

**`exit_zero_gravity()`** —— 退出零重力模式，以当前位置为目标、用 `config.kp` / `config.kd` 闭环保持。

> **注意**：**退出时不校验位置。** 如果手推把手指推到了行程之外，`exit_zero_gravity()` 会直接把实测位置当目标用（`send_mit_frame` 这条路不经过钳位）；只有之后调用普通运动接口时，目标才会被钳回标定端点。

> **手动示教只有上面两个零重力原语。** 要做"抓一下再松开"的循环，请自己组合 `enter_zero_gravity()` / `exit_zero_gravity()` / `grasp()`。

## 标定与零点

**四个标定入口：**

| 方法 | 驱动力 | 限位如何检测 | 需要人 |
|------|--------|---------------|--------|
| `zero()` | 电机 | 电机堵转检测，一次调用走完两端 | 需在场 |
| `calibrate()` | 电机 | **电机堵转检测**（位置增量连续多个周期低于阈值） | 需在场 |
| `calibrate_guided()` | 电机 | 每个端点用回车确认，或自动电机堵转检测 | 每个端点按回车 |
| `calibrate_manual()` | 手推（零重力） | 手推到底，记录极值 | 全程手推 |

`zero()` 是一次调用版：探测两端限位，算出行程与 `rad_to_mm`，并把结果存到默认标定路径。

> **注意**：**`zero()`、`calibrate()` 与 `calibrate_guided()` 会一路顶进机械硬限位。** 它们朝一个方向按电机动力步进，直到位置不再变化（电机堵转），中途不会自行停止。运行前请确认机械硬限位和结构受得住这股力，且**现场必须有人守着有效的硬件急停**。
>
> **推荐 `calibrate_manual()`**：手推到底不给机构施加任何电机力，是三者中最温和的。

```python
zero() -> CalibrationData

calibrate(kp=20.0, kd=2.0, step_rad=0.05,
          stall_delta=0.0015, stall_cycles=5,
          max_iter=200, tau_limit=2.0) -> CalibrationData

calibrate_guided(kp=20.0, kd=2.0, step_rad=0.05,
                 stall_delta=0.0015, stall_cycles=5,
                 max_iter=200, tau_limit=2.0) -> CalibrationData

calibrate_manual(duration=30.0, settle_time=2.0,
                 sample_interval=0.01) -> CalibrationData
```

两种探测法都把命令领先量限制在 `step_rad`，并在力矩达到 `tau_limit` 时中止，所以端点设错也不会让电机以满刚度撞进结构里。

`calibrate_manual()` 的步骤：调用后夹爪进入"变软"状态 → 用手推到全闭，再推到全开 → 反复几次 → 时间到自动返回（也可按 Ctrl+C 提前结束并保留已采到的读数）。

**标定文件的保存与加载：**

| 方法 | 签名与说明 |
|------|-----------|
| `save_calibration(path=None) -> str` | `path=None` 时写 `~/.litegrip/<channel>_calibration.json`，并**返回写入的绝对路径**。一个通道一个文件，这样同一台机器上的两个夹爪不会互相覆盖 |
| `load_calibration(path=None, template=None) -> bool` | 把标定加载进 `config`。请在 `connect()` 之后、`enable()` 之前调用 |
| `load_template(name) -> bool` | 加载 `"normal"` 或 `"reverse"` 安装模板，声明安装方向。`name` 必须是 `list_templates()` 之一 |

**不带参数时 `load_calibration()` 的查找顺序**：本通道自己的文件 → 旧的单文件路径 `~/.litegrip/litegrip_calibration.json` → SDK 内置的出厂标定。传 `path=` 读指定文件（仍可能退到出厂文件），传 `template="normal"` / `template="reverse"` 加载安装模板（这条路径是严格的，不会退）。同时传 `path` 与 `template` 会抛 `CommandError`。

> **注意**：**`load_calibration()` 不校验来源的任何内容。** 它只处理"文件不存在"和"JSON 解析失败"；文件里写什么它就信什么。如果文件标注的通道不是当前通道，它会跳过并打一条警告，而不是失败。
>
> **更换或维修夹爪、更换电机、更换手指、发生碰撞或过载之后，必须重新标定。**

**关于标定出的换算系数：**

系数按 `rad_to_mm = 用于标定的行程（mm）÷ 实测角行程（rad）` 计算，其中"用于标定的行程"取自：

| 入口 | 分子取值 |
|------|---------|
| `zero()` / `calibrate()` / `calibrate_manual()` | `config.max_stroke_mm`，**默认 `120.0`** |
| `calibrate_guided()` | `config.max_stroke_mm` |

> **该格的取值约定已定：用"有效行程"，本机为 `87.000 mm`** [卡尺复测全开开口 87.000 mm，与有效行程同值]。
> 该值已写入本机标定文件的 `max_stroke_mm`。
>
> **读数约定（必读）**：`87.000` 是 **SDK 位置 `p` 的跨度**（0 → 87.000），而**实际开口**用卡尺量出的跨度是
> **85.492 mm**（张开端 87.000，闭合端 1.508）。也就是说，`max_stroke_mm = 87.0` 会让 SDK 的"1 毫米"
> 比真实毫米**大 1.8 %**（87.000 ÷ 85.492）。**要毫米级精度，请用卡尺跨度 `85.492` 作分子**，
> 并在标定后核对 `rad_to_mm = 85.492 ÷ 实测 rad 跨度`。

> **注意**：**默认的 `120.0` 是占位行程，不是本机实测行程（本机 87.000 mm）。** 如果按默认配置标定，算出的 `rad_to_mm` **整体偏大 1.38 倍**（87.000 → 120 之比）并被写进标定文件；此后每一次毫米读数和每一个基于毫米的阈值都会差 38 %，而文件里的 `travel_range_rad` 那一格看起来完全正常，事后极难发现。
>
> **正确做法**：先用游标卡尺量出全开开口，把 `max_stroke_mm` 设成实测值（本机 `87.000`，若要卡尺跨度则 `85.492`），再标定；标定结束后核对写进去的 `rad_to_mm` 是否等于"你输入的分子 ÷ 实测 rad 跨度"。
>
> **注意**：这些入口只在 `travel <= 0` 时抛 `RuntimeError`；`max_stroke_mm` 取 `0` 或 `120.0` **不会**报错。

## 配置对象

**`GripperConfig` 字段（共 13 个）：**

| 字段 | 默认值 | 说明 |
|------|------|------|
| `can_channel` / `can_id` / `mst_id` / `canfd_mode` | `"can0"` / `0x08` / `None` / `False` | 连接参数 |
| `kp` / `kd` | `100.0` / `2.0` | 位置刚度 / 阻尼（各接口省略时的默认值） |
| `pos_closed_rad` / `pos_open_rad` | `1.14` / `0.0` | 行程两端（**标定后被标定文件覆盖**） |
| `calibrated` | `False` | 是否已加载标定（**由 `load_calibration()` 置位**） |
| `max_stroke_mm` | `120.0`（**占位值；本机应填入 `87.000`**） | 机械行程（mm），**只在标定时用作刻度分子**；见 [标定与零点](#标定与零点) |
| `rad_to_mm` | `105.26` [标定后由脚本算出] | 角度 → 毫米换算（**未标定时是占位值**） |
| `nm_to_n` | `10.0` | 力矩 → 力换算。**当前代码不读这个字段**，实际用的是类常量 `UnitConversion.NM_TO_N = 10.0`，改它没有效果 |
| `grasp_torque_threshold` | `0.5` [待实测 · C，无依据，力标定完成前无法定值] | `is_grasped()` 的判定阈值（N·m） |

**派生属性** —— 方向是数据，不是另一个开关：

| 属性 | 返回 |
|------|------|
| `close_sign` | 闭合对应 rad 增大时为 `+1.0`（常见安装），反装为 `-1.0`。由两个限位的数值顺序推出 |
| `mount` | `"normal"` / `"reverse"` —— 限位所拼出的安装方向，**`calibrated` 为 `False` 时返回 `None`** |

> **注意**：**`mount` 在加载标定之前刻意返回 `None`。** 占位默认值恰好也是闭合端数值较大，所以标定之前报 `"normal"` 是断言而不是读数。不要把 `config.mount` 当作"标定发生过"的凭据——要看 `config.calibrated`。

> **注意**：**`pos_closed_rad` / `pos_open_rad` / `rad_to_mm` 的默认值是占位值，不是本机的真值。** 真值在标定文件里，只有显式调用 `load_calibration()` 才生效（`connect()` 不会做这件事）。`config.calibrated` 告诉你现在跑的是哪一套。

> **注意**：**不要在默认配置下跑中层接口。** 它们不检查 `calibrated`，所以 `rad_to_mm = 105.26` 会把每个毫米目标静默换算成错误的角度，而 `max_stroke_mm = 120.0` 是错的标定分子。高层动作起码会抛 `CommandError`，它们不会。**这就是"下任何运动命令之前先调 `load_calibration()`"最直接的理由。**

## 前置条件与调用约束

**SDK 有三道前置检查，而且应用得并不一致。** `_check_connected()` 与 `_check_enabled()` 失败时抛 `NotInitializedError`；`_check_calibrated()` 抛 `CommandError`，且**只能**经由 `limit_target()` / `press_target()` 到达，也就是只有高层动作会触发它。

| 接口 | 已连接 | 已使能 | 已标定 | 说明 |
|------|:---:|:---:|:---:|------|
| `connect` / `disconnect` | — | — | — | 除非 `disable_on_disconnect` 为 `False`，`disconnect()` 会先试 `disable()` |
| `enable` / `disable` / `clear_fault` | ● | — | — | |
| `stop` | — | — | — | **不检查**。未连接或未使能时是空操作，返回 `None` |
| `send_mit_frame` | — | — | — | **不抛异常**。前置条件不满足时直接返回 `False` |
| `poll` | — | — | — | **不抛异常**。未连接时返回 `False` |
| `goto` / `goto_rad` / `move_to` / `move_at_speed` / `move_at_speed_rad` | ● | ● | — | |
| `home` | ● | ● | — | 用 `config.pos_closed_rad`——未标定时那是**占位值** |
| `open` / `close` / `grasp` | ● | ● | **●** | 未标定时抛 `CommandError` |
| `zero` / `calibrate` / `calibrate_guided` / `calibrate_manual` | ● | ● | — | 它们*产出*标定，所以不能要求已有标定 |
| `set_force` | ● | ● | — | 保持当前位置；不瞄准端点，因此不适用该检查 |
| `enter_zero_gravity` | ● | ● | — | |
| `exit_zero_gravity` | — | — | — | **不抛异常**。未使能时是空操作 |
| 所有 `get_*` 方法（含 `is_moving` / `is_grasped` / `wait_for_ready`） | ● | — | — | `get_info()` 读静态信息，不检查 |
| `load_calibration` / `save_calibration` / `load_template` | — | — | — | 纯文件 I/O |
| `read_param` | ● | — | — | |
| `teleop_start` | ● | ● | **●** | 会调 `check_ready(config)`；见 [遥操作（主从）](#遥操作主从) |

**图例**：● = 必须满足；— = 不需要。

> **不要**把这张表读成"凡是标 — 的都安全"。未标定的 `home()` 会朝占位值 `pos_closed_rad` 去，把你带到没打算去的位置；`set_force` 会在完全不知道端点在哪的情况下，把它恰好所在的当前位置保持住。**`—` 的意思是"没检查"，不是"没影响"。**

## 异常与错误处理

**基类与六个异常类**在 `litegrip.exceptions`：

| 异常 | 触发条件 |
|------|------|
| `LiteGripError` | 基类；带 `message` 与可选的 `error_code` |
| `CommError` | CAN 总线读或写失败 |
| `ConnectError` | CAN 接口不可用，或电机不应答 |
| `CommandError` | 电机拒绝命令，或参数越界 |
| `CANTimeoutError` | 总线上没有响应 |
| `HardwareError` | 达妙故障码：欠压、过流、过温 |
| `NotInitializedError` | 需要已连接 / 已使能的方法在未满足时被调用 |

**遥操作另有四个**，定义在 `litegrip.teleop`，同样派生自 `LiteGripError`：`TeleopError`、`TeleopBusyError`（已在运行时又启动）、`TeleopNotActiveError`（操作需要活动会话）、`TeleopNotReady`（夹爪还不能安全遥操作）。**合计 11 个类。**

```python
from litegrip import (
    LiteGripError, CommError, ConnectError, CommandError,
    CANTimeoutError, HardwareError, NotInitializedError,
)

try:
    with LiteGrip(channel="can0") as gripper:
        gripper.load_calibration()
        gripper.enable()
        gripper.grasp(force_n=20.0, hold_s=3.0)
except HardwareError as e:
    print(f"driver fault: {e}")
except CANTimeoutError as e:
    print(f"no response on the bus: {e}")
except LiteGripError as e:
    print(f"SDK error: {e}")
```

> **注意**：**钳位与跳过的力参数不会抛任何异常。** 超出行程的目标被静默钳位，越界的 `kp` / `kd` / `tau` 被静默饱和，未校验的 `force_n` 照常下发。**只捕异常的程序，这三样一个都发现不了。**
>
> **注意**：**`CommandError` 定义了，但实际中很少抛出**——电机拒绝命令目前并没有归到它。

## 运动调参（MotionConfig）

`MotionConfig` 装着高层动作引擎的全部可调项。默认值是在真机上验证过的那一套。可以在构造时传入，也可以事后替换：

```python
from litegrip import LiteGrip, MotionConfig

cfg = MotionConfig(speed_mm_s=25.0, force_n=15.0, stall_delta=0.001)

with LiteGrip(channel="can0", motion_config=cfg) as gripper:
    gripper.load_calibration()
    gripper.enable()
    gripper.open()                              # 25 mm/s
    gripper.grasp(hold_s=2.0)                   # 15 N，配置的默认值

# 也可以在运行中的实例上替换它
gripper.motion_config = MotionConfig(speed_mm_s=80.0)
```

**最可能改到的字段：**

| 字段 | 默认值 | 单位 | 控制什么 |
|------|------|------|------|
| `speed_mm_s` | 50.0 | mm/s | `open()` / `close()` 的斜坡速度 |
| `grasp_speed_mm_s` | 50.0 | mm/s | `grasp()` 闭合阶段的速度 |
| `force_n` | 20.0 | N | `grasp(force_n=None)` 时的默认力 |
| `margin` | 0.05 | 比例 | `limit_target()` 停在标定限位内侧多远 |
| `press_overshoot` | 0.05 | 比例 | `press_target()` 越过限位多远，好让夹口抵在限位上 |
| `stall_delta` | 0.0015 | rad | 加窗位置变化低于多少算堵转 |
| `stall_cycles` | 5 | 周期 | 连续堵转多少个采样算"抓住了" |
| `stall_ratio` | 0.2 | 比例 | 加窗堵转判据的相对阈值 |
| `press_zone_mm` | 2.0 | mm | 距限位多近时收窄命令领先量 |
| `stop_lead_mm` | 0.7 | mm | 收窄后的领先量，它限住了压紧力矩 |
| `max_lead_mm` | 4.0 | mm | 远离限位时的领先量上限 |
| `hold_kp` / `hold_kd` | 150.0 / 2.0 | — | 力保持阶段的增益 |
| `hold_interval` | 0.2 | s | 保持阶段多久重读一次位置 |
| `enable_retries` / `enable_retry_interval` | 3 / 0.2 | — / s | `enable()` 的重试预算 |
| `frame_interval` | 0.005 | s | MIT 帧周期（200 Hz） |
| `sample_interval` | 0.05 | s | 控制环采样周期 |
| `settle_s` | 0.3 | s | 判定运动结束前的稳定时间 |
| `reach_tol` | 0.02 | rad | 距目标多近算"到达" |
| `stop_tol` | 0.02 | rad | 距限位多近算"顶住" |

**标定探测字段**（`calib_*`）调的是 `zero()` 与 `calibrate()`：`calib_kp` / `calib_kd`（20.0 / 2.0）定探测刚度，`calib_step_rad`（0.05）限住命令领先量，`calib_tau_limit`（2.0 N·m）中止探测，`calib_stall_delta` / `calib_stall_cycles` / `calib_max_iter`（0.0015 / 5 / 200）决定何时判定找到了限位。

`sleep_fn` 与 `monotonic_fn` 是给测试和仿真用的时间缝；除非你在写测试，否则别碰。

**进度回调。** `open()`、`close()` 与 `grasp()` 接受 `progress` 回调，每次采样调一次，参数是 `MoveProgress`：

```python
def report(p):
    print(f"{p.phase} {p.i}/{p.total_steps} "
          f"cmd={p.cmd_rad:.3f} pos={p.pos_rad:.3f} tau={p.torque_nm:.2f}")

gripper.close(progress=report)
```

| `MoveProgress` 字段 | 含义 |
|------|------|
| `phase` | 当前阶段名 |
| `i` / `total_steps` | 采样序号与估计总数 |
| `cmd_rad` / `pos_rad` | 命令角度与实测角度 |
| `delta_rad` / `win_delta_rad` | 瞬时与加窗位置变化 |
| `torque_nm` / `temperature_coil` | 力矩与线圈温度 |

> **不要**在进度回调里以 200 Hz 打印。回调跑在控制环上；回调一慢，环就慢，它正在测量的运动本身就被改变了。请像 `examples/teleop.py` 那样先累积、运动结束后再打印。

> **注意**：**`limit_target()` 与 `press_target()` 就是余量与越位背后的辅助函数。** 两者签名都是 `(config, toward, amount)`，`toward` 取 `"close"` 或 `"open"`，返回 `(target, limit, offset_rad, travel_rad)`。`limit_target()` 瞄向限位*内侧*以免压上去；`press_target()` 瞄向限位*外侧*好让夹口抵在限位上。未标定或行程为零时两者都抛 `CommandError`。只有你自己写运动引擎时才需要直接用它们。

## 遥操作（主从）

遥操作把一台夹爪的开口通过网络镜像到另一台。主端由手在零重力下推动，从端跟随。

```python
# 主端：发布本夹爪的开口
with LiteGrip("can0") as master:
    master.load_calibration()
    master.enable()
    master.teleop_start("master")                      # zenoh，gripA，端口 17448

# 从端：连上主端，对齐首帧，然后跟随
with LiteGrip("can0") as slave:
    slave.load_calibration()
    slave.enable()
    slave.teleop_start("slave", host="192.168.1.20")
    while True:
        print(slave.teleop_status())   # frames、openness、loop_hz、stale 等
```

| 方法 | 签名 | 说明 |
|------|------|------|
| `teleop_start()` | `teleop_start(mode, *, transport=None, link="zenoh", host=None, port=17448, grip_id="gripA", kp=None, kd=None, align=True, watchdog_s=0.2, dq_max=10.0, rate_hz=50.0) -> dict` | 启动 `"master"` 或 `"slave"`；返回第一份 `teleop_status()` 快照 |
| `teleop_stop()` | `teleop_stop(timeout=2.0) -> dict` | 停止，并让夹爪保持住。两端都不会失能 |
| `teleop_status()` | `teleop_status() -> dict` | 会话快照，无会话时为 `{"active": False, "mode": None}` |

**传输方式：**

| 传输 | 依赖 | 用途 |
|------|------|------|
| zenoh | `pip install 'litegrip[zenoh]'` | 默认（`link="zenoh"`），用于可路由网络 |
| `UdpTeleopTransport` | 无 | 可信局域网上的纯 UDP。**无认证、不加密** |
| `InProcTeleopTransport` | 无 | 进程内总线，用于测试，或一个程序里带两台夹爪 |

```python
from litegrip import LiteGrip, InProcTeleopTransport

bus = InProcTeleopTransport()          # 两端共用同一个实例
# ……把 transport=bus 传给两端的 teleop_start()
```

线上传的是归一化到 `[0, 1]` 的 `openness`，不是弧度，装在 32 字节大端帧里（`openness | position_mm | force_n | timestamp`）。**因此两端不必共享标定、安装方向或零点**——各端用自己的换算。两端必须约定同一个 `grip_id`。

> **注意**：**遥操作会接管 CAN 总线。** 会话运行期间，遥操作环独占所有 CAN 收发，普通运动调用不会按预期工作。请先调 `teleop_stop()`。
>
> **注意**：**`teleop_start()` 拒绝在未标定的夹爪上运行**，抛 `TeleopNotReady`。想在 `enable()` 之前就知道，可以自己调 `check_ready(config)`。
>
> **注意**：**从端在数据陈旧时保持位置，而不是松掉。** 超过 `watchdog_s` 没有新帧，它停止跟随但继续保持，所以网络断开不会让负载掉落。非有限值的帧会被丢弃并计入 `rejected`。

**可运行示例。** SDK 自带 `examples/teleop.py`，每一端一个进程：

```bash
python3 examples/teleop.py --mode master --channel can0
python3 examples/teleop.py --mode slave  --channel can0 --host 192.168.1.20
```

| 选项 | 默认值 | 含义 |
|------|------|------|
| `--mode` | 必填 | `master`（主端）或 `slave`（从端） |
| `--channel` / `--can-id` | `can0` / `0x08` | CAN 接口与电机 ID |
| `--link` | `zenoh` | `zenoh` 或 `udp` |
| `--host` / `--port` | — / 17448 | 主端地址；主端只监听 |
| `--grip-id` | `gripA` | 话题 ID；两端必须一致 |
| `--mount` | — | 加载 `normal`/`reverse` 模板，代替本通道标定 |
| `--kp` / `--kd` | 取标定 | 从端刚度与阻尼 |
| `--watchdog` / `--dq-max` / `--rate` | 0.2 / 10.0 / 50.0 | 保持超时、前馈速度上限、环频 |
| `--no-align` | 关 | 跳过对齐到首帧的那一次动作 |
| `--dry-run` | 关 | 打印解析出的方案后退出，不碰硬件 |

> **注意**：`examples/teleop.py` 是 SDK 仓库里**唯一**的示例脚本。本手册早前的版本还列了另外十五个（`basic.py`、`cycle_test.py`、`can_diag.py` 等）；那些文件并不存在。**不用去找。**

## 直接驱动总线（litegrip.can）

`litegrip.can` 是 `LiteGrip` 下面那一层：SocketCAN 传输、达妙电机编解码，以及一个持有多个电机的控制器。一个进程要驱动多于一台夹爪，或者需要帧级控制时用它。

| 模块 | 内容 |
|------|------|
| `litegrip.can.transport` | SocketCAN socket 封装——打开、发送、接收 |
| `litegrip.can.protocol` | MIT 帧编解码，以及寄存器（RID）编解码 |
| `litegrip.can.motor` | 单个电机的状态缓存与命令通路 |
| `litegrip.can.controller` | 持有一个传输与多个电机的控制器 |

> **注意**：**这一层不做单位换算，也不做钳位。** 它讲的是弧度、rad/s 与 N·m。毫米与牛顿的便利接口在 `LiteGrip` 和 `GripperActions` 里。如果你直接用 `litegrip.can`，本手册讲的每一次换算、每一道限位和故障检查就都成了你自己的活。

线格式本身——帧布局、字段宽度、量化、寄存器地址——见 [CAN 通信协议](#can-通信协议)。

## 核心 API 速查

| 类别 | 接口 |
|------|------|
| **生命周期** | `LiteGrip(...)`、`connect()`、`disconnect()`、`__enter__` / `__exit__` |
| **使能与故障** | `enable()`、`disable()`、`clear_fault()`、`stop()` |
| **高层动作** | `open()`、`close()`、`grasp()`、`zero()`，以及 `actions` 属性 |
| **运动** | `home()`、`goto()`、`goto_rad()`、`move_to()`、`move_at_speed()`、`move_at_speed_rad()`、`send_mit_frame()` |
| **力控** | `set_force()` |
| **手动示教** | `enter_zero_gravity()`、`exit_zero_gravity()` |
| **标定** | `calibrate()`、`calibrate_guided()`、`calibrate_manual()`、`save_calibration()`、`load_calibration()`、`load_template()`、`list_templates()` |
| **状态** | `get_state()`、`poll()`、`get_position()`、`get_position_rad()`、`get_force()`、`get_torque()`、`get_error()`、`get_temperature()`、`get_info()`、`is_moving()`、`is_grasped()`、`wait_for_ready()` |
| **遥操作** | `teleop_start()`、`teleop_stop()`、`teleop_status()` |
| **专家** | `read_param()`、`send_mit_frame()`、`litegrip.can` 子包 |

**公开导出列表**（`litegrip/__init__.py` 的 `__all__`）：

```python
from litegrip import (
    __version__,
    # high-level interface
    LiteGrip, DEFAULT_CALIB, CALIB_TEMPLATES,
    default_calib_path, list_templates,
    # motion actions
    MotionConfig, MoveProgress, MoveResult, GraspResult, EnableResult,
    GripperActions, limit_target, press_target,
    # data models
    GripperState, GripperConfig, GripperInfo, GripperStatus, GripperMode,
    CalibrationData,
    # constants and enums
    GripperParams, UnitConversion, ErrorCode, DefaultParams,
    describe_error, DM_Motor_Type, Control_Mode,
    # exceptions
    LiteGripError, CommError, ConnectError, CommandError,
    CANTimeoutError, HardwareError, NotInitializedError,
    # teleoperation
    GripperTeleop, TeleopTransport, TeleopSubscription,
    UdpTeleopTransport, InProcTeleopTransport,
    TeleopError, TeleopBusyError, TeleopNotActiveError, TeleopNotReady,
    check_ready, clamp_to_calibrated,
    DEFAULT_GRIP_ID, DEFAULT_GRIP_PORT, DEFAULT_DQ_MAX, FRAME_SIZE,
    encode_frame, decode_frame, teleop_topic,
    # subpackages
    can,
)
```

`ZenohTeleopTransport`、`Listener`、`Connector` 与 `LatestSlot` 在首次访问时才惰性解析；缺少可选的 zenoh 依赖时会抛带安装提示的 `ImportError`。

# 二次开发

以上都是在用 Python 驱动夹爪。本章讲在 LiteGrip 上做二次开发的其它路子：扩展 Python SDK、使用 C++ SDK、集成 ROS 2、跑仿真，以及使用上位机。

**围绕其中任何一项做规划之前，请先读 [尚未就绪的部分](#尚未就绪的部分)。** 有几个组件并不完整，其中一个还是空仓库。

## 扩展 Python SDK

SDK 是刻意分层的，所以你可以换掉一层而不动其它层。

| 目标 | 做法 |
|------|------|
| 改开合与抓取的运动方式 | 传入自己的 `MotionConfig`；见 [运动调参](#运动调参motionconfig) |
| 加一个运动原语 | 组合 `GripperActions` 的原语，或用 `limit_target()` / `press_target()` 加 `send_mit_frame()` 自己搭一个 |
| 一个进程驱动多台夹爪 | 用 `litegrip.can.controller`；一个传输，多个电机 |
| 用自己的链路跑遥操作 | 继承 `TeleopTransport`，实现 `pub` / `sub` / `close` |
| 不带硬件运行 | `vcan0` 虚拟总线，或 `litegrip-pybullet` / `litegrip-mujoco` 做模型在环 |
| 改协议本身 | `litegrip.can.protocol` 就是编解码器；线格式见 [CAN 通信协议](#can-通信协议) |

**自定义遥操作传输：**

```python
from litegrip import TeleopTransport, TeleopSubscription

class MyTransport(TeleopTransport):
    def pub(self, topic: str, payload: bytes) -> None: ...
    def sub(self, topic: str) -> TeleopSubscription: ...
    def close(self) -> None: ...
```

`TeleopSubscription` 必须提供 `try_recv()`，也可以覆盖 `drain_latest()`。

> **不要**碰 `litegrip._internal` 里的名字，也不要碰 `_` 开头的私有方法。它们会无预警地变，而上面那层公开接口对这里列出的每一件事都够用。

## C++ SDK

`litegrip-cpp` 是与 ROS 无关的 C++ SDK，用 CMake 构建。它**只有第一层**：传输、总线持有、`LiteGrip` 对象、标定与 JSON 处理、`SafetyGuard`，以及 `ControlLoop`。

```bash
cmake -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

通过它自己的 CMake 包来 include 和链接：

```cmake
find_package(litegrip REQUIRED)
target_link_libraries(your_target PRIVATE litegrip::litegrip)
```

> **注意**：**力与速度相关的功能在 C++ 里没有实现。** `grasp()`、`set_force()` 与 `move_at_speed*()` 都不存在，而 `close(force_n=...)` **收下力参数然后忽略它**。需要自适应抓取就用 Python SDK，或者等后续 C++ 版本。不要指望把 Python 示例移植到 C++ 就能编译通过。

## ROS 2（ros2_control 与 MoveIt 2）

**`ros2_control` 硬件接口** —— `litegrip-ros2` 提供 `litegrip_ros2_control` 的 `SystemInterface` 插件，直接由 C++ SDK 支撑，链路里没有 Python 守护进程。把它加进控制器配置：

```xml
<ros2_control name="LiteGripSystem" type="system">
  <hardware>
    <plugin>litegrip_ros2_control/LiteGripSystem</plugin>
  </hardware>
  ...
</ros2_control>
```

**运动规划** —— `litegrip-moveit2` 提供夹爪的 MoveIt 2 配置，规划组为 `gripper`，命名状态为 `open`（0.087 m）与 `closed`（0.0 m）。

```bash
ros2 launch litegrip_moveit_config demo.launch.py
```

> **注意**：**该 demo 默认跑在 dry-run 模式。** 要驱动真机，请传 `dry_run:=false hardware_enable:=true max_feedback_velocity_rad_s:=0.9`。`max_feedback_velocity_rad_s` 的默认值是 `-1.0`，它会**拒绝一切运动**——这是刻意的失效安全行为，不是故障。

URDF 模型在 `litegrip-urdf` 里：

```bash
ros2 launch litegrip_urdf display.launch.py
```

加 `stroke:=` 可以覆盖可视化模型用的行程。

> **注意**：**`litegrip-ros1` 还不存在。** 该仓库是个桩，里面只有 CI 配置和一个 README；没有源码、没有包、没有发布。**不要围绕它规划 ROS 1 集成。**

## 仿真（MuJoCo、PyBullet、Isaac Sim）

| 包 | 入口 | 你能得到什么 |
|------|------|------|
| `litegrip-pybullet` | `python3 examples/01_sim_only.py --headless` | `GripperSim`，带 `command_fraction()`、`settle()`、`aperture_mm()`、`finger_force_n()`；以及 sim→real 与 real→sim 的示例 |
| `litegrip-mujoco` | `from litegrip_mujoco import MujocoGripper` | `MujocoGripper`，带 `open`/`close`/`goto`/`grasp`/`get_state`，另有 `MirrorMode` 与 `DualGripper` 做真机与仿真的镜像 |
| `litegrip-isaacsim` | `ISAAC_SIM_PATH=... ./run_gripper.sh` | 一个 Isaac Sim 节点，订阅 `/gripper/joint_traj`，以及一条连到真机 CAN 的桥 |

三者中 `litegrip-mujoco` 最完整，从 `01_hello_sim.py` 到 `05_dual_control.py` 有五个编号示例。

> **注意**：**三个仿真包都没发布到 PyPI**，尽管它们的 README 里写的是相反的话。请和 SDK 一样从检出安装。

> **注意**：**Isaac Sim 桥的真机标定是占位值。** 仿真模型与 sim 节点能用，但用来把真机开口映射到模型上的 `OPEN_MM` 没有实测过。把那条桥给出的 sim-to-real 开口值只当作参考。

## 上位机（litegrip-studio）

`litegrip-studio` 是操作台：一个 PyQt5 应用，用来驱动、标定和监视夹爪，带绘图页与自检模式。

```bash
./run_litegrip_studio.sh sim        # against the simulated backend
./run_litegrip_studio.sh gui        # against real hardware
./run_litegrip_studio.sh selftest   # non-interactive self-check
```

启动脚本最终分发到 `python -m litegrip_studio --backend sim|real`。`PYTHON_BIN` 可覆盖解释器，`LITEGRIP_SDK_PATH` 可覆盖 SDK 位置。`./build.sh` 会在**你的机器上**打出单文件可执行程序；它不作为发布附件发布。

> **注意**：**这是给"不想写代码的人"用的那个应用。** 连接、标定、运动与记录，一行 Python 都不用写。凡是要脚本化的，仍然走 SDK。

## 尚未就绪的部分

本手册记录的是已经存在的东西。这张表存在的意义，是让人不要围绕不存在的东西做规划。

| 组件 | 状态 |
|------|------|
| `litegrip-python` | 完整且在维护。主力路径 |
| `litegrip-cpp` | 只有第一层。没有 `grasp()`、没有 `set_force()`、没有 `move_at_speed*()`；`close(force_n=...)` 忽略力参数 |
| `litegrip-ros1` | **空桩。** 没有源码、没有包、没有发布 |
| `litegrip-ros2` | 可用；入口是 `ros2_control` 插件 |
| `litegrip-moveit2` | 可用；默认 dry-run，运动限位失效安全 |
| `litegrip-urdf` | 可视化与 `ros2_control` 已验证。**`effort` 与 `velocity` 是 SolidWorks 的占位默认值**，Gazebo 的 launch 从未执行过 |
| `litegrip-mujoco` | 完整，示例最丰富 |
| `litegrip-pybullet` | 完整 |
| `litegrip-isaacsim` | 仿真侧可用；真机 `OPEN_MM` 标定是占位值 |
| `litegrip-studio` | 完整且在维护 |

**没有任何发布附带二进制。** 每个仓库发布的都是只有 tag、没有附件的 release，而且**没有任何包在 PyPI 上**。一切都从源码检出安装。

## 报告与验证状态

本章记录的是仓库 `README.md` 中所标版本时点的 SDK。接口会变；当某个调用的签名与预期不符时，请先查 SDK 自己的 README 与 `py.typed` 标注，再怀疑手册。

| 内容 | 状态 |
|------|------|
| 接口名、签名、默认值与数据类字段 | **已核对** SDK 源码，逐方法比对 |
| CAN 协议章 | **已核对** 驱动与 SDK 编解码器；示例逐字节可复现 |
| [跑起来](#5-跑起来让夹爪动一下)及其后的运动示例 | **未在硬件上执行。** 按 SDK 源码及其 README 写成；打印值是示例 |
| 标有 `[待实测 · B]` / `[待实测 · C]` 的数值 | **未实测。** 它们是等台架实测的占位值 |
| 仿真与 ROS 入口 | **未执行。** 取自各仓库的 README 与文件树 |

> **不要**把本手册里的示例当作已测过程序。任何会让夹爪动的代码，都必须在你自己的硬件上、以降低后的力与速度验证过，才能靠近工件或人。

## 常见问题与技术支持

### Q&A

问：SDK 支持哪些平台？答：**仅 Linux**，需要内核支持 SocketCAN。库代码只用 Python 标准库——**本包没有声明任何运行时依赖**，因此它能在连不上软件源的裸控制器上装上就跑。

问：`pip install litegrip` 能用吗？答：**不能。** 本包没有发布到 PyPI。请克隆仓库，在仓库里执行 `python3 -m pip install .`。从别处找来的 wheel 不受支持。

问：为什么配置 CAN 时一定要加 `fd off`？答：本产品用**经典 CAN**。按 CAN FD 配置会**完全无法通信** —— 而且这个现象和"没接 24 V"很像，容易被误判成硬件故障。

问：为什么我监听总线什么都收不到？答：**反馈是问询式的** —— 驱动器只在收到主机发来的帧之后才回帧。**被动监听永远收不到任何帧**，必须先发帧。

问：连接之后要做什么？答：**先 `load_calibration()`，再 `enable()`。** `connect()` **不会**自动载入标定文件；未载入时 `config` 还是占位值（`rad_to_mm=105.26`），`config.calibrated` 为 `False`。哪些调用会因此拒绝执行、哪些会静默照跑，见 [加载标定](#4-加载标定)。

问：`open()` 抛 `CommandError` 说配置尚未标定，是哪里不对？答：标定没加载。`open()`、`close()`、`grasp()` 都要过标定检查，所以它们宁可直接拒绝，也不去猜方向。请先调 `load_calibration()`（或跑一次 `zero()`）。

问：`goto()` 去的位置不对，却不报任何错，为什么？答：中层接口（`goto`、`goto_rad`、`move_to`、`move_at_speed*`、`home`）**不检查 `calibrated`**，与高层动作不同。未加载标定时，它们用占位系数 `rad_to_mm = 105.26` 换算毫米。直接使用这些接口时，请自己检查 `config.calibrated`。

问：函数返回了 `True`，是不是就成功了？答：看是哪个函数。`enable()` 的 `True` 有反馈帧背书（且失败时会抛 `HardwareError`），可信度高；`disable()` 的 `True` **只代表命令已发出，未获证实**；运动接口的返回值只表示"这一串帧发出去了"，**不表示机构已经到位**。判断是否到位要读 `get_state()`。

问：电机其实没使能，为什么使能接口还返回成功？答：如果反馈里 `ERR = 0x0`，驱动器仍是失能状态 —— 此时电机会接受位置命令但**不出力矩**，表现为"命令发出去了，机构不动"。请先确认 24 V 已接、且 `enable()` 没有抛 `HardwareError`。

问：从菜单下发命令后机构不动？答：按顺序查：（1）24 V 是否已接（`ERR = 0x9` 是欠压）；（2）`enable()` 是否成功；（3）是否调过 `load_calibration()`；（4）目标位置是否与当前位置相同；（5）`kp` 是否为 0。

问：我想让夹爪"目标越界就报错"，怎么做？答：`goto_rad()` / `move_at_speed_rad()` 对越界目标是**静默钳位**，不抛异常。要拒绝就自己在调用前判断：读 `config.pos_closed_rad` / `pos_open_rad`，与目标值比较，再决定发不发。

问：为什么 `goto(60.0)` 到不了 60 mm？答：三种可能：（1）标定没加载，占位系数会把每个目标换算成错误的角度（见 [配置对象](#配置对象)）；（2）目标在标定端点之外，被钳到端点；（3）`duration` 太短，帧序列结束时机构还在路上。

问：为什么 `close()` 不按我设的力停住？答：`close()` 根本没有力参数。只有 `grasp()` 与 `set_force()` 收 `force_n`，而且即便在那儿，它也只是换算成 `force_n × 0.1 N·m` 的前馈力矩；**不做任何校验，也不保证夹持力等于设定值**。真实夹持力取决于对象刚度、位置与 `kp`。

问：`grasp()` 返回 `result.stalled == True`，是夹到东西了吗？答：**不一定。** 堵转判据是位置式的 —— 加窗位置变化连续 `stall_cycles` 个周期低于 `stall_delta`。夹住物体和走到行程端点对它来说完全一样，所以**光看 `stalled` 分不出来**。请读 `get_position()`：空夹停在闭合端点，夹到物体则停在端点之前。

问：`grasp()` 返回 `ok == False`，是坏了吗？答：不一定。`GraspResult.ok` 报的是保持阶段是否正常结束；`reached` 报是否到达目标角度，`stalled` 报位置是否停止变化。三个要一起读，而且要记住：成功的出力抓取是 `stalled` 为 `True`、`reached` 为 `False`。

问：`stop()` 返回什么？答：**返回 `None`**。这不代表"已经停住"：未连接或未使能时它是空操作，发完零力矩帧之后电机仍保持使能、可以被反驱。要切断出力请用 `disable()` 或断开硬件电源。

问：手指停在行程之外了，怎么办？答：用普通运动接口把它开回来 —— `goto_rad()` 会把目标钳到标定端点之内，所以"从外面回来"是**天然允许**的。如果机构已经卡死或别住，不要再继续施力，先手工排除干涉。

问：`enter_zero_gravity()` 之后松手，手指会掉吗？答：**会动。** 零重力模式意味着电机不出力矩，位置由重力和摩擦决定。要让它停在原处，松手后调 `exit_zero_gravity()`。

问：零重力模式下把手指推过行程两端会怎样？答：不会有任何提示 —— 那个模式不检查位置。只有之后调用普通运动接口时，目标才会被钳回标定端点。

问：标定时撞到硬限位了为什么还一直顶？答：`zero()`、`calibrate()` 与 `calibrate_guided()` 都是**靠电机堵转检测限位**：朝一个方向步进到位置增量连续多个周期低于阈值，中途不会自行停止。运行前请确认机械硬限位受得住这股力，并优先用 `calibrate_manual()`。

问：标出来的 `rad_to_mm` 不对（毫米读数偏大约 38%）？答：查 `max_stroke_mm`。它的默认值是占位值 `120.0`，而本机实测行程是 `87.000 mm`；每个标定入口都用 `config.max_stroke_mm` 作分子（`rad_to_mm = max_stroke_mm ÷ 实测 rad 跨度`），所以按默认标定会把一个偏大 1.38 倍的刻度写进标定文件。**标定前请先用卡尺量出全开开口，写进 `max_stroke_mm`。**

问：标定文件写在哪儿？答：不带参数的 `save_calibration()` 写 `~/.litegrip/<channel>_calibration.json`，并**返回它写入的路径** —— 一个通道一个文件，所以同一台机器上的两台夹爪不会互相覆盖。`~/.litegrip/litegrip_calibration.json` 是旧路径；`load_calibration()` 仍会把它当兜底读，但已经没有任何东西会写它了。

问：为什么 `home()` 不回闭合端？答：它应该回。`home()` 发的是 `self._config.pos_closed_rad` —— **本实例标定出的闭合限位**，不是模块常量 —— 所以常规安装回闭合端，反装也回正确的那一端。如果它去了错的那端，说明标定没加载，`pos_closed_rad` 还是占位值。（本手册早前的版本声称 `home()` 用的是常量 `0.0 rad`、会撞向张开侧。那是错的；请改查 `config.calibrated`。）

问：位置读数和卡尺量出来的差 1.5 mm？答：正常。SDK 的 mm 零点在**机械全闭处**，而该处两指之间还有 1.508 mm 间隙。卡尺读数 ≈ `get_position() + 1.508`（该式在闭合端精确；在张开端高估约 1.5 mm；精确关系见 [单位与换算](#单位与换算)）。

问：`tau` 读数总比我设的略小？答：正常。MIT 帧用的是**截断式**编码（向下取整），所以量化误差是单边的：`解码值 − 命令值` 落在区间 `(−1 LSB, 0]`，**永远不会大于**你设的值。

问：把 `kp` / `kd` 设成 1000 会报错吗？答：不会。编码时它们会被**静默饱和**到 `[0, 500]` / `[0, 5]`，`tau` 饱和到 `[−10, 10] N·m`；调用方收不到任何提示。

问：读 `OC_Value` 得到 0.8，是 0.8 A 吗？答：**不是。** 它是**比例值**，表示 80%。

问：`PMAX` / `VMAX` / `TMAX` 是我的保护阈值吗？答：**不是。** 它们是帧字段的 **MIT 量化范围**（范围定义），不能当作位置 / 速度 / 力矩的安全限值。**真正的速度保护在 `MAX_SPD`。** [待实测 · B，SDK 从不回读这三个寄存器、用的是硬编码范围，需回读验证]

问：我可以从两台上位机同时控制吗？答：**不能。** 必须保证**单一 CAN 主站**，并在软件上做互斥。多个主站并发时命令会互相覆盖。一个进程可以持有多个夹爪 —— 请用 `litegrip.can.controller`，而不是再开一个进程。

问：两端标定不同的夹爪能做遥操作吗？答：**可以。** 线上传的是归一化到 `[0, 1]` 的 `openness`，不是弧度，所以两端不必共享标定、安装方向或零点。两端必须约定同一个 `grip_id`。

问：技术支持渠道是什么？答：NEXFORM ROBOTICS 技术团队。联系方式见随产品交付的文档与销售渠道，或由购买时的对接人直接转接技术支持。

# CAN 通信协议

本章说明底层通信协议，供不使用 Python SDK、或需要在其他语言中自行实现控制程序的集成工程师使用。**SDK 的安全处理（位置钳制、零力矩停机等）对本文档的使用者不会自动生效** —— 自行实现协议时，越界判断、限速、急停回路与周期性发帧都需要你自己实现。

> **注意**：**自行实现协议意味着自行承担安全约束的实现责任。** 建议优先使用 Python SDK。若确需自行实现，请同时阅读《安全说明书》第 2 章与第 7 章。

## 物理层与节点

| 项目 | 数值 |
|------|------|
| 总线类型 | 经典 CAN（CAN 2.0） |
| 波特率 | 1 Mbps |
| CAN FD | **不使用（必须关闭）** |
| 数据帧长度 | 8 字节 |
| 终端电阻 | 总线两端各 120 Ω |

**ID 分配：**

| 名称 | 数值 | 含义 |
|------|------|------|
| 电机 CAN ID（`ESC_ID`） | `0x08` | 主机发往电机的控制帧与命令帧，用此 ID（**加模式偏移**） |
| 反馈 ID（`MST_ID`） | `0x18` | 电机发往主机的帧，使用此 ID |
| 广播 ID | `0x7FF` | **状态刷新帧与参数帧**发往此 ID，目标电机 ID 写在数据里 |

**控制帧与命令帧的仲裁 ID = 电机 CAN ID + 模式偏移。** 本产品使用 MIT 模式，偏移 `0x000`，故二者的仲裁 ID 都是 `0x08 + 0x000 = 0x08`。

| 帧类型 | 仲裁 ID | 目标电机如何指定 |
|--------|---------|-----------------|
| MIT 控制帧 | `0x08` | 仲裁 ID 本身 |
| 命令帧（使能 / 失能 / 清除故障 / 设置零点） | `0x08` | 仲裁 ID 本身 |
| 状态刷新帧 | `0x7FF` | 数据第 0、1 字节（低字节在前） |
| 参数帧（读 / 写 / 保存） | `0x7FF` | 数据第 0、1 字节（低字节在前） |

> **注意**：**只有状态刷新帧与参数帧用广播 ID `0x7FF` 寻址**（把目标电机 ID 写在数据里）；**MIT 控制帧与命令帧靠仲裁 ID 寻址**，发到 `0x08`。把命令帧发到 `0x7FF` 时，**没有电机会应答，也没有电机会执行** —— 而现象与"没接 24 V"很像，很容易误判成硬件故障。

## 帧类型总览

| 帧类型 | 方向 | 仲裁 ID | 用途 |
|--------|------|---------|------|
| 控制帧（MIT） | 主机 → 电机 | `0x08` | 同时携带位置、速度、刚度、阻尼、前馈力矩 |
| 命令帧 | 主机 → 电机 | `0x08` | 使能 / 失能 / 清除故障 / 设置零点 |
| 状态刷新帧 | 主机 → 电机 | `0x7FF` | 不改变输出，仅请求一帧状态 |
| 参数帧 | 主机 → 电机 | `0x7FF` | 读写驱动器寄存器、保存到 Flash |
| 反馈帧 | 电机 → 主机 | `0x18` | 状态、位置、速度、力矩、温度、错误码 |

## MIT 控制帧

**字段与量程：**

| 字段 | 位宽 | 量程 | 说明 |
|------|------|------|------|
| 位置 `q` | 16 位 | ±12.5 rad | 目标角度 |
| 速度 `dq` | 12 位 | ±30 rad/s | 目标速度 |
| 位置刚度 `kp` | 12 位 | 0 ~ 500 | 越大越"硬" |
| 阻尼 `kd` | 12 位 | 0 ~ 5 | |
| 前馈力矩 `tau` | 12 位 | ±10 N·m | |

电机内部的力矩输出为：

```text
tau_out = kp · (q_target − q_actual) + kd · (dq_target − dq_actual) + tau
```

**字节排布：**

| 字节 | 内容 |
|------|------|
| 0 | `q[15:8]` |
| 1 | `q[7:0]` |
| 2 | `dq[11:4]` |
| 3 | `dq[3:0]` 在高 4 位，`kp[11:8]` 在低 4 位 |
| 4 | `kp[7:0]` |
| 5 | `kd[11:4]` |
| 6 | `kd[3:0]` 在高 4 位，`tau[11:8]` 在低 4 位 |
| 7 | `tau[7:0]` |

**量化规则（截断，不是四舍五入）：**

```
码值 = int( (值 − 最小值) × (2^位宽 − 1) / (最大值 − 最小值) )
值   = 码值 × (最大值 − 最小值) / (2^位宽 − 1) + 最小值
```

> **量化误差是单边的**：`解码值 − 命令值` 落在 `(−1 LSB, 0]` 区间内。编码后的实际值**总是等于或略小于**你想要的值，**永远不会大于**。

**各字段 1 LSB：**

| 字段 | 1 LSB |
|------|-------|
| `q` | 3.814755 × 10⁻⁴ rad |
| `dq` | 1.465201 × 10⁻² rad/s |
| `tau` | 4.884005 × 10⁻³ N·m |
| `kp` | 0.1221（= 500 / 4095） |
| `kd` | 0.001221（= 5 / 4095） |

> **`kp` 与 `kd` 的量程从 0 开始**，所以"命令 0"恰好编码为"码值 0"，此时没有量化误差。但非零值的分辨率就是上表：`kp` 每级 0.1221、`kd` 每级 0.00122。

**示例一 —— 位置控制**（位置 −0.6 rad、速度 0、刚度 100、阻尼 2、无力矩前馈）：

| 字段 | 命令值 | 码值 |
|------|--------|------|
| `q` | −0.6 rad | 31194 = `0x79DA` |
| `dq` | 0 rad/s | 2047 = `0x7FF` |
| `kp` | 100 | 819 = `0x333` |
| `kd` | 2 | 1638 = `0x666` |
| `tau` | 0 N·m | 2047 = `0x7FF` |

```
79 DA 7F F3 33 66 67 FF
```

**示例二 —— 零力矩帧**（位置、速度、刚度、阻尼、力矩全部置零）：

```
7F FF 7F F0 00 00 07 FF
```

> **零力矩帧里为什么还要有位置字段？** MIT 帧的五个字段是固定长度的，`q` 字段**必须**存在。由于 `kp = kd = 0`，力矩公式中的两项恒为零，**`q` 的取值对输出没有任何影响** —— 它只是一个占位符。SDK 在发零力矩帧时把 `q` 固定填 `0`（即码值 32767 = `0x7FFF`），因此线上字节里不会出现任何"目标位置"含义的值。**这是一条固定取值，不是一个"安全区填充"算法。**

**零力矩帧的真实输出（重要）：**

| 字段 | 命令值 | 实际解码值 |
|------|--------|-----------|
| `kp` | 0 | **0**（精确） |
| `kd` | 0 | **0**（精确） |
| `dq` | 0 | **−7.326 mrad/s** |
| `tau` | 0 | **−2.442 mN·m** |

由于截断规则，命令 `tau = 0`、`dq = 0` 时码值都是 2047，**解码回来不是 0**。

> **这为什么是安全的：**
>
> 1. 残留的 −2.442 mN·m 是一个**与位置无关的常数**，不随机构位置变化，因此不构成把机构推向任何方向的驱动力。
> 2. 它的量级远小于机构的空载静摩擦（0.198 N·m，此处取的是实测区间下界；完整实测区间为 **0.198 ~ 0.222 N·m**），推不动机构。
> 3. `kp = kd = 0` 使位置字段完全失效，所以这一帧**不可能**因为位置偏差而产生力矩。
>
> **注意**：**零力矩帧之所以不会因为位置偏差而产生力矩，正确理由是"刚度与阻尼为零使位置字段失效"，而不是"输出恒等于零"。后者不成立。**

## 命令帧

**格式**：仲裁 ID = 电机 CAN ID + 模式偏移（本产品 = `0x08`，见上表）；字节 0 ~ 6 全部为 `0xFF`；字节 7 为命令码。**注意数据里没有目标电机 ID** —— 命令帧靠仲裁 ID 寻址。

| 命令 | 命令码 | 完整数据字节 |
|------|--------|-------------|
| 使能 | `0xFC` | `FF FF FF FF FF FF FF FC` |
| 失能 | `0xFD` | `FF FF FF FF FF FF FF FD` |
| 清除故障 | `0xFB` | `FF FF FF FF FF FF FF FB` |
| 设置零点 | `0xFE` | `FF FF FF FF FF FF FF FE` |

> **命令帧通常需要连发多帧。** 单帧可能因总线竞争或驱动器状态机时序而丢失。建议**连发 5 帧**（SDK 的实现是 5 帧、间隔 2 ms）。
>
> **注意**：**"设置零点"会把当前位置记为机械零点，此操作不可撤销。** 除非你明确知道自己在做什么，否则不要发送此命令。SDK 保留了该命令的实现（`litegrip.can` 子包里的 `set_zero()`），但**自己的高层接口不会主动发送它** —— 夹爪的零点是靠标定得到的，不是靠这条命令。

## 状态刷新帧

在不改变电机输出的前提下读取状态。

**格式**：仲裁 ID = `0x7FF`；数据 4 字节：`[can_id 低字节, can_id 高字节, 0xCC, 0x00]`

电机 CAN ID = `0x08` 时：`08 00 CC 00`

发送后电机会回送一帧状态帧。**用途**：轮询位置、温度、故障码，而不干扰正在执行的运动。

## 参数帧与寄存器

**帧格式**（仲裁 ID 一律为 `0x7FF`）：

| 操作 | 数据字节 |
|------|---------|
| **读** | `[can_id 低, can_id 高, 0x33, RID, 0, 0, 0, 0]` |
| **写** | `[can_id 低, can_id 高, 0x55, RID, d0, d1, d2, d3]` |
| **保存** | `[can_id 低, can_id 高, 0xAA, 0x01, 0, 0, 0, 0]` |

**响应帧**结构相同，字节 2 为操作码回显（`0x33` = 读响应、`0x55` = 写响应、`0xAA` = 保存响应），字节 3 为 RID，字节 4 ~ 7 为数据。

**数据编码**：整数寄存器为小端无符号 32 位整数；浮点寄存器为小端 IEEE 754 单精度浮点数。整数寄存器的 RID 范围为 `7 ~ 10`、`13 ~ 16`、`35 ~ 36`，**其余 RID 均为浮点寄存器**。

**寄存器编号表：**

| RID | 十六进制 | 名称 | 类型 | 说明 |
|-----|---------|------|------|------|
| 0 | `0x00` | `UV_Value` | 浮点 | 欠压保护阈值（V） |
| 1 | `0x01` | `KT_Value` | 浮点 | 扭矩系数 |
| 2 | `0x02` | `OT_Value` | 浮点 | 过温保护阈值（°C） |
| 3 | `0x03` | `OC_Value` | 浮点 | 过流保护阈值（**比例，非安培**） |
| 4 | `0x04` | `ACC` | 浮点 | 加速度（仅非 MIT 模式生效） |
| 5 | `0x05` | `DEC` | 浮点 | 减速度（仅非 MIT 模式生效） |
| 6 | `0x06` | `MAX_SPD` | 浮点 | 最大速度（**真正的限速**） |
| 7 | `0x07` | `MST_ID` | 整数 | 反馈帧 ID |
| 8 | `0x08` | `ESC_ID` | 整数 | 电机 CAN ID |
| 9 | `0x09` | `TIMEOUT` | 整数 | 通信超时（单位 50 µs） |
| 10 | `0x0A` | `CTRL_MODE` | 整数 | 控制模式 |
| 11 | `0x0B` | `Damp` | 浮点 | 阻尼系数 |
| 12 | `0x0C` | `Inertia` | 浮点 | 转动惯量 |
| 13 | `0x0D` | `hw_ver` | 整数 | 硬件版本（保留字段，读到 0 属正常） |
| 14 | `0x0E` | `sw_ver` | 整数 | 固件版本号 |
| 15 | `0x0F` | `SN` | 整数 | 序列号（保留字段） |
| 16 | `0x10` | `NPP` | 整数 | 极对数 |
| 17 | `0x11` | `Rs` | 浮点 | 相电阻 |
| 18 | `0x12` | `LS` | 浮点 | 相电感 |
| 19 | `0x13` | `Flux` | 浮点 | 转子磁链（Wb） |
| 20 | `0x14` | `Gr` | 浮点 | 齿轮减速比 |
| 21 | `0x15` | `PMAX` | 浮点 | 位置**映射范围**（rad） |
| 22 | `0x16` | `VMAX` | 浮点 | 速度**映射范围**（rad/s） |
| 23 | `0x17` | `TMAX` | 浮点 | 力矩**映射范围**（N·m） |
| 24 | `0x18` | `I_BW` | 浮点 | 电流环带宽 |
| 25 | `0x19` | `KP_ASR` | 浮点 | 速度环比例增益 |
| 26 | `0x1A` | `KI_ASR` | 浮点 | 速度环积分增益 |
| 27 | `0x1B` | `KP_APR` | 浮点 | 位置环比例增益 |
| 28 | `0x1C` | `KI_APR` | 浮点 | 位置环积分增益 |
| 29 | `0x1D` | `OV_Value` | 浮点 | 过压保护阈值（V） |
| 30 | `0x1E` | `GREF` | 浮点 | 齿轮比参考 |
| 31 | `0x1F` | `Deta` | 浮点 | — |
| 32 | `0x20` | `V_BW` | 浮点 | 速度环带宽 |
| 33 | `0x21` | `IQ_c1` | 浮点 | — |
| 34 | `0x22` | `VL_c1` | 浮点 | — |
| 35 | `0x23` | `can_br` | 整数 | CAN 波特率 |
| 36 | `0x24` | `sub_ver` | 整数 | 子版本号 |

> **关于本表的来源**：编号、类型划分与语义说明来自电机协议规范；其中本产品实际使用的寄存器**已在本产品上逐一回读确认**。其余寄存器本产品未使用，其数值以你的电机实际固件为准。
>
> **注意**：**RID 3（`OC_Value`）是比例，不是安培。** 取值范围 (0, 1)，`0.8` 表示 80%。把它当作电流值读取会得到完全错误的结论。
>
> **注意**：**RID 21 / 22 / 23（`PMAX` / `VMAX` / `TMAX`）是映射范围，不是保护阈值。** 它们定义 MIT 帧字段的量程，**不能**当作位置、速度、力矩的安全上限。**真正的速度保护在 RID 6（`MAX_SPD`）。**
>
> **待测**：本节 SDK 用的量程是**硬编码**的 `±12.5 / ±30 / ±10`（见 `litegrip/can/protocol.py`），**代码从不回读 RID 21/22/23**，因此无法断言它与本台电机寄存器的实际取值一致【待测·乙 用 `scripts/read_driver_limits.py` 回读核对】。

**示例帧：**

| 操作 | 数据字节 |
|------|---------|
| 读 `TIMEOUT`（RID 9） | `08 00 33 09 00 00 00 00` |
| 把 `TIMEOUT` 写为 8000（= 0.4 s） | `08 00 55 09 40 1F 00 00` |
| 把参数保存到 Flash | `08 00 AA 01 00 00 00 00` |

> **注意**：**保存参数前必须先失能电机。**
>
> **注意**：**写入的参数断电后不会自动保留。** 必须显式发送保存帧，否则重新上电后参数回到旧值。

## 反馈帧与错误码

**字节排布**（仲裁 ID = `0x18`）：

| 字节 | 内容 |
|------|------|
| 0 | `ERR[7:4]` 在高 4 位，`can_id[3:0]` 在低 4 位 |
| 1 | `q[15:8]` |
| 2 | `q[7:0]` |
| 3 | `dq[11:4]` |
| 4 | `dq[3:0]` 在高 4 位，`tau[11:8]` 在低 4 位 |
| 5 | `tau[7:0]` |
| 6 | MOS 温度（°C） |
| 7 | 线圈温度（°C） |

`q`、`dq`、`tau` 的解码规则与量程与 MIT 控制帧相同（±12.5 rad、±30 rad/s、±10 N·m）。

**`ERR` 字段全表** —— 高 4 位的 `ERR` 同时承担两个职责：**报告使能状态**、**报告故障**。

| 码值 | 含义 | 类别 |
|------|------|------|
| `0x0` | 已失能 | 状态 |
| `0x1` | 已使能 | 状态 |
| `0x9` | **欠压**故障 | 故障 |
| `0xA` | 过流故障 | 故障 |
| `0xB` | MOS 过温故障 | 故障 |
| `0xC` | 线圈过温故障 | 故障 |

> **注意**：**本表只列随货 SDK 能解析的码值。** 驱动器还会报告上表之外的故障（由驱动器**指示灯**给出），SDK 一律返回"未知错误 (0xXX)"，需要时请对照驱动器手册判读。`get_error()` 本身返回的是码值整数。
>
> **注意**：**判断使能状态必须用反馈帧，不能只看命令是否发出。** 读到 `ERR = 0x1` 表示已使能；`ERR = 0x0` 表示驱动器仍处于失能状态 —— 此时电机会接收位置指令但**不输出力矩**，表现为"指令发了，机构不动"。

**示例反馈帧**：`18 79 DA 7F F7 FF 23 28`

| 项目 | 值 |
|------|-----|
| 仲裁 ID | `0x18`（反馈帧） |
| `ERR` | `0x1` → **已使能** |
| `can_id` | `0x8` |
| `q` | 码值 31194 → **−0.600252 rad** |
| `dq` | 码值 2047 → **−0.007326 rad/s** |
| `tau` | 码值 2047 → **−0.002442 N·m** |
| MOS 温度 | 35 °C |
| 线圈温度 | 40 °C |

> **注意 `q` 的解码值**：命令 −0.6 rad，码值 31194，解码回 **−0.600252 rad**。误差 −0.000252 rad，落在 (−1 LSB, 0] 区间内 —— 这正是截断规则的效果。

## 通信时序

| 项目 | 数值 | 说明 |
|--------------------------|----------------|----------------------------------------------------------------|
| 使能等待窗口 | **2.0 s** | SDK 在此窗口内等待**命令发出之后**的反馈帧，判据是 `ERR ∈ {0x0, 0x1}` |
| 使能重试次数 | 5 次 | 每次重新走"失能 → MIT → 使能 → 等反馈"；全部失败抛 `HardwareError` |
| 失能验证 | **无** | SDK 发完失能帧就返回，不等待反馈证实 |
| 状态刷新等待 | 0.05 s | `get_state(wait=True)` 等待一帧反馈的时间 |
| 参数读取等待 | 0.5 s | `read_param()` 的默认超时 |
| 控制帧持续发送间隔 | 5 ms（200 Hz） | 运动过程中的节拍 |
| 驱动器通信超时 | 0.4 s【待测·乙 回读 RID 9 核对】 | 超时后驱动器**自动退出使能** |

> **注意**：**"新鲜反馈"的含义。** 使能判定不能只看"收到过 `ERR = 0x1` 的帧"。上电后驱动器可能已有一帧陈旧的状态帧在缓冲中。**必须在发送使能命令之后收到的帧才算数** —— SDK 正是这么判的。
>
> **注意**：**驱动器通信超时保护。** 若 0.4 s 内未收到主机任何帧，驱动器会**自动退出使能**。这意味着你的控制器必须保持周期性发送，否则电机会自行失能。
>
> **注意**：**该保护可以关闭**（把 RID 9 写为 0，属达妙协议层面的做法，SDK 自身不会去写这个寄存器）。**关闭后掉线时电机将保持最后一条力矩指令**，请谨慎评估。

## 典型交互序列

| 步骤 | 方向 | 帧 |
|------|------|-----|
| 1 | 主机 → 电机 | 清除故障 `FF FF FF FF FF FF FF FB` |
| 2 | 主机 → 电机 | 使能 `FF FF FF FF FF FF FF FC` |
| 3 | 电机 → 主机 | 反馈帧，校验 `ERR = 0x1` |
| 4 | 主机 → 电机 | 控制帧（MIT），持续发送 |
| 5 | 电机 → 主机 | 每收到一帧控制帧，回一帧反馈 |
| 6 | 主机 → 电机 | 零力矩帧（停止输出） |
| 7 | 主机 → 电机 | 失能 `FF FF FF FF FF FF FF FD` |
| 8 | 电机 → 主机 | 反馈帧，校验 `ERR = 0x0` |

> **第 3 步和第 8 步不能省略。** 命令帧是单向的，只有反馈帧能证明命令真正生效。

# 附录一 状态、错误码与异常

## 状态与错误字段

`GripperState` 的完整字段见 [读取状态](#读取状态)。与状态判断直接相关的三个字段：

| 字段 | 判据 | 含义 |
|------|------|------|
| `error_code` | `== 0` | 已失能 |
| | `== 1` | 已使能 |
| | 不是 0 也不是 1 | 存在故障 |
| `torque_nm` | — | 力矩读数，用于 `is_grasped()` 判定 |
| `force_n` | — | **估算**夹持力（`torque_nm × 10`，名义系数），力标定完成前不应作为依据 |

**错误码表**（与 `ERR` 字段一致；只列随货 SDK 能解析的码值）：

| 码值 | 含义 | 类别 |
|------|------|------|
| `0x0` | 已失能 | 状态 |
| `0x1` | 已使能 | 状态 |
| `0x9` | **欠压**故障 | 故障 |
| `0xA` | 过流故障 | 故障 |
| `0xB` | MOS 过温故障 | 故障 |
| `0xC` | 线圈过温故障 | 故障 |

> **注意**：**本表只列随货 SDK 能解析的码值。** 驱动器还会报告上表之外的故障（由驱动器**指示灯**给出），SDK 一律显示"未知错误 (0xXX)"，需要时请对照驱动器手册判读。

## Python 异常类型

SDK 共有 **11 个**异常类，全部继承自 `LiteGripError`：其中 **7 个**在 `litegrip.exceptions`，**4 个**在 `litegrip.teleop`。

| 异常 | 基类 | 含义 |
|------|------|------|
| `LiteGripError` | `Exception` | 所有 SDK 异常的基类，可携带 `error_code` |
| `NotInitializedError` | `LiteGripError` | 未连接或未使能时调用了该接口 |
| `ConnectError` | `LiteGripError` | 连接失败（CAN 接口打不开、注册电机失败） |
| `CommError` | `LiteGripError` | 通信错误（位置控制 / 力控的底层收发失败） |
| `CANTimeoutError` | `LiteGripError` | 总线读超时 |
| `HardwareError` | `LiteGripError` | 硬件故障（使能失败、故障清除失败、驱动器报故障） |
| `CommandError` | `LiteGripError` | 指令错误：未标定时执行了运动动作、行程为零，或 `load_calibration()` 同时收到 `path` 与 `template` |
| `TeleopError` | `LiteGripError` | 遥操作异常的基类 |
| `TeleopBusyError` | `TeleopError` | 会话已在运行时又调用了 `teleop_start()` |
| `TeleopNotActiveError` | `TeleopError` | 某个操作需要活动的遥操作会话 |
| `TeleopNotReady` | `TeleopError` | 夹爪还不能安全遥操作（未标定、行程为零，或 `rad_to_mm == 0`） |

> **注意**：那四个遥操作异常在 `litegrip.teleop` 里，要从那里导入，不是从 `litegrip`。越界目标被钳制、力参数不校验，这两件事都不会抛异常（详见 [运动控制（开合与位置）](#运动控制开合与位置) 与 [抓取与力控](#抓取与力控)）。

## 错误处理建议

1. `NotInitializedError`：先 `connect()`、再 `enable()`；若已连接，检查 `enable()` 是否成功。
2. `ConnectError`：检查接口是否已 up、`fd off` 是否配置、`can0` 是否存在。**不要重试到成功为止** —— 先看原因。
3. `CommError`：检查线缆、终端电阻、CAN FD 设置。
4. `CANTimeoutError`：检查 24 V 是否接通；检查是否只监听未发送。
5. `HardwareError`：按错误码逐项排查；**过温与过流应先停机冷却，再排查负载**。使能失败时先确认 24 V 已接通、`ERR` 不是 `0x9`。读到"未知错误"说明驱动器报的是 SDK 不解析的故障码，请对照驱动器**指示灯**判读。
6. `CommandError`：多为未加载标定就调用了 `open()` / `close()` / `grasp()`，也可能是行程为零。先检查 `config.calibrated`，再跑一次标定。

> **注意**：**位置越界、力参数未标定这两种情况都不会抛异常。** 不要指望用 `try/except` 捕获"越界"，必须自己先判断目标值。

# 附录二 通信与连接排查

## CAN 接口与端点信息

| 项目 | 数值 |
|------|------|
| 接口名（默认） | `can0` |
| 波特率 | 1 Mbps |
| 帧格式 | 经典 CAN，非 CAN FD |
| 电机 CAN ID | `0x08` |
| 反馈 ID（`mst_id`） | `0x18` |
| 广播 ID | `0x7FF` |
| 终端电阻 | 总线两端各 120 Ω |

## CAN 接口配置

```bash
# 配置物理接口
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000 fd off
sudo ip link set can0 up

# 确认接口状态
ip -details link show can0
```

**无硬件时的虚拟总线：**

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

> 虚拟总线上没有真实电机，因此**使能步骤会超时**（SDK 等待 2.0 s、重试 5 次后抛 `HardwareError`），这是**预期行为**。

## 不经 SDK 的总线自检

SDK 装不上、或者怀疑问题出在 SDK 这一层时，用 `can-utils` 直接看总线，可以先把"夹爪到底有没有回话"这件事判死。

```bash
sudo apt install can-utils          # 提供 candump / cansend

# 1) 被动监听：不发帧时应当什么都看不到
candump can0

# 2) 另一个终端里发一帧状态刷新（电机 CAN ID = 0x08）
cansend can0 7FF#0800CC00
#    预期：0x18 回一帧状态帧

# 3) 读一个寄存器（例：固件版本号 sw_ver，RID 14 = 0x0E）
cansend can0 7FF#0800330E00000000
#    预期：仲裁 ID 0x18，数据 08 00 33 0E <4 字节小端数据>
```

> **注意区分两种寻址方式。** 上面的**状态刷新帧与参数帧**发往广播 ID `0x7FF`，目标电机 ID 写在数据第 0 字节；而**命令帧（使能 / 失能 / 清除故障 / 设置零点）与 MIT 控制帧靠仲裁 ID 寻址**，要发到 `0x08`（= 电机 CAN ID + MIT 模式偏移 `0x000`）。搞混的典型现象是"发了没有任何反应"。
>
> **`candump` 长时间没有输出不等于夹爪坏了。** 本产品的反馈是**问询式**的：电机只在收到命令帧后应答，被动监听本来就是什么都收不到。先发第 2 步那一帧再判断。

**最安全的使能自检**：只接 USB-CAN 适配器、**暂不接 24 V**，然后连发 5 帧使能命令（**注意仲裁 ID 是 `08`，不是 `7FF`**）：

```bash
for i in $(seq 5); do cansend can0 08#FFFFFFFFFFFFFFFC; sleep 0.01; done
```

预期反馈帧的 `ERR` 字节为 `0x9`（欠压）。**能收到 `0x9` 就已经证明"总线通、电机在跑、回话正常"，问题被限定在供电侧** —— 这是不用给动力电就能做完的通信验证。

> **注意**：接通 24 V 之后再发使能帧，机构会**真的运动**。执行前确认夹指运动范围内无人、无干涉物。

## 连接排查

| 现象 | 可能原因 | 处理方法 |
|----------------------------------------|----------------------------|--------------------------------------|
| 完全收不到反馈帧 | 只监听未发送 | **反馈是问询式的**，必须先发帧 |
| | 命令帧发到了 `0x7FF` | 命令帧与 MIT 帧要发到 `0x08`（见 [CAN 通信协议](#can-通信协议) 的 ID 分配表） |
| | CAN FD 未关闭 | 加 `fd off` 重新配置 |
| | 终端电阻缺失 | 总线两端各接 120 Ω |
| | 接口未 up | `ip link show can0` 确认 |
| 使能无效（`ERR` 始终 `0x0`） | 24 V 动力电源未接通 | 接通 24 V |
| | 反馈帧陈旧 | 必须用命令发出**之后**的帧判定 |
| 反馈 `ERR = 0x9`（欠压） | 24 V 未接通或电压不足 | 检查供电 |
| 发指令后机构不动，`ERR = 0x1` | 目标位置与当前位置相同 | 确认目标值 |
| | `kp = 0` | 检查刚度参数 |
| 运动中突然失能 | 驱动器通信超时（0.4 s 内无帧） | 保持周期性发送 |
| | 触发过温 / 过流保护 | 停机冷却，排查负载 |
| 反馈的 `tau` 略小于预期 | 截断量化 | **正常现象**，见 [CAN 通信协议](#can-通信协议) |
| 把 `OC_Value` 的 0.8 当成 0.8 A | 它是比例值，表示 80% | 见 [参数帧与寄存器](#参数帧与寄存器) |
| 多台设备互相干扰 | 多主站并发 | **保证单主站**，软件层互斥 |
| 位置读数比卡尺小 1.5 mm | SDK 零点在闭合机械极限 | 卡尺读数 ≈ `get_position() + 1.508` |

**无法自行解决时**，请记录以下信息后联系我们：产品型号与序列号、SDK 版本、Python 版本、操作系统与内核版本、CAN 接口配置、完整异常信息与堆栈。

---


> **文档结束** 如有疑问或需要补充信息，请联系 NEXFORM ROBOTICS 技术团队。
