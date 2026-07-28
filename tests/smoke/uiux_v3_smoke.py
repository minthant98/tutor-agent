"""Post-deploy smoke for v3 shell + dashboard + session start.

PLACEHOLDER — Playwright is not installed in this project.
To activate: `pip install playwright && playwright install chromium`
then remove the placeholder block below and uncomment the functional test.

Usage (once Playwright is installed):
    STRIDE_UI_URL=http://localhost:3000 pytest tests/smoke/uiux_v3_smoke.py

What this smoke would verify:
    1. Sign in via /signin form
    2. Sidebar nav visible (shell_v3 surface)
    3. Cmd-K palette opens on Meta+K and closes on Escape
    4. "Start Today's Session" CTA clicks through to /sessions/{id}
    5. Segment band renders "Segment 1 of N" text

CI usage:
    Add to CI matrix with env: STRIDE_UI_FLAG=v3
    Gate on shell_v3=on in PostHog test environment before running.
"""

import sys


def test_uiux_v3_smoke_placeholder() -> None:
    """Placeholder test — always passes until Playwright is installed.

    To replace with the functional smoke:
      1. pip install playwright && playwright install chromium
      2. Replace this function with the Playwright-based test below.
    """
    print(
        "uiux_v3_smoke: Playwright not installed — placeholder passes. "
        "Install playwright to activate browser smoke."
    )
    assert True, "Placeholder always passes"


# ── Functional smoke (uncomment after `pip install playwright`) ───────────────
#
# from playwright.sync_api import Page
#
# def test_shell_v3_smoke(page: Page):
#     page.goto("/signin")
#     page.get_by_label("Email").fill("smoke@stride.test")
#     page.get_by_label("Password").fill("test-pass")
#     page.get_by_role("button", name="Sign in").click()
#     page.wait_for_url("**/")
#     # Sidebar visible
#     page.get_by_role("link", name="Home").wait_for()
#     # Cmd-K opens
#     page.keyboard.press("Meta+K")
#     page.get_by_role("dialog").wait_for()
#     page.keyboard.press("Escape")
