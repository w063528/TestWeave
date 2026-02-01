from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _qa_dir(root: Path) -> Path:
    return root / ".qa"


def _cycles_file(root: Path) -> Path:
    return _qa_dir(root) / "cycles.json"


def cycles_file_path(root: Path) -> Path:
    return _cycles_file(root.resolve())


def _normalize_cycle_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        raise ValueError("Cycle name is required.")
    for b in ["\n", "\r", "\t"]:
        n = n.replace(b, " ")
    n = " ".join(n.split())
    if len(n) > 120:
        raise ValueError("Cycle name is too long (max 120).")
    return n


def _member_key(tc_id: str, uri: str) -> str:
    return f"{tc_id}|{uri}"


@dataclass
class CycleMember:
    tc_id: str
    title: str
    uri: str
    line1: int | None = None
    feature: str | None = None
    addedAt: str | None = None

    def key(self) -> str:
        return _member_key(self.tc_id, self.uri)


@dataclass
class Cycle:
    name: str
    createdAt: str
    updatedAt: str
    members: list[CycleMember]

    def touch(self) -> None:
        self.updatedAt = _now_iso()


@dataclass
class CyclesDoc:
    version: int
    cycles: list[Cycle]


def _to_int(v: Any) -> int | None:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None


def _load_doc(root: Path) -> CyclesDoc:
    root = root.resolve()
    cf = _cycles_file(root)
    if not cf.exists():
        return CyclesDoc(version=1, cycles=[])

    try:
        raw = json.loads(cf.read_text(encoding="utf-8"))
    except Exception:
        return CyclesDoc(version=1, cycles=[])

    version = int(raw.get("version") or 1)
    cycles_raw = raw.get("cycles") or []

    cycles: list[Cycle] = []
    for c in cycles_raw:
        try:
            name = _normalize_cycle_name(c.get("name", ""))
            createdAt = (c.get("createdAt") or _now_iso())
            updatedAt = (c.get("updatedAt") or createdAt)
            members_raw = c.get("members") or []
            members: list[CycleMember] = []
            for m in members_raw:
                tc_id = (m.get("tc_id") or "").strip()
                title = (m.get("title") or "").strip()
                uri = (m.get("uri") or "").strip()
                if not (tc_id and uri):
                    continue
                members.append(
                    CycleMember(
                        tc_id=tc_id,
                        title=title or tc_id,
                        uri=uri,
                        line1=_to_int(m.get("line1")),
                        feature=(m.get("feature") or None),
                        addedAt=(m.get("addedAt") or None),
                    )
                )
            cycles.append(Cycle(name=name, createdAt=createdAt, updatedAt=updatedAt, members=members))
        except Exception:
            continue

    return CyclesDoc(version=version, cycles=cycles)


def _save_doc(root: Path, doc: CyclesDoc) -> None:
    root = root.resolve()
    qa = _qa_dir(root)
    qa.mkdir(parents=True, exist_ok=True)
    cf = _cycles_file(root)

    payload = {
        "version": doc.version,
        "cycles": [
            {
                "name": c.name,
                "createdAt": c.createdAt,
                "updatedAt": c.updatedAt,
                "members": [
                    {
                        "tc_id": m.tc_id,
                        "title": m.title,
                        "feature": m.feature,
                        "uri": m.uri,
                        "line1": m.line1,
                        "addedAt": m.addedAt,
                    }
                    for m in c.members
                ],
            }
            for c in doc.cycles
        ],
    }
    cf.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------
# Public API
# ---------------------------

def list_cycles(root: Path) -> list[dict[str, Any]]:
    doc = _load_doc(root)
    out: list[dict[str, Any]] = []
    for c in sorted(doc.cycles, key=lambda x: x.updatedAt, reverse=True):
        out.append(
            {
                "name": c.name,
                "createdAt": c.createdAt,
                "updatedAt": c.updatedAt,
                "membersCount": len(c.members),
            }
        )
    return out


def get_cycle(root: Path, name: str) -> Cycle | None:
    n = _normalize_cycle_name(name)
    doc = _load_doc(root)
    for c in doc.cycles:
        if c.name == n:
            return c
    return None


def ensure_cycle(root: Path, name: str) -> Cycle:
    n = _normalize_cycle_name(name)
    doc = _load_doc(root)

    for c in doc.cycles:
        if c.name == n:
            return c

    now = _now_iso()
    c = Cycle(name=n, createdAt=now, updatedAt=now, members=[])
    doc.cycles.append(c)
    _save_doc(root, doc)
    return c


def add_members(root: Path, cycle_names: list[str], members: list[CycleMember]) -> dict[str, Any]:
    if not cycle_names:
        raise ValueError("cycle_names is required.")
    if not members:
        raise ValueError("members is required.")

    names = [_normalize_cycle_name(n) for n in cycle_names]
    doc = _load_doc(root)

    name_to_cycle: dict[str, Cycle] = {c.name: c for c in doc.cycles}
    now = _now_iso()
    for n in names:
        if n not in name_to_cycle:
            c = Cycle(name=n, createdAt=now, updatedAt=now, members=[])
            doc.cycles.append(c)
            name_to_cycle[n] = c

    norm_members: list[CycleMember] = []
    for m in members:
        tc_id = (m.tc_id or "").strip()
        uri = (m.uri or "").strip()
        if not (tc_id and uri):
            continue
        title = (m.title or "").strip() or tc_id
        norm_members.append(
            CycleMember(
                tc_id=tc_id,
                title=title,
                uri=uri,
                line1=m.line1,
                feature=m.feature,
                addedAt=m.addedAt or now,
            )
        )

    result: dict[str, Any] = {"cycles": []}

    for n in names:
        c = name_to_cycle[n]
        existing = {mm.key() for mm in c.members}

        added = 0
        skipped = 0
        for m in norm_members:
            k = m.key()
            if k in existing:
                skipped += 1
                continue
            c.members.append(m)
            existing.add(k)
            added += 1

        if added > 0:
            c.touch()

        result["cycles"].append({"name": c.name, "added": added, "skipped": skipped})

    _save_doc(root, doc)
    return result


def remove_members(root: Path, cycle_name: str, member_keys: list[str]) -> dict[str, Any]:
    n = _normalize_cycle_name(cycle_name)
    if not member_keys:
        raise ValueError("member_keys is required.")

    doc = _load_doc(root)
    c = None
    for cc in doc.cycles:
        if cc.name == n:
            c = cc
            break
    if c is None:
        raise ValueError(f"Cycle not found: {n}")

    before = len(c.members)
    keys = set(member_keys)
    c.members = [m for m in c.members if m.key() not in keys]
    removed = before - len(c.members)

    if removed > 0:
        c.touch()
        _save_doc(root, doc)

    return {"name": c.name, "removed": removed, "membersCount": len(c.members)}