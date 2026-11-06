#!/usr/bin/env python3
"""로컬 사진 폴더를 레포에 올리고 인스타 게시(즉시) 또는 예약한다.

사용법:
  python3 scripts/post.py <사진폴더>              # 지금 바로 게시
  python3 scripts/post.py <사진폴더> 2026-11-10   # 해당 날짜 오전 9시(KST) 예약
  python3 scripts/post.py <사진폴더> --dry-run    # 검사만 하고 올리지 않음

사진폴더: JPG/PNG 1~10장 + caption.txt. 파일 이름 순서대로 올라간다.
PNG는 자동으로 JPG로 변환한다(macOS sips 사용).
"""
import datetime as dt
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
MAX_BYTES = 8 * 1024 * 1024


def run(*cmd, capture=False):
    r = subprocess.run(cmd, cwd=REPO_DIR, text=True, capture_output=capture)
    if r.returncode != 0:
        sys.exit(f"명령 실패: {' '.join(cmd)}\n{r.stderr if capture else ''}")
    return r.stdout.strip() if capture else ""


def image_size(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                         capture_output=True, text=True).stdout
    vals = [int(l.split(":")[1]) for l in out.splitlines() if "pixel" in l]
    return vals[0], vals[1]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        sys.exit(__doc__)
    src = Path(args[0]).expanduser().resolve()
    date = args[1] if len(args) > 1 else None

    photos = sorted(p for p in src.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not 1 <= len(photos) <= 10:
        sys.exit(f"사진은 1~10장이어야 함 (현재 {len(photos)}장)")
    cap_file = src / "caption.txt"
    caption = cap_file.read_text(encoding="utf-8").strip() if cap_file.exists() else ""
    if len(caption) > 2200:
        sys.exit(f"캡션이 2,200자를 넘음 ({len(caption)}자)")
    if caption.count("#") > 30:
        sys.exit("해시태그는 30개까지")

    for p in photos:
        w, h = image_size(p)
        ratio = w / h
        if not 0.8 - 0.005 <= ratio <= 1.91 + 0.005:
            sys.exit(f"{p.name}: 비율 {w}x{h}는 인스타 허용 범위(4:5 ~ 1.91:1) 밖")

    if date:
        d = dt.date.fromisoformat(date)
        if d <= dt.date.today():
            sys.exit("예약 날짜는 내일 이후여야 함")
        target = REPO_DIR / "posts" / d.isoformat()
    else:
        target = REPO_DIR / "posts" / f"now-{dt.datetime.now():%Y%m%d-%H%M%S}"
    if target.exists():
        sys.exit(f"{target.relative_to(REPO_DIR)} 가 이미 있음 (같은 날 예약은 1개)")

    print(f"올릴 위치: {target.relative_to(REPO_DIR)}")
    for i, p in enumerate(photos, 1):
        print(f"  {i:02d}. {p.name}")
    print(f"캡션 ({len(caption)}자):\n{caption[:300]}{'…' if len(caption) > 300 else ''}")
    if dry:
        print("\n[dry-run] 검사 통과. 실제로 올리지 않음.")
        return

    run("git", "pull", "--rebase", "-q")
    target.mkdir(parents=True)
    for i, p in enumerate(photos, 1):
        out = target / f"{i:02d}.jpg"
        if p.suffix.lower() == ".png":
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92",
                            str(p), "--out", str(out)], capture_output=True, check=True)
        else:
            shutil.copy(p, out)
        if out.stat().st_size > MAX_BYTES:
            shutil.rmtree(target)
            sys.exit(f"{p.name}: 8MB 초과")
    (target / "caption.txt").write_text(caption + "\n", encoding="utf-8")

    rel = str(target.relative_to(REPO_DIR))
    run("git", "add", rel)
    run("git", "commit", "-q", "-m", f"{'예약' if date else '즉시 게시'}: {rel}")
    run("git", "push", "-q")

    if date:
        print(f"\n예약 완료: {date} 오전 9시(KST) 무렵 자동 게시")
        return

    started = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)
    run("gh", "workflow", "run", "publish.yml", "-f", f"folder={rel}")
    print("\n게시 워크플로 실행 중…")
    run_id = None
    for _ in range(30):
        time.sleep(3)
        runs = json.loads(run("gh", "run", "list", "--workflow", "publish.yml",
                              "--event", "workflow_dispatch", "-L", "5",
                              "--json", "databaseId,createdAt", capture=True))
        fresh = [x for x in runs
                 if dt.datetime.fromisoformat(x["createdAt"].replace("Z", "+00:00")) >= started]
        if fresh:
            run_id = fresh[0]["databaseId"]
            break
    if not run_id:
        sys.exit("워크플로 실행을 찾지 못함. GitHub Actions 탭을 확인하세요.")
    r = subprocess.run(["gh", "run", "watch", str(run_id), "--exit-status"],
                       cwd=REPO_DIR, capture_output=True, text=True)
    log = subprocess.run(["gh", "run", "view", str(run_id), "--log"],
                         cwd=REPO_DIR, capture_output=True, text=True).stdout
    lines = [l.split("\t")[-1] for l in log.splitlines() if "게시 완료" in l or "오류" in l]
    print("\n".join(lines[-3:]) or "(로그 없음)")
    if r.returncode != 0:
        sys.exit(f"게시 실패. 자세한 로그: gh run view {run_id} --log")
    run("git", "pull", "--rebase", "-q")


if __name__ == "__main__":
    main()
