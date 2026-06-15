#!/usr/bin/env python3
"""Detect local runtime capabilities for BAGEL without assuming platform features."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def command_works(args: list[str]) -> bool:
    try:
        result = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def bool_yaml(value: bool) -> str:
    return "true" if value else "false"


def detect_platform() -> tuple[str, str]:
    if (
        os.environ.get("CODEX_SANDBOX")
        or os.environ.get("CODEX_ENV")
        or os.environ.get("CODEX_CI")
        or os.environ.get("CODEX_SHELL")
        or os.environ.get("CODEX_THREAD_ID")
        or "codex" in os.environ.get("__CFBundleIdentifier", "").lower()
    ):
        return "codex", "references/platform-codex.md"
    if exists("claude"):
        return "claude_code", "references/platform-claude-code.md"
    return "other", "none"


def cwd_is_git_repo() -> bool:
    """Probe whether the current working directory is inside a git work tree.

    Distinct from git-binary availability: a machine can have git installed while
    the target project folder has no .git. Rollback/branch governance depends on
    repo membership, so this is reported as a first-class capability flag.
    """
    if not (exists("git") and command_works(["git", "--version"])):
        return False
    return command_works(["git", "rev-parse", "--is-inside-work-tree"])


def render_yaml() -> str:
    platform, adapter = detect_platform()
    git_installed = exists("git") and command_works(["git", "--version"])
    git_worktrees = git_installed
    project_is_repo = cwd_is_git_repo()

    # Visual / screenshot capability detection
    screenshot_tools: list[str] = []
    for cmd in ["playwright", "puppeteer", "chromium", "google-chrome", "firefox"]:
        if exists(cmd):
            screenshot_tools.append(cmd)
    if exists("npx") and command_works(["npx", "--yes", "playwright", "--version"]):
        screenshot_tools.append("npx-playwright")
    if exists("open"):  # macOS preview
        screenshot_tools.append("open")
    browser_or_visual = len(screenshot_tools) > 0

    codex_cli = exists("codex")
    claude_cli = exists("claude")
    python_ok = exists("python3") or exists("python")
    node_ok = exists("node") or exists("npm") or exists("npx")
    cron_like = exists("crontab") or exists("launchctl")

    supports_background = codex_cli or claude_cli or cron_like
    # v1.1: Claude Code and Codex supply native loop primitives (/loop, app
    # automations, scheduled tasks, cloud tasks, codex exec) that are NOT
    # detectable via crontab/launchctl. Treat those platforms as timer-capable
    # so the mandatory-loop gate does not falsely force degraded_resume.
    supports_native_loop = platform in {"codex", "claude_code"}
    supports_timers = cron_like or supports_native_loop
    supports_subagents = platform in {"codex", "claude_code"}
    supports_hooks = platform in {"codex", "claude_code"}
    supports_self_provisioning = python_ok or node_ok

    if supports_native_loop:
        session_mode = "scheduled_resume"
    elif supports_timers:
        session_mode = "external_harness"
    else:
        session_mode = "degraded_resume"

    screenshot_list = ", ".join(screenshot_tools) if screenshot_tools else "none"

    return f"""runtime:
  platform: {platform}
  platform_adapter: "{adapter}"
  session_mode: {session_mode}
  project_is_git_repo: {bool_yaml(project_is_repo)}
  loop_interval_max_minutes: 25
  degradation_allowed: true
  supports_true_subagents: {bool_yaml(supports_subagents)}
  supports_context_isolation: {bool_yaml(supports_subagents or git_worktrees)}
  supports_timers_or_wakeup: {bool_yaml(supports_timers)}
  supports_native_loop: {bool_yaml(supports_native_loop)}
  supports_background_execution: {bool_yaml(supports_background)}
  supports_git_worktrees: {bool_yaml(git_worktrees)}
  supports_browser_or_visual_checks: {bool_yaml(browser_or_visual)}
  supports_hooks: {bool_yaml(supports_hooks)}
  supports_tool_self_provisioning: {bool_yaml(supports_self_provisioning)}
  screenshot_tools: [{screenshot_list}]
  detected_commands:
    codex: {bool_yaml(codex_cli)}
    claude: {bool_yaml(claude_cli)}
    git: {bool_yaml(git_installed)}
    python: {bool_yaml(python_ok)}
    node: {bool_yaml(node_ok)}
    cron_or_launchctl: {bool_yaml(cron_like)}
  max_safe_cycle_minutes: 25
  permitted_claims:
    - "Can leave durable checkpoints"
  forbidden_claims:
    - "Do not promise automatic wakeup unless a scheduler, automation, or harness is actually configured"
  resume_artifact: ".bagel/runs/<run_id>/handoff.json"
  next_action_artifact: ".bagel/ledger/next-dispatch.md"
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="Write YAML to this path instead of stdout")
    args = parser.parse_args()
    output = render_yaml()
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
