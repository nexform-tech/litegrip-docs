# litegrip-docs

[English](README.md) | [简体中文](README.zh-CN.md)

LiteGrip 是 NEXFORM ROBOTICS 面向科研教育、AI 机器人开发与轻量级工业自动化场景设计的自适应两指平动夹爪，采用电机直驱与自适应抓取机构，有效行程 85.000 mm。夹爪通过 USB-CAN 适配器与上位机通信（经典 CAN，1 Mbps），可用于抓取、搬运、上下料、分拣与算法验证等场景。

本仓库是 LiteGrip 的产品文档源仓库，汇总手册、SDK、驱动、仿真环境、模型与上位机的入口，并记录各组件的最新发布版本。

## 1. 软件使用说明手册

| 手册 | 读者 | 内容 |
| --- | --- | --- |
| [使用教程](user-guide-zh.md) | 首次使用者 | 开箱清点、机械安装、电气连接、上位机安装与首次运行 |
| [产品手册](product-manual-zh.md) | 使用与安装人员 | 规格、电气接口、安装、维护、故障排查 |
| [软件开发手册](soft-gripper-development-manual-zh.md) | 集成工程师 | SDK 安装与调用、生态集成、精简的 CAN 协议附录 |

说明文档包含如下内容：

1. SDK 二次开发接口说明 —— 安装，以及每个接口的参数、返回值、前置条件与异常。
2. 产品规格与安装说明 —— 行程、夹持力、负载、电气参数、接线与安装。
3. 常见问题解答 —— 通信、运动、标定与力控问题的排查路径。

## 2. SDK 与配套软件包

