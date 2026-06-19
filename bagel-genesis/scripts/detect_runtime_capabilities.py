#!/usr/bin/env python3
"""Detect local runtime capabilities for BAGEL without treating claims as proof."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
from datetime import datetime, timezone
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def proof_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capability_yaml(name: str, adapter_claim: bool, observed: bool | None, proof_ref: str, reason: str) -> str:
    if observed is True:
        observed_value = "true"
    elif observed is False:
        observed_value = "false"
    else:
        observed_value = "unknown"
    verified = now_iso() if observed is not None else "null"
    return f"""    {name}:
      adapter_claim: {bool_yaml(adapter_claim)}
      observed: {observed_value}
      proof_ref: "{proof_ref}"
      last_verified_at: {verified}
      proof_summary: "{reason}"
"""


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
    detected_at = now_iso()

    true_subagents_observed: bool | None = None
    timers_observed: bool | None = None
    hooks_observed: bool | None = None
    if platform == "codex":
        true_subagents_observed = None
        timers_observed = None
        hooks_observed = None
    elif platform == "claude_code":
        # observed stays UNKNOWN until a real isolated dispatch is recorded by
        # the Task PostToolUse hook (attest_subagent.py) into the proof file.
        # CLI presence is an adapter claim, NOT an observation — conflating them
        # taught the agent that observed:true precedes evidence (RUN-001 finding 2).
        true_subagents_observed = None
        timers_observed = None
        hooks_observed = None
    else:
        true_subagents_observed = False
        timers_observed = cron_like
        hooks_observed = False

    return f"""runtime:
  platform: {platform}
  platform_adapter: "{adapter}"
  session_mode: {session_mode}
  detected_at: "{detected_at}"
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
runtime_capabilities:
  platform: {platform}
  platform_adapter: "{adapter}"
  detected_at: "{detected_at}"
  capabilities:
{capability_yaml("true_subagents", supports_subagents, true_subagents_observed, ".bagel/evidence/runtime/subagent-proof.yaml", "adapter claim only unless proof file records a real isolated dispatch")}
{capability_yaml("timers_or_wakeup", supports_timers, timers_observed, ".bagel/evidence/runtime/loop-proof.yaml", "adapter claim only unless proof file records a bound schedule/loop")}
{capability_yaml("hooks", supports_hooks, hooks_observed, ".bagel/evidence/runtime/hooks-proof.yaml", "adapter claim only unless proof file records configured hook execution")}
{capability_yaml("browser_or_visual", browser_or_visual, browser_or_visual, ".bagel/evidence/runtime/visual-proof.yaml", "detected local visual commands: " + screenshot_list)}
  proof_model:
    adapter_claim_is_not_proof: true
    detector_digest: "{proof_hash(platform + adapter + detected_at)[:16]}"
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # Accept a positional <root> like every other BAGEL script
    # (bagel_v3_check.py <root>, runtime_proof_check.py <root>, …). Without
    # this, the convention-following invocation `detect…py .` errored out on
    # the first command of every run (RUN-001 finding 1).
    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Project root. Detection runs against it and YAML is written to "
        "<root>/.bagel/runtime_capabilities.yaml unless --out is given. "
        "Omit (or pass nothing) to print to stdout.",
    )
    parser.add_argument(
        "--out",
        help="Write YAML to this explicit path instead of the <root> default / stdout",
    )
    args = parser.parse_args()

    # When a root is given, detect against it (git-repo probe is cwd-sensitive).
    if args.root is not None:
        root = Path(args.root).resolve()
        if root.is_dir():
            os.chdir(root)
        out_path = Path(args.out) if args.out else root / ".bagel" / "runtime_capabilities.yaml"
    else:
        out_path = Path(args.out) if args.out else None

    output = render_yaml()
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"runtime capabilities written to {out_path}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
