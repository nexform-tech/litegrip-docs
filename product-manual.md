# Preface

LiteGrip is an adaptive two-finger parallel gripper that NEXFORM ROBOTICS designed for research and education, AI robot development, and lightweight industrial automation. It uses direct motor drive and an adaptive grasping mechanism, with an effective stroke of 87.000 mm. The gripper communicates with the host computer through a USB-CAN adapter (classic CAN, 1 Mbps), and ships with a Python SDK, the CAN Communication Protocol Manual, and the calibration file for this unit. It suits tasks such as grasping, transferring, loading and unloading, sorting, and algorithm validation.

## Hardware components

The composition of the standard delivery kit and the accompanying equipment is as follows (for the included accessories and the packing list, refer to the Packing List shipped with the product):

| No. | Item | Description |
|------|------|------|
| 1 | LiteGrip gripper body | Two-finger parallel gripper, including the drive motor and the fingertips |
| 2 | CAN terminating resistor | Required external device, one 120 Ω terminating resistor at each end of the bus |

## Units

The units of physical quantities used in this document and in the SDK are as follows:

| Parameter | Unit | Description |
|------|------|------|
| Aperture / position | mm | millimeter |
| Motor angle | rad | radian |
| Velocity | mm/s, rad/s | millimeters per second, radians per second |
| Torque | N·m | newton meter |
| Gripping force | N | newton |
| Temperature | °C | degrees Celsius |
| Voltage | V DC | volt (DC) |

**Aperture reading convention**: one physical aperture has three representations, and **their zero points and directions all differ**; mixing them is the most common cause of wrong numbers.

| Representation | Fully closed | Fully open | Value as it opens |
|---------|---------|---------|-----------|
| Motor angle `r` (rad) | **see the calibration file shipped with the product** | **see the calibration file shipped with the product** | **decreases** |
| SDK position `p` (mm) | 0 | **87.000** (= effective stroke) | increases |
| **Actual aperture** (mm) | 1.508 | **87.000** | increases |

> **Unless stated otherwise, "mm" in this document always means "actual aperture"** (the true distance between the inner faces of the two fingers), because that is the quantity a caliper can measure directly.
>
> **The position the SDK returns is `p` from the table above, not the actual aperture**; on the closed side the two differ by a 1.508 mm closing gap: `actual aperture ≈ p + 1.508`. See Section 2.3.7 of the Software Development Manual for details.
>
> **rad values are not a product specification.** The assembly phase between the motor and the gripper mechanism **differs from unit to unit**, so the rad endpoints differ on every gripper. Always use **the calibration file shipped with that unit** — this manual states no rad numbers for any sample unit.

## Safety

### Overview

This section describes the safety principles and standards you must follow when using the LiteGrip gripper and its system. Before installation and use, you must read this manual carefully, and you must understand and strictly follow any content marked with a warning symbol. Gripper systems carry potential hazards such as gripping, collision, and falling; users must fully recognize the operating risks and use the SDK or control software only after training.

### Safety symbols

Safety notes in other sections of this manual use the symbols below (for the graphics, refer to the labels shipped with the product):

- Danger: for hazardous situations that may cause death, personal injury, or severe equipment damage.
- Warning: for hazardous situations that, if not avoided, could cause death, personal injury, or severe equipment damage.
- High temperature: for hazardous situations with hot parts, where contact may cause burns or equipment damage.
- Caution: for general warnings that, if not avoided, may cause personal injury or equipment damage.

### Safety precautions

Before the first power-up of the gripper or the gripper system, you must understand and follow the basic information below.

#### Gripper handling precautions

1. Install the gripper body and the electrical equipment as this manual requires. The mounting surface must be flat and rigid enough, and the fastening bolts must carry an even load.
2. Before first use, have a qualified person perform a preliminary inspection of the gripper and the protection system, and test every safety function (hardware emergency stop, mechanical hard stop, enable state).
3. Before use, check that the equipment is intact and mounted securely, and confirm that the fingers' motion range holds no obstructions, no people, and no cables that could be pulled in.
4. **You must provide a hardware emergency stop loop whose action does not depend on CAN communication or host software**; **you must provide a mechanical hard stop** as the last line of defense.
5. Read the documentation carefully before you develop or debug with the SDK or the host computer, and make sure the input parameters (target position, velocity, gripping force) are correct. For the first motion, use a low velocity and a conservative stroke.
6. **This product has no power-off self-locking.** After disable or abnormal power-down, the motor no longer outputs a holding torque and the gripper may move under gravity or an external force. If the application does not allow movement after power-off, **you must add a separate mechanical holding device**.
7. If an accident or an abnormal condition occurs during operation, press the hardware emergency stop and cut the power immediately, then investigate the problem.
8. Unauthorized personnel must never modify this unit's calibration file, the motor registers, or the host-side limiting parameters. The modified stroke endpoints and conversion coefficients directly affect position control; see Section 2.2 and Section 2.3.11 of the Software Development Manual for details.
9. Before installation, maintenance, or cleaning, **you must disconnect the 24 V power supply and confirm that power is off**.

#### Personnel safety

