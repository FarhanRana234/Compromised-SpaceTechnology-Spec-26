# Compromised-SpaceTechnology-Spec-26

**Fault-tolerant TMR voter + watchdog supervisor, modeled in Python.**

Built for the **SPEC '26 SpaceTech Hackathon** at NED University, Karachi (27 Oct 2026).
Challenge: *Fault-Tolerant TMR and Watchdog Controller*.

---

## The problem

In orbit, a single high-energy particle can flip one bit in a chip's memory or logic. This is a **Single Event Upset (SEU)**. One flipped bit can corrupt data or freeze the CPU, and nobody can reach the satellite to repair it.

## What this project does

`main.py` models a radiation-mitigation supervisor with three parts:

- **TMR voter.** Three redundant paths (A, B, C) feed a bitwise majority vote: `(A & B) | (B & C) | (A & C)`. If one path has a flipped bit, the other two outvote it and the output stays correct.
- **Watchdog timer.** The CPU must send a heartbeat within a timeout (default 2.0 seconds). If it does not, the system forces itself into `SAFE_MODE`.
- **Telemetry registers.** Counters and a status value that report what happened: `SYS_STATUS`, `SINGLE_ERR_CNT`, `MULTI_ERR_CNT`.

In `SAFE_MODE`, the voter locks its output to `0x00`.

## Run it

Needs Python 3.8 or newer. No extra packages.

```bash
python main.py
```

The run takes about 3 seconds, because Test 4 waits 2.5 seconds to simulate a frozen CPU.

## What the testbench does

`run_testbench()` injects four faults on purpose. The golden data value is `0b10101010` (0xAA).

| Test | Fault injected | What happens |
|---|---|---|
| 1 | None (nominal) | Output stays `0b10101010`, status `NORMAL` |
| 2 | Bit 3 flipped in Path B (SEU) | Voter outvotes it, output is still `0b10101010`, `SINGLE_ERR_CNT` becomes 1 |
| 3 | Bit 1 flipped in Path A and bit 5 flipped in Path B at the same time | Two paths disagree with the majority, so it is reported as uncorrectable: `MULTI_ERR_CNT` becomes 1 and the system enters `SAFE_MODE` |
| 4 | CPU hang: no heartbeat for 2.5 s | Watchdog expires, status is forced to `SAFE_MODE` |

### Sample output

```
============================================================
      SPEC '26 FAULT-TOLERANT TMR & WATCHDOG TESTBENCH
============================================================

--- TEST 1: Nominal System Operation ---
Output: 0b10101010 | System Status: NORMAL

--- TEST 2: Single Event Upset (SEU) - Bit Flip in Path B ---
[TMR INFO] Single-bit SEU corrected! Telemetry count: 1
Corrupted Input B: 0b10100010 -> Voted Output: 0b10101010

--- TEST 3: Multi-Bit Uncorrectable Radiation Event ---
[TMR CRITICAL] Multi-bit failure detected! Entering SAFE_MODE.
System State: SAFE_MODE

--- TEST 4: Hardware Hang / Watchdog Timeout ---
Simulating CPU freeze (pausing 2.5 seconds)...
[WATCHDOG EXPIRED] No heartbeat! Status forced to: SAFE_MODE

============================================================
TELEMETRY REGISTERS:
  SYS_STATUS     : SAFE_MODE
  SINGLE_ERR_CNT : 1
  MULTI_ERR_CNT  : 1
============================================================
```

## Code reference

Everything lives in the class `FaultTolerantSystem`.

| Member | Purpose |
|---|---|
| `FaultTolerantSystem(watchdog_timeout=2.0)` | Creates the system. `watchdog_timeout` is in seconds. |
| `reset_watchdog()` | The CPU heartbeat. Call it regularly to keep the watchdog quiet. |
| `check_watchdog()` | Returns `True` if the heartbeat is recent. If the timeout has passed, sets `SAFE_MODE` and returns `False`. |
| `tmr_voter(path_a, path_b, path_c)` | Returns the majority-voted value. Counts a single-path error, or flags a multi-path error and enters `SAFE_MODE`. Returns `0x00` while in `SAFE_MODE`. |
| `single_err_cnt` | Number of corrected single-path errors. |
| `multi_err_cnt` | Number of uncorrectable multi-path events. |
| `system_state` | `"NORMAL"` or `"SAFE_MODE"`. |

### Using it in your own code

```python
from main import FaultTolerantSystem

system = FaultTolerantSystem(watchdog_timeout=2.0)

golden = 0b10101010
flipped = golden ^ (1 << 3)               # radiation flips bit 3 in one copy

out = system.tmr_voter(golden, flipped, golden)
print(bin(out))                            # 0b10101010 (corrected)
print(system.single_err_cnt)               # 1

system.reset_watchdog()                    # CPU heartbeat
if not system.check_watchdog():
    print("CPU hung:", system.system_state)
```

## Design notes and limitations

- **Why Test 3 goes to SAFE_MODE.** With bitwise voting, flips at different bit positions in two paths can still produce the right answer. The model deliberately does not trust the result once two paths disagree with the majority, and reports an uncorrectable event instead of hiding it.
- **Same-bit, same-way corruption in two paths** can fool any TMR voter. This model does not detect that case.
- **The watchdog is polled.** `check_watchdog()` must be called by the supervisor loop. It is a software model of a hardware timer, not a separate thread.
- **Counting is per call.** Each `tmr_voter` call that sees a bad path adds one to the counter.
- **Recovery is manual.** `SAFE_MODE` stays latched until the code resets `system_state` (Test 4 does this by hand).
- **Telemetry is printed, not transmitted.** The register names are modeled after status registers that a flight design would expose over SPI or AXI.

## Next steps

- Synthesizable HDL (Verilog) version of the same voter, watchdog and telemetry
- Fault-injection testbench for the HDL, with waveforms
- SPI or AXI interface for the telemetry registers

## Team

SPEC '26, NED University, Karachi. Add team member names here.

## License

Add a license of your choice (for example MIT) before publishing.
