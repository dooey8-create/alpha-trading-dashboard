#!/usr/bin/env python3
"""
Alpha Trading — 사진 자동 처리 스크립트
사용법: python3 process_photos.py
  → 📥 처리대기 폴더의 사진을 읽어
  → EXIF 날짜로 파일명 변경
  → 체크/오더장 자동 분류
  → ✅ 처리완료 폴더로 이동
"""

import os, re, shutil, json
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ─── 경로 설정 ───────────────────────────────────────────────
BASE        = Path(__file__).parent
INBOX       = BASE / "📥 처리대기"
DONE_CHECK  = BASE / "✅ 처리완료" / "체크"
DONE_ORDER  = BASE / "✅ 처리완료" / "오더장"
DONE_OTHER  = BASE / "✅ 처리완료" / "기타"
LOG_FILE    = BASE / "✅ 처리완료" / "처리로그.json"

# ─── 지원 확장자 ─────────────────────────────────────────────
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}

# ─── EXIF 날짜 추출 ──────────────────────────────────────────
def get_exif_date(filepath: Path) -> str | None:
    if not PIL_OK:
        return None
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        if not exif:
            return None
        for tag_id, val in exif.items():
            tag = TAGS.get(tag_id, '')
            if tag == 'DateTimeOriginal':
                # 형식: '2026:05:09 00:28:48'
                return val[:10].replace(':', '-')
    except Exception:
        pass
    return None

def get_file_date(filepath: Path) -> str:
    """EXIF 없으면 파일 수정일 사용"""
    exif = get_exif_date(filepath)
    if exif:
        return exif
    mtime = filepath.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

# ─── 파일 타입 추정 ──────────────────────────────────────────
def guess_type(filepath: Path, existing_name: str) -> str:
    """
    파일명 힌트로 체크/오더장 추정.
    실제 분류는 Claude가 이미지 보고 확인.
    """
    name_lower = existing_name.lower()
    # 이미 처리된 파일명 패턴
    if re.search(r'check|chk|ck|1[0-9]{3}', name_lower):
        return 'CHECK'
    if re.search(r'order|ord|오더', name_lower):
        return 'ORDER'
    # IMG_ 시리즈는 일단 OTHER로 — Claude가 보고 분류
    return 'PHOTO'

# ─── 파일명 생성 ─────────────────────────────────────────────
def make_new_name(date_str: str, file_type: str, original: str, idx: int) -> str:
    """
    형식: YYYY-MM-DD_TYPE_원본번호.ext
    예:   2026-05-09_PHOTO_IMG9365.jpg
    """
    ext = Path(original).suffix.lower()
    # 원본 번호만 추출 (IMG_9365 → 9365)
    num = re.sub(r'[^0-9]', '', Path(original).stem) or str(idx)
    return f"{date_str}_{file_type}_{num}{ext}"

# ─── 메인 처리 ───────────────────────────────────────────────
def process_inbox():
    if not INBOX.exists():
        print(f"📥 처리대기 폴더 없음: {INBOX}")
        return

    files = [f for f in INBOX.iterdir()
             if f.is_file() and f.suffix.lower() in IMAGE_EXT]

    if not files:
        print("📥 처리대기 폴더가 비어 있음.")
        return

    print(f"\n{'='*55}")
    print(f"  Alpha Trading 사진 처리 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  처리 대상: {len(files)}개 파일")
    print(f"{'='*55}\n")

    log = []
    for i, fp in enumerate(sorted(files), 1):
        date_str  = get_file_date(fp)
        ftype     = guess_type(fp, fp.name)
        new_name  = make_new_name(date_str, ftype, fp.name, i)

        # 목적 폴더 결정
        if ftype == 'CHECK':
            dest_dir = DONE_CHECK
        elif ftype == 'ORDER':
            dest_dir = DONE_ORDER
        else:
            dest_dir = DONE_OTHER

        # 날짜별 서브폴더
        month_dir = dest_dir / date_str[:7]   # YYYY-MM
        month_dir.mkdir(parents=True, exist_ok=True)

        dest = month_dir / new_name

        # 중복 파일명 처리
        counter = 1
        while dest.exists():
            stem = Path(new_name).stem
            ext  = Path(new_name).suffix
            dest = month_dir / f"{stem}_{counter}{ext}"
            counter += 1

        shutil.move(str(fp), str(dest))

        entry = {
            'original': fp.name,
            'renamed':  dest.name,
            'date':     date_str,
            'type':     ftype,
            'path':     str(dest.relative_to(BASE)),
            'processed_at': datetime.now().isoformat()
        }
        log.append(entry)
        print(f"  [{i:2d}] {fp.name}")
        print(f"       → {dest.relative_to(BASE)}")
        print()

    # 로그 저장 (누적)
    existing_log = []
    if LOG_FILE.exists():
        try:
            existing_log = json.loads(LOG_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    all_log = existing_log + log
    LOG_FILE.write_text(json.dumps(all_log, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"{'='*55}")
    print(f"  ✅ 완료: {len(log)}개 파일 처리 → ✅ 처리완료")
    print(f"  📄 로그: 처리완료/처리로그.json ({len(all_log)}건 누적)")
    print(f"{'='*55}\n")

    # 처리 결과 요약 반환 (Claude 대화용)
    return log

if __name__ == '__main__':
    process_inbox()
