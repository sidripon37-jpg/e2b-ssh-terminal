#!/usr/bin/env python3
# Made for sidripon37
"""
sidripon37's E2B SSH Terminal
Fast, reliable, cloud sandbox manager powered by E2B.
"""

from __future__ import annotations
import getpass
import json
import os
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from e2b import Sandbox
except Exception:
    Sandbox = None

APP_DIR = Path.home() / ".e2b_ssh"
CONFIG_FILE = APP_DIR / "config.json"
DEFAULT_TEMPLATE = "base"
DEFAULT_CWD = "/home/user"
DEFAULT_KEY = "e2b_55e129b4ff017d29acad08f5a9ce717089411230"
OWNER_NAME = "sidripon37"

class C:
    reset = "\033[0m"
    bold = "\033[1m"
    dim = "\033[2m"
    red = "\033[91m"
    green = "\033[92m"
    yellow = "\033[93m"
    blue = "\033[94m"
    cyan = "\033[96m"

def color(text: str, c: str) -> str:
    return c + text + C.reset if not os.environ.get("NO_COLOR") else text

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def pause() -> None:
    input(color("\npress enter...", C.dim))

def banner() -> None:
    clear()
    art = f"""
{C.cyan}{C.bold}╔══════════════════════════════════════════════════════════════╗
║                E 2 B   S S H   T E R M I N A L             ║
║                       by {OWNER_NAME:<36}║
╚══════════════════════════════════════════════════════════════╝{C.reset}
""".rstrip()
    print(art)
    print(color("simple · fast · reliable sandbox terminal · no web panel\n", C.dim))

def ok(msg: str) -> None: print(color("✓ ", C.green) + msg)
def warn(msg: str) -> None: print(color("! ", C.yellow) + msg)
def bad(msg: str) -> None: print(color("✗ ", C.red) + msg)
def info(msg: str) -> None: print(color("› ", C.cyan) + msg)

def load_config() -> Dict[str, Any]:
    try: return json.loads(CONFIG_FILE.read_text())
    except Exception: return {}

def save_config(cfg: Dict[str, Any]) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def require_sdk() -> None:
    if Sandbox is None:
        bad("e2b SDK is not installed")
        print("\nInstall it:\n  pip install e2b")
        sys.exit(2)

def setup_api_key() -> str:
    cfg = load_config()
    if cfg.get("api_key"): return str(cfg["api_key"])
    if os.environ.get("E2B_API_KEY"): return os.environ["E2B_API_KEY"]
    key = DEFAULT_KEY
    cfg["api_key"] = key
    save_config(cfg)
    return key

def set_current(sandbox_id: str) -> None:
    cfg = load_config()
    cfg["current_sandbox"] = sandbox_id
    cfg.setdefault("cwd", {})[sandbox_id] = cfg.setdefault("cwd", {}).get(sandbox_id, DEFAULT_CWD)
    save_config(cfg)

def get_current() -> str: return str(load_config().get("current_sandbox", ""))
def get_cwd(sandbox_id: str) -> str: return str(load_config().get("cwd", {}).get(sandbox_id, DEFAULT_CWD))
def set_cwd(sandbox_id: str, cwd: str) -> None:
    cfg = load_config()
    cfg.setdefault("cwd", {})[sandbox_id] = cwd
    save_config(cfg)

def reset_api_key() -> None:
    cfg = load_config()
    cfg.pop("api_key", None)
    save_config(cfg)
    warn("API key removed.")

def sid_of(sb: Any) -> str:
    return str(getattr(sb, "sandbox_id", None) or getattr(sb, "id", None) or "unknown")

def connect(api_key: str, sandbox_id: Optional[str] = None) -> Any:
    require_sdk()
    sid = sandbox_id or get_current()
    if not sid: sid = input("Sandbox ID: ").strip()
    if not sid: raise RuntimeError("No sandbox selected")
    sb = Sandbox.connect(sid, api_key=api_key)
    try: sb.set_timeout(3600)
    except Exception: pass
    set_current(sid_of(sb))
    return sb

