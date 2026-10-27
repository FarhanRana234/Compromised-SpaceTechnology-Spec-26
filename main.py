import time

class FaultTolerantSystem:
    def __init__(self, watchdog_timeout=2.0):
        self.watchdog_timeout = watchdog_timeout
        self.last_heartbeat = time.time()
        self.single_err_cnt = 0
        self.multi_err_cnt = 0
        self.system_state = "NORMAL"  # NORMAL or SAFE_MODE

    def reset_watchdog(self):
        """Heartbeat ping sent by CPU."""
        self.last_heartbeat = time.time()

    def check_watchdog(self):
        """Monitors system responsiveness."""
        if time.time() - self.last_heartbeat > self.watchdog_timeout:
            self.system_state = "SAFE_MODE"
            return False
        return True

    def tmr_voter(self, path_a: int, path_b: int, path_c: int) -> int:
        """
        Bitwise TMR Majority Voter logic: (A & B) | (B & C) | (A & C)
        Handles error tracking and safe-mode state enforcement.
        """
        if self.system_state == "SAFE_MODE":
            print("[SAFE_MODE ACTIVE] Data lines locked to 0x00.")
            return 0x00

        # Bitwise Majority Voting logic
        majority_output = (path_a & path_b) | (path_b & path_c) | (path_a & path_c)

        # Calculate path deviations
        err_a = path_a ^ majority_output
        err_b = path_b ^ majority_output
        err_c = path_c ^ majority_output

        failing_paths = sum([1 for err in (err_a, err_b, err_c) if err != 0])

        if failing_paths == 1:
            self.single_err_cnt += 1
            print(f"[TMR INFO] Single-bit SEU corrected! Telemetry count: {self.single_err_cnt}")
        elif failing_paths > 1:
            self.multi_err_cnt += 1
            self.system_state = "SAFE_MODE"
            print(f"[TMR CRITICAL] Multi-bit failure detected! Entering SAFE_MODE.")

        return majority_output

def run_testbench():
    print("=" * 60)
    print("      SPEC '26 FAULT-TOLERANT TMR & WATCHDOG TESTBENCH      ")
    print("=" * 60)

    sys = FaultTolerantSystem(watchdog_timeout=2.0)
    golden_data = 0b10101010

    print("\n--- TEST 1: Nominal System Operation ---")
    out = sys.tmr_voter(golden_data, golden_data, golden_data)
    sys.reset_watchdog()
    print(f"Output: {bin(out)} | System Status: {sys.system_state}")

    print("\n--- TEST 2: Single Event Upset (SEU) - Bit Flip in Path B ---")
    corrupted_b = golden_data ^ (1 << 3)  # Flip bit 3
    out = sys.tmr_voter(golden_data, corrupted_b, golden_data)
    sys.reset_watchdog()
    print(f"Corrupted Input B: {bin(corrupted_b)} -> Voted Output: {bin(out)}")

    print("\n--- TEST 3: Multi-Bit Uncorrectable Radiation Event ---")
    corrupted_a = golden_data ^ (1 << 1)
    corrupted_b = golden_data ^ (1 << 5)
    out = sys.tmr_voter(corrupted_a, corrupted_b, golden_data)
    print(f"System State: {sys.system_state}")

    print("\n--- TEST 4: Hardware Hang / Watchdog Timeout ---")
    sys.system_state = "NORMAL"
    sys.reset_watchdog()
    print("Simulating CPU freeze (pausing 2.5 seconds)...")
    time.sleep(2.5)
    if not sys.check_watchdog():
        print(f"[WATCHDOG EXPIRED] No heartbeat! Status forced to: {sys.system_state}")

    print("\n" + "=" * 60)
    print("TELEMETRY REGISTERS:")
    print(f"  SYS_STATUS     : {sys.system_state}")
    print(f"  SINGLE_ERR_CNT : {self_cnt if (self_cnt := sys.single_err_cnt) else 0}")
    print(f"  MULTI_ERR_CNT  : {sys.multi_err_cnt}")
    print("=" * 60)

if __name__ == "__main__":
    run_testbench()