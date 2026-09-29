# litegrip-docs

[English](README.md) | [简体中文](readme_zn.md)

Product documentation source, built and published as the public documentation
site for the **LiteGrip lightweight robotic gripper series**.

## Handbooks

This repository holds two handbooks, each in an English and a Chinese edition.
The unsuffixed filename is the English edition and `-zh` is the Chinese edition;
the two editions are kept line for line in step, so a change to one is a change
to both.

| Handbook | English | Chinese | Reader |
| --- | --- | --- | --- |
| Product Manual | [product-manual.md](product-manual.md) | [product-manual-zh.md](product-manual-zh.md) | Users and installers — specifications, electrical interface, installation, maintenance, troubleshooting |
| Software Development Manual | [soft-gripper-development-manual.md](soft-gripper-development-manual.md) | [soft-gripper-development-manual-zh.md](soft-gripper-development-manual-zh.md) | Integrators — SDK installation, interface usage and preconditions, the CAN protocol |

Read the Product Manual first: it covers the gripper's specifications, wiring,
installation, maintenance and troubleshooting, and assumes no knowledge of the
communication protocol. Read the Software Development Manual when you write your
own control program: it covers SDK installation, each interface's parameters and
return values, its **preconditions**, exceptions, and the underlying CAN
protocol.

## Scope

| | |
| --- | --- |
| Product | LiteGrip lightweight robotic gripper series |
| Repository role | Product documentation source, built and published as the public documentation site |

## Related repositories

| Repository | Role |
| --- | --- |
| [litegrip-python](https://github.com/nexform-tech/litegrip-python) | Python SDK |
| [litegrip-cpp](https://github.com/nexform-tech/litegrip-cpp) | C++ SDK |
| [litegrip-ros2](https://github.com/nexform-tech/litegrip-ros2) | ROS 2 driver |
| [litegrip-ros1](https://github.com/nexform-tech/litegrip-ros1) | ROS 1 driver |

## Repository standards

This repository follows the shared NEXFORM ROBOTICS repository standards: the
agent operating rules in [AGENTS.md](AGENTS.md), Conventional Commits, and
automated semantic-release versioning on every merge to `main`.

## License

Copyright © 2026 NEXFORM ROBOTICS. Licensed under the
[Apache License 2.0](LICENSE).
