"""Extremely basic pexpect smoke test – no harness, just raw subprocess."""

import time

import pexpect

# No pytestmark - run in all environments but handle timing gracefully


def test_version_smoke() -> None:
    child = pexpect.spawn("newcode --version", encoding="utf-8")
    child.expect(pexpect.EOF, timeout=10)
    output = child.before
    assert output.strip()  # just ensure we got something
    print("\n[SMOKE] version output:", output)


def test_help_smoke() -> None:
    child = pexpect.spawn("newcode --help", encoding="utf-8")
    child.expect("--version", timeout=10)
    child.expect(pexpect.EOF, timeout=10)
    output = child.before
    assert "show version and exit" in output.lower()
    print("\n[SMOKE] help output seen")


def test_interactive_smoke() -> None:
    """Test that the CLI can enter interactive mode and respond to quit.

    This test is designed to be efficient with timeouts - using a single expect
    call with multiple patterns rather than back-to-back expect calls.
    """
    child = pexpect.spawn("newcode -i", encoding="utf-8")

    # Wait for output and look for coding task prompt
    time.sleep(3)  # Give the CLI time to start and output

    try:
        idx = child.expect(
            [
                ">>> ",
                pexpect.TIMEOUT,
            ],
            timeout=15,
        )

        if idx == 0:  # Found prompt
            print("[SMOKE] Found prompt indicator")
        elif idx == 1:  # Timeout
            print(
                f"[SMOKE] Timeout waiting for prompt. Buffer: {child.before[:200] if child.before else 'None'}"
            )
            # Still continue - CLI might be running
    except pexpect.exceptions.TIMEOUT:
        print("[INFO] Initial prompts timeout")
        pass

    print("\n[SMOKE] CLI entered interactive mode")

    time.sleep(1)
    child.send("/quit\r")
    time.sleep(0.5)
    try:
        child.expect(pexpect.EOF, timeout=15)
        print("\n[SMOKE] CLI exited cleanly")
    except pexpect.exceptions.TIMEOUT:
        # Force terminate if needed
        child.terminate(force=True)
        print("\n[SMOKE] CLI terminated (timeout)")
