from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


ENV_FILE = ".env"
ENV_KEY_CMD = "CODEX_CLI"
ENV_KEY_MODE = "CODEX_MODE"  # "exec" or "stdin"
ENV_KEY_APPROVALS = "CODEX_APPROVALS"  # never|on-request|on-failure|untrusted
ENV_KEY_NO_TUI = "CODEX_NO_TUI"  # "1" to prefer --no-tui when supported
ENV_KEY_FULL_AUTO = "CODEX_FULL_AUTO"  # "1" to add --full-auto
ENV_KEY_YOLO = "CODEX_YOLO"  # "1" to add --yolo (danger: disables sandbox + approvals)
ENV_KEY_FLAGS = "CODEX_FLAGS"  # extra flags appended to command
ENV_KEY_PROFILE = "CODEX_PROFILE"  # --profile <name>
ENV_KEY_JSON = "CODEX_JSON"  # "1" to add --json
ENV_KEY_OUTPUT = "CODEX_OUTPUT"  # -o <path>
ENV_KEY_RESUME_LAST = "CODEX_RESUME_LAST"  # "1" to use: exec resume --last


def _load_env(root: Path) -> None:
    """Load a simple .env file (KEY=VALUE lines) into os.environ.

    This avoids adding dependencies just to read .env. Lines starting with
    '#' are ignored. Quotes around values are stripped.
    """

    env_path = root / ENV_FILE
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("\"\'")
            if key and val is not None:
                os.environ.setdefault(key, val)
    except Exception:
        # Best-effort; ignore malformed files
        pass


def _split_command(cmd: str) -> List[str]:
    """Split command string into args. Use Windows-compatible splitting."""

    # On Windows, many commands are batch files; we'll prefer shell=True later
    # but still provide a parsed argv when possible.
    try:
        return shlex.split(cmd, posix=(os.name != "nt"))
    except Exception:
        return [cmd]