| 组件 | 仓库 | 最新版本 | 发布日期 |
| --- | --- | --- | --- |
| Python SDK | [litegrip-python](https://github.com/nexform-tech/litegrip-python) | v1.1.0 | 2026-10-14 |
| C++ SDK | [litegrip-cpp](https://github.com/nexform-tech/litegrip-cpp) | v1.0.9 | 2026-10-14 |
| ROS 1 驱动 | [litegrip-ros1](https://github.com/nexform-tech/litegrip-ros1) | 暂无发布 | — |
| ROS 2 驱动 | [litegrip-ros2](https://github.com/nexform-tech/litegrip-ros2) | v0.1.1 | 2026-11-02 |
| MoveIt 2 配置 | [litegrip-moveit2](https://github.com/nexform-tech/litegrip-moveit2) | v0.1.2 | 2026-11-02 |
| MuJoCo 仿真 | [litegrip-mujoco](https://github.com/nexform-tech/litegrip-mujoco) | v0.5.0 | 2026-10-10 |
| PyBullet 仿真 | [litegrip-pybullet](https://github.com/nexform-tech/litegrip-pybullet) | v0.6.1 | 2026-10-10 |
| Isaac Sim 仿真 | [litegrip-isaacsim](https://github.com/nexform-tech/litegrip-isaacsim) | v1.0.1 | 2026-09-27 |
| URDF 模型 | [litegrip-description](https://github.com/nexform-tech/litegrip-description) | v2.0.0 | 2026-11-02 |
| 上位机 | [litegrip-studio](https://github.com/nexform-tech/litegrip-studio) | v0.12.4 | 2026-10-14 |

**表中只有一行写的是"暂无发布"。** `litegrip-ros1` 只是一个占位仓库：仓库已初始化，但源码、打包与文档都还没落地，目前没有任何可安装的内容。

**上表的发布目前都只提供源码。** 这些仓库都没有挂编译好的安装包，所以没有按平台下载的二进制包。要查某个组件的完整版本历史，请打开它的 Releases 页面。

Python SDK 尚未发布到 PyPI，请从源码安装：

```bash
git clone https://github.com/nexform-tech/litegrip-python.git
cd litegrip-python
python3 -m pip install .
```

## 3. 机械模型

模型在 [litegrip-description](https://github.com/nexform-tech/litegrip-description)。本节描述的是单总控关节形式，它从 **v2.0.0** 起提供；v1.0.0 仍是更早的两指独立关节模型。ROS 2 包名为 `litegrip_description`。

| 项目 | 取值 |
| --- | --- |
| 机器人描述 | `litegrip_description/urdf/litegrip_description.urdf.xacro` —— 唯一事实来源 |
| 连杆 | `base_footprint`（根）、`base_link`、`gripper_opening_link`（总控）、`gripper_slider_link1`（右）、`gripper_slider_link2`（左） |
| 关节 | `gripper_opening_joint`（总控，`+X`，移动副）；`gripper_slide_joint_right`（`+X`）与 `gripper_slide_joint_left`（`-X`）是它的 `<mimic>` 跟随关节 |
| 网格 | 三个 STL 文件：`base_link.STL`、`gripper_slider_link1.STL`、`gripper_slider_link2.STL` |
| launch 文件 | `display.launch.py`、`ros2_control.launch.py`、`gazebo.launch.py` |
| 环境要求 | Ubuntu 22.04 上的 ROS 2 Humble，系统 Python 3.10 |

夹爪只有一台电机、一套传动，因此只有 `gripper_opening_joint` 可命令。它的取值是开口
行程，单位米（`0` 闭合，`0.085452` 全开），每指按 `q = -0.5 × opening + stroke` 跟随。
随货模型的手指单侧行程默认值是 `0.042726` m。

```bash
ros2 launch litegrip_description display.launch.py
```

加 `stroke:=` 可覆盖模型使用的手指单侧行程。

各仿真环境并不都直接加载这个文件：PyBullet 随包提供的是更早的两指独立模型快照 —— 它的 URDF 导入器忽略 `<mimic>`，单总控关节形式在那里无法联动；MuJoCo 的 MJCF 则建立在这三个 STL 网格之上。

## 4. API 使用例程

示例脚本见 [litegrip-python/examples](https://github.com/nexform-tech/litegrip-python/tree/main/examples)。

## 5. 技术支持与帮助

两本手册的答疑章节先覆盖了常见问题。仍无法自行解决时，《软件开发手册》列出了联系我们前应记录的信息。技术支持由 NEXFORM ROBOTICS 技术团队提供，联系方式见随货单据与销售渠道。

## 文档中心

这里的每一份 PDF——手册、图纸与尺寸图都一样——都会同步到飞书上的 NEXFORM
文档中心。不需要人工上传：把 PDF 合并进 `main` 就是全部流程，几分钟内站点就会
更新。

1. 推送到 `main` 且改动 `*.pdf` 时，触发
   `.github/workflows/notify-docs.yml`；它用 `nexform-docs-dispatch` 这个
   GitHub App 换取短期令牌，向
   [nexform-guide](https://github.com/nexform-tech/nexform-guide) 发送
   `docs-updated` 事件。
2. `nexform-guide` 运行 `scripts/sync_files.py`，按它 `files.yaml` 的清单从
   拥有该文件的仓库下载，只提交字节有变化的那些。
3. 它的 `Publish` 流程逐个比对飞书文件块与本地副本的 SHA-256，只重传不同的
   那些，然后回读文档校验。

每天 03:00 UTC 还会跑一遍第 2 步，所以即使某次事件丢了，最多晚一天。你这边
不需要任何飞书凭据：跟飞书打交道的任务都在 CI 里跑。

文件名是这两个仓库之间的关联键。原地替换一份 PDF 不需要别的操作；新增、改名或
删除则需要同时在 `nexform-guide` 开 PR，改 `files.yaml` 和页面链接两处，否则
站点会继续指向旧文件。

## 仓库规范

本仓库遵循 NEXFORM ROBOTICS 的共享仓库规范：代理操作规则见 [`.nexform-standards.json`](.nexform-standards.json)；提交信息使用 Conventional Commits；每次合并到 `main` 由 semantic-release 自动发布版本。

## 许可证

Copyright © 2026 NEXFORM ROBOTICS，基于 [Apache License 2.0](LICENSE) 授权。
