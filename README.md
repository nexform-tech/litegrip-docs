# litegrip-docs

[English](README.md) | [简体中文](README.zh-CN.md)

LiteGrip is an adaptive two-finger parallel gripper from NEXFORM ROBOTICS, designed for research and
education, AI robotics development, and lightweight industrial automation. It uses direct motor drive
and an adaptive grasping mechanism, with an effective stroke of 85.000 mm. The gripper communicates
with the host computer through a USB-CAN adapter (classic CAN, 1 Mbps), and suits grasping, handling,
loading and unloading, sorting, and algorithm validation.

This repository is the documentation source for LiteGrip. It indexes the manuals, SDKs, drivers,
simulation environments, models and host application, and records the latest release of each.

## 1. Manuals

| Manual | Reader | Contents |
| --- | --- | --- |
| [Product Manual](product-manual.md) | Users and installers | Specifications, electrical interface, installation, maintenance, troubleshooting |
| [Software Development Manual](soft-gripper-development-manual.md) | Integrators | SDK installation and usage, ecosystem integration, and a condensed CAN protocol appendix |

The documentation covers:

1. The SDK development interface — installation, and each interface's parameters, return values, preconditions and exceptions.
2. Product specifications and installation — stroke, gripping force, load, electrical parameters, wiring and mounting.
3. Troubleshooting — how to work through communication, motion, calibration and force-control problems.

## 2. SDKs and companion packages

| Component | Repository | Latest version | Released |
| --- | --- | --- | --- |
| Python SDK | [litegrip-python](https://github.com/nexform-tech/litegrip-python) | v1.1.0 | 2026-10-14 |
| C++ SDK | [litegrip-cpp](https://github.com/nexform-tech/litegrip-cpp) | v1.0.9 | 2026-10-14 |
| ROS 1 driver | [litegrip-ros1](https://github.com/nexform-tech/litegrip-ros1) | Not released | — |
| ROS 2 driver | [litegrip-ros2](https://github.com/nexform-tech/litegrip-ros2) | v0.1.0 | 2026-09-28 |
| MoveIt 2 configuration | [litegrip-moveit2](https://github.com/nexform-tech/litegrip-moveit2) | v0.1.1 | 2026-10-12 |
| MuJoCo simulation | [litegrip-mujoco](https://github.com/nexform-tech/litegrip-mujoco) | v0.5.0 | 2026-10-10 |
| PyBullet simulation | [litegrip-pybullet](https://github.com/nexform-tech/litegrip-pybullet) | v0.6.1 | 2026-10-10 |
| Isaac Sim simulation | [litegrip-isaacsim](https://github.com/nexform-tech/litegrip-isaacsim) | v1.0.1 | 2026-09-27 |
| URDF model | [litegrip-description](https://github.com/nexform-tech/litegrip-description) | v1.0.0 | 2026-10-12 |
| Host application | [litegrip-studio](https://github.com/nexform-tech/litegrip-studio) | v0.12.4 | 2026-10-14 |

**One row says "Not released".** `litegrip-ros1` is a placeholder: the repository is initialized, but
its source code, packaging and documentation have not landed yet, so there is nothing to install.

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

[litegrip-description](https://github.com/nexform-tech/litegrip-description) holds the model, and it is released:
**v1.0.0**. The ROS 2 package is named `litegrip_description`.

| Item | Value |
| --- | --- |
| Robot description | `litegrip_description/urdf/litegrip_description.urdf.xacro` — the single source of truth |
| Links | `base_footprint` (root), `base_link`, `gripper_opening_link` (master), `gripper_slider_link1` (right), `gripper_slider_link2` (left) |
| Joints | `gripper_opening_joint` (master, `+X`, prismatic); `gripper_slide_joint_right` (`+X`) and `gripper_slide_joint_left` (`-X`) are its `<mimic>` followers |
| Meshes | Three STL files: `base_link.STL`, `gripper_slider_link1.STL`, `gripper_slider_link2.STL` |
| Launch files | `display.launch.py`, `ros2_control.launch.py`, `gazebo.launch.py` |
| Requirements | ROS 2 Humble on Ubuntu 22.04, system Python 3.10 |

The gripper has one motor and one transmission, so only `gripper_opening_joint` is
commandable. Its value is the opening travel in metres (`0` closed, `0.085452` fully open),
and each finger follows as `q = -0.5 × opening + stroke`. The shipped per-finger travel
default is `0.042726` m.

```bash
ros2 launch litegrip_description display.launch.py
```

Add `stroke:=` to override the per-finger travel used by the model.

The simulations use this model rather than a separate one. PyBullet loads the upstream xacro and
normalises it at load time, and MuJoCo builds its MJCF on the same three STL meshes.

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
in [`.nexform-standards.json`](.nexform-standards.json), Conventional Commits, and automated semantic-release versioning on every
merge to `main`.

## License

Copyright © 2026 NEXFORM ROBOTICS. Licensed under the
[Apache License 2.0](LICENSE).
