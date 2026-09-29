# Preface

[English](soft-gripper-development-manual.md) | [简体中文](soft-gripper-development-manual-zh.md)

LiteGrip is an adaptive two-finger parallel gripper from NEXFORM ROBOTICS, designed for research and education, AI robotics development, and lightweight industrial automation, with an effective stroke of 87.000 mm. The gripper communicates with the host computer through a USB-CAN adapter (classic CAN, 1 Mbps) and comes with a Python SDK (version 2.2.0) and complete protocol documentation; it supports grasping, handling, loading and unloading, sorting, and algorithm validation.

This document is for **integrators** and explains SDK installation, interface usage, parameters and return values, exceptions, the **precondition** of each interface, and the underlying CAN communication protocol. For product specification values (stroke, velocity, torque, temperature, electrical parameters, and so on), see the Product Manual and the Parameter Document; for the basis of the safety design, see the Safety Manual.

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

**Aperture reading convention**: the same physical aperture has three representations, and their **zero points and directions do not agree**; mixing them is the most common cause of wrong numbers.

| Representation | Fully closed | Fully open | Value when open |
|---------|---------|---------|-----------|
| Motor angle `r` (rad) | Calibrated value `pos_closed_rad` (**see the calibration file for this unit**) | Calibrated value `pos_open_rad` (**see the calibration file for this unit**) | **Decreases** |
| SDK position `p` (mm) | 0 | **87.000** (= effective stroke) | Increases |
| **Actual aperture** (mm) | 1.508 | **87.000** | Increases |

> **Unless this document states otherwise, "mm" always means the "actual aperture"** (that is, the true distance between the inner faces of the two fingers), because that is the quantity a caliper can measure directly.
>
> **`get_position()` and `position_mm` return the `p` of the table above, not the actual aperture**, and the two differ on the closed side by the 1.508 mm closing gap:
>
> ```
> actual aperture ≈ get_position() + 1.508
> ```
>
> You must perform this addition to get the caliper reading.
>
> **Note this convention difference**: the span of `p` is **87.000 mm** (0 → 87.000), while the span of the caliper actual aperture is **85.492 mm** (1.508 → 87.000). **"Effective stroke 87.000 mm" is in the `p` convention**, 1.8 % larger than the caliper span; the `+ 1.508` of the formula above is exact at the closed end and overestimates by 1.508 mm at the open end. For millimeter-level accuracy, calibrate `rad_to_mm` directly with a caliper (see Section 2.3.11).
>
> **Motor angle and calibrated values differ from unit to unit.** The rad endpoints come from the calibration file for this unit (`~/.litegrip/litegrip_calibration.json`), and **the values are different for every unit**, so this document gives no specific numbers; rely on the calibration file of your own unit.
>
> **The conversion factor only affects "the millimeter numbers displayed and millimeter targets".** The SDK position clamping uses the two **rad** values `pos_closed_rad` / `pos_open_rad` and is independent of the millimeter conversion factor — a wrong factor only makes the numbers wrong; it does not change the endpoint positions. **But this also means the SDK makes no out-of-range check for you**: if you need it to "refuse out-of-range targets", implement that yourself (see Section 2.3.6).

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

1. **The SDK makes no out-of-range check.** A position target beyond the calibrated stroke is **silently clamped** to the endpoint (see Section 2.3.6), with neither an error nor a notice; out-of-range `kp` / `kd` / `tau` are **silently saturated**. "Commands stay in range" must be implemented by the integrator.
2. **You must configure a hardware emergency stop circuit, and its action must not depend on CAN communication or host software.** When a process hangs, CAN drops, or Python raises an exception, the software side cannot stop the machine.
3. **You must configure mechanical hard stops** as the last line of defence. A calibrated endpoint is not a mechanical hard stop.
4. **Do not use a software stop as a safety function.** `stop()` only sends a zero-torque frame, the motor stays enabled and can be back-driven, and it does not return success or failure; the `disable()` return value only means the command was sent, not confirmed (see Section 2.3.5). Neither can replace a hardware emergency stop.
5. **Do not treat a return value as evidence that the command took effect.** A motion interface return value only means the frame was sent; only a feedback frame can prove the actual state.
6. **Do not use any force parameter before force calibration is complete.** The `force_n` conversion uses the nominal coefficient `0.1 N·m/N`, which the SDK neither validates nor limits (see Section 2.3.9).
7. Frames must be sent periodically during operation, otherwise the driver **automatically exits the enabled state** after 0.4 s [to be measured · B, verify by reading back RID 9]; **this timeout protection can be disabled, and once it is disabled the motor keeps the last torque command when the link drops** -- do not disable it without an assessment.
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
- A wrong target position calculation (especially mixing mm with rad, or forgetting the 1.508 mm gap) drives the mechanism into the endpoint;
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

> **Note**: **this SDK makes no safety decisions.** Out-of-range targets are **silently clamped** to the calibrated endpoint, force parameters get **no validation at all**, and out-of-range `kp` / `kd` / `tau` are **silently saturated** — none of these three cases **raises an error**. The preconditions of each interface are also only "connected" and "enabled"; see **Section 2.3.13**. **Read Section 2.3.13 first, then read the specific interfaces.**

# SDK usage guide

## Overview

The LiteGrip Python SDK (the `litegrip` package, version 2.2.0) is an upper-layer wrapper around the Damiao **DM-J4310-2EC** motor MIT protocol. It provides interfaces for connecting, enabling, motion, grasping, manual guidance, calibration, and reading state.

**The SDK has exactly two jobs: convert millimeters to motor angle and newtons to feedforward torque, then send MIT frames onto the bus at a fixed period.** It does not check for out-of-range targets, does not latch faults, and does not verify force calibration.

| Design principle | How it shows up in the interface |
|---------|--------------|
| **Commands are one-way; feedback is the truth** | CAN command frames have no acknowledgement; only the status frame the motor returns can prove a command actually took effect |
| **Position targets are clamped to the endpoints** | Targets beyond the calibrated stroke are **silently clamped** to the endpoint, neither raising an error nor rejecting them (see Section 2.3.6) |
| **Motion requires the calibration to be loaded explicitly first** | `connect()` **does not** load the calibration file automatically; without it, motion runs on placeholder coefficients (see Section 2.3.4) |
| **Driver protection is not reimplemented** | Overvoltage / undervoltage / overcurrent / overtemperature / disconnection protection is enforced by the DM-J4310-2EC driver firmware |

