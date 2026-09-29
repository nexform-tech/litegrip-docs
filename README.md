# litegrip-docs

[English](README.md) | [简体中文](readme_zn.md)

LiteGrip is an adaptive two-finger parallel gripper from NEXFORM ROBOTICS, designed for research and
education, AI robotics development, and lightweight industrial automation. It uses direct motor drive
and an adaptive grasping mechanism, with an effective stroke of 87.000 mm. The gripper communicates
with the host computer through a USB-CAN adapter (classic CAN, 1 Mbps), and suits grasping, handling,
loading and unloading, sorting, and algorithm validation.

This repository is the documentation source for LiteGrip. It indexes the manuals, SDKs, drivers,
simulation environments, models and host application, and records the latest release of each.

## 1. Manuals

| Manual | Reader | Contents |
| --- | --- | --- |
| [Product Manual](product-manual.md) | Users and installers | Specifications, electrical interface, installation, maintenance, troubleshooting |
| [Software Development Manual](soft-gripper-development-manual.md) | Integrators | SDK installation, interface usage and preconditions, the CAN protocol |

The documentation covers:

1. The SDK development interface — installation, and each interface's parameters, return values, preconditions and exceptions.
2. Product specifications and installation — stroke, gripping force, load, electrical parameters, wiring and mounting.
3. Troubleshooting — how to work through communication, motion, calibration and force-control problems.

## 2. SDKs and companion packages

| Component | Repository | Latest version | Released |
| --- | --- | --- | --- |
| Python SDK | [litegrip-python](https://github.com/nexform-tech/litegrip-python) | v0.9.1 | 2026-09-29 |
| C++ SDK | [litegrip-cpp](https://github.com/nexform-tech/litegrip-cpp) | v0.1.0 | 2026-09-28 |
| ROS 1 driver | [litegrip-ros1](https://github.com/nexform-tech/litegrip-ros1) | Not released | — |
| ROS 2 driver | [litegrip-ros2](https://github.com/nexform-tech/litegrip-ros2) | v0.1.0 | 2026-09-28 |
| MoveIt 2 configuration | [litegrip-moveit2](https://github.com/nexform-tech/litegrip-moveit2) | v0.1.0 | 2026-09-28 |
| MuJoCo simulation | [litegrip-mujoco](https://github.com/nexform-tech/litegrip-mujoco) | v0.2.0 | 2026-09-29 |
| PyBullet simulation | [litegrip-pybullet](https://github.com/nexform-tech/litegrip-pybullet) | v0.3.0 | 2026-09-29 |
| Isaac Sim simulation | [litegrip-isaacsim](https://github.com/nexform-tech/litegrip-isaacsim) | v1.0.1 | 2026-09-27 |
| URDF model | [litegrip-urdf](https://github.com/nexform-tech/litegrip-urdf) | Not released | — |
| Host application | [litegrip-studio](https://github.com/nexform-tech/litegrip-studio) | v0.6.0 | 2026-09-29 |

**Two rows say "Not released", and they mean different things.** `litegrip-ros1` is a placeholder:
the repository is initialized, but its source code, packaging and documentation have not landed
yet, so there is nothing to install. `litegrip-urdf` holds the model, its launch files and its
documentation, and simply has no tag yet — take it from the default branch.

**Every release in this table is source only.** None of these repositories attaches a compiled
package, so there is no per-platform binary to download. For a component's version history, open its
Releases page.

The Python SDK is not on PyPI yet. Install it from a checkout:

```bash
git clone https://github.com/nexform-tech/litegrip-python.git
cd litegrip-python
python3 -m pip install .
```

## 3. Mechanical model

[litegrip-urdf](https://github.com/nexform-tech/litegrip-urdf) holds the URDF description. It has no
tagged release yet, so take it from the default branch.

## 4. API examples

Example scripts are in
[litegrip-python/examples](https://github.com/nexform-tech/litegrip-python/tree/main/examples).

## 5. Support

The Q&A sections of both manuals answer the common questions first. If you cannot resolve a problem
yourself, the Software Development Manual lists what to record before you contact us. Support comes
from the NEXFORM ROBOTICS technical team; the contact details are on the documents shipped with the
product and through your sales channel.

## Repository standards

This repository follows the shared NEXFORM ROBOTICS repository standards: the agent operating rules
in [AGENTS.md](AGENTS.md), Conventional Commits, and automated semantic-release versioning on every
merge to `main`.

## License

Copyright © 2026 NEXFORM ROBOTICS. Licensed under the
[Apache License 2.0](LICENSE).
