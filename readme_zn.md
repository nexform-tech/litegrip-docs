# litegrip-docs

[English](README.md) | [简体中文](readme_zn.md)

LiteGrip 是 NEXFORM ROBOTICS 面向科研教育、AI 机器人开发与轻量级工业自动化场景设计的自适应两指平动夹爪，采用电机直驱与自适应抓取机构，有效行程 87.000 mm。夹爪通过 USB-CAN 适配器与上位机通信（经典 CAN，1 Mbps），可用于抓取、搬运、上下料、分拣与算法验证等场景。

本仓库是 LiteGrip 的产品文档源仓库，汇总手册、SDK、驱动、仿真环境、模型与上位机的入口，并记录各组件的最新发布版本。

## 1. 软件使用说明手册

| 手册 | 读者 | 内容 |
| --- | --- | --- |
| [产品手册](product-manual-zh.md) | 使用与安装人员 | 规格、电气接口、安装、维护、故障排查 |
| [软件开发手册](soft-gripper-development-manual-zh.md) | 集成工程师 | SDK 安装、接口用法与前置条件、CAN 通信协议 |

说明文档包含如下内容：

1. SDK 二次开发接口说明 —— 安装，以及每个接口的参数、返回值、前置条件与异常。
2. 产品规格与安装说明 —— 行程、夹持力、负载、电气参数、接线与安装。
3. 常见问题解答 —— 通信、运动、标定与力控问题的排查路径。

## 2. SDK 与配套软件包

| 组件 | 仓库 | 最新版本 | 发布日期 |
| --- | --- | --- | --- |
| Python SDK | [litegrip-python](https://github.com/nexform-tech/litegrip-python) | v0.9.1 | 2026-09-29 |
| C++ SDK | [litegrip-cpp](https://github.com/nexform-tech/litegrip-cpp) | v0.1.0 | 2026-09-28 |
| ROS 1 驱动 | [litegrip-ros1](https://github.com/nexform-tech/litegrip-ros1) | 暂无发布 | — |
| ROS 2 驱动 | [litegrip-ros2](https://github.com/nexform-tech/litegrip-ros2) | v0.1.0 | 2026-09-28 |
| MoveIt 2 配置 | [litegrip-moveit2](https://github.com/nexform-tech/litegrip-moveit2) | v0.1.0 | 2026-09-28 |
| MuJoCo 仿真 | [litegrip-mujoco](https://github.com/nexform-tech/litegrip-mujoco) | v0.2.0 | 2026-09-29 |
| PyBullet 仿真 | [litegrip-pybullet](https://github.com/nexform-tech/litegrip-pybullet) | v0.3.0 | 2026-09-29 |
| Isaac Sim 仿真 | [litegrip-isaacsim](https://github.com/nexform-tech/litegrip-isaacsim) | v1.0.1 | 2026-09-27 |
| URDF 模型 | [litegrip-urdf](https://github.com/nexform-tech/litegrip-urdf) | 暂无发布 | — |
| 上位机 | [litegrip-studio](https://github.com/nexform-tech/litegrip-studio) | v0.6.0 | 2026-09-29 |

**表中有两行写的是"暂无发布"，但两者含义不同。** `litegrip-ros1` 只是一个占位仓库：仓库已初始化，但源码、打包与文档都还没落地，目前没有任何可安装的内容。`litegrip-urdf` 则已有模型、launch 文件与文档，只是还没打 tag —— 请从默认分支获取。

**上表的发布目前都只提供源码。** 这些仓库都没有挂编译好的安装包，所以没有按平台下载的二进制包。要查某个组件的完整版本历史，请打开它的 Releases 页面。

Python SDK 尚未发布到 PyPI，请从源码安装：

```bash
git clone https://github.com/nexform-tech/litegrip-python.git
cd litegrip-python
python3 -m pip install .
```

## 3. 机械模型

URDF 描述在 [litegrip-urdf](https://github.com/nexform-tech/litegrip-urdf)，该仓库尚无发布版本，请从默认分支获取。

## 4. API 使用例程

示例脚本见 [litegrip-python/examples](https://github.com/nexform-tech/litegrip-python/tree/main/examples)。

## 5. 技术支持与帮助

两本手册的答疑章节先覆盖了常见问题。仍无法自行解决时，《软件开发手册》列出了联系我们前应记录的信息。技术支持由 NEXFORM ROBOTICS 技术团队提供，联系方式见随货单据与销售渠道。

## 仓库规范

本仓库遵循 NEXFORM ROBOTICS 的共享仓库规范：代理操作规则见 [AGENTS.md](AGENTS.md)；提交信息使用 Conventional Commits；每次合并到 `main` 由 semantic-release 自动发布版本。

## 许可证

Copyright © 2026 NEXFORM ROBOTICS，基于 [Apache License 2.0](LICENSE) 授权。