> **Note**: **This SDK does not implement "safety limits".** Out-of-range targets are clamped; `kp` / `kd` / `tau` are silently saturated when they fall outside the encoding range; force parameters are applied unconditionally. **Measures to keep the fingers from damaging the workpiece or crushing a person must be implemented by the integrator, in software or in hardware.**

## Library dependencies

| Item | Requirement |
|------|------|
| Python | 3.8 or later |
| Operating system | **Linux** (kernel must support SocketCAN) |
| Third-party dependencies | The library code **uses only the Python standard library + Linux SocketCAN**; it does not depend on `python-can` / `damiao_socketcan` |
| Installed alongside | `pyproject.toml` declares `eclipse-zenoh>=1.0` (used only by the `examples/zenoh_*.py` teleoperation examples); `pip install` installs it too |

> **Note**: **This SDK supports Linux only.** Windows and macOS are not adapted. For another platform, implement the protocol from Chapter 3 yourself.

## Python library installation and usage (primary path)

This section follows the order of use: installation, interface setup, power-up, then connect, enable, motion, grasping, calibration, and exception handling.

### Installation

```bash
cd LiteGrip
pip install -e .
```

After installation you can use `from litegrip import LiteGrip`.

### Dependencies and runtime environment

Configure the CAN interface as root or with the `CAP_NET_ADMIN` capability. Confirm the interface exists:

```bash
ip -details link show can0
```

### Configuring the CAN interface and applying drive power

**Step one, configure the CAN interface:**

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000 fd off
sudo ip link set can0 up
```

> **Note**: **`fd off` cannot be omitted.** If the interface is brought up in CAN FD mode, **communication will not succeed** even with the correct baud rate — and the symptom looks a lot like "no 24 V connected", so it is easily misdiagnosed as a hardware fault.

**Step two, apply the 24 V drive power.** The motor needs 24 V to produce torque and turn.

> **CAN communication is powered independently by the USB-CAN adapter**, so with no 24 V you **can still read state and parameters**, but the motor reports an undervoltage fault (`ERR = 0x9`) and does not respond to motion commands. When debugging "the command was sent but nothing moves", **check 24 V first**.

**Without hardware**, you can use a virtual bus to verify the software environment first:

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

> There is no real motor on a virtual bus, so **the enable step times out** (`enable()` gets no feedback frame and raises `HardwareError` after its retries are exhausted). This is **expected behavior**, not a fault.

### Connecting and the minimal example (run read-only first)

```python
from litegrip import LiteGrip

with LiteGrip(channel="can0", mst_id=0x18) as gripper:
    state = gripper.get_state()
    print(f"position: {state.position_mm:.1f} mm")
    print(f"error code: 0x{state.error_code:X}")
```

Exiting the `with` statement calls `disconnect()` automatically (which calls `disable()` internally). This is the recommended pattern.

**Constructor arguments:**

```python
LiteGrip(
    channel: str = "can0",
    can_id: int = 0x08,
    mst_id: Optional[int] = None,
    canfd_mode: Optional[bool] = None,
    motor_type: MotorType = MotorType.DM4310,
    config: Optional[GripperConfig] = None,
)
```

| Parameter | Default | Description |
|------|------|------|
| `channel` | `"can0"` | CAN interface name |
| `can_id` | `0x08` | Motor CAN ID |
| `mst_id` | `None` | Feedback frame ID; `None` = auto-detect on connect (usually yields `0x18`) |
| `canfd_mode` | `None` | `None` = decide automatically from the interface MTU |
| `motor_type` | DM4310 | Motor model |
| `config` | `None` | Full configuration object; when `None`, the defaults of `GripperConfig()` are used (see Section 2.3.12) |

**Properties:**

| Property | Type | Description |
|------|------|------|
| `channel` / `can_id` / `mst_id` | - | Connection identity |
| `is_connected` | `bool` | Whether it is connected |
| `is_enabled` | `bool` | Whether it is enabled |
| `config` | `GripperConfig` | Current configuration object |

**The next step after the read-only example: load the calibration.**

> **Note**: **`connect()` does not load the calibration file.** It does only two things: open the bus and register the motor. The calibration must be loaded **explicitly** by the caller:
>
> ```python
> gripper.connect()
> gripper.load_calibration()      # load ~/.litegrip/litegrip_calibration.json
> gripper.enable()
> ```
>
> **Move without loading the calibration and the risk is yours**: at this point `config` is still the defaults of `GripperConfig()` (`pos_closed_rad=0.0`, `pos_open_rad=1.14`, `rad_to_mm=105.26`), and both the millimeter conversion and the position clamping run on this set of placeholder values; see Section 2.3.6 and Section 2.3.12. **These three placeholder values differ from unit to unit and must be replaced by calibration** [to be measured · B].

### Enabling, disabling, and fault handling

```python
gripper.enable()        # enable, with full initialization and feedback verification
gripper.disable()       # disable
gripper.clear_fault()   # clear driver faults
```

**The full `enable()` sequence**: disable → switch to MIT mode → enable → **wait for a feedback frame to confirm**. If the current error code is not `0x0` / `0x1`, it first calls `clear_fault()` automatically to clear the fault once.

**`enable()` returning `True` means a valid feedback frame has already arrived after the command was sent** (`ERR ∈ {0x0, 0x1}`); if 5 feedback retries still bring no confirmation it raises `HardwareError` - it never fakes success.

> **Note**: **`enable()` reporting success only says "the motor reports itself healthy"; it does not say "the fingers are gripped shut"**, nor that the position zero point is correct.

**`disable()` returning `True` only means the disable command was sent; it is not confirmed by feedback.** To confirm the driver is really disabled, read `ERR` in the status frame (`0x0` is the disabled state).

**`clear_fault()` clears driver fault codes only** (undervoltage `0x9` / overcurrent `0xA` / MOS overtemperature `0xB` / coil overtemperature `0xC`). The sequence is disable → clear the fault (`0xFB`) → re-enable → verify. **It handles driver fault codes only and has nothing to do with position.**

**There is only one interface for stopping:**

```python
gripper.stop()          # send a zero-torque frame (kp=0, kd=0, tau=0)
```

| `stop()` behavior | Description |
|----------------|------|
| Cuts the output | **No**. It only commands zero torque; the motor stays enabled and can be back-driven |
| Latches a fault | **No** |
| Can motion continue afterward | **Yes**, with no manual intervention |
| Return value | `None`. **It does not mean "it has stopped"** — when not connected or not enabled it is a no-op |

> **Note**: For a stop at the "cut the output" level, use `disable()` (or cut the 24 V directly).
>
> **Note**: **`stop()` does not return success or failure.** To confirm "it really stopped", the only way is to keep reading feedback frames and watch position and torque.
>
> **Note**: **Both `stop()` and `disable()` are software actions and cannot replace a hardware emergency stop.** A true power-cut emergency stop must be implemented in a hardware circuit.

**Safe shutdown pattern:**

```python
try:
    ...
