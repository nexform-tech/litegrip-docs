# litegrip-docs

LiteGrip 轻量型夹爪系列的**产品文档源仓库**，构建并发布为公开文档站点。

## 手册

本仓库收录两本手册，各有中英两版。不带语言后缀的文件名是英文版，`-zh` 是中文版；两版逐行对齐，改一处就要同时改另一处。

| 手册 | 中文版 | 英文版 | 读者 |
| --- | --- | --- | --- |
| 产品手册 | [product-manual-zh.md](product-manual-zh.md) | [product-manual.md](product-manual.md) | 使用与安装人员 —— 规格、电气接口、安装、维护、故障排查 |
| 软件开发手册 | [soft-gripper-development-manual-zh.md](soft-gripper-development-manual-zh.md) | [soft-gripper-development-manual.md](soft-gripper-development-manual.md) | 集成工程师 —— SDK 安装、接口用法与前置条件、CAN 通信协议 |

先读《产品手册》：它讲清夹爪的规格、接线、安装、维护与故障排查，不要求你了解通信协议。要自己写控制程序时，再读《软件开发手册》：它说明 SDK 的安装、各接口的参数与返回值、每个接口的**前置条件**、异常，以及底层 CAN 通信协议。

本文件的中文版就是你现在读的这一份，英文版见 [README.md](README.md)。

## 仓库定位

| | |
| --- | --- |
| 产品 | LiteGrip 轻量型夹爪系列 |
| 仓库角色 | 产品文档源仓库，构建并发布为公开文档站点 |

## 相关仓库

| 仓库 | 作用 |
| --- | --- |
| [litegrip-python](https://github.com/nexform-tech/litegrip-python) | Python SDK |
| [litegrip-cpp](https://github.com/nexform-tech/litegrip-cpp) | C++ SDK |
| [litegrip-ros2](https://github.com/nexform-tech/litegrip-ros2) | ROS 2 驱动 |
| [litegrip-ros1](https://github.com/nexform-tech/litegrip-ros1) | ROS 1 驱动 |

## 仓库规范

本仓库遵循 NEXFORM ROBOTICS 的共享仓库规范：代理操作规则见 [AGENTS.md](AGENTS.md)；提交信息使用 Conventional Commits；每次合并到 `main` 由 semantic-release 自动发布版本。

## 许可证

Copyright © 2026 NEXFORM ROBOTICS，基于 [Apache License 2.0](LICENSE) 授权。