def run_codex(prompt: str, cwd: Path) -> str:
    """Run Codex CLI in non-interactive mode (preferred) or via stdin.

    - Command: from `CODEX_CLI` or default `npx -y @openai/codex`.
    - Mode: `CODEX_MODE=exec|stdin` (default: exec).
    - Approvals: `CODEX_APPROVALS` sets `-a/--ask-for-approval <mode>` in exec mode.
    - No TUI: `CODEX_NO_TUI=1` prefers `--no-tui` when the CLI supports it.
    - Full auto: `CODEX_FULL_AUTO=1` adds `--full-auto` (equiv: sandbox workspace-write + approvals on-failure).
    - YOLO: `CODEX_YOLO=1` adds `--yolo` (danger: disables sandbox and approvals; overrides approvals flag here).
    - Extra flags: `CODEX_FLAGS` appended as-is in exec mode.
    The prompt is passed as an argument in exec mode, or via stdin otherwise.
    """

    root = Path.cwd()
    _load_env(root)

    cmd_base = os.environ.get(ENV_KEY_CMD, "npx -y @openai/codex")
    mode = (os.environ.get(ENV_KEY_MODE, "exec") or "exec").lower()
    approvals = (os.environ.get(ENV_KEY_APPROVALS, "") or "").strip()
    no_tui = (os.environ.get(ENV_KEY_NO_TUI, "1") == "1")
    full_auto = (os.environ.get(ENV_KEY_FULL_AUTO, "0") == "1")
    yolo = (os.environ.get(ENV_KEY_YOLO, "0") == "1")
    extra = os.environ.get(ENV_KEY_FLAGS, "").strip()
    profile = (os.environ.get(ENV_KEY_PROFILE, "") or "").strip()
    want_json = (os.environ.get(ENV_KEY_JSON, "0") == "1")
    out_path = (os.environ.get(ENV_KEY_OUTPUT, "") or "").strip()
    resume_last = (os.environ.get(ENV_KEY_RESUME_LAST, "0") == "1")

    use_shell = os.name == "nt"

    def _popen(cmd: str, stdin_text: Optional[str]) -> subprocess.Popen:
        argv: Optional[List[str]] = None if use_shell else _split_command(cmd)
        return subprocess.Popen(
            argv or cmd,
            cwd=str(cwd),
            stdin=(subprocess.PIPE if stdin_text is not None else None),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=use_shell,
        )

    if mode == "exec":
        def q(s: str) -> str:
            return '"' + s.replace('"', '\\"') + '"'

        def build_cmd(use_cd_flag: bool, include_no_tui: bool) -> str:
            cd_flag = "--cd" if use_cd_flag else "-C"
            parts: List[str] = [cmd_base, "exec", cd_flag, q(str(cwd))]
            if resume_last:
                parts += ["resume", "--last"]
            if profile:
                parts += ["--profile", q(profile)]
            if yolo:
                parts.append("--yolo")
            elif approvals:
                parts += ["-a", q(approvals)]
            if include_no_tui:
                parts.append("--no-tui")
            if full_auto and not yolo:
                parts.append("--full-auto")
            if want_json:
                parts.append("--json")
            if out_path:
                parts += ["-o", q(out_path)]
            if extra:
                parts.append(extra)
            parts.append(q(prompt))
            return " ".join(parts)

        def launch(cmd_str: str) -> subprocess.Popen:
            try:
                return _popen(cmd_str, None)
            except FileNotFoundError as exc:
                raise FileNotFoundError(
                    f"[ERREUR] Commande introuvable: {cmd_base}\n"
                    f"Vérifiez CODEX_CLI dans .env (ex.: npx -y @openai/codex).\n\n{exc}"
                ) from exc
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"[ERREUR] Échec de lancement: {cmd_str}\n{exc}") from exc

        notes: List[str] = []
        use_cd_flag = True
        include_no_tui = no_tui
        attempted_cd_fallback = False
        attempted_no_tui_fallback = False

        while True:
            cmd_str = build_cmd(use_cd_flag, include_no_tui)
            try:
                proc = launch(cmd_str)
            except (FileNotFoundError, RuntimeError) as exc:  # surface message as string
                return str(exc)

            try:
                out, err = proc.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                proc.kill()
                return (
                    "[ERREUR] Délai dépassé (120s) en attendant la réponse de Codex.\n"
                    "Vérifiez la commande CODEX_CLI, le réseau et les flags."
                )
            except Exception as exc:  # noqa: BLE001
                proc.kill()
                return f"[ERREUR] Échec de la communication avec le processus Codex: {exc}"

            err_text = (err or "").strip()
            if (
                include_no_tui
                and not attempted_no_tui_fallback
                and "--no-tui" in err_text
                and "unexpected argument" in err_text.lower()
            ):
                attempted_no_tui_fallback = True
                include_no_tui = False
                notes.append(
                    "[INFO] Relance sans --no-tui (non reconnu par cette version de Codex)."
                )
                continue

            if (
                use_cd_flag
                and not attempted_cd_fallback
                and "--cd" in err_text
                and ("no such option" in err_text.lower() or "unknown option" in err_text.lower())
            ):
                attempted_cd_fallback = True
                use_cd_flag = False
                notes.append("[INFO] Relance avec -C (ancienne version du CLI détectée).")
                continue

            combined = (out or "").strip()
            if err_text:
                combined = (
                    f"{combined}\n[stderr]\n{err_text}"
                    if combined
                    else f"[stderr]\n{err_text}"
                )

            if notes:
                notes_text = "\n".join(notes)
                combined = f"{notes_text}\n{combined}" if combined else notes_text

            if proc.returncode not in (0, None):
                combined = (
                    f"[AVERTISSEMENT] Code de sortie {proc.returncode}.\n" + combined
                )

            return combined or "(aucune sortie)"
    else:
        # stdin mode
        cmd_str = cmd_base
        try:
            proc = _popen(cmd_str, prompt + "\n")
        except FileNotFoundError as exc:
            return (
                f"[ERREUR] Commande introuvable: {cmd_base}\n"
                f"Vérifiez CODEX_CLI dans .env (ex.: npx -y @openai/codex).\n\n{exc}"
            )
        except Exception as exc:  # noqa: BLE001
            return f"[ERREUR] Échec de lancement: {cmd_str}\n{exc}"

    try:
        inp = None if mode == "exec" else (prompt + "\n")
        out, err = proc.communicate(input=inp, timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        return (
            "[ERREUR] Délai dépassé (120s) en attendant la réponse de Codex.\n"
            "Vérifiez la commande CODEX_CLI, le réseau et les flags."
        )
    except Exception as exc:  # noqa: BLE001
        proc.kill()
        return f"[ERREUR] Échec de la communication avec le processus Codex: {exc}"

    combined = (out or "").strip()
    if err:
        combined = f"{combined}\n[stderr]\n{err.strip()}" if combined else f"[stderr]\n{err.strip()}"
    if proc.returncode not in (0, None):
        combined = (
            f"[AVERTISSEMENT] Code de sortie {proc.returncode}.\n" + combined
        )
    return combined or "(aucune sortie)"
