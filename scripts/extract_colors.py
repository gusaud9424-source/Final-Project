"""
SecuQuest — 참고 캡처 색상 추출 스크립트
docs/references/ 아래 PNG 캡처의 지정 좌표에서 픽셀 RGB 값을 추출하여
HEX / RGB 형식으로 출력한다. (디자인 토큰 산출용, DESIGN.md 작성 보조)

사전 준비 (WSL2):
    pip install Pillow

실행:
    python3 scripts/extract_colors.py
"""

from pathlib import Path

from PIL import Image

REFERENCES_DIR = Path(__file__).resolve().parent.parent / "docs" / "references"

# (파일명, 라벨, x, y)
SAMPLES = [
    # 헤더 (01-header-nav.png)
    ("01-header-nav.png", "header-bg", 400, 110),
    ("01-header-nav.png", "header-tab-active-pill-bg", 690, 90),
    ("01-header-nav.png", "header-tab-active-text", 710, 80),
    ("01-header-nav.png", "header-tab-inactive-text", 915, 80),
    ("01-header-nav.png", "header-border-bottom", 400, 135),

    # 페이지 배경 그라데이션 (01-header-nav.png)
    ("01-header-nav.png", "page-bg-top-left", 150, 300),
    ("01-header-nav.png", "page-bg-top-right", 1800, 200),
    ("01-header-nav.png", "page-bg-bottom-center", 960, 1000),

    # 카드 배경 (01-header-nav.png 캘린더 카드)
    ("01-header-nav.png", "card-bg", 500, 900),
    ("01-header-nav.png", "card-border", 400, 480),

    # 텍스트 색
    ("01-header-nav.png", "text-body", 180, 90),
    ("01-header-nav.png", "text-sub", 200, 90),
    ("01-header-nav.png", "primary-accent", 170, 58),

    # 뱃지 4종 (01-header-nav.png)
    ("01-header-nav.png", "badge-round-bg", 580, 715),
    ("01-header-nav.png", "badge-round-text", 580, 705),
    ("01-header-nav.png", "badge-submitted-bg", 605, 605),
    ("01-header-nav.png", "badge-submitted-text", 595, 600),
    ("01-header-nav.png", "badge-dday-bg", 1660, 595),
    ("01-header-nav.png", "badge-dday-text", 1645, 605),
    ("01-header-nav.png", "badge-absent-bg", 460, 775),
    ("01-header-nav.png", "badge-absent-text", 475, 775),
]

_image_cache = {}


def load_image(filename):
    if filename not in _image_cache:
        path = REFERENCES_DIR / filename
        if not path.exists():
            _image_cache[filename] = None
            return None
        _image_cache[filename] = Image.open(path).convert("RGB")
    return _image_cache[filename]


def format_line(label, x, y, rgb):
    hex_color = "#{:02X}{:02X}{:02X}".format(*rgb)
    return f"{label:<24} @ ({x:4d}, {y:4d}) → {hex_color}  rgb{rgb}"


def main():
    for filename, label, x, y in SAMPLES:
        image = load_image(filename)

        if image is None:
            print(f"[경고] 파일을 찾을 수 없음: {filename} (라벨: {label})")
            continue

        width, height = image.size
        if not (0 <= x < width and 0 <= y < height):
            print(
                f"[경고] 좌표 범위 밖: {label} ({x}, {y}) — "
                f"이미지 크기 {width}x{height} ({filename})"
            )
            continue

        rgb = image.getpixel((x, y))
        print(format_line(label, x, y, rgb))


if __name__ == "__main__":
    main()
