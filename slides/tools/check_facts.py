#!/usr/bin/env python3
"""Kiểm các file tài liệu trong slides/ còn khớp mã nguồn hiện tại không (chạy sau MỖI lần mã đổi, và trước khi dán prompt cho Antigravity).

Chạy:  python3 -I slides/tools/check_facts.py            kiểm nhanh, chỉ cần Python chuẩn (không import mã dự án)
       python3 -I slides/tools/check_facts.py --deep     thêm: tính lại các số tính được (cần .venv của dự án, mất ~15 giây)

Làm ba việc:
  1. Hằng số: so khối ```facts``` ở cuối 05_SO_LIEU_VA_NGUON.md (mục 17) với firmware, control.py, success.py, vision.py, calibration.json và số dòng.
  2. Dẫn `tệp:dòng`: mọi dẫn dạng `control.py:36-51` trong slides/*.md phải trỏ vào tệp còn tồn tại và dòng còn nằm trong tệp.
  3. Tên cũ: tên tệp đã xóa khi đơn giản hóa (grasp_assist_4dof, guide_screen...) chỉ được nhắc ở dòng nói rõ là bản cũ / đã bỏ.

Dòng cuối luôn là `KHỚP` hoặc `LỆCH (N chỗ)`. Mã thoát 0 khi KHỚP, 1 khi LỆCH.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLIDES = ROOT / "slides"
DOCS = sorted(SLIDES.glob("0[0-6]_*.md"))
INO = ROOT / "robot_arm_4dof" / "robot_arm_4dof.ino"
PY_MODULES = ("main.py", "control.py", "success.py", "screen.py", "vision.py", "cameras.py", "calibration.py")
SKIP_DIRS = {".venv", ".git", "__pycache__", "captures", ".idea", ".pytest_cache", "slides", "node_modules", "build", "out"}
STALE_NAMES = ("grasp_assist_4dof", "guide_screen", "simple_screen", "test_ik.py")
STALE_OK_WORDS = ("cũ", "đã bỏ", "đã xóa", "bị xóa", "xóa khỏi", "1 commit", "chưa commit", "bản 5 bước", "lịch sử", "CẤM", "đã bỏ khi")


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def fmt(value) -> str:
    """Số nguyên hiện không có phần thập phân (70.0 -> 70); còn lại giữ nguyên."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def same(doc: str, live: str) -> bool:
    """So từng token; token là số thì so số, còn lại so chuỗi."""
    a, b = doc.split(), live.split()
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        kx, _, vx = x.rpartition(":")
        ky, _, vy = y.rpartition(":")
        if kx != ky:
            return False
        try:
            if abs(float(vx) - float(vy)) > 1e-6:
                return False
        except ValueError:
            if vx != vy:
                return False
    return True


def define(text: str, name: str):
    m = re.search(rf"#define\s+{name}\s+(\d+)", text)
    return int(m.group(1)) if m else None


def py_literal(path: Path, name: str):
    text = read(path)
    if text is None:
        return None
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return None
    return None


def line_count(path: Path) -> int | None:
    """Số dòng của tệp (dòng cuối không có xuống dòng vẫn tính), dùng để kiểm dòng dẫn."""
    text = read(path)
    return None if text is None else text.count("\n") + (0 if text.endswith("\n") or not text else 1)


def wc_l(path: Path) -> int | None:
    """Đúng như `wc -l`: đếm ký tự xuống dòng. Dùng cho các số trong tài liệu."""
    text = read(path)
    return None if text is None else text.count("\n")


def doc_facts() -> dict[str, str]:
    text = read(SLIDES / "05_SO_LIEU_VA_NGUON.md") or ""
    m = re.search(r"```facts\n(.*?)```", text, re.S)
    out = {}
    for line in (m.group(1) if m else "").splitlines():
        if "=" in line:
            key, _, val = line.partition("=")
            out[key.strip()] = val.strip()
    return out