1. Users must read the Product Manual carefully and know the safe, standard operating procedure and how to handle errors.
2. While the equipment is running, the fingers may be waiting for a command even when they look stopped, so treat the gripper as still in motion.
3. Define the motion range of the gripper and the end tool and set up a safe working zone; **no person may enter the gripper's motion range while it is running**.
4. Inspect the gripper regularly to keep the mounting bolts and the fingertips from loosening.
5. In manual teaching (zero gravity mode) the motor outputs no torque, and **the mode itself does not hold position**, so the fingers move under gravity or an external force. To stop at a position, **exit zero gravity mode** after you let go. Keep the moving inertia of the fingers in mind and avoid injury from a sudden loss of force.
6. During debugging and calibration, **someone must be present to supervise**, and the hardware emergency stop must be available.

### Responsibility and standards

The gripper can form a complete system with other equipment (robot arm, fixtures, sensors, and so on), and this document does not cover all of the design, installation, and operation of that complete system. The safety of installing the complete system depends on how it is integrated; users must carry out a design and installation risk assessment for the complete system under the laws, regulations, and safety standards of their country or region, and take the corresponding protective measures.

Starting to use this gripper means you have read, understood, and accepted all the terms of this manual and of the safety information. Users undertake to be responsible for their own actions and their consequences, and to use the gripper only for legitimate purposes. We accept no liability for personal injury, accidents, or property damage caused by violation of the usage requirements or by force majeure. Users must, without limitation: assess the risks of the complete system, write operating procedures, establish safety measures, confirm that the system design and installation are correct, and not modify the safety measures on their own.

### Risk assessment

A risk assessment must consider every potential contact between a person and the gripper under normal use and foreseeable misuse, for example:

- The risk of fingers being pinched by the gripper fingers;
- The risk of impact between the gripper and the robot arm end or the fixtures;
- The risk of a workpiece falling because it is not gripped securely or the load is out of range;
- The risk of handling sharp workpieces or hot workpieces;
- The risk of **the gripper losing its holding torque and the workpiece coming loose after power-off or disable**;
- The risk of software failure (a frozen process, a dropped CAN connection, a host computer fault) leaving the gripper to keep executing a motion command.

Through the risk assessment, users must judge whether the relevant hazards constitute an unacceptable risk and take the corresponding measures. The gripper is not suitable for people who lack the guidance of a qualified professional or who do not have full civil capacity.

> **Note**: **The shipped SDK does not check for out-of-range targets.** It only **silently clamps** a target beyond a calibrated endpoint to that endpoint (neither raises an error nor reports one); it **does not** reject out-of-range commands, **does not** latch a fault, and **does not** validate force parameters. During operation, a command may stay in range while the actual position goes out of range — inertia, control cycle delay, communication delay, and encoder error all make the actual position exceed the expected one. **The integrator must implement limiting on the host computer; the hardware emergency stop and the mechanical hard stop are the last line of defense.**

# Technical specifications

> **This chapter lists only the specification items the customer needs for selection and use**; it does not include internal parameters that matter only for design or calibration,
> **nor does it include items that are not yet finalized and are not yet released externally**.
> For items still marked **to be measured**, the meaning is "**the item exists and must be measured, but the value has not been measured yet**"; it does not mean the item does not exist, nor that it can be left unmeasured.
> Until these items are measured and released, **do not use them for selection calculations, load design, or safety assessment**.
>
> For the complete list, including internal design values, measurement methods, and factory inspection items, see the Parameter Document, Chapter 8.

## General specifications

| Parameter name | Parameter |
|--------|------|
| Product name | LiteGrip adaptive two-finger parallel gripper |
| Structure | Adaptive two-finger parallel gripper |
| Drive method | Direct motor drive |
| Motor model | DM-J4310-2EC (MIT mode) |
| Gear ratio | 10 : 1 (gearbox built into the motor, no additional reduction) |
| Communication | Classic CAN, 1 Mbps |
| Operating voltage | 24 V DC (nameplate rating) |
| **Effective stroke** | **87.000 mm** (SDK position `p` 0 ~ 87.000; caliper actual aperture 1.508 ~ 87.000 mm) |
| **Per-finger stroke** | **43.500 mm** (= effective stroke ÷ 2) |
| Working stroke | **0 ~ 87.000 mm** (the entire stroke is usable, with no internally disabled region; by caliper actual aperture it is 1.508 ~ 87.000 mm) |
| Power-off self-locking | **None** (holding torque is lost when power is removed) |
| No-load starting torque | 0.198 ~ 0.222 N·m (measured on a single prototype, 2026-09-16) |
| Total mass | **0.483 kg**[A, measured with a scale, 2026-09-28; includes motor, cable, fingertips, and mounting parts] |

> **How "effective stroke" is measured**: with the drive force removed, push the two fingers together and pull them apart by hand to the two **extreme positions** (the open end rests against the mechanical hard stop; the closed end is the two fingers touching, with **no hard stop**), and measure between the inner faces of the two fingertips with a digital caliper. The mean of 5 readings at the closed end is **1.508 mm**, and the open end is **87.000 mm**.
>
> **"Effective stroke 87.000 mm" uses the SDK scale convention (`p` from 0 to 87.000)**. If you express the same stroke span as a caliper reading, the span is **85.492 mm** — what is missing is exactly the 1.508 mm gap at the closed end. Both conventions are stated in Section 2.2; **do not mix them**.
>
> **Note**: **The no-load starting torque is a record of the starting torque corresponding to no-load static friction. It is not the gripping force, not the continuous torque, and must not be used as a torque cap.**

