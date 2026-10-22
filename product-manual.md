# Preface

[English](product-manual.md) | [简体中文](product-manual-zh.md)

LiteGrip is an adaptive two-finger parallel gripper from NEXFORM ROBOTICS, designed for research and education, AI robot development, and lightweight industrial automation, with an effective stroke of 85.000 mm. The gripper communicates with the host computer through a USB-CAN adapter (classic CAN, 1 Mbps) and ships with a Python SDK and factory calibration data. It suits grasping, transferring, loading and unloading, sorting, and algorithm validation.

This manual covers the product's appearance, technical specifications, safety notices, selection guidance, and installation and daily use. For the software interface, parameters, and communication protocol, see the Software Development Manual.

## Contents

- [Hardware components](#hardware-components)
- [Units](#units)
- [Safety](#safety)
- [Technical specifications](#technical-specifications)
  - [General specifications](#general-specifications)
  - [Stroke and position](#stroke-and-position)
  - [Grip and load capacity](#grip-and-load-capacity)
  - [Motion performance](#motion-performance)
  - [Electrical specifications](#electrical-specifications)
  - [Mechanical and environment](#mechanical-and-environment)
  - [Selection guidance](#selection-guidance)
- [Electrical interface](#electrical-interface)
  - [Electrical safety](#electrical-safety)
  - [Interface overview](#interface-overview)
  - [Power supply](#power-supply)
  - [CAN bus](#can-bus)
- [Installation and use](#installation-and-use)
  - [Appearance and parts](#appearance-and-parts)
  - [Mounting](#mounting)
  - [Wiring](#wiring)
  - [Power-up sequence](#power-up-sequence)
  - [Host requirements](#host-requirements)
  - [Daily use](#daily-use)
  - [Maintenance](#maintenance)
  - [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
  - [Q&A](#qa)
- [Related documents and support](#related-documents-and-support)

## Hardware components

The standard delivery and the equipment you need to provide are listed below; the sales configuration list is the final authority:

| Category | Item | Description |
|------|------|------|
| Standard delivery | LiteGrip gripper body | Includes the drive motor, transmission, fingers, and fingertips |
| Standard delivery | CAN terminating resistors | One 120 Ω resistor at each end of the bus |
| You provide | 24 V DC power supply | Powers the motor; the motor outputs no torque when it is not connected |
| You provide | USB-CAN adapter | Connects the gripper to the host computer |
| You provide | Host computer | Linux with SocketCAN support in the kernel |

## Units

The physical quantities in this manual and in the SDK use the following units:

| Parameter | Unit | Description |
|------|------|------|
| Aperture / position | mm | Millimetres |
| Velocity | mm/s | Millimetres per second |
| Torque | N·m | Newton-metres |
| Gripping force | N | Newtons |
| Temperature | °C | Degrees Celsius |
| Voltage | V DC | Volts (DC) |

"Aperture" in this document and the position `p` returned by the SDK are the same quantity: the true distance between the inner faces of the two fingers. At full closure `p = 0`; at full opening `p = 85.000`, and the per-finger stroke is 42.500 mm. It is not a motor angle and not a per-finger displacement; it is exactly what a caliper measures between the two fingertips.

## Safety

### Overview

This section describes the safety principles you must follow when using the LiteGrip gripper and its system. Before installation and use, you must read this manual carefully and strictly follow every passage that carries a severity label. Gripper systems carry potential hazards such as gripping, collision, and falling; users must fully recognize the operating risks and use the SDK or control software only after training.

### Severity labels

Safety notes in this manual use the labels below; the graphical symbols on the product are the authority:

- Danger: a hazardous situation that may cause death, personal injury, or severe equipment damage.
- Warning: a hazardous situation that, if not avoided, could cause death, personal injury, or severe equipment damage.
- High temperature: hot parts, where contact may cause burns or equipment damage.
- Caution: a general warning that, if not avoided, may cause personal injury or equipment damage.

### Safety precautions

**Handling the gripper**

1. Install the gripper and the electrical equipment as this manual requires. The mounting surface must be flat and rigid enough, and the fastening bolts must carry an even load.
2. Before first use, have a qualified person inspect the gripper and the protection system, and test the hardware emergency stop, the mechanical stop, and the enable state.
3. Before use, check that the equipment is intact and mounted securely, and confirm that the fingers' motion range holds no obstructions, no people, and no cables that could be pulled in.
4. **You must provide a hardware emergency stop loop whose action does not depend on CAN communication or host software; you must provide a mechanical stop as the last line of defense.**
5. Read the documentation before development and debugging, and make sure the target position, velocity, and gripping force are correct. For the first motion, use a low velocity and a conservative stroke.
6. **This product has no power-off self-locking.** After disable or abnormal power-down the motor no longer outputs a holding torque, and the gripper may move under gravity or an external force. If the application does not allow movement after power-off, you must add a separate mechanical holding device.
7. Before installation, maintenance, or cleaning, you must disconnect the 24 V power supply and confirm that power is off.
8. Unauthorized personnel must not modify this unit's calibration file, the motor registers, or the host-side limiting parameters.

**Personnel safety**

1. Users must read the product manual and know the safe operating procedure and how to handle errors.
2. While the equipment is running, the fingers may be waiting for a command even when they look stopped, so treat the gripper as still in motion.
3. Define the motion range of the gripper and the end tool and set up a safe working zone; no person may enter the gripper's motion range while it is running.
4. Inspect the gripper regularly to keep the mounting bolts and the fingertips from loosening.
5. In manual teaching the motor outputs no torque, and the fingers move under gravity or an external force. To stop at a position, exit zero gravity mode after you let go. Debugging and calibration must be supervised by a person on site, with the hardware emergency stop available.

### Responsibility and standards

The gripper can form a complete system with other equipment, and this document does not cover all of the design, installation, and operation of that complete system. The safety of the complete system depends on how it is integrated; users must carry out a risk assessment for the complete system under the laws and safety standards of their country or region and take the corresponding protective measures.

Starting to use this gripper means you have read, understood, and accepted all the terms of this manual and of the safety information. Users are responsible for their own actions and their consequences, and must use the gripper only for legitimate purposes. We accept no liability for personal injury, accidents, or property damage caused by violation of the usage requirements or by force majeure.

### Risk assessment

A risk assessment must consider every potential contact between a person and the gripper under normal use and foreseeable misuse, for example:

- Fingers being pinched by the gripper fingers;
- Impact between the gripper and the robot arm end or the fixtures;
- A workpiece falling because it is not gripped securely or the load is out of range;
- Handling sharp or hot workpieces;
- The gripper losing its holding torque and the workpiece coming loose after power-off or disable;
- Software failure leaving the gripper to keep executing a motion command.

Through the risk assessment, users must judge whether the relevant hazards constitute an unacceptable risk and take the corresponding measures. The gripper is not suitable for people who lack the guidance of a qualified professional or who do not have full civil capacity.

# Technical specifications

## General specifications

| Parameter name | Value |
|--------|------|
| Product name | LiteGrip adaptive two-finger parallel gripper |
| Structure | Adaptive two-finger parallel gripper |
| Drive method | Direct motor drive |
| Motor model | DM-J4310-2EC (MIT mode) |
| Communication | Classic CAN, 1 Mbps |
| Operating voltage | 24 V DC (nameplate rating) |
| Effective stroke | 85.000 mm |
| Per-finger stroke | 42.500 mm (effective stroke ÷ 2) |
| Working stroke | 0 ~ 85.000 mm, the entire stroke is usable |
| Power-off self-locking | None (holding torque is lost when power is removed) |
| Total mass | 0.483 kg (includes motor, cable, fingertips, and mounting parts) |

## Stroke and position

The SDK position `p` runs from 0 at the fully closed end to 85.000 mm at the fully open end, with no disabled region in between; the whole stroke is usable. `p` is the actual aperture between the inner faces of the two fingers and agrees with a caliper measurement; there is no offset to add.

The factory calibration sets `work_stroke_mm` to 80.0 mm, so the default `open()` stops at 80 mm and does not reach the open-side mechanical stop. To open fully, use `goto(85.0)`.

> **Note**: When a position target exceeds the calibrated range, the SDK silently clamps it to the endpoint, neither raising an error nor giving any indication. "Commands must not go out of range" must be implemented by the integrator in the application layer. See "Motion control" in the Software Development Manual.

## Grip and load capacity

> **This section is the most important one for selection, and it deliberately carries no numbers.** How heavy an object this gripper can hold is fixed by the **gripping force**, the **friction coefficient** of the workpiece surface, and the **pose** — it is not one figure, and a figure measured on one test piece does not transfer to another.
>
> **Grip is friction holding, not structural strength.** The mass that can be held is `μ × total two-finger gripping force ÷ 9.81`, so any load figure holds only for the workpiece, contact surface and pose it was measured with. **Contact us for the grasping-force and load data for your application** instead of sizing against a number quoted for a different one.
>
> **The load capacity cannot be derived from the motor torque**; it has to be measured. **This product has no self-locking when power is removed**; if the application does not allow release after power loss, you must add a mechanical holding device.

## Motion performance

| Item | Specification |
|------|------|
| Position resolution | 0.0242 mm (encoder resolution; affected by this unit's calibration coefficient and may differ from unit to unit) |
| Absolute position accuracy | 2.708 mm (measured on a prototype; may differ from unit to unit — measure under your own conditions) |

## Electrical specifications

| Parameter name | Value |
|--------|------|
| Rated voltage | 24 V DC |
| Undervoltage protection point | 15 V |
| Overvoltage protection point | 32 V |
| No-load current | 0.037 A |
| Rated current | 3.1 A |
| Peak current | 16.5 A |
| Control / feedback period | 200 Hz |
| Motor overtemperature protection point | 100 °C |
| Communication dropout protection | Automatically exits enable after 0.4 s |
| Status feedback mode | Polled (responds after receiving a command frame); passive listening is not supported |

## Mechanical and environment

| Parameter name | Value |
|--------|------|
| Overall dimensions (length × width × height) | 150 × 85 × 170 mm |
| Fingertip dimensions (length × width × thickness) | 84 × 60 × 22 mm |
| Coil overtemperature protection point | 100 °C |
| Driver board overtemperature protection point | 120 °C |

> **Note**: This manual does not provide the mounting interface dimensions or the cable and connector specifications. If you need to mount the gripper on a robot arm end or a custom bracket, or need cable data, contact us.

> **Note**: The IP rating and CE, RoHS and REACH are not certified. Contact us before using the gripper in an environment with dust, moisture, or cutting fluid.

## Selection guidance

**First confirm applicability:**

| Suitable | Not suitable |
|------|--------|
| Grasping, transferring, loading/unloading, and sorting of small and medium-sized rigid objects | High-temperature objects, sharp objects |
| | Applications requiring precise gripping force (before force calibration is complete) |
| | Applications requiring power-off holding (this product has no self-locking) |
| | Dusty, humid, or corrosive environments (IP rating not certified) |

**Confirm the following in order when selecting:**

| # | Check | Basis for judgment |
|---|--------|---------|
| 1 | Object size | Whether it falls within the working stroke 0 ~ 85.000 mm |
| 2 | Object weight | Confirm it against your own workpiece, contact surface and pose; contact us for the data |
| 3 | Is release after power loss acceptable | This product has no power-off self-locking; if it is not acceptable, add a mechanical holding device |

# Electrical interface

## Electrical safety

1. Do not connect or disconnect the CAN or power cables while power is applied; cut the 24 V supply before installation and maintenance.
2. Check the power polarity; reversing it can damage the equipment. Confirm the polarity with a multimeter before powering up.
3. Protect the unit from water and moisture. If water gets in, cut the power immediately and contact support.
4. The 24 V supply must provide overcurrent and short-circuit protection.
5. Confirm a reliable ground connection between the host computer and the power supply.

## Interface overview

The LiteGrip external interface consists of three sets of connections:

| Connection | Description |
|------|------|
| 24 V power supply | Powers the motor; the motor produces no torque when it is not connected |
| CAN bus | Connects the gripper to the USB-CAN adapter, including CAN_H and CAN_L |
| CAN terminating resistors | One 120 Ω resistor at each physical end of the bus |

> **Note**: The terminating resistors are mandatory. The typical symptom when they are missing is communication that drops in and out.

## Power supply

| Item | Specification |
|------|------|
| Rated voltage | 24 V DC |
| Protection trip points | Undervoltage 15 V, overvoltage 32 V |
| No-load current | 0.037 A |
| Rated / peak current | 3.1 A / 16.5 A |

**Applying 24 V is the precondition for motor torque.** With only the USB-CAN adapter connected, the gripper can communicate and report status, but it will not move, and it reports an undervoltage fault (error code 0x9). This is normal behavior, not a fault.

Estimating from the peak current of 16.5 A, the 24 V supply should be at least 400 W; typical operation (rated 3.1 A) needs about 75 W.

## CAN bus

| Item | Specification |
|------|------|
| Protocol | Classic CAN (CAN 2.0, not CAN FD) |
| Baud rate | 1 Mbps |
| Data frame length | 8 bytes |
| Terminating resistors | 120 Ω at each end of the bus |
| Control mode | MIT |
| Communication timeout protection | Automatically disables after 0.4 s |

> **Note**: CAN FD must be explicitly disabled. If the interface is opened in FD mode, communication fails even with the correct baud rate, and this looks just like "no 24 V connected", so it is easily misdiagnosed as a hardware fault.

> **Note**: Feedback from this product is polled. The motor answers only after it receives a command frame; passively listening on the bus never yields a feedback frame.

For interface configuration commands, frame formats, and registers, see the protocol appendix of the Software Development Manual.

# Installation and use

## Appearance and parts

LiteGrip consists of the gripper body, two parallel-motion fingers, the fingertips, and the cable outlet:

| Part | Description |
|------|------|
| Gripper body | Contains the drive motor, transmission, and guide rail |
| Finger (left / right) | Moves in parallel along the guide rail; per-finger stroke 42.500 mm |
| Fingertip | The part that contacts the workpiece directly; dimensions 84 × 60 × 22 mm |

## Mounting

1. Check the packaging for obvious damage.
2. Check the gripper for deformation or impact damage.
3. Push the fingers by hand and confirm they move smoothly with no binding.
4. Mount the gripper on a bracket or robot-arm end flange with sufficient rigidity. The mounting face must be flat and the fastening bolts must be loaded evenly.
5. After mounting, confirm there are no obstructions in the fingers' range of motion.

> **Note**: The gripper has a mechanical stop in the opening direction and none in the closing direction. The fingers meet directly when closing; do not expect a closing motion to press a part onto a locating face. To keep the gripper holding, use force control rather than driving a position command to the limit.

> **Note**: You must cut the 24 V supply before installation or removal. Contact us for the mounting interface dimensions.

## Wiring

Wire the three connection groups as shown in "Interface overview": the 24 V power supply, the CAN bus, and the 120 Ω terminating resistors at both ends of the bus.

> **Note**: Reversed power polarity can damage the device; confirm the polarity with a multimeter before power-up.

> **Note**: Do not make your own cables or buy your own connectors; contact us if you need them.

## Power-up sequence

1. Confirm the wiring is correct and there is no short circuit.
2. Power on the USB-CAN adapter.
3. Last, power on the 24 V supply.

Power down in the reverse order: cut the 24 V first, then the adapter. This is the recommended convention; neither the SDK nor the driver enforces it.

**Handling abnormalities**: If you find obvious deformation or jamming of the fingers, damaged cables, bent connector pins, a cracked housing, or water or foreign objects inside the packaging, do not apply power; contact us.

## Host requirements

| Item | Requirement |
|------|------|
| Operating system | Linux with SocketCAN support in the kernel |
| Hardware interface | USB-CAN adapter |
| CAN configuration | Classic CAN, 1 Mbps, CAN FD disabled |
| Python | 3.8 or later (when using the Python SDK) |

For SDK installation, CAN interface configuration, and example scripts, see the Software Development Manual.

## Daily use

**Grasping and closing**

`grasp()` closes until it contacts an object and is obstructed, then holds a force. The criterion is whether the fingers stop moving, so gripping an object and reaching the stroke endpoint both count as a successful grasp; read the position to tell the two apart. `close()` is different: it presses onto the closed-side stop, and a stall halfway (an object) reports `ok=False`.

> **Note**: The gripping force parameter has not been calibrated against a real load; do not rely on it before force calibration is complete. For a pure position grasp, call `close()`, which takes no force argument and closes until an object obstructs it.

**Manual guidance**

To hold the gripper at a new position, put it in zero gravity mode; the motor then outputs no torque and you can push the fingers by hand. Leaving the mode holds the position at the moment you exit it.

> **Note**: Zero gravity mode does not itself hold position; the fingers stay wherever you let go and do not return on their own. Leaving the mode performs no range check, so it will hold a position even beyond the calibrated endpoint. Manual guidance must be supervised by a person on site.

## Maintenance

**Routine checks**

The intervals below are a recommended maintenance convention, not measured specifications, and are not a lifetime or reliability figure for this product:

| Interval | Check |
|------|--------|
| Every shift | Whether the fingers move smoothly, and whether there is any abnormal noise |
| Weekly | Whether the cables are damaged, and whether the connectors are loose |
| Monthly | Whether the fastening bolts are loose, and whether the fingers are worn |

**Cleaning and storage**

- After cutting power, wipe the housing with a dry, soft cloth;
- Do not use organic solvents or corrosive cleaners;
- Do not wash with water;
- Before long-term storage, disconnect the 24 V supply and store the unit in a dry environment free of corrosive gases.

**Recalibration**

After any of the following, you must recalibrate:

- Replacing the gripper body or the motor;
- Replacing or repairing a finger;
- A collision or an overload;
- An abnormal position reading after a power cycle.

## Troubleshooting

| Symptom | Possible cause | Remedy |
|------|----------|----------|
| No communication at all | CAN interface not configured, or CAN FD not disabled | Reconfigure the interface with CAN FD disabled |
| | Terminating resistors missing | Fit one 120 Ω at each end of the bus |
| | Loose cable | Check the connectors |
| Status can be read but the gripper does not move | The 24 V supply is not connected | Connect 24 V (the most common cause) |
| | Motor not enabled | Check whether the enable step succeeded |
| | No valid calibration | Reload the calibration or run the calibration procedure |
| The gripper stops halfway through a motion | It gripped an object or a foreign body | Check for obstructions |
| | Overcurrent or overtemperature protection tripped | Stop and let it cool, then check the load |
| The gripper stops at an endpoint and will not move | The target is outside the calibrated range and is silently clamped | The SDK does not report an error; check the target position |
| Grasping always reports failure | The fingers are still moving at timeout, usually because they never touched the object | Confirm the object is within the stroke range |
| | The timeout is set too short | Increase the grasp timeout |
| Insufficient gripping force | Force control has not been calibrated | Do not rely on the force parameter; use `close()` or add a mechanical limit |
| Abnormal noise or jamming during motion | Foreign matter on the guide rail or mechanical damage | Cut power and inspect; contact service |
| Shuts down after running for a while | Overtemperature protection | Reduce the load or improve heat dissipation |

**Error code reference:**

| Error code | Meaning | Action |
|--------|------|------|
| 0x0 | Disabled | Normal (not-enabled state) |
| 0x1 | Enabled | Normal |
| 0x8 | Overvoltage | Check whether the supply exceeds 32 V |
| 0x9 | Undervoltage | Check whether 24 V is connected |
| 0xA | Overcurrent | Check for binding and for an excessive load |
| 0xB | MOS overtemperature | Stop and let it cool |
| 0xC | Coil overtemperature | Stop and let it cool |
| 0xD | Communication loss | Check the CAN wiring and the terminating resistors |
| 0xE | Overload | Reduce the load |

> **Note**: 0x8 and 0x9 are very easy to mix up. The correct order is 8 = overvoltage, 9 = undervoltage.

> **Note**: These are the common codes the driver can report. The shipped SDK provides text for only some of them and displays the rest as "unknown error"; interpret them from this table.

**If you cannot resolve the problem yourself**, record the product model and serial number, a description of the symptom and how often it occurs, and the host operating system version, then contact us.

# FAQ

## Q&A

Q: How wide is the gripper aperture? A: The effective stroke is 85.000 mm. The SDK position `p` runs from 0 at the fully closed end to 85.000 at the fully open end, the whole stroke is usable, and `p` is the aperture a caliper would measure. Per finger that is 42.500 mm.

Q: How heavy an object can it grip? A: It depends on your workpiece, not on the gripper alone. Grip is friction holding, so the figure depends on the gripping force, the friction coefficient of the contact surface, and the pose. This manual publishes no load figure; contact us for the data for your application.

Q: How large is the gripping force? A: It is not published. `grasp(force_n=...)` accepts a value, but the SDK converts it through an uncalibrated nominal coefficient, so it is a qualitative reference only and must not be used as a calibrated gripping force.

Q: Can I set the gripping force? A: `grasp(force_n=...)` takes a force, but entering one does not make the force accurate. For a position grasp that stops on contact, use `close()`, which takes no force argument at all.

Q: Is Windows supported? A: No. The development kit currently supports Linux only.

Q: Is it water- and dust-proof? A: The IP rating is not yet certified. Contact us before using it in an environment with dust, moisture, or cutting fluid.

Q: Does the gripper release when power is cut? A: Yes. This product has no power-off self-locking. If your application cannot accept that, you must add a separate mechanical holding device.

Q: Must the 24 V supply be connected? A: Yes. With only USB-CAN connected, it can communicate and report status, but it will not move, and it reports undervoltage. That is normal, not a fault.

Q: How do I stop the gripper? A: The emergency stop must be implemented in hardware: cut the 24 V drive power (note that this product has no power-off self-locking, so the fingers will release when you cut it), or wire an independent emergency-stop circuit outside the host computer.

Q: What is the technical support channel? A: The NEXFORM ROBOTICS technical team. Contact details are in the documents shipped with the product and through the sales channel, or the contact person from your purchase can forward you to technical support directly.

# Related documents and support

This manual covers the product's appearance, technical specifications, safety notices, and installation and use. For the software interface and protocol details, see the development manual; for the SDK, simulation, and host application, see the repositories below:

| Document / repository | Contents |
|---|---|
| [the Software Development Manual](soft-gripper-development-manual.md) | SDK usage, ecosystem integration, and protocol appendix |
| [litegrip-python](https://github.com/nexform-tech/litegrip-python) | Python SDK |
| [litegrip-cpp](https://github.com/nexform-tech/litegrip-cpp) | C++ SDK |
| [litegrip-ros2](https://github.com/nexform-tech/litegrip-ros2) | ROS 2 driver |
| [litegrip-studio](https://github.com/nexform-tech/litegrip-studio) | Host application |
| [github.com/nexform-tech](https://github.com/nexform-tech) | All repositories and document downloads |

---

> **End of document** If you have questions or need more information, contact the NEXFORM ROBOTICS technical team.
