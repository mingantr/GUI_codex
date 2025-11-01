"""Helper to launch the Codex CLI in non-interactive mode.

This module exposes :func:`run_codex` mirroring the workflow requested by
power users who want to drive ``codex exec`` programmatically.  It handles
common pitfalls on Windows (missing shell, timeout behaviour, quoting) and
surfaces the executed command together with stdout/stderr so callers can log
or debug failures easily.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CodexResult:
    """Result container returned by :func:`run_codex`."""

    returncode: int
    stdout: str
    stderr: str
    cmd: List[str]


class CodexNotFoundError(RuntimeError):
    """Raised when the ``codex`` binary is not found on the system PATH."""


def _ensure_codex_binary() -> str:
    codex_path = shutil.which("codex")
    if codex_path is None:
        raise CodexNotFoundError(
            "Le binaire 'codex' est introuvable. Installe-le avec: "
            "npm install -g @openai/codex"
        )
    return codex_path


def run_codex(
    prompt: str,
    project_dir: Optional[str] = None,
    model: Optional[str] = None,
    approval_mode: str = "full-auto",
    skip_git_repo_check: bool = True,
    quiet: bool = True,
    json_events: bool = False,
    extra_flags: Optional[List[str]] = None,
    timeout: int = 600,
) -> CodexResult:
    """Execute the Codex CLI and return its output.

    Parameters are intentionally aligned with the long explanation shared in the
    support thread so the wrapper can be copied as-is.  The ``--`` separator is
    injected automatically to guarantee every flag is forwarded to the agent
    itself, avoiding the "unexpected argument" error seen on older CLI builds.
    """

    codex_path = _ensure_codex_binary()

    cmd: List[str] = [codex_path, "exec"]

    if project_dir:
        cmd += ["--cd", project_dir]

    cmd.append("--")

    if approval_mode:
        cmd += ["--approval-mode", approval_mode]
    if skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    if model:
        cmd += ["--model", model]
    if quiet:
        cmd.append("--quiet")
    if json_events:
        cmd.append("--json")
    if extra_flags:
        cmd.extend(extra_flags)

    cmd.append(prompt)

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    return CodexResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        cmd=cmd,
    )


if __name__ == "__main__":
    example_prompt = (
        "je ne veux pas d'onglets, mais la base de données, et les casiers sur 2 colonnes"
    )
    try:
        result = run_codex(
            prompt=example_prompt,
            project_dir=r"D:\devs\pyqt5\gwen_test",
            model="gpt-5-codex",
            approval_mode="full-auto",
            skip_git_repo_check=True,
            quiet=True,
            json_events=False,
            extra_flags=None,
            timeout=900,
        )
    except CodexNotFoundError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.exit(127)
    except subprocess.TimeoutExpired:
        sys.stderr.write("Codex a dépassé le délai d'exécution.\n")
        sys.exit(124)
    else:
        sys.stdout.write(result.stdout)
        if result.returncode != 0:
            sys.stderr.write("\n[Codex stderr]\n")
            sys.stderr.write(result.stderr)
            sys.stderr.write("\n[Command used]\n")
            sys.stderr.write(" ".join(result.cmd) + "\n")
            sys.exit(result.returncode)