## Stroke and position parameters

**Stroke (SDK position `p`): 0 ~ 87.000 mm.** `p = 0` is the fully closed end and `p = 87.000` is the fully open end — in between there is **no disabled region**; the whole stroke is usable.

> **The two conventions must be stated clearly (the same stroke span, two different numbers)**:
>
> | Convention | Closed end | Open end | Span |
> |---|---|---|---|
> | **SDK position `p`** | 0 | 87.000 | **87.000 mm** ← the "effective stroke" of this manual |
> | **Caliper actual aperture** | 1.508 | 87.000 | **85.492 mm** |
>
> The **1.508 mm** difference is exactly the gap that still remains between the two fingers when fully closed: `actual aperture ≈ p + 1.508`.
> **"Effective stroke 87.000 mm" is the SDK scale convention**, not a span measured with a caliper; the two differ by 1.8 %.
>
> **The rad value is not a product specification.** The assembly phase between the motor and the gripper mechanism **differs from unit to unit**, so **the rad endpoints differ for every gripper**; you must use **the calibration file shipped with that unit**, and must not copy the numbers of any prototype. The `pos_closed_rad` / `pos_open_rad` and `rad_to_mm` used inside the SDK are all in the calibration file shipped with the product; **this manual does not state specific numbers**.
>
> **The conversion coefficient `rad_to_mm` = the stroke used for calibration ÷ the rad span in this unit's calibration file**; it likewise **differs from unit to unit, and the value is in the calibration file shipped with the product**; a wrong coefficient only makes the displayed number wrong, and does not change the position of the calibrated endpoints.
>
> **Note**: **The calibration file must match that unit.** If the calibrated endpoints are found to be **wider than the mechanism's actual reachable range** (that is, a command can drive outside the mechanism), the calibration file is the wrong one or has become invalid — in that case the position target will be clamped outside the mechanism, and **the motor will keep pushing against the endpoint and never reach position**. If this happens, stop operation immediately and recalibrate.

**Sign convention**: for the motor angle, **a larger value = the closing direction**, a smaller value = the opening direction; `dq > 0` and `tau > 0` mean the closing direction.

> **Note**: When a position target exceeds the calibrated endpoint, the SDK **silently clamps** it to the endpoint — it neither raises an error nor gives any indication. **"Commands must not go out of range" must be implemented by the integrator in the application layer** (see the Software Development Manual, Section 2.3.6).
>
> **Note**: **The two endpoints are different in nature, and neither is "hard limit protection".** The table below gives the **observation** obtained by pushing the gripper by hand in a zero gravity state and recording the motion extremes.
>
> | Direction | Mechanical hard stop? | Measured evidence |
> |---|---|---|
> | **Opening (tension)** | **Yes** | At two levels of push force, it springs back to the same position after the force is removed (difference **0 counts**) |
> | **Closing (pressure)** | **No** | After the force is removed the two fingers **spring apart by about 72 counts (≈ 2 % of full stroke)** before they stop — this is the two fingers **colliding in contact**, held by the mechanism's elasticity, not hitting a hard stop |
>
> **Consequence**: **There is no hard limit protection in the closing direction.** Continuously issuing close commands = **continuous pushing against the stop**; the mechanism will not "stop when it hits the hard stop". This direction can only be covered by the SDK's **torque cap** (factory default **10.0 N·m**). When you need to hold a grip for a long time, use the **torque control** of `grasp()` / `close(force_n=...)`; do not let a position command keep pushing against the closed end.

## Grip and load capacity

> **This section is the most important one for selection.**
>
> **The values in this section fall into three categories; check the tag when you cite them**: **[A, measured]** = measured on this unit with weights / a push-pull gauge / a scale,
> valid only for the **test piece, contact surface, and pose** at that time; **[recommended value]** = a level we chose from the measured values, **not a measurement**;
> **[to be measured]** = the item exists and must be measured, but the value has not been measured yet. **A missing entry does not mean the item does not exist.**

| Item | Specification |
|------|------|
| Maximum per-finger gripping force | **20 N**[measured, 2026-09-28; = total two-finger gripping force ÷ 2] |
| Total two-finger gripping force | **40 N**[measured, 2026-09-28. In another test, the reading from gripping a scale with the gripper was **4500 g ≈ 44.1 N**; the two readings are of the same order of magnitude and differ by about 10%, and the difference comes from the measurement method and the sensor update rate; **take 40 N as the reference**] |
| Recommended working gripping force | **20 N**[recommended value: 50% of the total gripping force; do not use at the maximum gripping force for long-term continuous operation] |
| Rated load | **2 kg**[measured with weights, 2026-09-28; see the notes below for the pose and test piece] |
| Maximum short-term load | **3 kg**[measured with weights, 2026-09-28; only short-term holding is guaranteed] |
| Allowable static load in the vertical direction Fz | **20 N**[measured with weights, 2026-09-28] |