def live_facts() -> dict[str, str | None]:
    f: dict[str, str | None] = {}
    ino = read(INO)
    for name in ("STEP_ARM", "STEP_GRIP", "GRIP_CLOSE_LIMIT", "GRIP_IDLE_RELAX_MS", "GRIP_HOLD_MAX_MS"):
        v = define(ino, name) if ino else None
        f[name] = None if v is None else str(v)
    m = re.search(r"millis\(\)\s*-\s*lastReportMs\s*>=\s*(\d+)", ino or "")
    f["JSON_PERIOD_MS"] = m.group(1) if m else None

    succ = read(ROOT / "success.py") or ""
    for name in ("TOLERANCE_STEPS", "HOLD_S"):
        m = re.search(rf"^{name}\s*=\s*([\d.]+)", succ, re.M)
        f[name] = m.group(1) if m else None

    ctl = ROOT / "control.py"
    steps = py_literal(ctl, "SERVO_STEPS")
    f["SERVO_STEPS"] = " ".join(f"{k}:{fmt(v)}" for k, v in steps.items()) if isinstance(steps, dict) else None
    limits = py_literal(ctl, "SERVO_LIMITS")
    f["SERVO_LIMITS_GRIP"] = " ".join(fmt(x) for x in limits["grip"][:2]) if isinstance(limits, dict) and "grip" in limits else None
    m = re.search(r"^GRASP_Z_MM\s*=\s*([\d.]+)", read(ctl) or "", re.M)
    f["GRASP_Z_MM"] = m.group(1) if m else None
    arm = py_literal(ctl, "ARM_CONFIG")
    if isinstance(arm, dict):
        names = (("d1", "d1_mm"), ("L2", "L2_mm"), ("L3", "L3_mm"), ("L4_r", "L4_r_mm"), ("L4_z", "L4_z_mm"),
                 ("theta2_90", "theta2_at_90_deg"), ("theta3_90", "theta3_at_90_deg"))
        f["ARM_DEFAULT"] = " ".join(f"{short}:{fmt(arm[key])}" for short, key in names if key in arm)
    else:
        f["ARM_DEFAULT"] = None

    m = re.search(r"^CAM_HEIGHT_CM\s*=\s*([\d.]+)", read(ROOT / "vision.py") or "", re.M)
    f["CAM_HEIGHT_CM"] = m.group(1) if m else None

    cal = read(ROOT / "calibration.json")
    try:
        data = json.loads(cal) if cal else None
    except ValueError:
        data = None
    if data is None:
        for key in ("CALIB_BASE", "CALIB_THETA", "CALIB_CLAW", "CALIB_FIT"):
            f[key] = "SKIP"          # calibration.json nằm trong .gitignore nên máy khác không có
    else:
        b, a, c, fit = data.get("base", {}), data.get("arm", {}), data.get("claw", {}), data.get("arm_fit", {})
        f["CALIB_BASE"] = " ".join(fmt(b.get(k)) for k in ("x_cm", "y_cm", "heading_deg")) if b else None
        f["CALIB_THETA"] = " ".join(fmt(a.get(k)) for k in ("theta2_at_90_deg", "theta3_at_90_deg")) if a else None
        f["CALIB_CLAW"] = " ".join(fmt(c.get(k)) for k in ("L3_mm", "L4_r_mm", "L4_z_mm")) if c else None
        f["CALIB_FIT"] = f"n:{fmt(fit.get('n'))} rms:{fmt(fit.get('rms_xy_mm'))} loo:{fmt(fit.get('loo_rms_xy_mm'))}" if fit else None

    counts = [wc_l(ROOT / m) for m in PY_MODULES]
    f["PY_LINES"] = None if any(c is None for c in counts) else str(sum(counts))
    n = wc_l(INO)
    f["FIRMWARE_LINES"] = None if n is None else str(n)
    return f


DEEP_SNIPPET = r"""
import json, math, control as c
from calibration import apply_calibration
hugs = [((85, 60, 90), (16.9, 14.4)), ((80, 70, 75), (13.3, 14.0)), ((75, 85, 50), (10.8, 7.7))]
err = [round(math.hypot(c.predict_tip(s)[0] - u[0], c.predict_tip(s)[1] - u[1]), 1) for s, u in hugs]
apply_calibration(c.ARM_CONFIG)
rx, ry = c.table_cm_to_robot_mm(20.1, 7.4)
ik = c.ik_4dof_joint(rx, ry, c.GRASP_Z_MM)
goal = c.joint_to_servo(ik["theta1_deg"], ik["theta2_deg"], ik["theta3_deg"])
keys = {m.key: m.steps for m in c.plan_moves([90, 90, 90, 95], goal) if m.key}
print(json.dumps({"hug": err, "goal": goal, "keys": keys}))
"""