finally:
    gripper.stop()          # zero torque
    gripper.disable()       # disable
```

### Motion control (open/close and position)

> **The interfaces in this section check only two things: connected and enabled.** If either is missing they raise `NotInitializedError`. **They do not check whether the calibration has been loaded** — with no calibration loaded they raise no error and keep running on the placeholder coefficients in the default configuration.

| Method | Target | Description |
|------------------------|--------------------------------------------|--------------------------------|
| `home()` | Module constant `GripperParams.POS_CLOSED_RAD` (`0.0 rad`) | **Does not read the calibrated value**; see the warning below |
| `open()` | `config.pos_open_rad` | The calibrated open endpoint |
| `close()` | `config.pos_closed_rad` | The calibrated closed endpoint; omitting `force_n` = pure position control |
| `goto()` | Absolute position (mm) | Converted to rad internally, then goes through `goto_rad()` |
| `goto_rad()` | Absolute position (rad) | The only externally facing entry point that clamps |
| `move_to()` | Absolute position (rad) | It is `goto_rad()`, just with a longer default duration |
| `move_at_speed()` | Constant linear velocity motion | The endpoint is clamped the same way |
| `move_at_speed_rad()` | Constant angular velocity motion | The endpoint is clamped the same way |
| `send_mit_frame()` | Send one MIT frame directly | Expert interface, **no clamping, no saturation check** |

**Common parameters** (when `kp` / `kd` are omitted, the values from `config` are used):

| Parameter | Default | Description |
|------|------|------|
| `kp` / `kd` | 100.0 / 2.0 | Position stiffness / damping |
| `duration` | See the signature | Motion duration (seconds) |
| `force_n` | `None` | Target gripping force (N); `None` = no feedforward torque |
| `dq_target` | `0.0` | Target velocity feedforward (rad/s), `goto_rad` only |
| `tau_feedforward` | `0.0` | Feedforward torque (N·m); `goto_rad` / `move_to` take it directly, `close` / `grasp` receive it converted from `force_n` |
| `speed_mm_s` | 30.0[not measured] | Linear velocity for `move_at_speed` (mm/s) |
| `speed_rad_s` | 0.5[not measured] | Angular velocity for `move_at_speed_rad` (rad/s) |

> The default values of `duration` are in the signatures below: `open` / `close` / `move_to` are 1.0 second, `goto` / `goto_rad` are 0.5 second.

**Full signatures:**

```python
home() -> bool
open(kp=None, kd=None, duration=1.0) -> bool
close(kp=None, kd=None, force_n=None, duration=1.0) -> bool
goto(position_mm, kp=None, kd=None, duration=0.5) -> bool
goto_rad(position_rad, kp=None, kd=None,
         dq_target=0.0, tau_feedforward=0.0, duration=0.5) -> bool
move_to(target_rad, kp=None, kd=None,
        tau_feedforward=0.0, duration=1.0) -> bool
move_at_speed(target_mm, speed_mm_s=30.0, kp=None, kd=None) -> bool
move_at_speed_rad(target_rad, speed_rad_s=0.5, kp=None, kd=None) -> bool
send_mit_frame(q, kp, kd, dq=0.0, tau=0.0) -> bool
```

Typical usage:

```python
with LiteGrip(channel="can0", mst_id=0x18) as gripper:
    gripper.load_calibration()      # load the calibration first
    gripper.enable()
    gripper.open()                  # open to the calibrated endpoint
    gripper.goto(60.0)              # move to 60 mm
    gripper.close()                 # close to the calibrated endpoint
```

> **Note**: **A target beyond the calibrated endpoint is silently clamped.** Inside `goto_rad()` it is
> `position_rad = max(pos_open_rad, min(pos_closed_rad, position_rad))`,
> and `move_at_speed_rad()` likewise clamps the endpoint to `[pos_open_rad, pos_closed_rad]`.
> **It raises no exception and does not tell you it clamped.** If you need "reject anything out of range" semantics, check before the call yourself.

> **Note**: **`home()` uses the module constant `0.0 rad`, not the calibrated closed endpoint.** The `zero_position_rad` (closed endpoint) in this machine's calibration file is a **rad value clearly greater than 0** (see this machine's calibration file for the exact value), so the `0.0 rad` target of `home()` lands on the **open side, very close to the open endpoint**, and the motor will drive almost all the way into the mechanical hard stop at the open end. **To return to the closed endpoint use `close()`; do not use `home()` as a "return to zero".**

> **Note**: **`send_mit_frame()` has no clamping and no range check at all.** It only checks "connected and enabled"; an out-of-range `q` is sent as is; `kp` / `kd` / `tau` outside the encoding range are silently saturated at the encoding stage to `[0, 500]` / `[0, 5]` / `[−10, 10]`. Unless you need to control single-frame timing yourself, use the high-level interfaces.

> **Note**: **Velocity is "duration distribution", not "velocity limiting".** `duration` only decides how long this run of frames lasts — frames are sent at 200 Hz (5 ms period) and the position target transitions smoothly over the whole duration. To actually cap the maximum velocity, use `move_at_speed()` / `move_at_speed_rad()`, which compute the target sequence from the given velocity.

### Units and conversion

**The SDK does not expose conversion methods.** The `mm ↔ rad` conversion is inlined in two places:

```python
# goto() (gripper.py:925)
position_rad = config.pos_closed_rad - position_mm / config.rad_to_mm