> **Per-finger force and total two-finger force must not be mixed up**; when selecting, confirm which of the two values you are citing.
>
> **All the load values above are the result of "friction holding", not structural strength.** How heavy an object can be lifted depends on both the gripping force and the **friction coefficient**
> (`mass that can be lifted = μ × total two-finger gripping force ÷ 9.81`). The load values therefore **hold only for the test piece, contact surface, and pose that were measured** —
> change the workpiece surface and the value changes. When selecting, re-verify against your actual workpiece, or ask us for the test records.
>
> **The rated load cannot be derived from the motor torque**; it must be measured. **This product has no self-locking when power is removed**; if the application does not allow release after power loss, you must add a mechanical holding device.

## Motion performance

| Item | Specification |
|------|------|
| Recommended upper limit of open/close velocity (derived value) | 28.39 mm/s (opening) / 42.72 mm/s (closing) — **the SDK does not implement this speed limit**
| Position resolution | **0.0242 mm** (encoder resolution)[derived value: 1 position count (3.8147 × 10⁻⁴ rad) × this unit's `rad_to_mm`; **the conversion coefficient differs from unit to unit**, and this unit's value is in the calibration file shipped with the product] |
| Absolute position accuracy | **0.5 mm** |
| Repeatability | **0.5 mm**, acceptance criterion ≤ 0.5 mm |

> **The velocities in the table above are recommended values derived by the Parameter Document using a "stopping distance model"; they are not measured data, and they are not the gripper's own speed limit.** The shipped SDK **does not implement this model** — it will not slow down automatically near an endpoint, nor will it reject or truncate the velocity value you supply; instead it converts the velocity you give and sends it as-is (see the Software Development Manual, Section 2.3.6). These two numbers therefore **can only serve as design input when the integrator limits the speed itself**, and **until they are measured, the velocities in this section must not be used for safety assessment**.
>
> **Position resolution is the encoder resolution, not repeatability.** The latter is affected by mechanical backlash, friction, control gain, and other factors; treat it as a design target when you cite it.

## Electrical specifications