def deep_facts() -> dict[str, str | None]:
    py = ROOT / ".venv" / "bin" / "python"
    if not py.exists():
        return {k: "SKIP" for k in ("HUG_ERR_CM", "GOAL_CUP_20_1_7_4", "KEYS_FROM_HOME")}
    out: dict[str, str | None] = {}
    r = subprocess.run([str(py), "-B", "-c", DEEP_SNIPPET], cwd=ROOT, capture_output=True, text=True, timeout=120)
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
        out["HUG_ERR_CM"] = " ".join(fmt(x) for x in d["hug"])
        out["GOAL_CUP_20_1_7_4"] = " ".join(str(x) for x in d["goal"][:3])
        out["KEYS_FROM_HOME"] = " ".join(f"{k}:{v}" for k, v in sorted(d["keys"].items()))
    except (ValueError, IndexError):
        for k in ("HUG_ERR_CM", "GOAL_CUP_20_1_7_4", "KEYS_FROM_HOME"):
            out[k] = None
    return out


def file_index() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".py", ".ino", ".json", ".sh", ".md", ".js") and not (set(p.relative_to(ROOT).parts[:-1]) & SKIP_DIRS):
            index.setdefault(p.name, []).append(p)
    return index


CITE = re.compile(r"`([A-Za-z0-9_./-]+\.(?:py|ino|json|sh|md|js)):(\d[\d,–-]*)`")


def check_citations() -> tuple[int, list[str]]:
    index, bad, total = file_index(), [], 0
    for doc in DOCS:
        text = read(doc) or ""
        for ln, line in enumerate(text.splitlines(), 1):
            for m in CITE.finditer(line):
                name, spec = m.group(1), m.group(2)
                total += 1
                if "/" in name:
                    path = ROOT / name if (ROOT / name).exists() else SLIDES / name
                    path = path if path.exists() else None
                else:
                    cands = index.get(name, [])
                    path = cands[0] if cands else None
                where = f"{doc.name}:{ln}"
                if path is None:
                    bad.append(f"HỎNG  {where}: `{name}:{spec}` tệp không còn trong dự án")
                    continue
                n_lines = line_count(path) or 0
                for part in spec.split(","):
                    nums = [int(x) for x in re.split(r"[–-]", part) if x]
                    if not nums:
                        continue
                    if min(nums) < 1 or max(nums) > n_lines or (len(nums) == 2 and nums[0] > nums[1]):
                        bad.append(f"HỎNG  {where}: `{name}:{spec}` dòng {part} ngoài tệp ({n_lines} dòng)")
    return total, bad


def check_stale_names() -> list[str]:
    bad = []
    for doc in DOCS:
        for ln, line in enumerate((read(doc) or "").splitlines(), 1):
            if any(name in line for name in STALE_NAMES) and not any(w in line for w in STALE_OK_WORDS):
                names = ", ".join(n for n in STALE_NAMES if n in line)
                bad.append(f"CŨ    {doc.name}:{ln}: nhắc {names} mà không nói rõ là bản cũ / đã bỏ")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deep", action="store_true", help="tính lại các số tính được bằng .venv của dự án")
    args = ap.parse_args()

    problems = 0
    doc, live = doc_facts(), live_facts()
    if args.deep:
        live.update(deep_facts())
    if not doc:
        print("THIẾU  không đọc được khối ```facts``` trong 05_SO_LIEU_VA_NGUON.md mục 17")
        problems += 1

    print("== 1. Hằng số (05 mục 17) so với mã ==")
    skipped = 0
    for key, want in doc.items():
        got = live.get(key, "SKIP")
        if got == "SKIP" or (not args.deep and key not in live):
            skipped += 1
            print(f"bỏ qua {key} (cần --deep hoặc thiếu calibration.json)")
        elif got is None:
            problems += 1
            print(f"THIẾU  {key}: tài liệu {want!r} nhưng không đọc được từ mã")
        elif same(want, got):
            print(f"KHỚP   {key} = {want}")
        else:
            problems += 1
            print(f"LỆCH   {key}: tài liệu {want!r}, mã {got!r}")
    if skipped:
        print(f"({skipped} mục bỏ qua)")

    print("== 2. Dẫn `tệp:dòng` trong slides/*.md ==")
    total, bad = check_citations()
    print(f"{total} dẫn đã kiểm, {len(bad)} hỏng")
    for msg in bad:
        print(msg)
    problems += len(bad)

    print("== 3. Tên tệp cũ ==")
    stale = check_stale_names()
    print(f"{len(stale)} chỗ nhắc tên cũ không nói rõ là bản cũ")
    for msg in stale:
        print(msg)
    problems += len(stale)

    print("KHỚP" if problems == 0 else f"LỆCH ({problems} chỗ)")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