def create(api_key: str) -> Any:
    require_sdk()
    template = input(f"Template [{DEFAULT_TEMPLATE}]: ").strip() or DEFAULT_TEMPLATE
    info(f"creating E2B sandbox template={template} (1 hour timeout) ...")
    sb = Sandbox.create(template=template, api_key=api_key, timeout=3600)
    sid = sid_of(sb)
    set_current(sid)
    ok(f"created {sid}")
    show_info(sb)
    return sb

def show_info(sb: Any) -> None:
    sid = sid_of(sb)
    print()
    print(color("Sandbox Info", C.bold + C.cyan))
    print(color("─" * 40, C.dim))
    print(f"sandbox_id    : {sid}")
    print(f"status        : active")
    print(f"timeout       : 3600 seconds (auto-refreshed on use)")
    print(f"workspace     : /home/user\n")

def list_sandboxes(api_key: str) -> None:
    require_sdk()
    info("fetching active sandboxes...")
    try:
        boxes = list(Sandbox.list(api_key=api_key))
        if not boxes:
            warn("No active sandboxes found on account")
            return
        print()
        print(color("#   Sandbox ID                         Status", C.bold))
        print(color("─" * 50, C.dim))
        for i, sb in enumerate(boxes, 1):
            sid = sid_of(sb)
            mark = "*" if sid == get_current() else " "
            print(f"{mark}{i:<3} {sid:<34} active")
        print()
    except Exception as e:
        warn(f"Could not list sandboxes: {e}")

def action(api_key: str, name: str) -> None:
    sb = connect(api_key)
    sid = sid_of(sb)
    if name in ("stop", "delete"):
        confirm = input(color(f"Delete/Kill {sid} permanently? type DELETE: ", C.red)).strip()
        if confirm != "DELETE":
            warn("cancelled")
            return
        sb.kill()
        ok(f"deleted {sid}")
        cfg = load_config()
        if cfg.get("current_sandbox") == sid: cfg.pop("current_sandbox", None)
        cfg.get("cwd", {}).pop(sid, None)
        save_config(cfg)

def run_command(sb: Any, command: str, cwd: str, timeout: int = 300) -> Tuple[str, str, int, str]:
    marker = "__E2B_SSH_CWD__"
    safe_cwd = shlex.quote(cwd)
    wrapped = (
        f"cd {safe_cwd} 2>/dev/null || cd /home/user 2>/dev/null || cd /\n"
        f"{command}\n"
        f"__e2b_ssh_code=$?\n"
        f"printf '\\n{marker}:%s\\n' "$PWD"\n"
        f"exit $__e2b_ssh_code\n"
    )
    stdout, stderr, code = "", "", 0
    try:
        sb.set_timeout(3600)
        res = sb.commands.run(wrapped, timeout=timeout)
        stdout = str(getattr(res, "stdout", "") or "")
        stderr = str(getattr(res, "stderr", "") or "")
        code = int(getattr(res, "exit_code", 0) or 0)
    except Exception as e:
        stderr = str(e)
        code = 1

    new_cwd = cwd
    if marker + ":" in stdout:
        before, _, after = stdout.rpartition(marker + ":")
        stdout = before.rstrip("\n") + ("\n" if before.rstrip("\n") else "")
        new_cwd = after.splitlines()[0].strip() or cwd
    return stdout, stderr, code, new_cwd

def terminal_help() -> None:
    print(color("""
Terminal commands:
  help / :help              show this
  exit / :exit              exit terminal, keep sandbox running
  clear                     clear screen
  info                      sandbox info
  files [path]              list remote files
  cat <file>                read remote file
  upload <local> <remote>   upload text file
  download <remote> <local> download text file
  py                        paste Python code, end with EOF
  delete                    delete sandbox and exit

Anything else runs as shell command in the sandbox.
Examples:
  pwd
  ls -la
  whoami
  pip install requests
  python3 --version
""".strip(), C.cyan))

def paste_until_eof(language: str) -> str:
    print(f"Paste {language} code. End with a single line: EOF")
    lines = []
    while True:
        line = input()
        if line.strip() == "EOF": break
        lines.append(line)
    return "\n".join(lines)