| Parameter name | Parameter |
|--------|------|
| Rated voltage | 24 V DC (nameplate) |
| Allowed voltage range | **15 ~ 32 V** (source: drive motor manual, 24 V version)[Note: these are the **undervoltage / overvoltage protection trigger points**, not the range recommended for long-term operation; |
| Undervoltage protection point | 15 V |
| Overvoltage protection point | 32 V |
| No-load current | **0.037 A** |
| Rated current | **3.1 A** |
| Peak current | **16.5 A** |
| Control / feedback period | 200 Hz |
| Motor overtemperature protection point | 100 °C |
| Communication dropout protection | Automatically exits enable after 0.4 s |
| Feedback status items | Position, velocity, torque, temperature, error code |
| Status feedback mode | **Polled** (responds after receiving a command frame); passive listening is not supported |

> **Note**: **The driver's overcurrent protection threshold is a ratio, not amperes.** The register reads `0.8`, meaning 80%; do not enter it as 0.8 A in the specification table.
>
> **Note**: **The driver's "position / velocity / torque MIT quantization range" defines the range of an MIT protocol field; it is not a protection threshold.** Treating it as a safety cap on torque or velocity is wrong.
>
> **Note**: **The communication timeout protection can be disabled.** Once disabled, on a dropout the motor will **hold the last torque command**, and the mechanism will not stop on its own. Unless a clear safety assessment concludes otherwise, do not disable this protection.

## Mechanical and environmental specifications

| Parameter name | Parameter |
|--------|------|
| Overall dimensions (length × width × height) | **150 × 85 × 170 mm** |
| Fingertip dimensions (length × width × thickness) | **84 × 60 × 22 mm** |
| Operating temperature range | Coil overtemperature protection point 100 °C, driver board overtemperature protection point 120 °C |

> **Note**: **This manual does not provide the mounting interface dimensions** (flange standard, mounting hole positions, threads, allowable screw length, recommended tightening torque). **If you need to mount the gripper on a robot arm end or a custom bracket, contact us first for the interface data.**
>
> **Note**: **Do not claim any IP rating externally before certification.** Contact us before using the gripper in an environment with dust, moisture, or cutting fluid.


> **Note**: **This manual does not provide cable and connector specifications** (specification / length / minimum bend radius, connector model / pin definitions, cable exit position and direction). **Do not make cables or buy connectors yourself** — contact us if you need them.
>
> **Note**: **None of CE, RoHS, REACH, or the IP protection rating has been certified**; do not claim compliance externally until they are.

## Selection guidance

**First confirm applicability:**

| Suitable | Not suitable |
|------|--------|
| Grasping, transferring, loading/unloading, and sorting of small and medium-sized **rigid** objects | High-temperature objects, sharp objects |
| | Applications requiring **precise gripping force** (before force calibration is complete) |
| | Applications requiring **power-off holding** (this product has no self-locking) |
| | Dusty, humid, or corrosive environments (IP rating not certified) |

**Confirm the following in order when selecting:**

| # | Check | Basis for judgment |
|---|--------|---------|
| 1 | Object size | Whether it falls within the working stroke **0 ~ 87.000 mm** (SDK position convention) |
| 2 | Object weight | **Load capacity is under 3 kg**; contact us for a case-by-case assessment |
| 3 | Is release after power loss acceptable | **This product has no power-off self-locking**; if it is not acceptable, add a mechanical holding device |

**Values that must not be used when selecting** (these are design values or historical values, not measured specifications):

| Value | Why it must not be used |
|------|-------------|
| No-load starting torque 0.198 ~ 0.222 N·m | It is **no-load static friction**, not the gripping force and not a torque cap |
| Total torque cap 10.0 N·m | A design choice, not calibrated against a real load |
| The driver's "torque MIT quantization range of 10 N·m" | It is the **quantization range** of a protocol field, not a protection threshold |
| Absolute position accuracy | **0.5 mm** |

> **The torque ceiling of the drive motor (order-of-magnitude reference)**: the manufacturer-rated nominal torque of the DM-J4310-2EC used in this product is **3.5 N·m**,
> and the peak torque **12.5 N·m**.
> — The gripper's current design value is **1.0 N·m**. **No torque reading above 10 N·m can ever appear** (the feedback `tau` field is decoded as ±10 N·m, so the range itself is capped at 10).

> **A complete selection Q&A table is in Section 4.7.1.**

# Electrical interface

## Electrical safety

1. Do not connect or disconnect the gripper's CAN or power cables while power is applied. Cut the 24 V supply before installation and maintenance work.
2. **Check the power polarity; reversing it can damage the equipment.** Confirm the polarity with a multimeter before powering up.
3. Protect the unit from water and moisture. If water gets in, cut the power immediately and contact support.
4. The 24 V supply must provide overcurrent and short-circuit protection.
5. The supply must meet the specification (DC 24 V, undervoltage / overvoltage protection trip points 15 ~ 32 V). Never connect the positive and negative leads in reverse.
6. Confirm a reliable ground connection between the host computer and the power supply.

## Interface overview

The LiteGrip external interface consists of three sets of connections:

| Connection | Description |
|------|------|
| **24 V power supply** | Powers the motor. **The motor produces no torque when it is not connected** |
| **CAN bus** | Connects the gripper to the USB-CAN adapter |
| **CAN terminating resistor** | One 120 Ω terminating resistor at each end of the bus |

The connections are as follows:

```
        ┌──────────────┐
        │  24 V DC     │
        │ power supply │
        └──────┬───────┘
               │  24V / GND
               │  observe polarity
               ▼
        ┌──────────────────────────┐
        │        LiteGrip          │
        │       gripper body       │
        └────────────┬─────────────┘
                     │  CAN_H / CAN_L
        ┌────────────┴─────────────┐
        │      USB-CAN adapter     │
        └────────────┬─────────────┘
                     │  USB
                     ▼
              ┌──────────────┐
              │ host computer│
              │ (Linux)      │
              └──────────────┘

  Terminating resistor 120 Ω: one at each physical end of the CAN bus
```

> **Note**: **This manual does not provide cable and connector specifications** (see Section 2.6). **Do not make your own cables or buy your own connectors** — contact us and we will supply them.

## Power supply

| Item | Specification |
|------|------|
| Rated voltage | 24 V DC |
| Permitted voltage range | **15 ~ 32 V** (protection trip points; the full description is in Section 2.5) |
| Undervoltage protection point | 15 V |
| Overvoltage protection point | 32 V |
| No-load current | **0.037 A**[A, measured from the power supply reading, 2026-09-28] |
| Rated / peak current | **3.1 A / 16.5 A**[drive motor manual nominal **power supply** current @24 V] |

**Applying 24 V is the precondition for motor torque.** With only the USB-CAN adapter connected, the gripper can communicate and report status, but **it will not move**, and it reports an undervoltage fault (error code `0x9`). This is normal behavior, not a fault.

> **Power supply sizing**: estimating from the peak supply current of 16.5 A given in the drive motor manual, the 24 V supply **should be at least 400 W**;
> typical operation (rated 3.1 A) needs about 75 W.
> Verify this against the measured peak current before finalizing.
>
> **Note**: **When the 24 V supply is abnormal, the driver's own protection takes over** (undervoltage 15 V / overvoltage 32 V). For its behavior, see the Safety Manual, Chapter 9.

## CAN bus

| Item | Specification |
|------|------|
| Protocol | **Classic CAN** (CAN 2.0, not CAN FD) |
| Baud rate | 1 Mbps |
| Data frame length | 8 bytes |
| Terminating resistor | 120 Ω at each end of the bus |
| Motor CAN ID | 0x08 |
| Feedback frame ID | 0x18 |
| Broadcast ID | 0x7FF |
| Control mode | MIT |
| Communication timeout protection | Automatically disables after 0.4 s |

> **Note**: **CAN FD must be explicitly disabled.** If the interface is opened in FD mode, communication fails even with the correct baud rate — and this looks just like "no 24 V connected", so it is easily misdiagnosed as a hardware fault.
>
> **Note**: **Feedback from this product is polled.** The motor answers only after it receives a command frame; **passively listening on the bus never yields a feedback frame**.
>
> **Note**: **The CAN ID may differ from unit to unit**; use the label shipped with the product.

For interface configuration commands, frame formats, and register numbers, see the CAN Communication Protocol Manual.

# Installation and usage guide

## Overview

This chapter covers acceptance, installation, wiring, host environment setup, daily use and maintenance, troubleshooting, and common questions for LiteGrip. It does not use specialized terminology to describe communication details; if you need to develop your own control program, see the technical documents shipped with the product:

| Document | Reader |
|------|------|
| the Software Development Manual | Integration engineers — software interface usage and preconditions |
| the CAN Communication Protocol Manual | Integration engineers — communication protocol and registers |
| the Parameter Document | Integration engineers — all parameter values and their sources |
| the Safety Manual | Safety and quality staff — safety design, boundaries, and usage requirements |
| the Documents Shipped with the Product | End users — factory certificate of conformity, packing list, warranty card |

## Appearance and parts

LiteGrip consists of the gripper body, two parallel-motion fingers, the fingertips, and the cable outlet:

| Part | Description |
|------|------|
| Gripper body | Contains the DM-J4310-2EC drive motor, the transmission mechanism, and the guide rail |
| Finger (left / right) | Moves in parallel along the guide rail; per-finger stroke 43.500 mm |
| Fingertip | The part that contacts the workpiece directly; dimensions **84 × 60 × 22 mm** |

## Unboxing and installation

### Mounting the gripper

1. Check the packaging for obvious damage.
2. Check the gripper for deformation or impact damage.
3. Push the fingers by hand and confirm they move smoothly with no binding.
4. Mount the gripper on a bracket or robot-arm end flange with **sufficient rigidity**. The mounting face must be flat and the fastening bolts must be loaded evenly (**contact us first to request the mounting interface dimensions**).
5. After mounting, confirm there are **no obstructions** in the fingers' range of motion.

> **Warning**: **This gripper has a mechanical hard stop in the opening direction, and none in the closing direction.** Closing is the two fingers **colliding**, held only by the mechanism's elasticity; **it will not "stop when it hits a hard stop"**. You must therefore confirm at installation that **nothing in the closing path of the two fingers needs the gripper to "push against" it**, and do not expect to use the gripper to press a part onto a locating face. To keep the gripper holding, use the **torque control** of `grasp()` / `close(force_n=...)`, not a position command driven to the limit. See the note at the end of the "Stroke and position parameters" section.

> **Warning**: **You must cut the 24 V power supply before installation or removal.**
>
> **Warning**: **This manual does not provide the mounting interface dimensions** (flange standard, hole pattern, thread, permitted screw length, recommended tightening torque). **Contact us for the mounting documentation before you install the gripper.**

### Wiring

Wire the three connection groups as shown in Section 3.2: the 24 V power supply, the CAN bus, and the CAN terminating resistors (one 120 Ω terminating resistor at each end of the bus).

> **Warning**: **Reversed power polarity can damage the device.** Before power-up, confirm the polarity with a multimeter.
>
> **The terminating resistors are mandatory.** The typical symptom when they are missing is "communication that drops in and out".

### Power-up sequence

1. Confirm the wiring is correct and there is no short circuit.
2. Power on the USB-CAN adapter (on the host computer side).
3. **Last**, power on the 24 V supply.

> **Power down in the reverse order**: cut the 24 V first, then the adapter.
>
> **Note**: The above is the recommended power-up convention; **neither the SDK nor the driver enforces this order**. Following it avoids triggering the driver communication timeout that occurs when drive power is applied first and communication is connected afterwards, because nobody is sending frames.

**Handling abnormalities**: If you find obvious deformation or jamming of the fingers, damaged cables, bent connector pins, a cracked housing, or water or foreign objects inside the packaging, **do not apply power**; contact us.

## Host environment setup

| Item | Requirement |
|------|------|
| Operating system | **Linux** (kernel support for SocketCAN required) |
| Python | 3.8 or later |
| Hardware interface | USB-CAN adapter |
| Third-party dependencies | The library code uses only the Python standard library and Linux SocketCAN; `pip install` also installs `eclipse-zenoh` (used only by the teleoperation example) |

Configure the CAN interface:

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000 fd off
sudo ip link set can0 up
```

> `fd off` is not optional — this product uses classic CAN, not CAN FD.

If you do not have the hardware yet, you can verify the software environment first on a virtual bus:

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
python examples/dry_run.py
```

> There is no real motor on the virtual bus, so **the enable step will time out**. This is **expected behavior**, not a fault.

**If you only want to check whether the gripper is powered and responds**: you can skip the SDK and send a single frame with `can-utils`, which ships with Linux, to see whether there is any feedback. For the exact commands, see "Bus self-check without the SDK" in Appendix B of the Software Development Manual. This is the fastest way to tell whether the problem is no communication or no motion.

For detailed software installation, interface usage, and examples, see the Software Development Manual.

## Daily use and maintenance

### Basic motions

If you use the example scripts shipped with the product, you can run them directly:

| Script | Purpose |
|------|------|
| `examples/basic.py` | Basic opening and closing, and status readout |
| `examples/slow_open.py` | Slow opening |
| `examples/slow_close.py` | Slow closing |
| `examples/cycle_test.py` | Cyclic open/close test |
| `examples/can_diag.py` | Communication diagnostics |
| `examples/dry_run.py` | Verification without hardware |

**Grasping**: After you run the grasp function, the gripper closes until it **contacts the object and is obstructed**, which is taken as a successful grip, and it holds position.

| Result | Meaning |
|------|------|
| Success | The fingers stop moving (they gripped the object, **or they hit the stroke endpoint**) |
| Failure | The fingers are still moving when the set time elapses (**timeout**; usually means nothing was touched) |

> **Note**: The criterion is whether the fingers stop moving. **Gripping an object and hitting the stroke endpoint both count as "stopped moving" and both report success** — so you cannot rely on the return value alone to distinguish "gripped it" from "hit the endpoint". To tell them apart, use the position reading.
>
> **Warning**: **The force parameter is currently not validated at all.** The shipped SDK converts the force value directly into a feedforward torque and sends it (the conversion coefficient is a nominal value never calibrated against a real load); **it neither checks whether force calibration has been completed nor refuses to execute**. Before force calibration is complete, **do not rely on the force parameter**; for pure position grasping, set the force parameter explicitly to 0. See Section 2.3.9 and Section 4.7.1 of the Software Development Manual.

**Manual teaching**: When you need the gripper to hold at a new position, you can enter **zero gravity mode** (the SDK's `enter_zero_gravity()`): the motor then outputs no torque (`kp = kd = 0`) and you can push the fingers by hand. When you call `exit_zero_gravity()` to leave the mode, the SDK uses the `kp` / `kd` from the configuration to **hold the position at the moment of exit**.

> **Warning**: Zero gravity mode **does not itself hold position** — once you enter it, the fingers are free, and they stay wherever you let go; they do not return on their own. Position is held only at the moment you leave the mode. Also, `exit_zero_gravity()` **performs no range check**: even if you push the fingers beyond the calibrated endpoint, it will hold that position anyway and **will not report an error**. **Manual teaching must be supervised by a person on site.**

### Routine checks

The intervals below are a **recommended maintenance convention, not measured specifications**. They are a starting point based on common practice for comparable electromechanical modules, given for you to use when scheduling, and **they are not a lifetime or reliability figure for this product**.

| Interval | Check |
|------|--------|
| Every shift | Whether the fingers move smoothly, and whether there is any abnormal noise |
| Weekly | Whether the cables are damaged, and whether the connectors are loose |
| Monthly | Whether the fastening bolts are loose, and whether the fingers are worn |

### Cleaning

The following is likewise **recommended practice, not measured specifications**:

- After cutting power, wipe the housing with a dry, soft cloth;
- **Do not** use organic solvents or corrosive cleaners;
- **Do not** wash with water.

### Long-term storage

Before long-term storage, disconnect the 24 V power supply and store the gripper in a dry environment free of corrosive gases. This is a **recommended storage practice, not measured environmental specifications**: the ingress protection rating and environmental tolerance are **neither certified nor measured, and this manual does not provide those specifications**.

### When recalibration is required

After any of the following, you **must recalibrate**:

- Replacing the gripper body or the motor;
- Replacing or repairing a finger;
- A collision or an overload;
- An abnormal position reading after a power cycle.

## Troubleshooting

| Symptom | Possible cause | Remedy |
|--------------------------|------------------------------------|--------------------------------------|
| No communication at all | CAN interface not configured / CAN FD not disabled | Reconfigure as in Section 4.4 |
| | Terminating resistors missing | Fit one 120 Ω at each end of the bus |
| | Loose cable | Check the connectors |
| Status can be read but **the gripper does not move** | **The 24 V supply is not connected** | Connect 24 V (the most common cause) |
| | Motor not enabled | Check whether the enable step succeeded |
| | No valid calibration on the gripper | Run the calibration procedure again |
| The gripper stops halfway through a motion | It gripped an object or a foreign body (position stall) | Check for obstructions |
| | Motor overcurrent or overtemperature protection tripped | Stop and let it cool, then check the load |
| The gripper stops at an endpoint and will not move | The target position is outside the calibrated range and is **silently clamped** to the endpoint | **The SDK does not report an error**; check the calibrated values and the target position |
| Grasping always reports failure | The fingers are still moving at timeout — usually they never touched the object | Confirm the object is within the stroke range |
| | The timeout is set too short | Increase the time parameter of `grasp()` |
| Insufficient gripping force | **Force control has not yet completed factory calibration** | **Do not rely on the force parameter**; use position grasping or add a mechanical limit |
| Abnormal noise or jamming during motion | Foreign matter on the guide rail / mechanical damage | Cut power and inspect; contact service |
| Shuts down after running for a while | Overtemperature protection | Reduce the load or improve heat dissipation |

**Error code reference:**

| Error code | Meaning | Action |
|--------|------|------|
| 0x0 | Disabled | Normal (not-enabled state) |
| 0x1 | Enabled | Normal |
| 0x3 | Output shaft calibration fault | Contact technical support |
| 0x4 | Sensor output fault | Contact technical support |
| 0x5 | Encoder calibration fault | Contact technical support |
| 0x8 | **Overvoltage** fault | Check whether the supply exceeds 32 V |
| 0x9 | **Undervoltage** fault | **Check whether 24 V is connected** |
| 0xA | Overcurrent fault | Check for binding and for an excessive load |
| 0xB | MOS overtemperature fault | Stop and let it cool |
| 0xC | Coil overtemperature fault | Stop and let it cool |
| 0xD | Communication loss | Check the CAN wiring and the terminating resistors |
| 0xE | Overload | Reduce the load |

> **Note**: **`0x8` and `0x9` are very easy to mix up.** The correct order is **8 = overvoltage (OV), 9 = undervoltage (UV)**, not "low voltage first".
>
> **Note (source of this table)**: The full code table above comes from the **official protocol documentation of the Damiao motor (DM4310)** and is every code the driver can report. `get_error()` reads the raw **integer** value of that code; for text, call `describe_error()`, which gives the Chinese descriptions from the table above for `0x0`, `0x1`, `0x9`, `0xA`, `0xB`, and `0xC`, and displays all other codes as "unknown error (0xXX)", leaving you to interpret them from the table above.

**If you cannot resolve the problem yourself**, record the following information and contact us: product model and serial number, a description of the symptom and how often it occurs, the host computer operating system version, and the output of the communication diagnostics script.

## FAQ and technical support

### Q&A

Q: How wide is the gripper aperture? A: **The effective stroke is 87.000 mm** (SDK position `p` runs from 0 to 87.000; the full stroke is usable). If you measure the actual aperture between the two fingers with a caliper, it is **1.508 mm** fully closed and **87.000 mm** fully open, a span of **85.492 mm**. Note that the position the SDK returns is the millimeter reading `p`, **not** the caliper reading: `actual aperture ≈ p + 1.508`.

Q: How heavy an object can it grip? A: **We cannot answer that yet.** The load capacity has not been measured — it cannot be derived from the motor torque; it must be measured. Send us the workpiece dimensions, weight, material, and grasp pose, and we will assess it case by case.

Q: How large is the gripping force? A: **We cannot answer that yet.** It can only be measured after factory force calibration is complete, and it depends strongly on the fingertip material.

Q: Can I set the gripping force? A: **You can enter a force value in the interface, but entering one does not make the force accurate.** The shipped SDK converts the force value through a **nominal coefficient** into a feedforward torque and sends it directly, **performing no validation and never refusing to execute**. That coefficient has never been calibrated against a real load, so the number is only a qualitative reference (larger means more force) and **must not be used as a calibrated gripping force**. For pure position grasping that stops on contact, **the force parameter is not needed at all**: the gripper closes until it contacts an object and is obstructed, which meets most grasping needs.

Q: Is Windows supported? A: **No.** The development kit currently supports Linux only.

Q: Is it water- and dust-proof? A: **The IP rating is not yet certified.** Contact us before using it in an environment with dust, moisture, or cutting fluid.

Q: Does the gripper release when power is cut? A: **Yes.** This product has **no power-off self-locking**. If your application cannot accept that, you must add a separate mechanical holding device.

Q: Must the 24 V supply be connected? A: **Yes.** With only USB-CAN connected, it can communicate and report status, but it **will not move**, and it reports undervoltage. That is normal, not a fault.

Q: Why must `fd off` be added when configuring CAN? A: Because this product uses **classic CAN**. Configuring it as CAN FD makes **communication completely impossible** — and that symptom looks a lot like "24 V not connected", so it is easily misdiagnosed as a hardware fault.

Q: Why do I receive nothing when I listen on the bus? A: **Feedback from this product is query-based**: the motor answers only after it receives a command frame. **Passive listening will never receive any frames**; you must send frames first.

Q: The enable interface returns success, but the motor is actually not enabled? A: `enable()` **does validate** — after sending the enable frame it waits for feedback, confirms that the feedback is new and that the error code is within `0x0` / `0x1`, retries if it cannot read it, up to 5 times, and raises `HardwareError` if it still fails. So if `enable()` returns without raising an exception, the motor really is enabled. **But `disable()` does not validate** — it returns `True` as soon as the frame is sent, and you must read the status yourself to confirm that disabling succeeded.

Q: How do I make the gripper grasp something? A: Use `grasp(force_n=0)`. **Set the force parameter explicitly to 0** — the force parameter is not validated at all, and a non-zero value is converted directly into a feedforward torque applied to the motor; until force calibration is complete, the magnitude of that torque is not guaranteed. Writing 0 gives pure position grasping.

Q: How do I use the emergency stop? A: On the software side, use `stop()` — it sends a zero-torque frame to stop the fingers, **does not disable the motor and does not latch any fault**, and you can keep sending commands afterwards; if the motor is not enabled, it does nothing. For a power-level stop, use `disable()`. **The emergency stop must be implemented in hardware**: cut the 24 V drive power (note that this product has no power-off self-locking, so the fingers will release when you cut it), or wire an independent emergency-stop circuit outside the host computer.

Q: What does the "to be measured" marker in the manual mean? A: It means **the item definitely exists and must be measured, but the value has not been measured yet**. **A missing entry does not mean the item does not exist.** Until it is measured, do not use these values for selection or safety assessment.

Q: What is the technical support channel? A: The NEXFORM ROBOTICS technical team. Contact details are in the documents shipped with the product and through the sales channel, or the contact person from your purchase can forward you to technical support directly.

---

> **End of document** If you have questions or need more information, contact the NEXFORM ROBOTICS technical team.