# get_state() (gripper.py:1281)
position_mm = (config.pos_closed_rad - position_rad) * config.rad_to_mm
```

That is, **a smaller `rad` means a wider aperture**; `pos_closed_rad` is the end with the larger value and `pos_open_rad` is the end with the smaller value.

**The conversion coefficient `rad_to_mm` is written by the calibration process** and equals "the stroke used for calibration (mm) ÷ the measured angular stroke (rad)". The value measured on this unit is:

> **Effective stroke 87.000 mm ÷ the angular stroke measured on this unit (rad) = this unit's `rad_to_mm`**. The numerator is `config.max_stroke_mm` and the denominator is the rad span measured during calibration; **both numbers differ from unit to unit**. For this unit's values see the calibration file shipped with the product and Section 2.2 of the Product Manual.

> **Note**: **`rad_to_mm` only affects "the millimeter values displayed and the millimeter targets"**; it does not move any boundary, because the `pos_closed_rad` / `pos_open_rad` used for clamping are rad values themselves and do not depend on `rad_to_mm`. A wrong coefficient only makes the millimeter numbers wrong.
>
> **Note**: **`position_mm` differs from the aperture measured with a caliper by 1.508 mm.** The SDK's mm zero point is at the fully closed mechanical limit, and the two fingers still have a 1.508 mm gap at that point. Caliper reading ≈ `get_position() + 1.508` (this expression is exact at the closed end and overestimates by about 1.5 mm at the open end; for the exact relation see Section 2.3.7).

### Reading state

```python
state = gripper.get_state(wait=True)
```

| `GripperState` field | Type | Description |
|---------------------|------|------|
| `position_rad` | `float` | Position (rad) |
| `position_mm` | `float` | Position (mm, converted with the conversion coefficient) |
| `velocity_rad_s` | `float` | Velocity (rad/s) |
| `torque_nm` | `float` | Torque (N·m) |
| `force_n` | `float` | **Estimated** gripping force (N) |
| `temperature_mos` | `int` | MOS temperature (°C) |
| `temperature_coil` | `int` | Coil temperature (°C) |
| `error_code` | `int` | Motor error code |
| `timestamp` | `float` | Sampling timestamp |

`get_state(wait=True)` waits up to 50 ms for one new feedback frame; `wait=False` returns the last cached state directly, which suits high-rate control loops.

**Derived properties:**

| Property | Description |
|------|------|
| `is_enabled` | Whether the motor is enabled (`error_code == 1`) |
| `is_error` | Whether a fault is present (`error_code` is neither 0 nor 1) |
| `is_moving` | Whether the velocity exceeds a small threshold (0.01) |
| `aperture_mm` | Aperture reading (**per-finger displacement**) |

> **Note**: **`force_n` is an estimate**, derived as `torque_nm × UnitConversion.NM_TO_N`, and `NM_TO_N = 10.0` is a **nominal conversion coefficient** (the source comment marks it `approximate`), not a calibrated one. **Until force calibration is complete, do not treat `force_n` as the real gripping force.**
>
> **Total aperture = `aperture_mm` × 2** (this field is per-finger displacement). Per-finger stroke 43.500 mm × 2 = total stroke 87.000 mm.

**Convenience read methods:**

| Method | Returns |
|------|------|
| `get_position()` / `get_position_rad()` | Position (mm / rad) |
| `get_force()` | Estimated gripping force (N) |
| `get_torque()` | Torque (N·m) |
| `get_error()` | Error code |
| `get_temperature()` | `(MOS temperature, coil temperature)` |
| `get_info()` | Device metadata (model, motor model, ID, firmware version, and so on) |

**State test methods:**

| Method | Returns |
|--------------------------------------|--------------------------------------------------------------|
| `is_moving()` | Whether the gripper is moving |
| `is_grasped()` | Whether the torque exceeds the grasp detection threshold (`config.grasp_torque_threshold`, default 0.5 N·m) [to be measured · C, can only be fixed after force calibration] |
| `wait_for_ready(timeout=5.0)` | Blocks until enabled and stationary; returns `False` on timeout |

**Polling and expert interfaces:**

| Method | Description |
|------|------|
| `poll(timeout_s=0.0) -> bool` | Polls one feedback frame and updates the internal state; returns `False` when not connected |
| `read_param(rid, timeout_s=0.5) -> float` | Reads a driver parameter by register ID |

> **Note**: **Feedback is request-driven.** The driver replies only after it receives a frame from the host — **merely listening on the bus receives no feedback at all**.
>
> **Note**: **For the `read_param` register table see Section 3.6.** Note carefully: `OC_Value` is a ratio, not amperes; the MIT quantization range of position / velocity / torque is not a protection threshold.

### Grasping and force control

```python
grasp(force_n=10.0, kp=150.0, kd=2.0,
      duration=3.0, stall_threshold=0.001, stall_cycles=5) -> bool