def terminal(api_key: str) -> None:
    try:
        sb = connect(api_key)
    except Exception as e:
        bad(f"Cannot connect: {e}")
        warn("Sandbox may have expired. Create a new one using option 1.")
        return

    sid = sid_of(sb)
    cwd = get_cwd(sid)
    clear()
    ok(f"connected terminal: {sid}")
    print(color("type 'help' for special commands, 'exit' to return to menu\n", C.dim))

    while True:
        try:
            cmd = input(color(f"{sid[:8]}:{cwd}$ ", C.cyan + C.bold)).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return

        if not cmd: continue
        if cmd in {"exit", ":exit", "quit"}:
            warn("returning to menu; sandbox still running")
            return
        if cmd in {"help", ":help"}:
            terminal_help()
            continue
        if cmd == "clear":
            clear(); continue
        if cmd == "info":
            show_info(sb); continue
        if cmd.startswith("files"):
            try:
                parts = shlex.split(cmd)
                path = parts[1] if len(parts) > 1 else cwd
                for f in sb.files.list(path):
                    print(f"- {getattr(f, 'name', str(f))}")
            except Exception as e:
                bad(str(e))
            continue
        if cmd.startswith("cat "):
            try:
                print(sb.files.read(shlex.split(cmd)[1]))
            except Exception as e:
                bad(str(e))
            continue
        if cmd.startswith("upload "):
            try:
                _, local, remote = shlex.split(cmd)
                data = Path(local).read_text(errors="replace")
                sb.files.write(remote, data)
                ok(f"uploaded {local} -> {remote}")
            except Exception as e:
                bad(str(e))
            continue
        if cmd.startswith("download "):
            try:
                _, remote, local = shlex.split(cmd)
                data = sb.files.read(remote)
                Path(local).write_text(str(data))
                ok(f"downloaded {remote} -> {local}")
            except Exception as e:
                bad(str(e))
            continue
        if cmd == "py":
            code = paste_until_eof("Python")
            res = sb.commands.run(f"python3 -c {shlex.quote(code)}")
            out = getattr(res, "stdout", "") or ""
            err = getattr(res, "stderr", "") or ""
            if out: print(out.rstrip())
            if err: print(color(err.rstrip(), C.red))
            continue
        if cmd == "delete":
            confirm = input(color("Delete sandbox permanently? type DELETE: ", C.red)).strip()
            if confirm == "DELETE":
                sb.kill()
                ok("deleted")
                return
            warn("cancelled")
            continue

        try:
            stdout, stderr, code, cwd = run_command(sb, cmd, cwd)
            set_cwd(sid, cwd)
            if stdout: print(stdout.rstrip("\n"))
            if stderr: print(color(stderr.rstrip("\n"), C.red), file=sys.stderr)
        except Exception as e:
            bad(str(e))

def menu(api_key: str) -> None:
    while True:
        banner()
        current = get_current()
        print(color(f"Current sandbox: {current or 'none selected'}", C.bold))
        print()
        print("1) create")
        print("2) stop / delete")
        print("3) connect existing")
        print("4) terminal")
        print("5) exit")
        print(color("\nMore:", C.dim))
        print("6) list sandboxes")
        print("7) info")
        print("8) change API key")
        print()
        choice = input(color("Choose: ", C.cyan)).strip().lower()
        try:
            if choice == "1":
                create(api_key); pause()
            elif choice == "2":
                action(api_key, "delete"); pause()
            elif choice == "3":
                sid = input("Paste Sandbox ID: ").strip()
                if sid: set_current(sid); ok(f"selected {sid}")
                pause()
            elif choice == "4":
                terminal(api_key)
                pause()
            elif choice in {"5", "exit", "q", "quit"}:
                ok(f"Goodbye {OWNER_NAME}!"); return
            elif choice == "6":
                list_sandboxes(api_key); pause()
            elif choice == "7":
                show_info(connect(api_key)); pause()
            elif choice == "8":
                reset_api_key(); return
            else:
                warn("invalid choice"); time.sleep(0.8)
        except Exception as e:
            bad(str(e)); pause()

def main() -> None:
    require_sdk()
    api_key = setup_api_key()
    menu(api_key)

if __name__ == "__main__":
    main()
