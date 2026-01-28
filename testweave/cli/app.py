from __future__ import annotations

import importlib
from typing import Iterable

import click


def _find_click_command(module_path: str, preferred_names: Iterable[str]) -> click.Command | None:
    """
    Return a click.Command if found in the module, otherwise None.
    This must NEVER raise on missing commands (so server can still run).
    """
    try:
        mod = importlib.import_module(module_path)
    except Exception:
        return None

    # 1) Try preferred variable names first
    for name in preferred_names:
        obj = getattr(mod, name, None)
        if isinstance(obj, click.core.Command):
            return obj  # type: ignore[return-value]

    # 2) Fallback: first click.Command in module
    for _, obj in vars(mod).items():
        if isinstance(obj, click.core.Command):
            return obj  # type: ignore[return-value]

    return None


@click.group()
def main() -> None:
    """TestWeave CLI"""
    pass


def _register_if_exists(module_path: str, preferred_names: list[str]) -> None:
    cmd = _find_click_command(module_path, preferred_names)
    if cmd is not None:
        main.add_command(cmd)


# ✅ server는 Step 2 필수이므로 반드시 등록 (없으면 여기서 바로 에러 나게)
from testweave.cli.server import server as server_cmd  # noqa: E402

main.add_command(server_cmd)

# 나머지 커맨드는 “있으면 등록 / 없으면 스킵”
# (scan.py 등이 click.Command가 아니어도 서버가 죽지 않게 함)
_register_if_exists("testweave.cli.scan", ["scan", "scan_cmd", "cmd", "command", "cli", "main"])
_register_if_exists("testweave.cli.cycle", ["cycle", "cycle_cmd", "cmd", "command", "cli", "main"])
_register_if_exists("testweave.cli.run", ["run", "run_cmd", "cmd", "command", "cli", "main"])
_register_if_exists("testweave.cli.report", ["report", "report_cmd", "cmd", "command", "cli", "main"])


if __name__ == "__main__":
    main()