```

**Sequence**: push toward the closed endpoint with `kp` / `kd` → **compare the position increment every cycle** → once the increment is below `stall_threshold` for `stall_cycles` consecutive cycles it is judged "grasped", and the call then holds for 0.3 s with a **feedforward torque**.

> **"Adaptive" here means position stall detection, not torque detection.** The criterion is `abs(current position - previous cycle position) < 0.001 rad` and is independent of the torque reading.

| Return value | Meaning |
|------|------|
| `True` | A stall was detected (**includes gripping an object and also includes hitting the stroke endpoint**) |
| `False` | Still moving when `duration` expires, **or** not connected / not enabled |

> **Note**: **`False` only means a timeout.** After hitting the endpoint the position stops changing, so that is also judged a "stall" and returns `True` — **so you cannot use the return value to tell "gripped an object" from "hit the endpoint".** If you need to tell them apart, combine it with `get_position()` yourself.

> **Note**: **The force argument is not validated at all.** The first thing `grasp()` does is `tau_ff = force_n × 0.1` (`N_TO_NM = 0.1 N·m/N`, a nominal value), and it sends that as usual. `force_n=10.0` corresponds to a `1.0 N·m` feedforward, only one tenth of the torque encoding limit `10 N·m`.
>
> ```python
> gripper.grasp(force_n=0)      # position-only grasp: no feedforward torque
> gripper.grasp()               # default 10 N → 1.0 N·m feedforward, sent as usual
> ```

**`set_force(force_n, duration=0.3) -> bool`** — applies a gripping force at the current position (holds the position with `kp=150.0, kd=2.0` and adds a `force_n × 0.1` N·m feedforward for `duration` seconds).

> **Note**: **`set_force()` cannot tell "gripped an object" from "hit the mechanical endpoint"**, and it makes no check near either boundary. Confirm the position is safe yourself.
>
> **Note**: **The physical meaning of `force_n` is not calibrated.** `0.1 N·m/N` is a nominal conversion coefficient; **do not use it for safety decisions or load design until force calibration is complete**.

### Manual guidance (zero gravity)

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

### Calibration and zero point

**Three calibration methods:**

| Method | Driving force | How the limit is detected | Human needed |
|------|--------|---------------|--------|
| `calibrate()` | Motor | **Motor stall detection** (position increment below the threshold for consecutive cycles) | Attending in person |
| `calibrate_guided()` | Motor | Confirm each endpoint with Enter, or automatic motor stall detection | Press Enter at each endpoint |
| `calibrate_manual()` | Pushed by hand (zero gravity) | Pushed all the way by hand, extremes recorded | Hand-push throughout |

> **Note**: **The first two push all the way into the mechanical hard stop.** They step in one direction under motor power until the position stops changing (motor stall) and do not stop by themselves in between. Before running them, confirm the mechanical hard stops and the structure can take that force, and **someone must be present with a working hardware emergency stop**.
>
> **`calibrate_manual()` is recommended**: pushing all the way by hand applies no motor force to the mechanism and is the gentlest of the three.

```python
calibrate(kp=60.0, kd=2.0, step_rad=0.1,
          stall_delta=0.0003, stall_cycles=8, max_iter=30) -> CalibrationData

calibrate_guided(kp=60.0, kd=2.0, step_rad=0.08,
                 stall_delta=0.0004, stall_cycles=6, max_iter=40) -> CalibrationData

