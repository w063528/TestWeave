from __future__ import annotations

import argparse

from testweave import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="testweave",
        description="TestWeave - local-first test management core (Python).",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True)

    # scan
    scan_p = sub.add_parser("scan", help="Scan test cases from specs")
    scan_p.add_argument("--root", default=".", help="Workspace root directory")

    # cycle
    cycle_p = sub.add_parser("cycle", help="Manage test cycles")
    cycle_sub = cycle_p.add_subparsers(dest="cycle_cmd", required=True)
    cycle_sub.add_parser("list", help="List cycles")
    create_p = cycle_sub.add_parser("create", help="Create a cycle")
    create_p.add_argument("name", help="Cycle name (e.g., 2026-01)")

    # report
    rep_p = sub.add_parser("report", help="Export reports")
    rep_p.add_argument("--cycle", default="", help="Cycle name (optional)")
    rep_p.add_argument("--out", default="report", help="Output directory")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # For now, just confirm wiring works.
    if args.cmd == "scan":
        print(f"[testweave] scan requested (root={args.root})")
        return 0

    if args.cmd == "cycle":
        if args.cycle_cmd == "list":
            print("[testweave] cycle list requested")
            return 0
        if args.cycle_cmd == "create":
            print(f"[testweave] cycle create requested (name={args.name})")
            return 0

    if args.cmd == "report":
        print(f"[testweave] report requested (cycle={args.cycle}, out={args.out})")
        return 0

    parser.print_help()
    return 1
