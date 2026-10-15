# Preface

[English](soft-gripper-development-manual.md) | [简体中文](soft-gripper-development-manual-zh.md)

LiteGrip is an adaptive two-finger parallel gripper from NEXFORM ROBOTICS, designed for research and education, AI robotics development, and lightweight industrial automation, with an effective stroke of 85.000 mm. The gripper communicates with the host computer through a USB-CAN adapter (classic CAN, 1 Mbps) and comes with a Python SDK and complete protocol documentation; it supports grasping, handling, loading and unloading, sorting, and algorithm validation.

This document is for **integrators** and explains SDK installation, interface usage, parameters and return values, exceptions, the **precondition** of each interface, and the underlying CAN communication protocol. For product specification values (stroke, velocity, torque, temperature, electrical parameters, and so on), see [the Product Manual](product-manual.md) and the Parameter Document; for the basis of the safety design, see the Safety Manual.

## Contents

- [Hardware components](#hardware-components)
- [Units](#units)
- [Safety](#safety)
- [SDK usage guide](#sdk-usage-guide)
  - [Overview](#overview-1)
  - [Library dependencies](#library-dependencies)
  - [1. Installing the SDK](#1-installing-the-sdk)
  - [2. Bringing up the CAN interface](#2-bringing-up-the-can-interface)
  - [3. Applying 24 V drive power](#3-applying-24-v-drive-power)
  - [4. Loading the calibration](#4-loading-the-calibration)
  - [5. First run: make the gripper move](#5-first-run-make-the-gripper-move)
  - [6. When the gripper does not move](#6-when-the-gripper-does-not-move)
  - [Enabling, disabling, and fault handling](#enabling-disabling-and-fault-handling)
  - [Motion control (open/close and position)](#motion-control-openclose-and-position)
  - [Grasping and force control](#grasping-and-force-control)
  - [Reading state](#reading-state)
  - [Units and conversion](#units-and-conversion)
  - [Manual guidance (zero gravity)](#manual-guidance-zero-gravity)
  - [Calibration and zero point](#calibration-and-zero-point)
  - [Configuration object](#configuration-object)
  - [Preconditions and calling constraints](#preconditions-and-calling-constraints)
  - [Exceptions and error handling](#exceptions-and-error-handling)
  - [Motion tuning (MotionConfig)](#motion-tuning-motionconfig)
  - [Teleoperation (leader/follower)](#teleoperation-leaderfollower)
  - [Trajectory record and replay](#trajectory-record-and-replay)
  - [Driving the bus directly (litegrip.can)](#driving-the-bus-directly-litegripcan)
  - [Core API quick reference](#core-api-quick-reference)
- [Secondary development](#secondary-development)
  - [Extending the Python SDK](#extending-the-python-sdk)
  - [C++ SDK](#c-sdk)
  - [ROS 2 (ros2_control and MoveIt 2)](#ros-2-ros2_control-and-moveit-2)
  - [Simulation (MuJoCo, PyBullet, Isaac Sim)](#simulation-mujoco-pybullet-isaac-sim)
  - [Host application (litegrip-studio)](#host-application-litegrip-studio)
  - [What is not ready yet](#what-is-not-ready-yet)
  - [Reporting and verification status](#reporting-and-verification-status)
  - [FAQ and technical support](#faq-and-technical-support)
- [CAN communication protocol](#can-communication-protocol)
  - [Physical layer and nodes](#physical-layer-and-nodes)
  - [Frame types](#frame-types)
  - [MIT control frame](#mit-control-frame)
  - [Command frame](#command-frame)
  - [Status refresh frame](#status-refresh-frame)
  - [Parameter frames and registers](#parameter-frames-and-registers)
  - [Feedback frames and error codes](#feedback-frames-and-error-codes)
  - [Communication timing](#communication-timing)
  - [Typical interaction sequences](#typical-interaction-sequences)
- [Appendix A: Status, error codes, and exceptions](#appendix-a-status-error-codes-and-exceptions)
  - [Status and error fields](#status-and-error-fields)
  - [Python exception types](#python-exception-types)
  - [Error handling guidance](#error-handling-guidance)
- [Appendix B: Communication and connection troubleshooting](#appendix-b-communication-and-connection-troubleshooting)
  - [CAN interface and endpoint information](#can-interface-and-endpoint-information)
  - [CAN interface configuration](#can-interface-configuration)
  - [Bus self-check without the SDK](#bus-self-check-without-the-sdk)
  - [Connection troubleshooting](#connection-troubleshooting)

## Hardware components

| No. | Device | Description |
|------|------|------|
| 1 | LiteGrip gripper body | Adaptive two-finger parallel gripper, including the drive motor **DM-J4310-2EC** (the motor has a built-in 10:1 gearbox, with no additional reduction stage) |
| 2 | 24 V DC power supply | Required external device. **The motor outputs no torque while it is not connected** |
| 3 | USB-CAN adapter | Required external device. It powers the communication link independently |
| 4 | CAN terminating resistor | Required external device, one 120 Ω terminating resistor at each end of the bus |
| 5 | Host computer | **Linux**, Python 3.8 or later |
| 6 | Calibration file for this unit | The measured calibration data for this unit, one set per gripper |

## Units

| Parameter | Unit | Description |
|------|------|------|
| Aperture / position | mm | Millimeter |
| Motor angle | rad | Radian |
| Velocity | mm/s, rad/s | Millimeters per second, radians per second |
| Torque | N·m | Newton-meter |
| Gripping force | N | Newton |
| Temperature | °C | Degree Celsius |
| Voltage | V DC | Volt (DC) |

**Aperture reading convention**: the same physical aperture has two representations, and their **zero points and directions do not agree**; mixing them is the most common cause of wrong numbers.

| Representation | Fully closed | Fully open | Value when open |
|---------|---------|---------|-----------|
| Motor angle `r` (rad) | Calibrated value `pos_closed_rad` (**see the calibration file for this unit**) | Calibrated value `pos_open_rad` (**see the calibration file for this unit**) | **Decreases** |
| SDK position `p` = actual aperture (mm) | 0 | **85.000** (= effective stroke) | Increases |

> **Unless this document states otherwise, "mm" always means the "actual aperture"** (that is, the true distance between the inner faces of the two fingers), because that is the quantity a caliper can measure directly.
>
> **`get_position()` and `position_mm` return the actual aperture.** The SDK's millimeter zero point sits at the fully closed end, where the two fingertips touch, and the reading counts up from there to **85.000** at the open end. **There is no offset to add** — the value is what a caliper measures between the two fingertips.
>
> **Motor angle and calibrated values differ from unit to unit.** The rad endpoints come from the calibration file for this unit (`~/.litegrip/litegrip_calibration.json`), and **the values are different for every unit**, so this document gives no specific numbers; rely on the calibration file of your own unit.
>
> **The conversion factor only affects "the millimeter numbers displayed and millimeter targets".** The SDK position clamping uses the two **rad** values `pos_closed_rad` / `pos_open_rad` and is independent of the millimeter conversion factor — a wrong factor only makes the numbers wrong; it does not change the endpoint positions. **But this also means the SDK makes no out-of-range check for you**: if you need it to "refuse out-of-range targets", implement that yourself (see [Motion control](#motion-control-openclose-and-position)).

> **The effective stroke is `85.000 mm`, and the SDK agrees.** Its geometry constant `JAW_TRAVEL_MM` is `85.0`, and the per-finger travel is `42.5 mm`. Every millimeter figure in this manual and in the Product Manual is that same stroke; there is no second convention to reconcile.

## Safety

### Overview

This section describes the safety principles and standards you must follow when using the LiteGrip gripper and system. Before installing or using it, you must read this document and the Safety Manual carefully; content that carries a severity label must be understood and strictly followed. Gripper systems present potential hazards during operation, including gripping, collision, and falling; users must fully understand the operating risks and use the SDK for development and debugging only after training.

### Severity labels

Safety notices in the other sections of this document name their severity with the labels below; the matching graphical symbols are on the labels shipped with the product:

- Danger: for hazardous situations that may lead to death or serious injury, or severe equipment damage.
- Warning: for hazardous situations that, if not avoided, could lead to death or serious injury, or severe equipment damage.
- High temperature: for hazardous situations involving hot parts, where contact may cause burns or equipment damage.
- Caution: for general warnings that, if not avoided, may lead to personal injury or equipment damage.

### Safety precautions (software side)

**Protection has three layers; software is only one of them:**

| Layer | Implemented by | What it protects |
|------|---------|---------|
| Out-of-range checking | **Implemented by the integrator** | Commands stay in range (the SDK itself makes no out-of-range check) |
| Driver-level protection | Motor driver firmware | Overvoltage / undervoltage / overcurrent / overtemperature / disconnection |
| Physical hard stops and hardware emergency stop | **Must be configured by the integrator** | The mechanism stays in range; a real power cut stops the machine |

1. **The SDK makes no out-of-range check.** A position target beyond the calibrated stroke is **silently clamped** to the endpoint (see [Motion control](#motion-control-openclose-and-position)), with neither an error nor a notice; out-of-range `kp` / `kd` / `tau` are **silently saturated**. "Commands stay in range" must be implemented by the integrator.
2. **You must configure a hardware emergency stop circuit, and its action must not depend on CAN communication or host software.** When a process hangs, CAN drops, or Python raises an exception, the software side cannot stop the machine.
3. **You must configure mechanical hard stops** as the last line of defence. A calibrated endpoint is not a mechanical hard stop.
4. **Do not use a software stop as a safety function.** `stop()` only sends a zero-torque frame, the motor stays enabled and can be back-driven, and it does not return success or failure; the `disable()` return value only means the command was sent, not confirmed (see [Enabling, disabling, and fault handling](#enabling-disabling-and-fault-handling)). Neither can replace a hardware emergency stop.
5. **Do not treat a return value as evidence that the command took effect.** A motion interface return value only means the frame was sent; only a feedback frame can prove the actual state.
6. **Do not use any force parameter before force calibration is complete.** The `force_n` conversion uses the nominal coefficient `0.1 N·m/N`, which the SDK neither validates nor limits (see [Grasping and force control](#grasping-and-force-control)).
7. Frames must be sent periodically during operation, otherwise the driver **automatically exits the enabled state** after 0.4 s (verify by reading back RID 9); **this timeout protection can be disabled, and once it is disabled the motor keeps the last torque command when the link drops** -- do not disable it without an assessment.
8. Debugging and calibration **must be supervised by a person present**, and the hardware emergency stop must be available.
9. If you find anything abnormal (unusual noise, jamming, abnormal temperature rise, jumping position readings), **stop the machine immediately and cut the 24 V**, then investigate.

### Responsibility and standards

The gripper can form a complete system with other equipment, and this document does not cover all the design, installation, and operation content of a complete system. The safety of a complete system installation depends on how it is integrated; you must assess the design and installation risks of the complete system under the laws, regulations, and safety standards of your country or region, and take the corresponding protective measures.

Starting to use this gripper is taken as having read, understood, and accepted all terms of this document and the safety information. You undertake to be responsible for your own actions and their consequences and to use the gripper only for legitimate purposes. We accept no liability for personal injury, accidents, or property damage caused by violation of the usage requirements or by force majeure. You must, but not only: perform a risk assessment of the complete system, write operating procedures, establish safety measures, confirm that the system is designed and installed correctly, and **not modify or bypass safety measures without authorization**.

### Risk assessment

From the software side, a risk assessment should consider the following failure modes in particular:

- The host process hangs or crashes; motion commands stop being sent but the mechanism still carries the last torque command;
- A CAN disconnection leaves the software unable to stop the machine;
- Position readings jump or fail, causing a wrong closed-loop decision;
- A wrong target position calculation (especially mixing mm with rad) drives the mechanism into the endpoint;
- A wrong force parameter calculation makes the gripping force too large;
- **Mistaking "the function returned" for "the motion is complete"**;
- Several processes or several host computers sending commands to the same gripper at the same time.

| Failure mode | Consequence | Mitigation |
|---------|------|---------|
| Process hangs | The mechanism keeps the last command | Driver communication timeout (0.4 s) + hardware emergency stop |
| CAN disconnection | Software stop fails | Driver timeout auto-disable + hardware emergency stop |
| Reading fails | Wrong closed-loop decision | Host validates the readings itself + hardware emergency stop |
| Wrong target calculation | Collision with the endpoint | Host-side limiting first + **mechanical hard stops** |
| Concurrent CAN masters | Commands overwrite each other | Guarantee a **single CAN master** and mutual exclusion in software |

You must use the risk assessment to judge whether the hazards concerned constitute an unacceptable risk and take the corresponding measures. The gripper is not suitable for use by persons without professional guidance or without full civil capacity.

> **Note**: **this SDK makes no safety decisions.** Out-of-range targets are **silently clamped** to the calibrated endpoint, force parameters get **no validation at all**, and out-of-range `kp` / `kd` / `tau` are **silently saturated** — none of these three cases **raises an error**. The preconditions of each interface are also only "connected" and "enabled"; see [Preconditions and calling constraints](#preconditions-and-calling-constraints). **Read that section first, then read the specific interfaces.**

# SDK usage guide

## Overview

The LiteGrip Python SDK is the `litegrip` package. It wraps the Damiao **DM-J4310-2EC** motor MIT protocol and provides interfaces for connecting, enabling, motion, grasping, manual guidance, calibration, teleoperation, trajectory record and replay, and reading state.

**The SDK has exactly two jobs: convert millimeters to motor angle and newtons to feedforward torque, then send MIT frames onto the bus at a fixed period.** It does not verify force calibration, does not reimplement the driver's own protection, and does not latch faults.

| Design principle | How it shows up in the interface |
|---------|--------------|
| **Commands are one-way; feedback is the truth** | CAN command frames have no acknowledgement; only the status frame the motor returns can prove a command actually took effect |
| **Position targets are clamped to the endpoints** | Targets beyond the calibrated stroke are **silently clamped** to the endpoint, neither raising an error nor rejecting them (see [Motion control](#motion-control-openclose-and-position)) |
| **Motion requires a calibration first** | `connect()` **does not** load a calibration; until one is loaded, every motion method raises `CommandError` instead of moving on placeholder coefficients (see [Preconditions and calling constraints](#preconditions-and-calling-constraints)) |
| **Driver protection is not reimplemented** | Overvoltage / undervoltage / overcurrent / overtemperature / disconnection protection is enforced by the DM-J4310-2EC driver firmware |

> **Note**: **This SDK does not implement "safety limits".** Out-of-range targets are clamped; `kp` / `kd` / `tau` are silently saturated when they fall outside the encoding range; and the force setpoint is an approximate conversion, not a calibrated measurement. **Measures to keep the fingers from damaging the workpiece or crushing a person must be implemented by the integrator, in software or in hardware.**

**Supported environment:**

| Item | Requirement |
|------|------|
| Operating system | **Linux only** (the kernel must support SocketCAN). Windows and macOS are not adapted |
| Architecture | x86_64 or arm64 |
| Python | 3.8 or later |
| Runtime dependencies | **None.** The package uses the Python standard library plus Linux SocketCAN; it does not need `python-can` or `damiao_socketcan` |
| Optional extra | `eclipse-zenoh>=1.0`, needed only by the zenoh teleoperation link |
| Hardware | A USB-CAN adapter, a 24 V supply, and 120 Ω termination at both ends of the bus |

> **Note**: **This SDK supports Linux only.** On another platform, implement the protocol from [CAN communication protocol](#can-communication-protocol) yourself.

**Modules in the package:**

| Module | Contents |
|------|------|
| `litegrip.gripper` | `LiteGrip`, the connection and motion entry point |
| `litegrip.actions` | `GripperActions` — the open/close/grasp/zero engine, plus `MotionConfig` and the result objects |
| `litegrip.models` | `GripperState`, `GripperConfig`, `GripperInfo`, `GripperStatus`, `GripperMode`, `CalibrationData`, `STALE_AFTER_S` |
| `litegrip.constants` | `GripperParams`, `GripperGeometry`, `UnitConversion`, `ErrorCode`, `DefaultParams`, `describe_error` |
| `litegrip.exceptions` | Six fault classes plus the base class |
| `litegrip.teleop` | `GripperTeleop` and the transports |
| `litegrip.trajectory` | `Trajectory`, `TrajectoryRecorder`, `TrajectoryPlayer` — a hand-taught motion, captured and replayed |
| `litegrip.zenoh_link` | The zenoh transport for teleoperation. Imported lazily; needs `pip install 'litegrip[zenoh]'` |
| `litegrip.can` | Raw SocketCAN transport and the DM motor codec, for multi-motor rigs |
| `litegrip.protocols` | `LiteGripCAN` — the single-motor bus object the high-level class drives |

## Library dependencies

**The package installs nothing.** `pyproject.toml` declares an empty `dependencies` list: the SDK is standard library plus Linux SocketCAN, so it runs on a bare robot controller with no package index reachable. Do not add a runtime dependency without a compelling reason — that property is the point.

| Dependency class | Item | Note |
|------|------|------|
| Runtime | *(none)* | Nothing is installed alongside `litegrip` |
| Optional | `eclipse-zenoh>=1.0` | Only the zenoh teleoperation link imports it; install with `pip install 'litegrip[zenoh]'` |
| System | SocketCAN | Part of the Linux kernel; `modprobe vcan` for a virtual bus |

> **Note**: **The SDK is not on PyPI.** `pip install litegrip` fails. Install from a source checkout, as the next section describes.

## 1. Installing the SDK

The package is not published to PyPI, so installation starts from a checkout of the [`litegrip-python`](https://github.com/nexform-tech/litegrip-python) repository.

**Step one, clone the repository:**

```bash
git clone https://github.com/nexform-tech/litegrip-python.git
cd litegrip-python
```

**Step two, install it:**

```bash
python3 -m pip install .
```

**Step three, confirm the import works:**

```bash
python3 -c "import litegrip; print(litegrip.__version__)"
```

A successful install prints the installed version. A checkout that was never installed prints `0.0.0+source`, which is the SDK's marker for "imported from loose files rather than an installed distribution" — it is not an error.

**Alternative: run without installing.** If you would rather not install into the interpreter, point `PYTHONPATH` at the source tree:

```bash
PYTHONPATH=/path/to/litegrip-python/src python3 your_script.py
```

**Uninstall:**

```bash
python3 -m pip uninstall litegrip
```

> **Note**: **Do not use `pip install -e .` in a deployment.** An editable install points the interpreter at your working copy, so a later `git checkout` on that directory silently changes what the robot runs. Use `pip install .` on the machine that drives the gripper, and an editable install only on a development machine.

## 2. Bringing up the CAN interface

The interface must exist and be up at the right bitrate before the SDK can open it. This needs root, or the `CAP_NET_ADMIN` capability.

**Step one, check that the interface exists:**

```bash
ip -details link show can0
```

**Step two, bring it up:**

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000 fd off
sudo ip link set can0 up
```

> **Note**: **`fd off` cannot be omitted.** If the interface is brought up in CAN FD mode, **communication will not succeed** even with the correct baud rate — and the symptom looks a lot like "no 24 V connected", so it is easily misdiagnosed as a hardware fault.

**Without hardware**, use a virtual bus to verify the software environment first:

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

> There is no real motor on a virtual bus, so **the enable step times out** (`enable()` gets no feedback frame and raises `HardwareError` after its retries are exhausted). This is **expected behavior**, not a fault.

## 3. Applying 24 V drive power

The motor needs 24 V to produce torque and turn. Apply it before the first motion command.

> **CAN communication is powered independently by the USB-CAN adapter**, so with no 24 V you **can still read state and parameters**, but the motor reports an undervoltage fault (`ERR = 0x9`) and does not respond to motion commands. When debugging "the command was sent but nothing moves", **check 24 V first**.

## 4. Loading the calibration

Every unit's stroke endpoints and millimeter scale differ, so a calibration has to be loaded before anything moves. A no-argument `load_calibration()` reads the factory calibration the SDK ships, which describes the shipped units (normal mount).

```python
gripper.connect()
gripper.load_calibration()      # the calibration shipped inside the SDK
gripper.enable()
```

> **Note**: **`connect()` does not load a calibration.** It does only two things: open the bus and register the motor. The calibration must be loaded **explicitly** by the caller.
>
> **Note**: **Nothing moves before a calibration is loaded.** At this point `config` still holds the `GripperConfig()` defaults (`pos_closed_rad=1.14`, `pos_open_rad=0.0`, `rad_to_mm=75.44`), and `config.calibrated` is `False`.
>
> | Layer | Uncalibrated behaviour |
> |------|------|
> | `open()`, `close()`, `grasp()` | **Refuse to run** — they raise `CommandError`. The action engine goes through `limit_target()` / `press_target()`, which both call the calibration guard |
> | `goto()`, `goto_rad()`, `move_to()`, `move_at_speed()`, `move_at_speed_rad()`, `home()` | **Refuse as well** — every positioning call is gated the same way, because the placeholder limits describe no real travel |
> | `send_mit_frame()`, `enter_zero_gravity()`, `stop()` | **Run anyway**, because they carry no position target to check |
>
> So the rule is the target, not the layer: a call that aims the jaws somewhere refuses, and a call that only puts a raw frame on the bus does not. **Treat the guard as a safety net, not as a substitute for calling `load_calibration()`.**

`load_calibration()` accepts no argument, a `path=`, or a `template=`; with no argument it reads the factory calibration bundled with the SDK, plus `LITEGRIP_CALIB` when that environment variable is set. For the full lookup order see [Calibration and zero point](#calibration-and-zero-point).

## 5. First run: make the gripper move

This is the whole program. It connects, loads the calibration, enables the motor, opens, closes, and grasps at 20 N.

```python
from litegrip import LiteGrip

with LiteGrip(channel="can0", can_id=0x08) as gripper:
    gripper.load_calibration()   # the calibration shipped inside the SDK
    gripper.enable()             # retries until the status frame reports err == 1

    gripper.open()                                     # 50 mm/s to the open-side stop
    gripper.close()                                    # 50 mm/s to the closed-side stop
    result = gripper.grasp(force_n=20.0, hold_s=3.0)   # close until gripped, then hold 20 N
    print(result.reached, result.stalled, result.cycles)
```

Save it as `first_move.py` and run it:

```bash
python3 first_move.py
```

**Line by line:**

| Line | What it does |
|------|------|
| `with LiteGrip(...) as gripper:` | Opens the CAN bus and registers the motor. Leaving the block calls `disconnect()`, which disables the motor by default |
| `gripper.load_calibration()` | Reads this unit's stroke endpoints and millimeter scale into `config` |
| `gripper.enable()` | Clears a latched fault if one is present, enables, then **waits for the status frame to report `err == 1`**. Returns an `EnableResult` |
| `gripper.open()` | Ramps toward the open side until the mechanical stop ends the move. Returns a `MoveResult` |
| `gripper.close()` | The same on the closed side |
| `gripper.grasp(force_n=20.0, hold_s=3.0)` | Closes onto the object — or onto the closed-side stop if there is nothing there — then holds `force_n` for 3 seconds. Returns a `GraspResult` |

**Expected output** — the three fields of the `GraspResult`:

```text
False True 12
```

`stalled=True` means the position stopped changing, which is what happens when the fingers meet an object. `reached` is `False` because the jaw did not reach the target angle. `cycles` is how many control cycles the closing phase took. **Read `result.ok`, not `reached`**: a grasp that is holding something reports `ok=True` with `stalled=True`.

> **Do not** expect `reached=True` from a grasp that is holding something. In a grasp, `stalled=True` and `reached=False` is the success case. For `open()` and `close()` it is the other way round: those succeed by pressing onto the mechanical stop, so `ok=True` comes with `stalled=True`.

> **Note**: **These three examples were written from the SDK source and its README; they were not executed against hardware for this revision of the manual.** The interface names, signatures and defaults are checked against the SDK, but the printed values are illustrative — your `cycles` count and exact positions will differ. See [Reporting and verification status](#reporting-and-verification-status).

## 6. When the gripper does not move

| Symptom | Likely cause | Check |
|------|------|------|
| `HardwareError` from `enable()`, no feedback | No 24 V; the motor never answers | Measure the 24 V rail; with no 24 V the error code reads `0x9` |
| `HardwareError` from `enable()` on a virtual bus | Expected — `vcan0` has no motor | Nothing to fix; use real hardware for the enable step |
| `CommandError` naming a calibration, or nothing moves | Calibration never loaded — every positioning call refuses | Call `load_calibration()` and check `config.calibrated` |
| Nothing moves, `ERR = 0x9` | Undervoltage — the drive supply is missing or sagging | Measure the 24 V rail under load |
| Nothing moves, `ERR = 0xA` | Overcurrent — the fingers hit an obstacle or a hard stop | Clear the obstruction, then `clear_fault()` |
| Nothing moves, `ERR = 0xB` / `0xC` | MOS or coil overtemperature | Let it cool; check the duty cycle |
| Communication fails at the right bitrate | The interface came up in CAN FD mode | Re-run step two with `fd off` |
| Intermittent frames, bus errors | Missing or wrong termination | Fit 120 Ω at both ends of the bus |
| `connect()` raises `ConnectError` | Interface down, or wrong `channel` name | `ip -details link show can0` |
| Motion is jerky or the fingers buzz | `kp` / `kd` not suited to the load | See [Motion tuning (MotionConfig)](#motion-tuning-motionconfig) |

**Reading the error code directly:**

```python
state = gripper.get_state()
print(f"0x{state.error_code:X}")
```

`is_error` is `True` for any code other than `0` (disabled) and `1` (enabled). For the full code table see [Feedback frames and error codes](#feedback-frames-and-error-codes); for the exception classes see [Exceptions and error handling](#exceptions-and-error-handling).

## Enabling, disabling, and fault handling

```python
gripper.enable()        # enable, with full initialization and feedback verification
gripper.disable()       # disable
gripper.clear_fault()   # clear driver faults
```

**The full `enable()` sequence**: disable → switch to MIT mode → enable → **wait for a feedback frame to confirm**. If the current error code is not `0x0` / `0x1`, it first calls `clear_fault()` automatically to clear the fault once.

**`enable()` returns an `EnableResult`**, whose `ok` field is `True` only when a valid feedback frame arrived after the command was sent (`ERR ∈ {0x0, 0x1}`); if the retries are exhausted with no confirmation it raises `HardwareError` — it never fakes success. `tries` reports how many attempts it took.

**The interfaces in this section check only two things: connected and enabled.** If either is missing they raise `NotInitializedError`.

| Method | Signature | Description |
|------|------|------|
| `enable()` | `enable(retries=None) -> EnableResult` | Enables and verifies. `retries=None` uses `MotionConfig.enable_retries` (3) |
| `disable()` | `disable() -> bool` | Zero torque, back-drivable. Success is not confirmed by feedback |
| `clear_fault()` | `clear_fault() -> bool` | Disable → clear (`0xFB`) → enable → verify, retried up to `GripperParams.FAULT_CLEAR_RETRIES` (5) |
| `stop()` | `stop() -> None` | Emergency stop: sends one zero-torque MIT frame. **Does not disable**, does not latch, returns nothing |

> **Note**: **`stop()` is not a safety-rated stop.** It sends a single zero-torque frame and returns; the motor stays enabled and will accept the next command. For an actual emergency stop, cut the 24 V supply with a hardware switch — see the [safety section](product-manual.md#safety) of the Product Manual.

## Motion control (open/close and position)

**Two layers, and one calibration gate over both.**

| Layer | Methods | Preconditions | Uncalibrated |
|------|------|------|------|
| **High-level actions** | `open`, `close`, `grasp`, `zero` | Connected, enabled, **calibrated** | Raises `CommandError` |
| **Positioning calls** | `goto`, `goto_rad`, `move_to`, `move_at_speed*`, `home` | Connected, enabled, **calibrated** | Raises `CommandError` too |

The high-level actions run a closed-loop engine that ramps with a bounded lead, watches for a stall, and returns a result object. The positioning calls run one bounded ramp as well; the families differ in how the speed is given, not in what they guarantee.

> **Every positioning call refuses an uncalibrated configuration**, because the target is derived from the calibrated travel and the placeholders describe no real travel. Earlier revisions of this manual said the `goto` / `move_at_speed*` / `home` family ran on the placeholder `rad_to_mm`; it no longer does.

| Method | Target | Description |
|------------------------|--------------------------------------------|--------------------------------|
| `open()` | Past the calibrated open endpoint | Ramps onto the open-side mechanical stop and lets the stop end the move. With `GripperConfig.work_stroke_mm` set it stops at that opening instead — the shipped calibration sets `80.0`; returns `MoveResult` |
| `close()` | Past the calibrated closed endpoint | The same on the closed side; `work_stroke_mm` does not change where a close ends. Use `grasp()` for a power grasp |
| `grasp()` | Closes until stall, then holds force | Returns `GraspResult`; see [Grasping and force control](#grasping-and-force-control) |
| `zero()` | Both endpoints in turn | Full calibration; returns `CalibrationData` |
| `home()` | `config.pos_closed_rad` | Ramps to the calibrated closed position — a stop *on* the zero, not a press onto it; returns `MoveResult` |
| `goto()` | Absolute position (mm) | Converted to rad internally, then goes through `goto_rad()` |
| `goto_rad()` | Absolute position (rad) | The same in radians. `dq_target` and `tau_feedforward` must be 0, or it raises `CommandError` |
| `move_to()` | Absolute position (rad) | It is `goto_rad()`, just with a longer default duration |
| `move_at_speed()` | Constant linear velocity motion | The endpoint is clamped the same way |
| `move_at_speed_rad()` | Constant angular velocity motion | The endpoint is clamped the same way |
| `send_mit_frame()` | Send one MIT frame directly | Expert interface, **no clamping, no saturation check** |

**Common parameters** (when `kp` / `kd` are omitted, the values from `config` are used):

| Parameter | Default | Description |
|------|------|------|
| `kp` / `kd` | 100.0 / 2.0 | Position stiffness / damping |
| `duration` | See the signature | Motion duration (seconds) |
| `force_n` | `None` | Target gripping force (N), `grasp()` only; `None` falls back to `MotionConfig.force_n` (20.0) |
| `dq_target` | `0.0` | Target velocity feedforward (rad/s), `goto_rad` only. **Must be 0** |
| `tau_feedforward` | `0.0` | Feedforward torque (N·m) for `goto_rad` / `move_to`. **Must be 0**: the ramp derives its own feed-forward, so anything else raises `CommandError` |
| `speed_mm_s` | `MotionConfig.speed_mm_s` (50.0) | Opening/closing speed for `open` / `close` |
| `speed_mm_s` | 30.0[not measured] | Linear velocity for `move_at_speed` (mm/s) |
| `speed_rad_s` | 0.5[not measured] | Angular velocity for `move_at_speed_rad` (rad/s) |

> The default values of `duration` are in the signatures below: `move_to` is 1.0 second, and `goto` / `goto_rad` are 0.5 second.

**Full signatures:**

```python
home() -> MoveResult
open(speed_mm_s=None, *, progress=None) -> MoveResult
close(speed_mm_s=None, *, progress=None) -> MoveResult
goto(position_mm, kp=None, kd=None, duration=0.5) -> MoveResult
goto_rad(position_rad, kp=None, kd=None,
         dq_target=0.0, tau_feedforward=0.0, duration=0.5) -> MoveResult
move_to(target_rad, kp=None, kd=None,
        tau_feedforward=0.0, duration=1.0) -> MoveResult
move_at_speed(target_mm, speed_mm_s=30.0, kp=None, kd=None) -> MoveResult
move_at_speed_rad(target_rad, speed_rad_s=0.5, kp=None, kd=None) -> MoveResult
send_mit_frame(q, kp, kd, dq=0.0, tau=0.0) -> bool
```

Typical usage:

```python
with LiteGrip(channel="can0", mst_id=0x18) as gripper:
    gripper.load_calibration()      # load the calibration first
    gripper.enable()
    gripper.open()                  # open onto the calibrated open stop
    gripper.goto(60.0)              # move to 60 mm
    gripper.close()                 # close onto the calibrated closed stop
```

> **Note**: **A target beyond the calibrated endpoint is silently clamped.** Inside `goto_rad()` it is
> `position_rad = max(pos_open_rad, min(pos_closed_rad, position_rad))`,
> and `move_at_speed_rad()` likewise clamps the endpoint to `[pos_open_rad, pos_closed_rad]`.
> **It raises no exception and does not tell you it clamped.** If you need "reject anything out of range" semantics, check before the call yourself.

> **Note**: **`open()` and `close()` deliberately drive past the calibrated limit.** The mechanical stop ends the move, which is why a successful `open()` reports `stalled=True`: the jaw is resting against the stop with a small pressing torque. That is intended for a full open or close, but it means the position after the call is not the calibrated endpoint — read `result.state.position_mm` if you need the actual resting position. To stop short of the stop, use `goto()`.

> **Note**: **`send_mit_frame()` has no clamping and no range check at all.** It only checks "connected and enabled"; an out-of-range `q` is sent as is; `kp` / `kd` / `tau` outside the encoding range are silently saturated at the encoding stage to `[0, 500]` / `[0, 5]` / `[−10, 10]`. Unless you need to control single-frame timing yourself, use the high-level interfaces.

> **Note**: **Velocity is "duration distribution", not "velocity limiting".** `duration` only decides how long this run of frames lasts — frames are sent at 200 Hz (5 ms period) and the position target transitions smoothly over the whole duration. To actually cap the maximum velocity, use `move_at_speed()` / `move_at_speed_rad()`, which compute the target sequence from the given velocity.

## Grasping and force control

```python
grasp(force_n=None, hold_s=0.0, *, progress=None) -> GraspResult
```

`force_n=None` uses `MotionConfig.force_n` (20.0 N). `hold_s=0.0` holds until a fault, the runaway watch, or Ctrl+C.

**Sequence**: ramp toward the object (or the closed-side stop) → **compare the position every cycle** → the hold takes over only once the jaw has stopped, and it then streams **zero-gain frames** whose only output is the feedforward torque `force_n × 0.1` N·m.

> **"Adaptive" here means position stall detection, not torque detection.** The criterion is the windowed position change falling below `MotionConfig.stall_delta`, and it is independent of the torque reading.

**`grasp()` is the only way to press with a force.** There is no call that applies a force at the current position, and that is deliberate: such a call cannot tell whether anything is between the jaws, and the hold frames give the drive no position or velocity error to work against, so with nothing there the jaws accelerate. `grasp()` avoids it by construction.

| `GraspResult` field | Meaning |
|------|------|
| `ok` | The hold ended normally. This is what `bool(result)` returns |
| `reached` | The jaw reached the target angle without stalling — the jaws closed empty |
| `stalled` | The position stopped changing — **the normal outcome when an object is gripped** |
| `state` | The `GripperState` at the end of the hold |
| `target_rad` / `force_n` | The target angle and the force that was held |
| `cycles` | Control cycles the closing phase took. `0` means the hold was never entered |
| `travel_guard` | The runaway watch tripped and released the torque; see below |

> **Note**: **A successful grasp reports `stalled=True` and `reached=False`.** Because the stall test is positional, gripping an object and hitting the stroke endpoint look the same to it — **you cannot use those two flags alone to tell "gripped an object" from "closed on nothing".** Combine them with `get_position()`: a grasp on nothing ends at the closed endpoint, an object ends short of it.

> **Note**: **One failure combination is new in this release.** `ok=False, reached=False, stalled=False` with `cycles=0` means the closing leg ran out of frames while the jaw was still in free travel. The hold is not entered — its frames carry no position and no velocity term, so handing a moving jaw over to them leaves the feed-forward torque as the only thing acting on it. The call releases in place instead, and nothing was gripped.

**The runaway watch.** The hold frames carry no position error, so no position limit can act on them; the only lever is removing the torque. Once the measured position is `hold_runaway_rad` (`0.05 rad`) past the closed-side calibrated limit, `grasp()` streams zero-torque release frames and returns with `travel_guard` set. It is a runaway detector, not an accuracy bound. **An empty `grasp()` is the case that reaches it**, and the trip leaves the jaws outside the calibrated travel: `disable()` the motor, push them back clear of the stop by hand, then `enable()` before commanding anything else.

> **Do not** simply call `grasp()` again after a `travel_guard` trip: the closing leg re-approaches the same stop and the hold presses it again.

> **Note**: **The force argument is not calibrated and not validated.** `force_n` is converted with the nominal `UnitConversion.N_TO_NM = 0.1 N·m/N`; a negative value is sent as a negative torque. `force_n=20.0` corresponds to a `2.0 N·m` feedforward, one fifth of the torque encoding limit `10 N·m`.
>
> ```python
> gripper.grasp(force_n=0)      # position-only grasp: no feedforward torque
> gripper.grasp()               # MotionConfig.force_n (20 N) → 2.0 N·m feedforward
> ```

> **Note**: **The physical meaning of `force_n` is not calibrated.** `0.1 N·m/N` is a nominal conversion coefficient; **do not use it for safety decisions or load design until force calibration is complete**.

## Reading state

```python
state = gripper.get_state(wait=True)
```

| `GripperState` field | Type | Description |
|---------------------|------|-------------|
| `position_rad` | `float` | Position (rad) |
| `position_mm` | `float` | Position (mm, converted with the conversion coefficient) |
| `velocity_rad_s` | `float` | Velocity (rad/s) |
| `torque_nm` | `float` | Torque (N·m) |
| `force_n` | `float` | **Estimated** gripping force (N) |
| `temperature_mos` | `int` | MOS temperature (°C) |
| `temperature_coil` | `int` | Coil temperature (°C) |
| `error_code` | `int` | Motor error code |
| `timestamp` | `float` | When the frame behind the snapshot arrived. `0.0` means there is no frame at all |
| `fresh` | `bool` | A frame answered **this** read |
| `data_age_s` | `float` or `None` | Seconds since that frame arrived, or `None` if none ever has |

`get_state(wait=True)` waits up to 50 ms for one new feedback frame; `wait=False` returns the last cached state directly, which suits high-rate control loops.

> **Note**: **The readings are a cache, and only a status frame updates it.** A driven motor answers the control frames it receives and reports on its own; one holding a pose, or disabled, sends nothing, and `wait=True` then waits out its 50 ms and hands back the previous frame. Check `fresh` and `is_stale()` before trusting a number, and call `refresh_status()` to elicit a frame when the bus is idle. **Do not** time a loop with `timestamp` — that is what `data_age_s` is for.

**Derived properties:**

| Property | Description |
|------|------|
| `is_enabled` | Whether the motor is enabled (`error_code == 1`) |
| `is_error` | Whether a fault is present (`error_code` is neither 0 nor 1) |
| `is_moving` | Whether the velocity exceeds a small threshold (0.01) |
| `aperture_mm` | Aperture reading (**per-finger displacement**) |

> **Note**: **`force_n` is an estimate**, derived as `torque_nm × UnitConversion.NM_TO_N`, and `NM_TO_N = 10.0` is a **nominal conversion coefficient** (the source comment marks it `approximate`), not a calibrated one. **Until force calibration is complete, do not treat `force_n` as the real gripping force.**
>
> **Total aperture = `aperture_mm` × 2** (this field is per-finger displacement). Per-finger stroke 42.500 mm × 2 = total stroke 85.000 mm.

**Convenience read methods:**

| Method | Returns |
|------|------|
| `get_position()` / `get_position_rad()` | Position (mm / rad) |
| `get_force()` | Estimated gripping force (N) |
| `get_torque()` | Torque (N·m) |
| `get_error()` | Error code |
| `get_temperature()` | `(MOS temperature, coil temperature)` |
| `get_info()` | `GripperInfo` — model, motor model, CAN IDs, firmware version, serial number |
| `refresh_status()` | Asks the motor for a status frame (0xCC) **without moving the jaws**. Use it before `get_state()` on a gripper that has been idle |

**State test methods:**

| Method | Returns |
|--------------------------------------|--------------------------------------------------------------|
| `is_moving()` | Whether the gripper is moving |
| `is_grasped()` | Whether `abs(torque_nm)` exceeds `config.grasp_torque_threshold` (default 0.5 N·m; can only be fixed after force calibration) |
| `wait_for_ready(timeout=5.0)` | Blocks until enabled and stationary; returns `False` on timeout |

**Polling and expert interfaces:**

| Method | Description |
|------|------|
| `poll(timeout_s=0.0) -> bool` | Polls one feedback frame and updates the internal state; returns `False` when not connected |
| `read_param(rid, timeout_s=0.5) -> float` | Reads a driver parameter by register ID |

> **Note**: **Feedback is request-driven.** The driver replies only after it receives a frame from the host — **merely listening on the bus receives no feedback at all**.

> **Note**: **For the `read_param` register table see [Parameter frames and registers](#parameter-frames-and-registers).** Note carefully: `OC_Value` is a ratio, not amperes; the MIT quantization range of position / velocity / torque is not a protection threshold.

## Units and conversion

**The SDK does not expose conversion methods.** The `mm ↔ rad` conversion is inlined in two places:

```python
# goto() (gripper.py)
position_rad = config.pos_closed_rad - position_mm / config.rad_to_mm

# get_state() (gripper.py)
position_mm = (config.pos_closed_rad - position_rad) * config.rad_to_mm
```

That is, **a smaller `rad` means a wider aperture**; `pos_closed_rad` is the end with the larger value and `pos_open_rad` is the end with the smaller value.

**The conversion coefficient `rad_to_mm` is written by the calibration process** and equals "the stroke used for calibration (mm) ÷ the measured angular stroke (rad)". The value measured on this unit is:

> **Effective stroke 85.000 mm ÷ the angular stroke measured on this unit (rad) = this unit's `rad_to_mm`**. The numerator is `config.max_stroke_mm` and the denominator is the rad span measured during calibration; **both numbers differ from unit to unit**. For this unit's values see the calibration file shipped with the product and the [stroke and position parameters](product-manual.md#stroke-and-position-parameters) section of the Product Manual.

> **Note**: **`rad_to_mm` only affects "the millimeter values displayed and the millimeter targets"**; it does not move any boundary, because the `pos_closed_rad` / `pos_open_rad` used for clamping are rad values themselves and do not depend on `rad_to_mm`. A wrong coefficient only makes the millimeter numbers wrong.
>
> **Note**: **`position_mm` is the aperture a caliper measures.** The SDK's mm zero point is at the fully closed mechanical limit, where the two fingertips touch, and the reading counts up from there to 85.000 at the open end. **Add no offset**; if your caliper and `position_mm` disagree, the `rad_to_mm` scale is wrong, not the formula.

## Manual guidance (zero gravity)

```python
gripper.enter_zero_gravity()       # the gripper goes soft and can be pushed by hand
input("Press Enter once the position is set...")
gripper.exit_zero_gravity()        # hold the current position
```

**`enter_zero_gravity(duration=0.0)`** — enters zero gravity mode: the motor stays enabled but frames with `kp=0, kd=0, tau=0` are sent continuously, so the mechanism can be pushed freely.

| `duration` | Effect |
|-----------|------|
| `> 0` | Blocks for that duration and keeps sending zero-torque frames; when it expires it **only stops sending frames**, it does not return to position holding automatically |
| `0` (default) | Sends **one** guidance frame only; **the caller must keep polling / sending frames**, otherwise the driver disables after the communication timeout |

> **Note**: **Position is not held in zero gravity mode.** The motor outputs no torque, so gravity and friction decide where the fingers sit. To "stay where you let go", you must call `exit_zero_gravity()` after letting go.
>
> **Note**: The `duration > 0` form **does not leave zero gravity mode automatically**; after the loop ends no further frames are sent. If you need position holding, call `exit_zero_gravity()` explicitly.

**`exit_zero_gravity()`** — leaves zero gravity mode and holds using the current position as the target, closed-loop with `config.kp` / `config.kd`.

> **Note**: **The position is not validated on exit.** If pushing by hand moved the finger outside the stroke, `exit_zero_gravity()` uses that measured position directly as the target (the `send_mit_frame` path does not go through clamping); only a later call to an ordinary motion interface clamps the target to the calibrated endpoint.

> **Manual guidance has only the two zero gravity primitives above.** For a "grasp → release" cycle, combine `enter_zero_gravity()` / `exit_zero_gravity()` / `grasp()` yourself.

## Calibration and zero point

**Four calibration entry points:**

| Method | Driving force | How the limit is detected | Human needed |
|------|--------|---------------|--------|
| `zero()` | Motor | Motor stall detection, both endpoints in one call | Attending in person |
| `calibrate()` | Motor | **Motor stall detection** (position increment below the threshold for consecutive cycles) | Attending in person |
| `calibrate_guided()` | Motor | Confirm each endpoint with Enter, or automatic motor stall detection | Press Enter at each endpoint |
| `calibrate_manual()` | Pushed by hand (zero gravity) | Pushed all the way by hand, extremes recorded | Hand-push throughout |

`zero()` is the one-call form: it probes both limits, computes the travel and `rad_to_mm`, and saves the result to the default calibration path.

> **Note**: **`zero()`, `calibrate()` and `calibrate_guided()` push all the way into the mechanical hard stop.** They step in one direction under motor power until the position stops changing (motor stall) and do not stop by themselves in between. Before running them, confirm the mechanical hard stops and the structure can take that force, and **someone must be present with a working hardware emergency stop**.
>
> **`calibrate_manual()` is recommended**: pushing all the way by hand applies no motor force to the mechanism and is the gentlest of the three.

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

Both probing methods bound the command lead to `step_rad` and abort when the torque reaches `tau_limit`, so a mis-set endpoint cannot drive the motor into the structure at full stiffness.

`calibrate_manual()` steps: after the call the gripper goes "soft" → push it all the way closed by hand, then all the way open → repeat a few times → it returns when the time is up (or press Ctrl+C to end early and keep the readings taken so far).

**Saving and loading the calibration file:**

| Method | Signature and description |
|------|-----------|
| `save_calibration(path=None) -> str` | With `path=None` it writes `~/.litegrip/<channel>_calibration.json` and **returns the absolute path written**. One file per channel is what keeps two grippers on one machine from overwriting each other |
| `load_calibration(path=None, template=None) -> bool` | Loads calibration into `config`. Call it after `connect()` and before `enable()` |
| `load_template(name) -> bool` | Loads a `"normal"` or `"reverse"` mount template, declaring the mount. `name` must be one of `list_templates()` |

**`load_calibration()` lookup order** with no arguments: this channel's own file → the legacy single-file path `~/.litegrip/litegrip_calibration.json` → the factory calibration bundled with the SDK. Pass `path=` to read a specific file (it may still fall back to the factory file), or `template="normal"` / `template="reverse"` to load a mount template, which is strict and never falls back. Passing both `path` and `template` raises `CommandError`.

> **Note**: **`load_calibration()` does not validate the source in any way.** It only handles "the file does not exist" and "JSON parsing failed"; whatever the file says, it believes. It also skips a file that names a different channel, and logs a warning rather than failing.
>
> **Recalibration is mandatory after replacing or repairing the gripper, replacing the motor, replacing a finger, or a collision or overload.**

**About the calibrated conversion coefficient:**

The scale is computed as `rad_to_mm = (max_stroke_mm + STOP_INSET_MM) ÷ measured angular stroke (rad)`, where the inset is `GripperGeometry.STOP_INSET_MM` (1.0 mm).

| Entry point | Numerator value |
|------|---------|
| `zero()` / `calibrate()` / `calibrate_guided()` / `calibrate_manual()` | `config.max_stroke_mm + GripperGeometry.STOP_INSET_MM` |

The numerator is one millimetre more than the jaw travel on purpose: the probe presses *into* the open stop
to find it, so the two recorded extremes span about a millimetre more than the jaws can actually travel.

> **Note**: **`max_stroke_mm` defaults to `85.0`, the jaw travel the shipped hardware has.** Set it to your own
> jaw travel before you re-probe — it is the one per-unit measurement no calibration file carries.

> **Do not** use a nominal aperture borrowed from another unit as `max_stroke_mm`. `p` is derived from the
> calibrated `rad_to_mm`, so it only matches the jaw travel when the scale is right.

> **Note**: **A scale derived from `max_stroke_mm` alone would be 1.2 % short** — 1 mm lost per full stroke — which is exactly why the inset is added.

> **Note**: **Earlier revisions of this manual warned of a 1.38× error against a `120.0` placeholder.** That number is obsolete: `120 mm` never belonged to a gripper in this family. The jaw travel is `85.0`.

> **Note**: These entry points raise `RuntimeError` only when `travel <= 0`; a `max_stroke_mm` of `0` **does not** raise an error, so check what you entered.

## Configuration object

**`GripperConfig` fields (14 in total):**

| Field | Default | Description |
|------|------|------|
| `can_channel` / `can_id` / `mst_id` / `canfd_mode` | `"can0"` / `0x08` / `None` / `False` | Connection parameters |
| `kp` / `kd` | `100.0` / `2.0` | Position stiffness / damping (the default of each interface when omitted) |
| `pos_closed_rad` / `pos_open_rad` | `1.14` / `0.0` | The two ends of the stroke (**overwritten by the calibration file after calibration**) |
| `calibrated` | `False` | Whether a calibration has been loaded (**set by `load_calibration()`**) |
| `max_stroke_mm` | `85.0` (`GripperGeometry.JAW_TRAVEL_MM`) | The jaw travel your unit has. **Used only as the scale numerator during calibration**, with `STOP_INSET_MM` added; see [Calibration and zero point](#calibration-and-zero-point) |
| `work_stroke_mm` | `0.0` (**the shipped calibration sets `80.0`**) | Where a plain `open()` stops, measured from the closed zero (mm). It never moves where a `close()` ends: the closed end stays on the mechanical stop |
| `rad_to_mm` | `75.44` (**placeholder while uncalibrated**) | Angle → millimetre conversion; the calibration file overwrites it |
| `nm_to_n` | `10.0` | Torque → force conversion. **The current code does not read this field**; it actually uses the class constant `UnitConversion.NM_TO_N = 10.0`, so changing it has no effect |
| `grasp_torque_threshold` | `0.5` (no basis, can only be fixed after force calibration) | The decision threshold of `is_grasped()` (N·m) |

**Derived properties** — direction is data, not a separate switch:

| Property | Returns |
|------|------|
| `close_sign` | `+1.0` when closing means increasing radians (the usual mount), `-1.0` for a reverse mount. Derived from the ordering of the two limits |
| `mount` | `"normal"` / `"reverse"` — the mount the limits spell out, or **`None` while `calibrated` is `False`** |

> **Note**: **`mount` returns `None` until a calibration is loaded, deliberately.** The placeholder defaults also happen to order close above open, so reporting `"normal"` before a calibration would be a claim rather than a reading. Do not use `config.mount` as the credential that a calibration happened — use `config.calibrated`.

> **Note**: **The default values of `pos_closed_rad` / `pos_open_rad` / `rad_to_mm` are placeholders, not this unit's real values.** The real values live in the calibration file and take effect only when you call `load_calibration()` explicitly (`connect()` does not do this). `config.calibrated` tells you which set you are running on.

> **Note**: **Do not command motion under the default configuration.** Every positioning call checks `calibrated` and raises `CommandError` while it is `False`, and the placeholders describe the shipped pattern rather than your unit — `max_stroke_mm = 85.0` is a measurement you still have to confirm before you calibrate, and `rad_to_mm = 75.44` is the wrong scale for every unit including this one. **This is the most direct reason to call `load_calibration()` before commanding any motion.**

## Preconditions and calling constraints

**The SDK performs three precondition checks.** `_check_connected()` and `_check_enabled()` raise `NotInitializedError` when they fail; `_check_calibrated()` raises `CommandError`. Since v1.1.0 every motion path runs the calibration check, mid-level and high-level alike.

| Interface | Connected | Enabled | Calibrated | Description |
|------|:---:|:---:|:---:|------|
| `connect` / `disconnect` | — | — | — | `disconnect()` first tries `disable()` unless `disable_on_disconnect` is `False` |
| `enable` / `disable` / `clear_fault` | ● | — | — | |
| `stop` | — | — | — | **Not checked**. When not connected or not enabled it is a no-op and returns `None` |
| `send_mit_frame` | — | — | — | **Does not raise**. When a precondition is not satisfied it returns `False` directly |
| `poll` | — | — | — | **Does not raise**. Returns `False` when not connected |
| `goto` / `goto_rad` / `move_to` / `move_at_speed` / `move_at_speed_rad` | ● | ● | **●** | All five funnel into the same ramp, which refuses an uncalibrated config |
| `home` | ● | ● | **●** | Ramps to the calibrated closed limit through `move_to()` |
| `open` / `close` / `grasp` | ● | ● | **●** | Raise `CommandError` while uncalibrated |
| `zero` / `calibrate` / `calibrate_guided` / `calibrate_manual` | ● | ● | — | They *produce* the calibration, so they cannot require one |
| `write_zero` | ● | ● | — | Rewrites the encoder offset in place; touches neither the end stops nor the calibration file |
| `enter_zero_gravity` | ● | ● | — | |
| `exit_zero_gravity` | — | — | — | **Does not raise**. When not enabled it is a no-op |
| `get_state` / `get_position*` / `get_force` / `get_torque` / `get_temperature` / `get_error` / `refresh_status` | ● | — | — | `get_info()` reads static information and is not checked |
| `is_moving` / `is_grasped` / `wait_for_ready` | ● | — | — | |
| `load_calibration` / `save_calibration` / `load_template` | — | — | — | Pure file I/O |
| `read_param` | ● | — | — | |
| `teleop_start` | ● | ● | **●** | Calls `check_ready(config)`; see [Teleoperation](#teleoperation-leaderfollower) |
| `record` / `record_start` / `play` / `play_start` | ● | ● | **●** | Raise `TrajectoryError` while uncalibrated — the normalised opening would be a guess; see [Trajectory record and replay](#trajectory-record-and-replay) |
| `record_stop` / `play_stop` / `trajectory_status` | — | — | — | They act on an already-running session and check nothing |

**Legend**: ● = required; — = not needed.

> **Do not** read this table as "everything marked — is safe". `—` means "unchecked", not "unaffected", and one entry carries real risk: **`send_mit_frame()` is a raw frame** — no calibration check, no clamp to the calibrated limits, no direction check — so it can drive the jaws past a stop that every other motion path refuses to cross.

## Exceptions and error handling

**The base class and six fault classes** live in `litegrip.exceptions`:

| Exception | Trigger |
|------|------|
| `LiteGripError` | Base class; carries `message` and an optional `error_code` |
| `CommError` | CAN bus read or write failure |
| `ConnectError` | CAN interface unavailable, or the motor does not respond |
| `CommandError` | A high-level action ran on an uncalibrated or zero-travel gripper, a command frame could not be sent, or `load_calibration()` was given a bad template or both `path` and `template` |
| `CANTimeoutError` | No response on the bus |
| `HardwareError` | Damiao fault codes: undervoltage, overcurrent, overtemperature |
| `NotInitializedError` | A method that requires connected/enabled was called without it |

**Teleoperation adds four more**, defined in `litegrip.teleop` and also derived from `LiteGripError`: `TeleopError`, `TeleopBusyError` (started while already running), `TeleopNotActiveError` (an operation needs an active session), and `TeleopNotReady` (the gripper cannot safely be teleoperated yet).

**Trajectory record and replay adds six**, defined in `litegrip.trajectory`: `TrajectoryError`, `TrajectoryBusyError`, `TrajectoryNotActiveError`, `TrajectoryEmptyError`, `TrajectoryRecordingError` and `TrajectoryFormatError`. **That is 17 classes in total**, all derived from `LiteGripError` — see [Python exception types](#python-exception-types) for the full table.

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

> **Note**: **Clamping and force skipping raise nothing.** A target outside the stroke is silently clamped, an out-of-range `kp` / `kd` / `tau` is silently saturated, and an unvalidated `force_n` is sent as usual. **A program that only catches exceptions will not notice any of them.**
>
> **Note**: **`CommandError` is the calibration guard, not a general command error.** It is raised by the actions layer when the configuration is uncalibrated or has zero travel, when a command frame cannot be sent, and by `load_calibration()` for a bad template or for both `path` and `template`. **A refusal by the motor itself is not routed to it** — that shows up in the status frame's error code instead (see [Feedback frames and error codes](#feedback-frames-and-error-codes)).

## Motion tuning (MotionConfig)

`MotionConfig` holds every tunable of the high-level action engine. The defaults are the values validated on real hardware. Pass your own through the constructor, or replace it later:

```python
from litegrip import LiteGrip, MotionConfig

cfg = MotionConfig(speed_mm_s=25.0, force_n=15.0, stall_delta=0.001)

with LiteGrip(channel="can0", motion_config=cfg) as gripper:
    gripper.load_calibration()
    gripper.enable()
    gripper.open()                              # 25 mm/s
    gripper.grasp(hold_s=2.0)                   # 15 N, the configured default

# or replace it on a live instance
gripper.motion_config = MotionConfig(speed_mm_s=80.0)
```

**The fields you are most likely to change:**

| Field | Default | Unit | What it controls |
|------|------|------|------|
| `speed_mm_s` | 50.0 | mm/s | Ramp speed for `open()` / `close()` |
| `grasp_speed_mm_s` | 50.0 | mm/s | Closing speed during `grasp()` |
| `force_n` | 20.0 | N | The default force when `grasp(force_n=None)` |
| `force_ramp_n_s` | 20.0 | N/s | How fast the hold ramps from the in-flight torque up to the set force |
| `margin` | 0.05 | fraction | How far inside the calibrated limit `limit_target()` aims |
| `press_overshoot` | 0.05 | fraction | How far past the limit `press_target()` aims, so the jaw rests on the stop |
| `press_safety` | 0.9 | fraction | Torque the closing segment of `grasp()` may spend before contact, as a fraction of the set force |
| `stall_delta` | 0.0015 | rad | Position change below which the window counts as stalled |
| `stall_cycles` | 5 | cycles | Consecutive stalled samples before "grasped" |
| `stall_ratio` | 0.2 | fraction | The windowed stall test's relative threshold |
| `press_zone_mm` | 2.0 | mm | Distance from the limit at which the command lead narrows |
| `stop_lead_mm` | 0.7 | mm | The narrowed lead, which bounds the pressing torque |
| `max_lead_mm` | 4.0 | mm | The lead cap away from the limit |
| `stop_torque_nm` | 0.7 | N·m | Travel-segment guard: torque above this while the speed lags (about 7 N) |
| `stop_torque_cycles` | 3 | cycles | Consecutive samples over that torque before the guard fires |
| `stop_speed_ratio` | 0.5 | fraction | Measured speed below this fraction of the commanded speed counts as "not keeping up" |
| `stop_release_s` | 0.2 | s | How long the guard drops the torque after firing |
| `hold_interval` | 0.2 | s | How often the hold re-reads position |
| `hold_runaway_rad` | 0.05 | rad | The hold aborts past this much excursion beyond the closed limit |
| `enable_retries` / `enable_retry_interval` | 3 / 0.2 | — / s | `enable()` retry budget |
| `frame_interval` | 0.005 | s | MIT frame period (200 Hz) |
| `sample_interval` | 0.05 | s | Control-loop sample period |
| `settle_s` | 0.3 | s | Settling time before a move is judged finished |
| `reach_tol` | 0.02 | rad | How close counts as "reached" |
| `stop_tol` | 0.03 | rad | How close to the stop counts as pressed |

**`hold_kp` / `hold_kd` are deprecated.** The hold is a pure torque source (`kp = kd = 0`), so position and velocity gains would follow the jaws instead of the force; the fields stay only so older configuration files still load, and setting them changes nothing.

> **Note**: **The torque guard covers the travel segment, not the pressing segment, and that is deliberate.** Pressing against a limit is *supposed* to sit on torque, so a torque threshold there would fire on every `open()` / `close()`. The windowed stall test alone misses a hard stop that yields slowly, which is what `stop_torque_nm` catches: measured speed well below the commanded speed, with torque over the threshold for `stop_torque_cycles` samples, drops the torque for `stop_release_s` and reports a stall. **Do not raise `stop_torque_nm` to silence it** — it fires because something is blocking the travel.

**Calibration probe fields** (`calib_*`) tune `zero()` and `calibrate()`: `calib_kp` / `calib_kd` (20.0 / 2.0) set the probing stiffness, `calib_step_rad` (0.05) bounds the command lead, `calib_tau_limit` (2.0 N·m) aborts the probe, and `calib_stall_delta` / `calib_stall_cycles` / `calib_max_iter` (0.0015 / 5 / 200) decide when the limit has been found.

`sleep_fn` and `monotonic_fn` are timing seams for tests and simulation; leave them alone unless you are writing a test.

**Progress callbacks.** `open()`, `close()` and `grasp()` accept a `progress` callback, called once per sample with a `MoveProgress`:

```python
def report(p):
    print(f"{p.phase} {p.i}/{p.total_steps} "
          f"cmd={p.cmd_rad:.3f} pos={p.pos_rad:.3f} tau={p.torque_nm:.2f}")

gripper.close(progress=report)
```

| `MoveProgress` field | Meaning |
|------|------|
| `phase` | The current phase name |
| `i` / `total_steps` | Sample index and the estimated total |
| `cmd_rad` / `pos_rad` | Commanded and measured angle |
| `delta_rad` / `win_delta_rad` | Instantaneous and windowed position change |
| `torque_nm` / `temperature_coil` | Torque and coil temperature |

> **Do not** print from inside a progress callback at 200 Hz. The callback runs on the control loop; a slow one slows the loop and changes the motion it is measuring. Accumulate and print after the move, as `examples/teleop.py` does.

> **Note**: **`limit_target()` and `press_target()` are the helpers behind the margin and overshoot.** Both take `(config, toward, amount)` with `toward` being `"close"` or `"open"`, and return `(target, limit, offset_rad, travel_rad)`. `limit_target()` aims *inside* the limit so the jaw does not press; `press_target()` aims *past* it so the jaw rests on the stop. Both raise `CommandError` on an uncalibrated or zero-travel gripper. Reach for them directly only if you are writing your own motion engine.

## Teleoperation (leader/follower)

Teleoperation mirrors one gripper's opening onto another over a network. The leader is pushed by hand in zero gravity; the follower tracks it.

```python
# Leader: publish this gripper's opening.
with LiteGrip("can0") as master:
    master.load_calibration()
    master.enable()
    master.teleop_start("master")                      # zenoh, gripA, port 17448

# Follower: connect to the leader, align to the first frame, then follow.
with LiteGrip("can0") as slave:
    slave.load_calibration()
    slave.enable()
    slave.teleop_start("slave", host="192.168.1.20")
    while True:
        print(slave.teleop_status())   # frames, openness, loop_hz, stale, ...
```

| Method | Signature | Description |
|------|------|------|
| `teleop_start()` | `teleop_start(mode, *, transport=None, link="zenoh", host=None, port=17448, grip_id="gripA", kp=None, kd=None, align=True, align_speed_mm_s=50.0, watchdog_s=0.2, dq_max=10.0, torque_limit_nm=0.0, lead_cap_mm=4.0, require_ready=True, ready_timeout_s=10.0, ready_tolerance_mm=2.0, ready_period_s=0.1, rate_hz=50.0) -> dict` | Starts `"master"` or `"slave"`; returns the first `teleop_status()` snapshot |
| `teleop_stop()` | `teleop_stop(timeout=2.0) -> dict` | Stops and leaves the gripper holding. Neither side disables |
| `teleop_status()` | `teleop_status() -> dict` | Session snapshot, or `{"active": False, "mode": None}`. Carries `frames`, `openness`, `position_mm`, `force_n`, `loop_hz`, `stale`, `rejected`, `send_failed`, `fault`, `matching`, and the guard keys `torque_nm` / `over_torque` / `torque_trips`; the handshake adds `ready`, `ready_rx`, `ready_pubs`, `ready_timed_out` |

**Transports:**

| Transport | Dependency | Use |
|------|------|------|
| zenoh | `pip install 'litegrip[zenoh]'` | The default (`link="zenoh"`), for a routed network |
| `UdpTeleopTransport` | none | Plain UDP on a trusted LAN. **Unauthenticated and unencrypted** |
| `InProcTeleopTransport` | none | In-process bus for tests, or two grippers in one program |

```python
from litegrip import LiteGrip, InProcTeleopTransport

bus = InProcTeleopTransport()          # one instance shared by both ends
# ... pass transport=bus to both teleop_start() calls
```

The wire carries a normalised `openness` in `[0, 1]`, not radians, in a 32-byte big-endian frame (`openness | position_mm | force_n | timestamp`). **The two ends therefore need not share a calibration, a mount, or a zero point** — each side converts using its own. Both ends must agree on `grip_id`.

> **Note**: **Teleoperation takes over the CAN bus.** While a session is running the teleop loop owns all CAN I/O, so ordinary motion calls will not behave as expected. Call `teleop_stop()` first.
>
> **Note**: **`teleop_start()` refuses to run on an uncalibrated gripper** and raises `TeleopNotReady`. Call `check_ready(config)` yourself if you want to know before `enable()`.
>
> **Note**: **A stale follower holds position rather than going slack.** After `watchdog_s` without a fresh frame it stops following but keeps holding, so a network drop does not drop the payload. Non-finite frames are discarded and counted in `rejected`.

> **Note**: **The leader keeps the jaws under gain until the follower says it has arrived.** With `require_ready=True` (the default) the master does not go slack on the first cycle, so the gripper stays where you put it while the follower is still aligning instead of falling open. The follower announces readiness once it is within `ready_tolerance_mm` of the leader's opening and republishes every `ready_period_s`. A follower that never announces cannot stall the leader: after `ready_timeout_s` the master releases the hand-back anyway and sets `ready_timed_out`.

> **Note**: **`torque_limit_nm` is off by default (`0.0`).** Set it to bound the follower's own torque; held over it, the follower releases in place rather than pushing, and `teleop_status()["torque_trips"]` counts how often that happened this session. A leader pushed by hand into a hard stop is the case it exists for.

**Runnable example.** The SDK ships `examples/teleop.py`, one process per end:

```bash
python3 examples/teleop.py --mode master --channel can0
python3 examples/teleop.py --mode slave  --channel can0 --host 192.168.1.20
```

| Option | Default | Meaning |
|------|------|------|
| `--mode` | required | `master` (leader) or `slave` (follower) |
| `--channel` / `--can-id` | `can0` / `0x08` | CAN interface and motor ID |
| `--link` | `zenoh` | `zenoh` or `udp` |
| `--host` / `--port` | — / 17448 | The leader's address; the master only listens |
| `--grip-id` | `gripA` | Topic id; both ends must agree |
| `--mount` | — | Load a `normal`/`reverse` template instead of this channel's calibration |
| `--kp` / `--kd` | calibration | Follower stiffness and damping |
| `--watchdog` / `--dq-max` / `--rate` | 0.2 / 10.0 / 50.0 | Hold timeout, fed-forward velocity ceiling, loop rate |
| `--no-align` | off | Skip the one-shot align to the first frame |
| `--align-speed` | 50.0 | Speed of that align move, in mm/s |
| `--lead-cap` | 4.0 | Ceiling on how far the align command may lead the measured position |
| `--torque-limit` | 0.0 | Follower torque ceiling in N·m; `0` leaves the guard off |
| `--ready-timeout` | 10.0 | How long the leader holds on before releasing the hand-back anyway |
| `--no-require-ready` | off | Skip the handshake: the leader goes slack from the first cycle |
| `--fake-leader` | off | Drive the follower from a synthetic leader on an in-process bus, no second gripper |
| `--openness-rate` | 0.3 | Sweep rate of that synthetic leader, in strokes per second |
| `--dry-run` | off | Print the resolved plan and exit without touching hardware |

> **Note**: The SDK repository ships **six** example scripts: `stroke_test.py`, `grasp_test.py`, `hold_force_test.py`, `zero_closed.py`, `teleop.py` above, and `trajectory.py`, covered in [Trajectory record and replay](#trajectory-record-and-replay). Earlier revisions of this manual listed fifteen others (`basic.py`, `cycle_test.py`, `can_diag.py`, and so on); those files do not exist. **Do not go looking for them.**

## Trajectory record and replay

A motion you teach by hand can be captured once and repeated later. Recording puts the motor into zero gravity so you can push the jaws through the approach, the squeeze and the release; replay streams the captured openings back as MIT command frames.

```python
from litegrip import LiteGrip

with LiteGrip("can0") as gripper:
    gripper.load_calibration()
    gripper.enable()

    taught = gripper.record(5.0)   # 5 s of hand-teaching; the jaws are slack
    taught.save("pick")            # ~/.litegrip/trajectories/pick.lgt
    gripper.play(taught)           # repeat it
```

| Method | Signature | Description |
|------|------|------|
| `record()` | `record(duration_s, rate_hz=100.0, zero_gravity=True) -> Trajectory` | Blocking hand-teach for `duration_s` seconds |
| `record_start()` | `record_start(rate_hz=100.0, zero_gravity=True, max_samples=None) -> dict` | Background recording; returns the first `trajectory_status()` snapshot |
| `record_stop()` | `record_stop(allow_empty=False) -> Trajectory` | Stops and returns the capture |
| `play()` | `play(trajectory, speed=1.0, kp=None, kd=None, loop=False, align=True) -> dict` | Blocking replay; `loop` must be `False` |
| `play_start()` | `play_start(trajectory, speed=1.0, kp=None, kd=None, loop=False, align=True) -> dict` | Background replay |
| `play_stop()` | `play_stop(timeout=2.0)` | Stops and leaves the gripper holding its last target |
| `trajectory_status()` | `trajectory_status() -> dict` | Session snapshot, or `{"active": False}` |

**What is stored, and why it is portable.** A sample holds the opening normalised by the *recording* unit's travel — dimensionless and direction-free, the same quantity teleoperation puts on the wire. Each gripper has its own zero, direction and calibration, so a raw angle would be meaningless on another unit; a trajectory taught on a normal-mount gripper replays on a reverse-mounted one. The recorded angle, velocity and torque are kept for diagnostics only.

`Trajectory.save("pick")` writes `~/.litegrip/trajectories/pick.lgt`; a name containing a path separator is used as written, and `LITEGRIP_TRAJ_DIR` moves that directory. `Trajectory.load("pick")` reads it back. The file is compact binary with an 8-byte magic header (`LGRTRJ01`, format version 1); a file whose length disagrees with the sample count in its header is rejected with `TrajectoryFormatError` rather than parsed into half a motion.

> **Do not** expect a replay to reproduce a **force**. Replay commands position: the opening is clamped to the local calibrated travel and the recorded torque is never fed forward, so a squeeze recorded against an object repeats as a position path pressing with whatever `kp` yields. **The grip force you taught is not preserved.** When the force matters, follow the replay with `grasp(force_n=...)`.

> **Do not** leave the gripper unattended during `record()`, and do not drive it from the caller while that runs. The recorder streams the zero-torque frames itself, the jaws hold nothing for the whole duration, and whatever is between them will drop. Keep a hand on the gripper.

> **Note**: **To capture a *programmatic* motion, record without zero gravity.** `record_start(zero_gravity=False)` only reads state, so the caller is free to run a `grasp()` or a move sequence from another thread and capture it.

> **Note**: **Recording, replay and teleoperation are mutually exclusive.** All three own the CAN I/O, and starting a second one raises `TeleopBusyError` or `TrajectoryBusyError`; `disconnect()` stops whichever is running. Recording and replay both also require a loaded calibration, and raise `TrajectoryError` without one — the normalised opening has to be converted back through *this* gripper's travel.

> **Note**: **A blocking `play()` returns with only one hold frame sent.** The motor self-locks a communication-loss fault about 100 ms after the frames stop, so call the next action promptly — or use `play_start(loop=True)` with `play_stop()` for a hold that lasts. A one-sample trajectory is a pose with nothing to repeat, so looping it holds that opening.

**`trajectory_status()` keys.** `active`, `kind` (`"record"` or `"play"`), `samples` and `error` are always present. A recording adds `rate_hz`, `zero_gravity` and `loop_hz`; a replay adds `frames`, `speed`, `loop`, `completed`, `openness` and `loop_hz`.

**Runnable example.** `examples/trajectory.py` runs the same thing from the command line:

```bash
python3 examples/trajectory.py --record 5 --save pick   # hand-teach, then save
python3 examples/trajectory.py --list                   # no hardware needed
python3 examples/trajectory.py --play pick --repeat 3
```

| Option | Default | Meaning |
|------|------|------|
| `--record` | — | Hand-teach for this many seconds; the jaws go slack |
| `--play` | — | Replay a saved trajectory (a bare name, or a path to a `.lgt` file) |
| `--list` | off | List the saved trajectories and exit; needs no hardware |
| `--save` | — | Save the recording under this name (default: show it, save nothing) |
| `--channel` / `--can-id` | `can0` / `0x08` | CAN interface and motor ID |
| `--mount` | — | Load a `normal`/`reverse` template instead of this channel's calibration |
| `--rate` | 100.0 | Samples per second while recording |
| `--speed` | 1.0 | Playback speed multiplier; 0.5 is half speed |
| `--kp` / `--kd` | configured | Replay stiffness and damping |
| `--no-align` | off | Do not move to the first sample before following |
| `--repeat` | 1 | Replay this many times |
| `--dry-run` | off | Print the resolved plan and exit without touching hardware |

## Driving the bus directly (litegrip.can)

`litegrip.can` is the layer under `LiteGrip`: the SocketCAN transport, the DM motor codec, and a controller that owns several motors. Use it when one process must drive more than one gripper, or when you need frame-level control.

| Module | Contents |
|------|------|
| `litegrip.can.transport` | The SocketCAN socket wrapper — open, send, receive |
| `litegrip.can.protocol` | MIT frame encoding and decoding, and the register (RID) codec |
| `litegrip.can.motor` | One motor's state cache and command path |
| `litegrip.can.controller` | A controller owning a transport and several motors |

> **Note**: **This layer does no unit conversion and no clamping.** It speaks radians, rad/s and N·m. The millimeter and newton conveniences live in `LiteGrip` and `GripperActions`. If you drive `litegrip.can` directly, every conversion, limit and fault check in this manual becomes yours to implement.

For the wire format itself — frame layout, field widths, quantisation, register addresses — see [CAN communication protocol](#can-communication-protocol).

## Core API quick reference

| Category | Interfaces |
|------|------|
| **Lifecycle** | `LiteGrip(...)`, `connect()`, `disconnect()`, `__enter__` / `__exit__` |
| **Enable and faults** | `enable()`, `disable()`, `clear_fault()`, `stop()` |
| **High-level actions** | `open()`, `close()`, `grasp()`, `zero()`, and the `actions` property |
| **Motion** | `home()`, `goto()`, `goto_rad()`, `move_to()`, `move_at_speed()`, `move_at_speed_rad()` |
| **Manual guidance** | `enter_zero_gravity()`, `exit_zero_gravity()` |
| **Calibration** | `calibrate()`, `calibrate_guided()`, `calibrate_manual()`, `write_zero()`, `save_calibration()`, `load_calibration()`, `load_template()`, `list_templates()` |
| **State** | `get_state()`, `poll()`, `refresh_status()`, `get_position()`, `get_position_rad()`, `get_force()`, `get_torque()`, `get_error()`, `get_temperature()`, `get_info()`, `is_moving()`, `is_grasped()`, `wait_for_ready()` |
| **Teleoperation** | `teleop_start()`, `teleop_stop()`, `teleop_status()` |
| **Trajectory** | `record()`, `record_start()`, `record_stop()`, `play()`, `play_start()`, `play_stop()`, `trajectory_status()` |
| **Expert** | `read_param()`, `send_mit_frame()`, the `litegrip.can` subpackage |

> **Note**: **There is no `set_force()`.** It was removed from the public API before v1.0.0: it held the current position with a torque, which is neither a move nor a grasp, and callers reached for it where they meant `grasp()`. **To press with a force, call `grasp(force_n, hold_s)`; that is the only interface that applies one.**

**Public export list** (the `__all__` of `litegrip/__init__.py`):

```python
from litegrip import (
    __version__,
    # high-level interface
    LiteGrip, DEFAULT_CALIB, CALIB_TEMPLATES,
    default_calib_path, list_templates,
    # motion actions
    MotionConfig, MoveProgress, MoveResult, GraspResult, HoldResult,
    EnableResult, WriteZeroResult, GripperActions,
    limit_target, press_target, work_limit_target,
    clamp_to_travel, closing_travel_excursion_rad, force_approach_terms,
    # data models
    GripperState, GripperConfig, GripperInfo, GripperStatus, GripperMode,
    CalibrationData, GripperGeometry, STALE_AFTER_S,
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
    DEFAULT_ALIGN_SPEED_MM_S, DEFAULT_LEAD_CAP_MM, DEFAULT_TORQUE_LIMIT_NM,
    DEFAULT_READY_TIMEOUT_S, DEFAULT_READY_TOLERANCE_MM, DEFAULT_READY_PERIOD_S,
    READY_FRAME_SIZE, encode_ready_frame, decode_ready_frame, ready_topic,
    # teleoperation — zenoh link (resolved lazily; needs litegrip[zenoh])
    ZenohTeleopTransport, Listener, Connector, LatestSlot,
    # trajectory record and replay
    Trajectory, TrajectorySample, TrajectoryRecorder, TrajectoryPlayer,
    trajectory_dir, resolve_path, DEFAULT_RATE_HZ,
    TrajectoryError, TrajectoryBusyError, TrajectoryNotActiveError,
    TrajectoryEmptyError, TrajectoryRecordingError, TrajectoryFormatError,
    # subpackages
    can,
)
```

`ZenohTeleopTransport`, `Listener`, `Connector` and `LatestSlot` are resolved lazily on first access and raise `ImportError` with an install hint when the optional zenoh dependency is absent.

# Secondary development

Everything above drives the gripper from Python. This chapter covers the other ways to build on LiteGrip: extending the Python SDK, using the C++ SDK, integrating with ROS 2, running a simulation, and using the host application.

**Read [What is not ready yet](#what-is-not-ready-yet) before planning around any of them.** Several components are incomplete, and one is an empty repository.

## Extending the Python SDK

The SDK is deliberately layered so you can replace one layer without the others.

| Goal | Do this |
|------|------|
| Change how open/close/grasp move | Pass your own `MotionConfig`; see [Motion tuning](#motion-tuning-motionconfig) |
| Add a motion primitive | Compose `GripperActions` primitives, or build one from `limit_target()` / `press_target()` plus `send_mit_frame()` |
| Drive several grippers from one process | Use `litegrip.can.controller`; one transport, several motors |
| Carry teleoperation over your own link | Subclass `TeleopTransport` and implement `pub` / `sub` / `close` |
| Run without hardware | The `vcan0` virtual bus, or `litegrip-pybullet` / `litegrip-mujoco` for a model in the loop |
| Change the protocol itself | `litegrip.can.protocol` is the codec; the wire format is documented in [CAN communication protocol](#can-communication-protocol) |

**Custom teleoperation transport:**

```python
from litegrip import TeleopTransport, TeleopSubscription

class MyTransport(TeleopTransport):
    def pub(self, topic: str, payload: bytes) -> None: ...
    def sub(self, topic: str) -> TeleopSubscription: ...
    def close(self) -> None: ...
```

`TeleopSubscription` must provide `try_recv()` and may override `drain_latest()`.

> **Do not** reach into `litegrip._internal` names or the private `_`-prefixed methods. They change without notice, and the public surface above is enough for everything listed here.

## C++ SDK

[`litegrip-cpp`](https://github.com/nexform-tech/litegrip-cpp) is the ROS-agnostic C++ SDK: C++17, CMake 3.16 or newer, Linux with SocketCAN, and no third-party dependency beyond the C++17 standard library, `pthread` and the SocketCAN headers.

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure
cmake --install build --prefix "$HOME/.local"
```

`ctest` needs no hardware, no CAN interface and no root. Installing writes the library, the headers, the packaged calibration, and the CMake and pkg-config files under the prefix.

Consume it from your own project:

```cmake
find_package(litegrip_cpp REQUIRED)
target_link_libraries(my_app PRIVATE litegrip_cpp::litegrip_cpp)
```

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH="$HOME/.local"
```

> **Do not** put `~/.local` in `CMAKE_PREFIX_PATH`. CMake does not expand `~`, so it looks for a directory literally named `~` and fails with "Could not find a package configuration file". Use `$HOME` or an absolute path.

Or through pkg-config once installed, with `PKG_CONFIG_PATH="$HOME/.local/lib/pkgconfig"`:

```bash
g++ -std=c++17 $(pkg-config --cflags litegrip_cpp) main.cpp \
    $(pkg-config --libs litegrip_cpp) -o my_app
```

> **Do not** point `PKG_CONFIG_PATH` at `build/`. The `litegrip_cpp.pc` sitting there is the uninstalled copy, whose paths are relative to where the file ends up, so it reports paths that do not exist. Use the installed one.

**The surface matches Python, under C++ names.** `grasp()` and `move_at_speed*()` exist, as do `goto_mm()` / `goto_rad()` / `move_to()`, the four calibration entry points, `get_state()` with `is_stale()` and `data_age_s`, and `send_mit_frame()`. Two differences matter when you port:

- **`set_force()` exists in neither SDK.** It was removed from both public APIs before v1.0.0; use `grasp()`.
- **`close()` takes a speed, not a force.** The old `close(kp, kd, force_n, duration)` signature is gone; `close(speed_mm_s)` is the whole parameter list, and a port that relied on the force argument needs `grasp()` instead.

The C++ SDK also carries a ceiling the Python one does not: `kMaxCommandVelocityCeilingRadS` (1.5 rad/s) in `safety.hpp`. `ControlLoop::max_velocity_rad_s` defaults to it and may only be lowered, never raised.

## ROS 2 (ros2_control and MoveIt 2)

**`ros2_control` hardware interface** — [`litegrip-ros2`](https://github.com/nexform-tech/litegrip-ros2) ships one package, `litegrip_ros2_control`: an ament_cmake C++ `SystemInterface` plugin backed directly by the C++ SDK, with no Python daemon and no shared memory in the path. Its description file is `litegrip_ros2_control/urdf/litegrip.ros2_control.xacro`.

```xml
<ros2_control name="LitegripSystem" type="system">
  <hardware>
    <plugin>litegrip_ros2_control/LitegripSystem</plugin>
    ...
  </hardware>
</ros2_control>
```

**One joint carries the motion.** The plugin commands `gripper_opening_joint`; the two fingers are its mimics and have no command port of their own, because a real gripper has one transmission. That joint name must match the description package's URDF.

| Parameter | Default | What it decides |
|------|------|------|
| `channel` / `can_id` / `mst_id` / `canfd_mode` | `can0` / `0x08` / — / `false` | The bus the plugin owns |
| `dry_run` / `hardware_enable` | — | Both switches must be on before a motion frame goes out |
| `max_velocity_rad_s` | `1.5` | Command velocity ceiling. It can be lowered, never raised |
| `max_feedback_velocity_rad_s` | `-1.0` | Worst-case feedback velocity bound. **`-1.0` means "not given", and the plugin then refuses to send any motion frame** |
| `torque_limit_nm` | `3.5` | Total control torque budget, allocated between `kp` and `kd` every frame; 3.5 N·m is the DM-J4310-2EC rating |
| `safety_baseline` | `3.5` | Versioned safety baseline. An unknown version or a missing file makes the component **refuse to start** |
| `max_position_error_rad` | `-1.0` | Worst-case position error; `-1` derives it from the travel limits |
| `kp` / `kd` | `20.0` / `0.5` | Gain upper bounds, re-allocated from the budget each frame |
| `control_rate_hz` / `feedback_timeout_s` / `command_timeout_s` | — | Loop and watchdog timing |
| `temperature_limit_c` | — | Coil and MOS temperature cutoff |
| `closed_rad` / `rad_to_mm` / `min_width` / `max_width` | — | The travel the plugin clamps to |
| `export_diagnostics` | `true` | Exports temperature, error code, fault code and feedback age as state interfaces. `joint_state_broadcaster` does not claim them, so the controller manager warns on activation — that warning is expected. Set it to `false` if it is too noisy |

> **Do not** raise `max_velocity_rad_s` above `1.5`. The ceiling rests on a documented worst-case comms assumption (the model saturates at about `1.39 rad/s`), not on a measurement: raise it only with a measurement behind it.

**Motion planning** — [`litegrip-moveit2`](https://github.com/nexform-tech/litegrip-moveit2) provides a MoveIt 2 configuration, with the planning group `gripper`, the master joint `gripper_opening_joint`, and named states `open` (0.087 m) and `closed` (0.0 m).

```bash
ros2 launch litegrip_moveit_config demo.launch.py
```

> **Note**: **The demo runs in dry run by default** — no CAN socket is opened and no motor is touched. To drive real hardware, pass both switches and a feedback-velocity bound:

```bash
ros2 launch litegrip_moveit_config demo.launch.py \
  dry_run:=false hardware_enable:=true \
  max_feedback_velocity_rad_s:=0.9
```

> **Note**: **`max_feedback_velocity_rad_s` defaults to `-1.0`, which means "not given", and the control loop then refuses to send any motion frame.** That is deliberate fail-closed behaviour, not a fault. Treat the `0.9` above as an example: calibrate it on your unit by running it through its real working conditions, taking the peak feedback velocity and adding margin.

The URDF model lives in [`litegrip-description`](https://github.com/nexform-tech/litegrip-description):

```bash
ros2 launch litegrip_description display.launch.py
```

Add `stroke:=` to override the per-finger travel the model uses.

> **Note**: **[`litegrip-ros1`](https://github.com/nexform-tech/litegrip-ros1) does not exist yet.** The repository is a stub containing only CI configuration and a README; it has no source, no package and no release. **Do not plan a ROS 1 integration around it.**

## Simulation (MuJoCo, PyBullet, Isaac Sim)

| Package | Entry point | What it gives you |
|------|------|------|
| [`litegrip-pybullet`](https://github.com/nexform-tech/litegrip-pybullet) | `python3 examples/01_hello_sim.py --headless` | `GripperSim` with `command_fraction()`, `settle()`, `aperture_mm()`, `finger_force_n()`; examples for sim→real and real→sim |
| [`litegrip-mujoco`](https://github.com/nexform-tech/litegrip-mujoco) | `from litegrip_mujoco import MujocoGripper` | `MujocoGripper` with `open`/`close`/`goto`/`grasp`/`get_state`, plus `MirrorMode` and `DualGripper` for real↔sim mirroring |
| [`litegrip-isaacsim`](https://github.com/nexform-tech/litegrip-isaacsim) | `ISAAC_SIM_PATH=... ./run_gripper.sh` | An Isaac Sim node subscribing to `/gripper/joint_traj`, and a bridge to real hardware over CAN |

`litegrip-mujoco` is the richest of the three, with five numbered examples from `01_hello_sim.py` to `05_dual_control.py`.

**Both Python simulators run the same model as the URDF package, not a copy of it.** PyBullet bundles the upstream ROS 2 xacro from `litegrip-description`, normalised at load time (mesh paths rewritten, the massless root link stripped), and MuJoCo builds its MJCF on the same three STL meshes.

> **Note**: **None of the simulation packages is on PyPI**, despite what their READMEs show — `pip install litegrip-mujoco` returns 404 (checked 2026-10-15). Install them from a checkout, the same way as the SDK.

> **Note**: **The Isaac Sim bridge's real-gripper calibration is a placeholder.** The simulated model and the sim node work, but the `OPEN_MM` value used to map the real gripper's opening onto the model has not been measured: with `OPEN_MM = None` the bridge falls back to `OPEN_MM_CALIB = 120.06` and logs a warning. Treat sim-to-real opening values from that bridge as indicative only.

## Host application (litegrip-studio)

[`litegrip-studio`](https://github.com/nexform-tech/litegrip-studio) is the operator console: a PyQt5 application for driving, calibrating and monitoring the gripper, with a plotting page and a self-test mode. It needs Python 3.10 or newer plus `PyQt5`, `pyqtgraph` and `numpy`.

```bash
./run_litegrip_studio.sh sim        # the console, against the built-in simulated gripper
./run_litegrip_studio.sh gui        # the console, against a real gripper on can0
./run_litegrip_studio.sh selftest   # self-check: no Qt, no hardware
./run_litegrip_studio.sh test       # the test suite
./run_litegrip_studio.sh build      # one-file executable in dist/
```

The launcher dispatches to `python -m litegrip_studio --backend sim|real`; `--backend` defaults to `real`, and `-h` lists every subcommand and option. `PYTHON_BIN` picks the interpreter the launcher and the build script use, and `LITEGRIP_SDK_PATH` points at an SDK checkout — the checkout root or its `src/` — instead of the vendored copy.

**The SDK is vendored under `src/litegrip`**, at a pinned commit, so a fresh clone runs with nothing installed beside it. `./run_litegrip_studio.sh build` produces a single-file executable in `dist/` **on your machine**; it is not published as a release asset.

> **Note**: **This is the application to hand to someone who does not want to write code.** It covers connect, calibrate, move and log without a line of Python. The SDK remains the path for anything scripted.

## What is not ready yet

This manual documents what exists. This table exists so nobody plans around something that does not.

| Component | Status |
|------|------|
| [`litegrip-python`](https://github.com/nexform-tech/litegrip-python) | Complete and active. The primary path |
| [`litegrip-cpp`](https://github.com/nexform-tech/litegrip-cpp) | Covers motion, grasping, calibration and the bus. No `set_force()` — gone from both SDKs; `close()` takes a speed |
| [`litegrip-ros1`](https://github.com/nexform-tech/litegrip-ros1) | **Empty stub.** No source, no package, no release |
| [`litegrip-ros2`](https://github.com/nexform-tech/litegrip-ros2) | Usable; the `ros2_control` plugin is the entry point |
| [`litegrip-moveit2`](https://github.com/nexform-tech/litegrip-moveit2) | Usable; dry-run by default, fail-closed on motion limits |
| [`litegrip-description`](https://github.com/nexform-tech/litegrip-description) | Visualisation and `ros2_control` verified. **`effort` and `velocity` limits are SolidWorks placeholder defaults**, and the Gazebo launch has never been executed |
| [`litegrip-mujoco`](https://github.com/nexform-tech/litegrip-mujoco) | Complete, with the richest example set |
| [`litegrip-pybullet`](https://github.com/nexform-tech/litegrip-pybullet) | Complete |
| [`litegrip-isaacsim`](https://github.com/nexform-tech/litegrip-isaacsim) | Sim side works; the real-gripper `OPEN_MM` calibration is a placeholder |
| [`litegrip-studio`](https://github.com/nexform-tech/litegrip-studio) | Complete and active |

**No releases ship binaries.** Every repository publishes tag-only releases with no attached assets, and **no package is on PyPI**. Everything installs from a source checkout.

## Reporting and verification status

This chapter documents the SDK as of the revision named in the repository's `README.md`. Interfaces change; when a call fails with an unexpected signature, check the SDK's own [README](https://github.com/nexform-tech/litegrip-python#readme) and `py.typed` annotations before assuming the manual is right.

| Content | Status |
|------|------|
| Interface names, signatures, defaults and dataclass fields | **Verified** against the SDK source, method by method |
| CAN protocol chapter | **Verified** against the driver and the SDK codec; worked examples reproduce byte for byte |
| Motion examples in [First run](#5-first-run-make-the-gripper-move) and below | **Not executed on hardware.** Written from the SDK source and its README; the printed values are illustrative |
| The 0.4 s communication timeout, the MIT quantization ranges, and `grasp_torque_threshold` | **Not measured.** They are placeholders awaiting bench measurement |
| Simulation and ROS entry points | **Not executed.** Taken from each repository's README and file tree |
| C++ SDK interfaces, build and link flags | **Verified** against the C++ SDK by the maintainer |
| litegrip-studio commands, paths and backend names | **Not executed.** Taken from the repository's README and file tree |

> **Do not** treat an example in this manual as a tested program. Anything that moves the gripper must be validated on your own hardware, at reduced force and speed, before it goes near a workpiece or a person.

## FAQ and technical support

### Q&A

Q: Which platforms does the SDK support? A: **Linux only**, with kernel support for SocketCAN. The library code uses only the Python standard library — **the package declares no runtime dependencies at all**, so it installs and runs on a bare controller with no package index reachable.

Q: Does `pip install litegrip` work? A: **No.** The package is not on PyPI. Clone the repository and run `python3 -m pip install .` inside it. Installing from a wheel you found elsewhere is not supported.

Q: Why must `fd off` be added when configuring CAN? A: Because this product uses **classic CAN**. Configuring it as CAN FD makes **communication completely impossible** — and that symptom looks a lot like "24 V not connected", so it is easily misdiagnosed as a hardware fault.

Q: Why do I receive nothing when I listen on the bus? A: **Feedback is query-based** — the driver sends a frame back only after it receives a frame from the host computer. **Passive listening will never receive any frames**; you must send a frame first.

Q: What do I do after connecting? A: **Call `load_calibration()` first, then `enable()`.** `connect()` does **not** load the calibration file automatically; until it is loaded, `config` still holds placeholder values (`rad_to_mm=75.44`) and `config.calibrated` is `False`. See [Loading the calibration](#4-loading-the-calibration) for which calls refuse to run in that state and which silently do not.

Q: `open()` raises `CommandError` saying the configuration is not calibrated. What is wrong? A: The calibration was never loaded. `open()`, `close()` and `grasp()` all go through the calibration guard, so they refuse rather than guess a direction. Call `load_calibration()` (or run `zero()`) before them.

Q: `goto()` moves to the wrong place, but no error appears. Why? A: It should have raised. Since v1.1.0 every positioning interface — `goto`, `goto_rad`, `move_to`, `move_at_speed*` and `home` — goes through the same ramp, and the ramp raises `CommandError` on an uncalibrated config. If it moved and said nothing, the calibration **was** loaded and your expectation is what is off: check `config.rad_to_mm` against the value in your calibration file, and remember that a target beyond the calibrated endpoint is silently clamped.

Q: A function returned `True`; does that mean it succeeded? A: It depends on the function. `enable()`'s `True` is backed by a feedback frame (and a failure raises `HardwareError`), so it is trustworthy; `disable()`'s `True` **only means the command was sent, not confirmed**; a motion interface's return value only means "this run of frames was sent", **not that the mechanism has reached its target**. To tell whether it has arrived, read `get_state()`.

Q: Why does the enable interface return success when the motor is not actually enabled? A: If the feedback has `ERR = 0x0`, the driver is still disabled — the motor then accepts position commands but **outputs no torque**, which shows up as "the command was sent, but the mechanism does not move". First confirm that 24 V is connected and that `enable()` did not raise `HardwareError`.

Q: The mechanism does not move after I send a command from the menu? A: Check in order: (1) whether 24 V is connected (`ERR = 0x9` means undervoltage); (2) whether `enable()` succeeded; (3) whether `load_calibration()` was called; (4) whether the target position equals the current position; (5) whether `kp` is 0.

Q: I want the gripper to "raise an error when the target is out of range". How? A: `goto_rad()` / `move_at_speed_rad()` **silently clamp** an out-of-range target and raise no error. If you want it rejected, check before the call yourself: read `config.pos_closed_rad` / `pos_open_rad`, compare with the target value, and only then decide whether to send it.

Q: Why does `goto(60.0)` not reach 60 mm? A: Three possibilities: (1) the jaws stalled on the way, in which case `MoveResult.ok` is `False` and the `state` it returns shows where they actually stopped; (2) the target lies beyond the calibrated endpoint, so it is clamped to the endpoint; (3) `duration` is too short, so the mechanism is still in transit when the frame sequence ends.

Q: Why does `close()` not stop at the force I set? A: `close()` has no force argument at all, and never had one that worked. `force_n` is accepted only by `grasp()`, where it is converted into a feed-forward torque of `force_n × 0.1 N·m` with no position or velocity gain; **no validation is performed and no guarantee is made that the gripping force equals the set value**, because the realised force depends on the object's stiffness and on where the jaws land. Commanding a force at a position is what `set_force()` used to do — it is gone, and `grasp()` is the replacement.

Q: `grasp()` returned `result.stalled == True`. Did it grip the object? A: **Not necessarily.** The stall test is positional — the windowed position change falling below `stall_delta` for `stall_cycles` consecutive cycles. Gripping an object and running into the stroke endpoint look identical to it, so **`stalled` alone cannot tell them apart**. Read `get_position()`: a grasp on nothing ends at the closed endpoint, a grasp on an object ends short of it.

Q: `grasp()` returned `ok == False`. Does that mean something is broken? A: Not necessarily. `GraspResult.ok` reports whether the hold phase ended normally; `reached` reports whether the target angle was reached and `stalled` whether the position stopped changing. Read all three together, and remember that on a successful power grasp `stalled` is `True` and `reached` is `False`.

Q: What does `stop()` return? A: **It returns `None`**. That does not mean "it has stopped": when not connected or not enabled it is a no-op, and after the zero-torque frame is sent the motor stays enabled and can be back-driven. To cut the output, use `disable()` or remove the hardware power.

Q: The finger has stopped outside the stroke; what do I do? A: Drive it back with an ordinary motion interface — `goto_rad()` clamps the target to within the calibrated endpoints, so "coming back from outside" is **naturally allowed**. If the mechanism has already jammed or is stuck, do not keep applying force; clear the interference by hand first.

Q: If I let go after `enter_zero_gravity()`, will the finger drop? A: **It will move.** Zero gravity mode means the motor outputs no torque; gravity and friction decide the position. To hold it in place, call `exit_zero_gravity()` after you let go.

Q: What happens if I push past either end of the stroke in zero gravity mode? A: There is no indication of any kind — that mode does not check position. Only when you later call an ordinary motion interface is the target clamped back to the calibrated endpoints.

Q: During calibration, why does it keep pushing after it hits the hard stop? A: `zero()`, `calibrate()` and `calibrate_guided()` **detect the limit by motor stall**: they step in one direction until the position increment stays below the threshold for several consecutive cycles, and they do not stop on their own in between. Before running it, confirm that the mechanical hard stop can take that force, and prefer `calibrate_manual()`.

Q: The calibrated `rad_to_mm` came out wrong? A: Check `max_stroke_mm`. It defaults to `85.0`, the jaw travel the shipped hardware has, and every calibration entry point uses `max_stroke_mm + STOP_INSET_MM` as the scale numerator (`rad_to_mm = (max_stroke_mm + 1.0) ÷ measured rad span`). Set it to **your** unit's jaw travel — measured from the closed stop with a caliper — before you re-probe; it is the one per-unit number no calibration file carries. One wrong value to avoid: the long-gone `120.0` placeholder belonged to no gripper in this family.

Q: Where is the calibration file written? A: `save_calibration()` with no argument writes `~/.litegrip/<channel>_calibration.json` and **returns the path it wrote** — one file per channel, so two grippers on one machine do not overwrite each other. The name `~/.litegrip/litegrip_calibration.json` is the legacy path; `load_calibration()` still reads it as a fallback, but nothing writes it any more.

Q: Why does `home()` not return to the closed end? A: It should. `home()` sends `self._config.pos_closed_rad` — **this instance's calibrated closed limit**, not a module constant — so it returns to the closed end for a normal mount and to the correct end for a reverse mount. If it moves to the wrong end, the calibration was not loaded and `pos_closed_rad` is still the placeholder. (Earlier revisions of this manual claimed `home()` used the constant `0.0 rad` and would drive into the open side. That was wrong; check `config.calibrated` instead.)

Q: The position reading disagrees with my caliper? A: They should agree — `position_mm` **is** the aperture between the fingertips, measured from the fully closed mechanical limit. If the two differ by a consistent percentage, the `rad_to_mm` scale is wrong; if they differ by a constant offset, you are measuring to a different reference surface. See the reading convention in [Units and conversion](#units-and-conversion).

Q: The `tau` reading is always slightly smaller than what I set? A: Normal. MIT frames use **truncating** encoding (rounding down), so the quantization error is one-sided: `decoded value − commanded value` falls in the interval `(−1 LSB, 0]`, and it is **never greater than** the value you set.

Q: Does setting `kp` / `kd` to 1000 raise an error? A: No. At encoding time they are **silently saturated** to `[0, 500]` / `[0, 5]`, and `tau` is saturated to `[−10, 10] N·m`; the caller receives no indication at all.

Q: Reading `OC_Value` gives 0.8; is that 0.8 A? A: **No.** It is a **ratio**, meaning 80%.

Q: Are `PMAX` / `VMAX` / `TMAX` my protection thresholds? A: **No.** They are the **MIT quantization range** of the frame fields (the range definition) and must not be used as safety limits for position / velocity / torque. **The real velocity protection is in `MAX_SPD`.** (The SDK never reads these three registers back and uses a hardcoded range, so it needs verification by reading back.)

Q: Can I control it from two host computers at the same time? A: **No.** You must guarantee a **single CAN master** and enforce mutual exclusion in software. With multiple masters running concurrently, the commands overwrite each other. One process may own several grippers — use `litegrip.can.controller` rather than a second process.

Q: Can I teleoperate two grippers whose calibrations differ? A: **Yes.** The wire carries a normalised `openness` in `[0, 1]`, not radians, so the two ends need not share a calibration, a mount, or a zero point. They must agree on `grip_id`.

Q: What is the technical support channel? A: The NEXFORM ROBOTICS technical team. Contact details are in the documents shipped with the product and through the sales channel, or the contact person from your purchase can forward you to technical support directly.

# CAN communication protocol

This chapter describes the low-level communication protocol, for integrators who do not use the Python SDK or who need to implement their own control program in another language. **The SDK's safety handling (position clamping, zero-torque stop, and so on) does not take effect automatically for readers of this document** — when you implement the protocol yourself, the out-of-range checks, rate limiting, emergency-stop path, and periodic frame transmission are all yours to implement.

> **Note**: **Implementing the protocol yourself means taking on the responsibility for implementing the safety constraints yourself.** Prefer the Python SDK. If you really must implement it yourself, also read the Safety Manual, Chapter 2 and Chapter 7.

## Physical layer and nodes

| Item | Value |
|------|------|
| Bus type | Classic CAN (CAN 2.0) |
| Baud rate | 1 Mbps |
| CAN FD | **Not used (must be off)** |
| Data frame length | 8 bytes |
| Terminating resistor | One 120 Ω terminating resistor at each end of the bus |

**ID assignment:**

| Name | Value | Meaning |
|------|------|------|
| Motor CAN ID (`ESC_ID`) | `0x08` | Control frames and command frames from host to motor use this ID (**plus the mode offset**) |
| Feedback ID (`MST_ID`) | `0x18` | Frames from motor to host use this ID |
| Broadcast ID | `0x7FF` | **Status refresh frames and parameter frames** go to this ID; the target motor ID goes in the data |

**The arbitration ID of a control frame or command frame = motor CAN ID + mode offset.** This product uses MIT mode, offset `0x000`, so the arbitration ID of both is `0x08 + 0x000 = 0x08`.

| Frame type | Arbitration ID | How the target motor is specified |
|--------|---------|-----------------|
| MIT control frame | `0x08` | The arbitration ID itself |
| Command frame (enable / disable / clear fault / set zero point) | `0x08` | The arbitration ID itself |
| Status refresh frame | `0x7FF` | Data bytes 0 and 1 (low byte first) |
| Parameter frame (read / write / save) | `0x7FF` | Data bytes 0 and 1 (low byte first) |

> **Note**: **Only status refresh frames and parameter frames are addressed with the broadcast ID `0x7FF`** (the target motor ID goes in the data); **MIT control frames and command frames are addressed by arbitration ID**, sent to `0x08`. When you send a command frame to `0x7FF`, **no motor answers and no motor acts** — and the symptom closely resembles "24 V not connected", so it is easily misdiagnosed as a hardware fault.

## Frame types

| Frame type | Direction | Arbitration ID | Purpose |
|--------|------|---------|------|
| Control frame (MIT) | Host -> motor | `0x08` | Carries position, velocity, stiffness, damping, and feedforward torque at the same time |
| Command frame | Host -> motor | `0x08` | Enable / disable / clear fault / set zero point |
| Status refresh frame | Host -> motor | `0x7FF` | Does not change the output; only requests one status frame |
| Parameter frame | Host -> motor | `0x7FF` | Read and write driver registers, save to Flash |
| Feedback frame | Motor -> host | `0x18` | Status, position, velocity, torque, temperature, error code |

## MIT control frame

**Fields and ranges:**

| Field | Width | Range | Description |
|------|------|------|------|
| Position `q` | 16 bits | ±12.5 rad | Target angle |
| Velocity `dq` | 12 bits | ±30 rad/s | Target velocity |
| Position stiffness `kp` | 12 bits | 0 ~ 500 | The larger it is, the "harder" |
| Damping `kd` | 12 bits | 0 ~ 5 | |
| Feedforward torque `tau` | 12 bits | ±10 N·m | |

The torque output inside the motor is:

```text
tau_out = kp · (q_target − q_actual) + kd · (dq_target − dq_actual) + tau
```

**Byte layout:**

| Byte | Content |
|------|------|
| 0 | `q[15:8]` |
| 1 | `q[7:0]` |
| 2 | `dq[11:4]` |
| 3 | `dq[3:0]` in the high 4 bits, `kp[11:8]` in the low 4 bits |
| 4 | `kp[7:0]` |
| 5 | `kd[11:4]` |
| 6 | `kd[3:0]` in the high 4 bits, `tau[11:8]` in the low 4 bits |
| 7 | `tau[7:0]` |

**Quantization rule (truncation, not rounding):**

```
code  = int( (value − min) × (2^width − 1) / (max − min) )
value = code × (max − min) / (2^width − 1) + min
```

> **The quantization error is one-sided**: `decoded value − command value` falls in the interval `(−1 LSB, 0]`. The value after encoding is **always equal to or slightly less than** the one you wanted, and **never greater**.

**1 LSB per field:**

| Field | 1 LSB |
|------|-------|
| `q` | 3.814755 × 10⁻⁴ rad |
| `dq` | 1.465201 × 10⁻² rad/s |
| `tau` | 4.884005 × 10⁻³ N·m |
| `kp` | 0.1221 (= 500 / 4095) |
| `kd` | 0.001221 (= 5 / 4095) |

> **The range of `kp` and `kd` starts at 0**, so "command 0" encodes exactly as "code value 0", and there is no quantization error there. But for nonzero values the resolution is the table above: `kp` steps by 0.1221, `kd` steps by 0.00122.

**Example 1 — position control** (position −0.6 rad, velocity 0, stiffness 100, damping 2, no torque feedforward):

| Field | Command value | Code value |
|------|--------|------|
| `q` | −0.6 rad | 31194 = `0x79DA` |
| `dq` | 0 rad/s | 2047 = `0x7FF` |
| `kp` | 100 | 819 = `0x333` |
| `kd` | 2 | 1638 = `0x666` |
| `tau` | 0 N·m | 2047 = `0x7FF` |

```
79 DA 7F F3 33 66 67 FF
```

**Example 2 — zero-torque frame** (position, velocity, stiffness, damping, and torque all set to zero):

```
7F FF 7F F0 00 00 07 FF
```

> **Why does a zero-torque frame still carry a position field?** The five fields of a MIT frame are fixed-length, so the `q` field **must** be present. Because `kp = kd = 0`, the two terms in the torque formula are always zero, so **the value of `q` has no effect on the output** — it is only a placeholder. When the SDK sends a zero-torque frame it fills `q` with a fixed `0` (that is, code value 32767 = `0x7FFF`), so no value with a "target position" meaning ever appears in the bytes on the wire. **This is a fixed value, not a "fill the safe zone" algorithm.**

**The real output of a zero-torque frame (important):**

| Field | Command value | Actual decoded value |
|------|--------|-----------|
| `kp` | 0 | **0** (exact) |
| `kd` | 0 | **0** (exact) |
| `dq` | 0 | **−7.326 mrad/s** |
| `tau` | 0 | **−2.442 mN·m** |

Because of the truncation rule, with `tau = 0` and `dq = 0` the code value is 2047 in both cases, and **it does not decode back to 0**.

> **Why this is safe:**
>
> 1. The residual −2.442 mN·m is a **constant independent of position**; it does not vary with the mechanism's position, so it is not a driving force that pushes the mechanism in any direction.
> 2. Its magnitude is far below the no-load static friction of the mechanism (0.198 N·m, taken here as the lower bound of the measured interval; the full measured interval is **0.198 ~ 0.222 N·m**), so it cannot move the mechanism.
> 3. `kp = kd = 0` makes the position field completely inactive, so this frame **cannot** produce torque from a position error.
>
> **Note**: **The correct reason a zero-torque frame produces no torque from a position error is that "zero stiffness and damping make the position field inactive", not that "the output is always zero". The latter does not hold.**

## Command frame

**Format**: arbitration ID = motor CAN ID + mode offset (for this product = `0x08`, see the table above); bytes 0 ~ 6 are all `0xFF`; byte 7 is the command code. **Note that the data contains no target motor ID** — a command frame is addressed by its arbitration ID.

| Command | Command code | Full data bytes |
|------|--------|-------------|
| Enable | `0xFC` | `FF FF FF FF FF FF FF FC` |
| Disable | `0xFD` | `FF FF FF FF FF FF FF FD` |
| Clear fault | `0xFB` | `FF FF FF FF FF FF FF FB` |
| Set zero point | `0xFE` | `FF FF FF FF FF FF FF FE` |

> **A command frame usually has to be sent several times in a row.** A single frame may be lost to bus contention or to the driver's state-machine timing. Send **5 frames in a row** (the SDK's implementation is 5 frames with a 2 ms gap).
>
> **Note**: **"Set zero point" records the current position as the mechanical zero, and this cannot be undone.** Do not send this command unless you know exactly what you are doing. The SDK keeps an implementation of this command (`set_zero()` in the `litegrip.can` subpackage), but **its own high-level interface never sends it on its own** — the gripper's zero point comes from calibration, not from this command.

## Status refresh frame

Read the status without changing the motor output.

**Format**: arbitration ID = `0x7FF`; 4 data bytes: `[can_id low byte, can_id high byte, 0xCC, 0x00]`

When the motor CAN ID = `0x08`: `08 00 CC 00`

After you send it, the motor sends back one status frame. **Use**: poll position, temperature, and fault codes without disturbing a motion in progress.

## Parameter frames and registers

**Frame format** (the arbitration ID is always `0x7FF`):

| Operation | Data bytes |
|------|---------|
| **Read** | `[can_id low, can_id high, 0x33, RID, 0, 0, 0, 0]` |
| **Write** | `[can_id low, can_id high, 0x55, RID, d0, d1, d2, d3]` |
| **Save** | `[can_id low, can_id high, 0xAA, 0x01, 0, 0, 0, 0]` |

A **response frame** has the same structure: byte 2 echoes the opcode (`0x33` = read response, `0x55` = write response, `0xAA` = save response), byte 3 is the RID, and bytes 4 ~ 7 are the data.

**Data encoding**: integer registers are little-endian unsigned 32-bit integers; float registers are little-endian IEEE 754 single-precision floats. The RID ranges of the integer registers are `7 ~ 10`, `13 ~ 16`, and `35 ~ 36`; **all other RIDs are float registers**.

**Register number table:**

| RID | Hex | Name | Type | Description |
|-----|---------|------|------|------|
| 0 | `0x00` | `UV_Value` | Float | Undervoltage protection threshold (V) |
| 1 | `0x01` | `KT_Value` | Float | Torque coefficient |
| 2 | `0x02` | `OT_Value` | Float | Overtemperature protection threshold (°C) |
| 3 | `0x03` | `OC_Value` | Float | Overcurrent protection threshold (**a ratio, not amperes**) |
| 4 | `0x04` | `ACC` | Float | Acceleration (takes effect only in non-MIT modes) |
| 5 | `0x05` | `DEC` | Float | Deceleration (takes effect only in non-MIT modes) |
| 6 | `0x06` | `MAX_SPD` | Float | Maximum velocity (**the real speed limit**) |
| 7 | `0x07` | `MST_ID` | Integer | Feedback frame ID |
| 8 | `0x08` | `ESC_ID` | Integer | Motor CAN ID |
| 9 | `0x09` | `TIMEOUT` | Integer | Communication timeout (unit 50 µs) |
| 10 | `0x0A` | `CTRL_MODE` | Integer | Control mode |
| 11 | `0x0B` | `Damp` | Float | Damping coefficient |
| 12 | `0x0C` | `Inertia` | Float | Inertia |
| 13 | `0x0D` | `hw_ver` | Integer | Hardware version (reserved field; reading 0 is normal) |
| 14 | `0x0E` | `sw_ver` | Integer | Firmware version number |
| 15 | `0x0F` | `SN` | Integer | Serial number (reserved field) |
| 16 | `0x10` | `NPP` | Integer | Pole pairs |
| 17 | `0x11` | `Rs` | Float | Phase resistance |
| 18 | `0x12` | `LS` | Float | Phase inductance |
| 19 | `0x13` | `Flux` | Float | Rotor flux linkage (Wb) |
| 20 | `0x14` | `Gr` | Float | Gear reduction ratio |
| 21 | `0x15` | `PMAX` | Float | Position **MIT quantization range** (rad) |
| 22 | `0x16` | `VMAX` | Float | Velocity **MIT quantization range** (rad/s) |
| 23 | `0x17` | `TMAX` | Float | Torque **MIT quantization range** (N·m) |
| 24 | `0x18` | `I_BW` | Float | Current loop bandwidth |
| 25 | `0x19` | `KP_ASR` | Float | Velocity loop proportional gain |
| 26 | `0x1A` | `KI_ASR` | Float | Velocity loop integral gain |
| 27 | `0x1B` | `KP_APR` | Float | Position loop proportional gain |
| 28 | `0x1C` | `KI_APR` | Float | Position loop integral gain |
| 29 | `0x1D` | `OV_Value` | Float | Overvoltage protection threshold (V) |
| 30 | `0x1E` | `GREF` | Float | Gear ratio reference |
| 31 | `0x1F` | `Deta` | Float | — |
| 32 | `0x20` | `V_BW` | Float | Velocity loop bandwidth |
| 33 | `0x21` | `IQ_c1` | Float | — |
| 34 | `0x22` | `VL_c1` | Float | — |
| 35 | `0x23` | `can_br` | Integer | CAN baud rate |
| 36 | `0x24` | `sub_ver` | Integer | Sub-version number |

> **On the source of this table**: the numbers, the type classification, and the semantic descriptions come from the motor protocol specification; the registers this product actually uses **have been confirmed by reading each one back on this product**. The other registers are not used by this product, and their values are subject to your motor's actual firmware.
>
> **Note**: **RID 3 (`OC_Value`) is a ratio, not amperes.** The value range is (0, 1); `0.8` means 80%. Reading it as a current value leads to a completely wrong conclusion.
>
> **Note**: **RID 21 / 22 / 23 (`PMAX` / `VMAX` / `TMAX`) are MIT quantization ranges, not protection thresholds.** They define the range of the MIT frame fields, and **must not** be treated as safety limits for position, velocity, or torque. **The real velocity protection is in RID 6 (`MAX_SPD`).**
>
> **Note**: the ranges the SDK uses in this section are **hardcoded** `±12.5 / ±30 / ±10` (see `litegrip/can/protocol.py`), and **the code never reads RID 21/22/23 back**, so it cannot be asserted that they match the actual values in this motor's registers (verify by reading back with `scripts/read_driver_limits.py`).

**Example frames:**

| Operation | Data bytes |
|------|---------|
| Read `TIMEOUT` (RID 9) | `08 00 33 09 00 00 00 00` |
| Write `TIMEOUT` as 8000 (= 0.4 s) | `08 00 55 09 40 1F 00 00` |
| Save the parameters to Flash | `08 00 AA 01 00 00 00 00` |

> **Note**: **You must disable the motor before saving parameters.**
>
> **Note**: **Written parameters do not survive a power cycle automatically.** You must send the save frame explicitly, otherwise the parameters revert to their old values after the next power-up.

## Feedback frames and error codes

**Byte layout** (arbitration ID = `0x18`):

| Byte | Content |
|------|------|
| 0 | `ERR[7:4]` in the high 4 bits, `can_id[3:0]` in the low 4 bits |
| 1 | `q[15:8]` |
| 2 | `q[7:0]` |
| 3 | `dq[11:4]` |
| 4 | `dq[3:0]` in the high 4 bits, `tau[11:8]` in the low 4 bits |
| 5 | `tau[7:0]` |
| 6 | MOS temperature (°C) |
| 7 | Coil temperature (°C) |

`q`, `dq`, and `tau` are decoded with the same rule and ranges as the MIT control frame (±12.5 rad, ±30 rad/s, ±10 N·m).

**Full table of the `ERR` field** — the `ERR` in the high 4 bits carries two jobs at once: **reporting the enable state** and **reporting faults**.

| Code value | Meaning | Category |
|------|------|------|
| `0x0` | Disabled | State |
| `0x1` | Enabled | State |
| `0x9` | **Undervoltage** fault | Fault |
| `0xA` | Overcurrent fault | Fault |
| `0xB` | MOS overtemperature fault | Fault |
| `0xC` | Coil overtemperature fault | Fault |

> **Note**: **This table lists only the code values the shipped SDK can parse.** The driver also reports faults outside the table above (given by the driver's **indicator light**), and the SDK returns "unknown error (0xXX)" for all of them; consult the driver manual when you need to interpret one. `get_error()` itself returns the code value as an integer.
>
> **Note**: **You must use a feedback frame to determine the enable state; do not just check whether the command was sent.** Reading `ERR = 0x1` means enabled; `ERR = 0x0` means the driver is still in the disabled state — the motor then accepts position commands but **outputs no torque**, which appears as "the command was sent, but the mechanism does not move".

**Example feedback frame**: `18 79 DA 7F F7 FF 23 28`

| Item | Value |
|------|-----|
| Arbitration ID | `0x18` (feedback frame) |
| `ERR` | `0x1` -> **enabled** |
| `can_id` | `0x8` |
| `q` | code value 31194 -> **−0.600252 rad** |
| `dq` | code value 2047 -> **−0.007326 rad/s** |
| `tau` | code value 2047 -> **−0.002442 N·m** |
| MOS temperature | 35 °C |
| Coil temperature | 40 °C |

> **Note on the decoded value of `q`**: the command was −0.6 rad, the code value 31194, and it decodes back to **−0.600252 rad**. The error is −0.000252 rad, inside the interval (−1 LSB, 0] — exactly the effect of the truncation rule.

## Communication timing

| Item | Value | Description |
|--------------------------|----------------|----------------------------------------------------------------|
| Enable wait window | **2.0 s** | The SDK waits within this window for a feedback frame **received after the command was sent**; the criterion is `ERR ∈ {0x0, 0x1}` |
| Enable retry count | 5 | Each retry runs "disable -> MIT -> enable -> wait for feedback" again; if all fail it raises `HardwareError` |
| Disable verification | **None** | The SDK returns as soon as it has sent the disable frame; it does not wait for feedback to confirm |
| Status refresh wait | 0.05 s | The time `get_state(wait=True)` waits for one feedback frame |
| Parameter read wait | 0.5 s | The default timeout of `read_param()` |
| Control frame repeat interval | 5 ms (200 Hz) | The beat during a motion |
| Driver communication timeout | 0.4 s (verify by reading back RID 9) | After the timeout the driver **exits the enabled state automatically** |

> **Note**: **What "fresh feedback" means.** The enable decision cannot just look at "a frame with `ERR = 0x1` was received at some point". After power-up the driver may already have a stale status frame buffered. **Only a frame received after the enable command was sent counts** — that is exactly how the SDK judges it.
>
> **Note**: **Driver communication timeout protection.** If the driver receives no frame from the host within 0.4 s, it **exits the enabled state automatically**. That means your controller must keep sending periodically, or the motor disables itself.
>
> **Note**: **This protection can be turned off** (write RID 9 as 0; this is a Damiao protocol-level measure, and the SDK itself never writes this register). **Once it is off, the motor holds the last torque command when the link drops**, so assess this carefully.

## Typical interaction sequences

| Step | Direction | Frame |
|------|------|-----|
| 1 | Host -> motor | Clear fault `FF FF FF FF FF FF FF FB` |
| 2 | Host -> motor | Enable `FF FF FF FF FF FF FF FC` |
| 3 | Motor -> host | Feedback frame, verify `ERR = 0x1` |
| 4 | Host -> motor | Control frame (MIT), sent continuously |
| 5 | Motor -> host | One feedback frame for every control frame received |
| 6 | Host -> motor | Zero-torque frame (stop the output) |
| 7 | Host -> motor | Disable `FF FF FF FF FF FF FF FD` |
| 8 | Motor -> host | Feedback frame, verify `ERR = 0x0` |

> **Steps 3 and 8 cannot be omitted.** Command frames are one-way; only a feedback frame can prove that a command actually took effect.

# Appendix A: Status, error codes, and exceptions

## Status and error fields

`GripperState` has the full field list given in [Reading state](#reading-state). Three fields bear directly on status decisions:

| Field | Test | Meaning |
|------|------|------|
| `error_code` | `== 0` | disabled |
| | `== 1` | enabled |
| | neither 0 nor 1 | a fault is present |
| `torque_nm` | — | torque reading, used by the `is_grasped()` decision |
| `force_n` | — | **estimated** gripping force (`torque_nm × 10`, nominal coefficient); do not rely on it before force calibration is complete |

**Error code table** (matches the `ERR` field; only the codes the shipped SDK can parse are listed):

| Code | Meaning | Category |
|------|------|------|
| `0x0` | disabled | status |
| `0x1` | enabled | status |
| `0x9` | **undervoltage** fault | fault |
| `0xA` | overcurrent fault | fault |
| `0xB` | MOS overtemperature fault | fault |
| `0xC` | coil overtemperature fault | fault |

> **Note**: **This table lists only the codes the shipped SDK can parse.** The driver also reports faults outside the table above (given by the driver's **indicator LEDs**), and the SDK shows the Chinese text "unknown error (0xXX)" for every one of them. Consult the driver manual to interpret them when you need to.

## Python exception types

The SDK has **17** exception classes in total, all inheriting from `LiteGripError`: **7** in `litegrip.exceptions`, **4** in `litegrip.teleop` and **6** in `litegrip.trajectory`.

| Exception | Base class | Meaning |
|------|------|------|
| `LiteGripError` | `Exception` | base class of all SDK exceptions; may carry an `error_code` |
| `NotInitializedError` | `LiteGripError` | the interface was called while not connected or not enabled |
| `ConnectError` | `LiteGripError` | connection failed (the CAN interface cannot be opened, motor registration failed) |
| `CommError` | `LiteGripError` | communication error (low-level send or receive failed for position control / force control) |
| `CANTimeoutError` | `LiteGripError` | bus read timed out |
| `HardwareError` | `LiteGripError` | hardware fault (enable failed, fault clear failed, the driver reported a fault) |
| `CommandError` | `LiteGripError` | command error: a motion action ran while uncalibrated, the travel is zero, or `load_calibration()` was given both `path` and `template` |
| `TeleopError` | `LiteGripError` | base class of the teleoperation errors |
| `TeleopBusyError` | `TeleopError` | `teleop_start()` was called while a session is already running |
| `TeleopNotActiveError` | `TeleopError` | an operation needs an active teleoperation session |
| `TeleopNotReady` | `TeleopError` | the gripper cannot safely be teleoperated yet (uncalibrated, zero travel, or `rad_to_mm == 0`) |
| `TrajectoryError` | `LiteGripError` | base class of the trajectory errors; also raised when the unit is uncalibrated, so a normalised opening would be a guess |
| `TrajectoryBusyError` | `TrajectoryError` | a recording or replay was started while another session (teleop, record, play) is running |
| `TrajectoryNotActiveError` | `TrajectoryError` | `record_stop()` was called with nothing being recorded |
| `TrajectoryEmptyError` | `TrajectoryError` | a capture or a replay dealt with zero samples |
| `TrajectoryRecordingError` | `TrajectoryError` | the sampling loop died, or a timed capture did not fill — a partial capture is never returned as if it were whole |
| `TrajectoryFormatError` | `TrajectoryError` | a byte stream is not a well-formed trajectory file (magic, version, length or sample values invalid) |

> **Note**: The four teleoperation exceptions live in `litegrip.teleop` and the six trajectory ones in `litegrip.trajectory`; all ten are re-exported from `litegrip`, so `from litegrip import TrajectoryFormatError` works. Clamping an out-of-range target and skipping validation of force parameters -- neither raises an exception (see [Motion control](#motion-control-openclose-and-position) and [Grasping and force control](#grasping-and-force-control)).

## Error handling guidance

1. `NotInitializedError`: call `connect()` first, then `enable()`; if it is already connected, check whether `enable()` succeeded.
2. `ConnectError`: check whether the interface is up, whether `fd off` is configured, and whether `can0` exists. **Do not retry until it succeeds** — look at the cause first.
3. `CommError`: check the cabling, the terminating resistors, and the CAN FD setting.
4. `CANTimeoutError`: check whether 24 V is connected; check whether you are only listening and never sending.
5. `HardwareError`: work through the error codes one by one; **for overtemperature and overcurrent, stop the unit and let it cool down first, then investigate the load**. When enable fails, first confirm that 24 V is connected and that `ERR` is not `0x9`. Reading the Chinese "unknown error" means the driver reported a fault code the SDK does not parse; consult the driver's **indicator LEDs**.
6. `CommandError`: the actions layer's calibration guard. Check `config.calibrated` and that the two endpoints differ; if it came from `load_calibration()`, check the template name and that only one of `path` / `template` was given.

> **Note**: **An out-of-range position and uncalibrated force parameters -- neither raises an exception.** Do not expect `try/except` to catch "out of range"; you must check the target value yourself first.

# Appendix B: Communication and connection troubleshooting

## CAN interface and endpoint information

| Item | Value |
|------|------|
| Interface name (default) | `can0` |
| Baud rate | 1 Mbps |
| Frame format | classic CAN, not CAN FD |
| Motor CAN ID | `0x08` |
| Feedback ID (`mst_id`) | `0x18` |
| Broadcast ID | `0x7FF` |
| Terminating resistor | one 120 Ω resistor at each end of the bus |

## CAN interface configuration

```bash
# configure the physical interface
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000 fd off
sudo ip link set can0 up

# confirm the interface state
ip -details link show can0
```

**A virtual bus when you have no hardware:**

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

> A virtual bus has no real motor, so **the enable step times out** (the SDK waits 2.0 s, retries 5 times, then raises `HardwareError`). This is **expected behavior**.

## Bus self-check without the SDK

When the SDK will not install, or when you suspect the problem lies in the SDK layer itself, look at the bus directly with `can-utils`. That settles, before anything else, whether the gripper answers at all.

```bash
sudo apt install can-utils          # provides candump / cansend

# 1) Passive listen: with no frames being sent you should see nothing
candump can0

# 2) In another terminal, send one status refresh frame (motor CAN ID = 0x08)
cansend can0 7FF#0800CC00
#    expected: 0x18 returns one status frame

# 3) Read one register (example: firmware version sw_ver, RID 14 = 0x0E)
cansend can0 7FF#0800330E00000000
#    expected: arbitration ID 0x18, data 08 00 33 0E <4-byte little-endian data>
```

> **Note the two addressing modes.** The **status refresh frame and parameter frame** above go to broadcast ID `0x7FF`, with the target motor ID written in data byte 0; whereas the **command frame (enable / disable / clear fault / set the zero point) and the MIT control frame are addressed by arbitration ID** and must be sent to `0x08` (= motor CAN ID + MIT mode offset `0x000`). The typical symptom of mixing them up is "it was sent and nothing happened".
>
> **A long silence from `candump` does not mean the gripper is broken.** Feedback in this product is **query-based**: the motor answers only after it receives a command frame, so passive listening is meant to receive nothing at all. Send the frame from step 2 first, then judge.

**The safest enable self-check**: connect only the USB-CAN adapter and **leave 24 V disconnected for now**, then send 5 enable commands in a row (**note that the arbitration ID is `08`, not `7FF`**):

```bash
for i in $(seq 5); do cansend can0 08#FFFFFFFFFFFFFFFC; sleep 0.01; done
```

Expect the `ERR` byte of the feedback frame to be `0x9` (undervoltage). **Receiving `0x9` already proves that the bus is up, the motor is running, and it answers correctly**, which narrows the problem to the power supply side — this is a communication check you can complete without applying drive power.

> **Note**: once 24 V is connected, sending an enable frame makes the mechanism **really move**. Before you run it, confirm that no one and nothing is inside the fingers' range of motion.

## Connection troubleshooting

| Symptom | Possible cause | What to do |
|----------------------------------------|----------------------------|--------------------------------------|
| No feedback frame at all | listening only, never sending | **feedback is query-based**; you must send a frame first |
| | the command frame went to `0x7FF` | command frames and MIT frames must go to `0x08` (see the ID assignment table in [CAN communication protocol](#can-communication-protocol)) |
| | CAN FD is not turned off | reconfigure with `fd off` |
| | terminating resistors missing | fit a 120 Ω resistor at each end of the bus |
| | the interface is not up | confirm with `ip link show can0` |
| enable has no effect (`ERR` stays `0x0`) | 24 V drive power is not connected | connect 24 V |
| | the feedback frame is stale | judge only by a frame from **after** the command was sent |
| feedback `ERR = 0x9` (undervoltage) | 24 V is not connected or the voltage is too low | check the power supply |
| the mechanism does not move after a command, `ERR = 0x1` | the target position equals the current position | confirm the target value |
| | `kp = 0` | check the stiffness parameter |
| it suddenly disables mid-motion | driver communication timeout (no frame within 0.4 s) | keep sending periodically |
| | overtemperature / overcurrent protection tripped | stop and cool down, then investigate the load |
| the reported `tau` is slightly below expectation | truncating quantization | **normal**, see [CAN communication protocol](#can-communication-protocol) |
| reading the 0.8 of `OC_Value` as 0.8 A | it is a ratio, meaning 80% | see [Parameter frames and registers](#parameter-frames-and-registers) |
| several units interfering with each other | several CAN masters at once | **keep a single master**; make the software layer mutually exclusive |
| the position reading disagrees with the caliper by a constant percentage | the `rad_to_mm` scale is wrong | recalibrate, or check `max_stroke_mm` |

**If you cannot resolve the problem yourself**, record the following information and contact us: product model and serial number, SDK version, Python version, operating system and kernel version, CAN interface configuration, and the full exception message and stack trace.

---


> **End of document** If you have questions or need more information, contact the NEXFORM ROBOTICS technical team.