calibrate_manual(duration=30.0, settle_time=2.0, sample_interval=0.01) -> CalibrationData
```

`calibrate_manual()` steps: after the call the gripper goes "soft" → push it all the way closed by hand, then all the way open → repeat a few times → it returns when the time is up (or press Ctrl+C to end early and keep the readings taken so far).

**Saving and loading the calibration file:**

| Method | Signature and description |
|------|-----------|
| `save_calibration(path=None) -> str` | With `path=None` it writes `~/.litegrip/litegrip_calibration.json` (override with the `LITEGRIP_CALIB` environment variable) and **returns the absolute path written** |
| `load_calibration(path=None) -> bool` | With `path=None` it looks for the default file above first and falls back to the bundled `factory_calibration.json` if that is missing; returns `True` on success |

> **Note**: **`load_calibration()` does not validate the source in any way.** It only handles "the file does not exist" and "JSON parsing failed"; whatever the file says, it believes.
>
> **Recalibration is mandatory after replacing or repairing the gripper, replacing the motor, replacing a finger, or a collision or overload.**

**About the calibrated conversion coefficient (a known defect in the current implementation):**

The scale is computed as `rad_to_mm = stroke used for calibration (mm) ÷ measured angular stroke (rad)`, and the "stroke used for calibration" comes from:

| Entry point | Numerator value |
|------|---------|
| `calibrate()` | `config.max_stroke_mm`, **default `120.0`** |
| `calibrate_guided()` | **hardcoded `120.0`**; it does not even read `config` |
| `calibrate_manual()` | `config.max_stroke_mm`, **default `120.0`** |

> **The value convention for this cell is settled: use the "effective stroke", which on this unit is `87.000 mm`** [caliper re-measurement of the fully open aperture 87.000 mm, the same number as the effective stroke].
> That value has been written into this unit's calibration file as `max_stroke_mm`.
>
> **Reading convention (required reading)**: `87.000` is the **span of the SDK position `p`** (0 → 87.000), while the **actual aperture** span measured with a caliper is
> **85.492 mm** (open end 87.000, closed end 1.508). That is, `max_stroke_mm = 87.0` makes the SDK's "1 mm"
> **1.8 % larger** than a real millimeter (87.000 ÷ 85.492). **For millimeter-level accuracy, use the caliper span `85.492` as the numerator**,
> and after calibration check that `rad_to_mm = 85.492 ÷ measured rad span`.

> **Note**: **The default `120.0` is a placeholder stroke, not the stroke measured on this unit (87.000 mm on this unit).** If you calibrate with the default configuration, the `rad_to_mm` computed is **too large by a factor of 1.38 overall** (the ratio 87.000 → 120) and is written into the calibration file; from then on every millimeter reading and every millimeter-based threshold is off by 38 %, while the `travel_range_rad` cell in the file looks perfectly normal, so it is very hard to find afterwards.
>
> **Do this instead**: first measure the fully open aperture with a vernier caliper, set `max_stroke_mm` to the measured value (`87.000` on this unit, or `85.492` if you want the caliper span), and then calibrate; when calibration finishes, check that the `rad_to_mm` written equals "the numerator you entered ÷ the measured rad span".
>
> **Note**: These entry points raise `RuntimeError` only when `travel <= 0`; a `max_stroke_mm` of `0` or `120.0` **does not** raise an error.

### Configuration object

**`GripperConfig` fields (12 in total):**

| Field | Default | Description |
|------|------|------|
| `can_channel` / `can_id` / `mst_id` / `canfd_mode` | `"can0"` / `0x08` / `None` / `False` | Connection parameters |
| `kp` / `kd` | `100.0` / `2.0` | Position stiffness / damping (the default of each interface when omitted) |
| `pos_closed_rad` / `pos_open_rad` | `0.0` / `1.14` | The two ends of the stroke (**overwritten by the calibration file after calibration**) |
| `max_stroke_mm` | `120.0` (**placeholder value; `87.000` should be entered on this unit**) | Mechanical stroke (mm), **used only during calibration as the scale numerator**; see Section 2.3.11 |
| `rad_to_mm` | `105.26` [computed by the script after calibration] | Angle → millimeter conversion (**placeholder value when uncalibrated**) |
| `nm_to_n` | `10.0` | Torque → force conversion. **The current code does not read this field**; it actually uses the class constant `UnitConversion.NM_TO_N = 10.0`, so changing it has no effect |
| `grasp_torque_threshold` | `0.5` [to be measured · C, no basis, can only be fixed after force calibration] | The decision threshold of `is_grasped()` (N·m) |

> **Note**: **The default values of `pos_closed_rad` / `pos_open_rad` / `rad_to_mm` are placeholders, not this unit's real values.** The real values live in the calibration file and take effect only when you call `load_calibration()` explicitly (`connect()` does not do this).
>
> **Note**: **Do not command motion under the default configuration.** The clamping expression assumes "the closed end has the larger value", and the defaults are exactly the opposite (`pos_closed_rad = 0.0 < pos_open_rad = 1.14`), so `max(pos_open_rad, min(pos_closed_rad, x))` yields `1.14` for **any** `x` — that is, without a loaded calibration every target of `goto()` / `goto_rad()` is clamped to the same value, `1.14 rad`. **This is the most direct reason why you must call `load_calibration()` before commanding motion.**

### Preconditions and calling constraints

**The SDK performs only two precondition checks**: `_check_connected()` and `_check_enabled()`; when either is not satisfied it raises `NotInitializedError`.

| Interface | Connected | Enabled | Description |
|------|:---:|:---:|------|
| `connect` / `disconnect` | — | — | `disconnect()` first tries `disable()` |
| `enable` / `disable` / `clear_fault` | ● | — | |
| `stop` | — | — | **Not checked**. When not connected or not enabled it is a no-op and returns `None` |
| `send_mit_frame` | — | — | **Does not raise**. When a precondition is not satisfied it returns `False` directly |
| `poll` | — | — | **Does not raise**. Returns `False` when not connected |
| `home` / `open` / `close` / `goto` / `goto_rad` / `move_to` | ● | ● | |
| `move_at_speed` / `move_at_speed_rad` | ● | ● | |
| `grasp` / `set_force` | ● | ● | |
| `enter_zero_gravity` | ● | ● | |
| `exit_zero_gravity` | — | — | **Does not raise**. When not enabled it is a no-op |
| `calibrate` / `calibrate_guided` / `calibrate_manual` | ● | ● | |
| All `get_*` methods (including `is_moving` / `is_grasped` / `wait_for_ready`) | ● | — | `get_info()` reads static information and is not checked |
| `load_calibration` / `save_calibration` | — | — | Pure file I/O |
| `read_param` | ● | — | |

**Legend**: ● = required; — = not needed.

> **Note**: **The table above has only the two precondition columns "connected / enabled".** Motion still works without a loaded calibration (see the warning in Section 2.3.12), and force arguments are still sent — neither of these is among the checks.

### Core API quick reference

| Category | Interfaces |
|------|------|
| **Lifecycle** | `LiteGrip(...)`, `connect()`, `disconnect()`, `__enter__` / `__exit__` |
| **Enable and faults** | `enable()`, `disable()`, `clear_fault()`, `stop()` |
| **Motion** | `home()`, `open()`, `close()`, `goto()`, `goto_rad()`, `move_to()`, `move_at_speed()`, `move_at_speed_rad()`, `send_mit_frame()` |
| **Grasping and force control** | `grasp()`, `set_force()` |
| **Manual guidance** | `enter_zero_gravity()`, `exit_zero_gravity()` |
| **Calibration** | `calibrate()`, `calibrate_guided()`, `calibrate_manual()`, `save_calibration()`, `load_calibration()` |
| **State** | `get_state()`, `poll()`, `get_position()`, `get_position_rad()`, `get_force()`, `get_torque()`, `get_error()`, `get_temperature()`, `get_info()`, `is_moving()`, `is_grasped()`, `wait_for_ready()` |
| **Expert** | `read_param()`, `send_mit_frame()`, the `litegrip.can` subpackage |

**Public export list** (the `__all__` of `litegrip/__init__.py`, version 2.2.0):

```python
from litegrip import (
    __version__,
    # high-level interfaces
    LiteGrip,
    DEFAULT_CALIB,                    # default calibration file path
    # data models
    GripperState, GripperConfig, GripperInfo, GripperStatus, GripperMode,
    CalibrationData,
    # constants and enums
    GripperParams, UnitConversion, ErrorCode, DefaultParams,
    describe_error, DM_Motor_Type, Control_Mode,
    # exceptions
    LiteGripError, CommError, ConnectError, CommandError,
    CANTimeoutError, HardwareError, NotInitializedError,
    # subpackages
    can,
)
```

### Exceptions and error handling

The SDK has only **7** exception classes, all inheriting directly from `LiteGripError`:

| Exception | Triggered when |
|------|---------|
| `LiteGripError` | Base class of all SDK exceptions; can carry an `error_code` |
| `NotInitializedError` | An interface is called while not connected (`_check_connected`) or not enabled (`_check_enabled`) |
| `ConnectError` | Connection failure: the CAN interface cannot be opened, or motor registration fails |
| `CommError` | Communication failure: wrapped around an error raised by the low-level send/receive of position control or force control |
| `CANTimeoutError` | Bus read timeout |
| `HardwareError` | Hardware fault: enabling fails, fault clearing fails, the driver reports a fault |
| `CommandError` | Command error. **The current version keeps this class but no code raises it** |

**General error handling template:**

```python
from litegrip import (
    LiteGrip, LiteGripError, NotInitializedError,
    CommError, ConnectError, HardwareError, CANTimeoutError,
)

try:
    with LiteGrip("can0") as gripper:
        gripper.load_calibration()
        gripper.enable()
        gripper.goto(60.0)
except NotInitializedError as e:
    print(f"connection or enable state is wrong: {e}")
except ConnectError as e:
    print(f"cannot connect: {e}")
except CommError as e:
    print(f"communication error: {e}")
except HardwareError as e:
    print(f"hardware fault (0x{e.error_code:X}): {e}" if e.error_code else f"hardware fault: {e}")
except CANTimeoutError as e:
    print(f"no response on the bus: {e}")
except LiteGripError as e:
    print(f"other SDK error: {e}")
```

> **Note**: **These seven are the only exceptions.** An out-of-range target being clamped and force arguments not being validated both raise nothing.

## Other languages and software ecosystem

| Item | Status |
|------|------|
| **Python SDK** | Available (`litegrip` 2.2.0), the primary path in this document |
| **CAN communication protocol** | Public, see Chapter 3 — any language can implement it from the protocol |
| **Command-line examples** | 16 scripts under `examples/`, covering connection self-check, calibration, grasping, contact detection, force control, teleoperation, and bus diagnostics |

> **To use this from a non-Python language**: implement the MIT frame, the command frame, and the parameter frame directly from the protocol in Chapter 3. The SDK itself contains no proprietary protocol.

**Example scripts under `examples/`:**

| Script | Purpose |
|------|------|
| `basic.py` | Minimal example: connect, enable, open and close |
| `slow_open.py` / `slow_close.py` | Slow open / slow close |
| `cycle_test.py` | Cyclic open/close test |
| `can_diag.py` | CAN communication diagnostics |
| `dry_run.py` | Dry run on the `vcan0` virtual bus |
| `calibrate.py` / `calibrate_manual.py` | The two calibration flows |
| `force_control.py` / `force_monitor.py` | Force control and force monitoring |
| `wiggle.py` / `test.py` | Back-and-forth wiggle / quick self-test |
| `contact_grasp.py` | Grasping that stops on a **torque threshold** (distinguishes "gripped an object" from "hit the endpoint") |
| `travel_calibrate.py` | Stroke calibration: press both ends against the mechanical limits, then write the new endpoints back to the calibration file |
| `zenoh_master.py` / `zenoh_slave.py` | Zenoh teleoperation master/slave examples (requires `eclipse-zenoh`) |

## FAQ and technical support

### Q&A

Q: Which platforms does the SDK support? A: **Linux only**, with kernel support for SocketCAN. The library code itself uses only the Python standard library, but `pip install` also installs `eclipse-zenoh` (used only by the teleoperation examples).

Q: Why must `fd off` be added when configuring CAN? A: Because this product uses **classic CAN**. Configuring it as CAN FD makes **communication completely impossible** — and that symptom looks a lot like "24 V not connected", so it is easily misdiagnosed as a hardware fault.

Q: Why do I receive nothing when I listen on the bus? A: **Feedback is query-based** — the driver sends a frame back only after it receives a frame from the host computer. **Passive listening will never receive any frames**; you must send a frame first.

Q: What do I do after connecting? A: **Call `load_calibration()` first, then `enable()`.** `connect()` does **not** load the calibration file automatically; until it is loaded, `config` still holds placeholder values (`rad_to_mm=105.26`), and neither millimeter readings nor millimeter targets can be trusted.

Q: A function returned `True`; does that mean it succeeded? A: It depends on the function. `enable()`'s `True` is backed by a feedback frame (and a failure raises `HardwareError`), so it is trustworthy; `disable()`'s `True` **only means the command was sent, not confirmed**; a motion interface's return value only means "this run of frames was sent", **not that the mechanism has reached its target**. To tell whether it has arrived, read `get_state()`.

Q: Why does the enable interface return success when the motor is not actually enabled? A: If the feedback has `ERR = 0x0`, the driver is still disabled — the motor then accepts position commands but **outputs no torque**, which shows up as "the command was sent, but the mechanism does not move". First confirm that 24 V is connected and that `enable()` did not raise `HardwareError`.

Q: The mechanism does not move after I send a command from the menu? A: Check in order: (1) whether 24 V is connected (`ERR = 0x9` means undervoltage); (2) whether `enable()` succeeded; (3) whether the target position equals the current position; (4) whether `kp` is 0.

Q: I want the gripper to "raise an error when the target is out of range". How? A: `goto_rad()` / `move_at_speed_rad()` **silently clamp** an out-of-range target and raise no error. If you want it rejected, check before the call yourself: read `config.pos_closed_rad` / `pos_open_rad`, compare with the target value, and only then decide whether to send it.

Q: Why does `goto(60.0)` not reach 60 mm? A: Three possibilities: (1) the calibration was not loaded, in which case the default configuration clamps **every** target to the same value (see Section 2.3.12); (2) the target lies beyond the calibrated endpoint, so it is clamped to the endpoint; (3) `duration` is too short, so the mechanism is still in transit when the frame sequence ends.

Q: Why does `close()` not stop at the force I set? A: `force_n` is only converted into a feedforward torque of `force_n × 0.1 N·m`; it **performs no validation and does not guarantee that the gripping force equals the set value**. The actual gripping force depends on the object's stiffness, the position, and `kp`.

Q: Does `grasp()` returning `False` mean something is broken? A: No. `False` means **timeout** (the position was still changing when `duration` elapsed). Also note the opposite case: **hitting the stroke endpoint also counts as a "position stall" and returns `True`** — so `True` does not mean "the object was grasped".

Q: What does `stop()` return? A: **It returns `None`**. That does not mean "it has stopped": when not connected or not enabled it is a no-op, and after the zero-torque frame is sent the motor stays enabled and can be back-driven. To cut the output, use `disable()` or remove the hardware power.

Q: The finger has stopped outside the stroke; what do I do? A: Drive it back with an ordinary motion interface — `goto_rad()` clamps the target to within the calibrated endpoints, so "coming back from outside" is **naturally allowed**. If the mechanism has already jammed or is stuck, do not keep applying force; clear the interference by hand first.

Q: If I let go after `enter_zero_gravity()`, will the finger drop? A: **It will move.** Zero gravity mode means the motor outputs no torque; gravity and friction decide the position. To hold it in place, call `exit_zero_gravity()` after you let go.

Q: What happens if I push past either end of the stroke in zero gravity mode? A: There is no indication of any kind — that mode does not check position. Only when you later call an ordinary motion interface is the target clamped back to the calibrated endpoints.

Q: During calibration, why does it keep pushing after it hits the hard stop? A: `calibrate()` and `calibrate_guided()` **detect the limit by motor stall**: they step in one direction until the position increment stays below the threshold for several consecutive cycles, and they do not stop on their own in between. Before running it, confirm that the mechanical hard stop can take that force, and prefer `calibrate_manual()`.

Q: The calibrated `rad_to_mm` is wrong (millimeter readings about 38% too large)? A: Check `max_stroke_mm`. Its default value is the placeholder value `120.0`, while the stroke measured on this machine is `87.000 mm`; `calibrate_guided()` even **hardcodes it to 120.0**. Calibrating with the default writes a scale that is wrong by a factor of 1.38 into the calibration file. **Before calibrating, measure the fully open aperture with a caliper and write it into `max_stroke_mm`.**

Q: Why does `home()` not return to the closed end? A: `home()` sends the module constant `GripperParams.POS_CLOSED_RAD = 0.0 rad`; it **does not read the calibrated value**. The closed endpoint calibrated on this machine is a **rad value clearly greater than 0** (see this machine's calibration file for the exact value), so `0.0 rad` lands on the **open side**. **To return to the closed end, use `close()`.**

Q: The position reading differs from the caliper measurement by 1.5 mm? A: Normal. The SDK's mm zero point is at the **fully closed mechanical limit**, and the two fingers still have a 1.508 mm gap there. Caliper reading ≈ `get_position() + 1.508` (this formula is exact at the closed end; at the open end it overestimates by about 1.5 mm; for the exact relation see the reading convention in Section 2.3.7).

Q: The `tau` reading is always slightly smaller than what I set? A: Normal. MIT frames use **truncating** encoding (rounding down), so the quantization error is one-sided: `decoded value − commanded value` falls in the interval `(−1 LSB, 0]`, and it is **never greater than** the value you set.

Q: Does setting `kp` / `kd` to 1000 raise an error? A: No. At encoding time they are **silently saturated** to `[0, 500]` / `[0, 5]`, and `tau` is saturated to `[−10, 10] N·m`; the caller receives no indication at all.

Q: Reading `OC_Value` gives 0.8; is that 0.8 A? A: **No.** It is a **ratio**, meaning 80%.

Q: Are `PMAX` / `VMAX` / `TMAX` my protection thresholds? A: **No.** They are the **MIT quantization range** of the frame fields (the range definition) and must not be used as safety limits for position / velocity / torque. **The real velocity protection is in `MAX_SPD`.** [to be measured · B, the SDK never reads these three registers back and uses a hardcoded range, so it needs verification by reading back]

Q: Can I control it from two host computers at the same time? A: **No.** You must guarantee a **single CAN master** and enforce mutual exclusion in software. With multiple masters running concurrently, the commands overwrite each other.

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
> **To be measured**: the ranges the SDK uses in this section are **hardcoded** `±12.5 / ±30 / ±10` (see `litegrip/can/protocol.py`), and **the code never reads RID 21/22/23 back**, so it cannot be asserted that they match the actual values in this motor's registers [to be measured · B, verify by reading back with `scripts/read_driver_limits.py`].

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
| Driver communication timeout | 0.4 s [to be measured · B, verify by reading back RID 9] | After the timeout the driver **exits the enabled state automatically** |

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

`GripperState` has the full field list given in Section 2.3.8. Three fields bear directly on status decisions:

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

The SDK has only **7** exception classes, and all of them inherit directly from `LiteGripError`:

| Exception | Base class | Meaning |
|------|------|------|
| `LiteGripError` | `Exception` | base class of all SDK exceptions; may carry an `error_code` |
| `NotInitializedError` | `LiteGripError` | the interface was called while not connected or not enabled |
| `ConnectError` | `LiteGripError` | connection failed (the CAN interface cannot be opened, motor registration failed) |
| `CommError` | `LiteGripError` | communication error (low-level send or receive failed for position control / force control) |
| `CANTimeoutError` | `LiteGripError` | bus read timed out |
| `HardwareError` | `LiteGripError` | hardware fault (enable failed, fault clear failed, the driver reported a fault) |
| `CommandError` | `LiteGripError` | command error. **Defined, but no code in the current version raises it** |

> **Note**: There are only the seven exception names in the table above. Clamping an out-of-range target and skipping validation of force parameters -- neither raises an exception (see Section 2.3.6 and Section 2.3.9).

## Error handling guidance

1. `NotInitializedError`: call `connect()` first, then `enable()`; if it is already connected, check whether `enable()` succeeded.
2. `ConnectError`: check whether the interface is up, whether `fd off` is configured, and whether `can0` exists. **Do not retry until it succeeds** — look at the cause first.
3. `CommError`: check the cabling, the terminating resistors, and the CAN FD setting.
4. `CANTimeoutError`: check whether 24 V is connected; check whether you are only listening and never sending.
5. `HardwareError`: work through the error codes one by one; **for overtemperature and overcurrent, stop the unit and let it cool down first, then investigate the load**. When enable fails, first confirm that 24 V is connected and that `ERR` is not `0x9`. Reading the Chinese "unknown error" means the driver reported a fault code the SDK does not parse; consult the driver's **indicator LEDs**.
6. `CommandError`: the current version never raises it; if you see it in your environment, the version in use does not match this document.

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
| | the command frame went to `0x7FF` | command frames and MIT frames must go to `0x08` (see the ID assignment table in Chapter 3) |
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
| the reported `tau` is slightly below expectation | truncating quantization | **normal**, see Chapter 3 |
| reading the 0.8 of `OC_Value` as 0.8 A | it is a ratio, meaning 80% | see Section 3.6 |
| several units interfering with each other | several CAN masters at once | **keep a single master**; make the software layer mutually exclusive |
| the position reading is 1.5 mm lower than the caliper | the SDK zero point is at the closed mechanical limit | caliper reading ≈ `get_position() + 1.508` |

**If you cannot resolve the problem yourself**, record the following information and contact us: product model and serial number, SDK version, Python version, operating system and kernel version, CAN interface configuration, the full exception message and stack trace, and the output of `examples/can_diag.py`.

---


> **End of document** If you have questions or need more information, contact the NEXFORM ROBOTICS technical team.
