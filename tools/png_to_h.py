from PIL import Image
from pathlib import Path
import argparse


TARGET_WIDTH = 1872
TARGET_HEIGHT = 1404

# 设为 None：完全按照原图灰度量化
# 例如设为 240：灰度 >= 240 的像素全部强制变成纯白
WHITE_CLIP = 220


def packbits_encode(data: bytes) -> bytearray:
    """PackBits-style RLE, compatible with the current V4 ESPHome decoder."""
    out = bytearray()
    i = 0
    n = len(data)

    while i < n:
        # Detect repeated run.
        run = 1
        while (
            i + run < n
            and run < 128
            and data[i + run] == data[i]
        ):
            run += 1

        # Encode runs of 3+ identical bytes.
        if run >= 3:
            out.append(257 - run)
            out.append(data[i])
            i += run
            continue

        # Otherwise build literal block.
        start = i
        i += run

        while i < n:
            r = 1

            while (
                i + r < n
                and r < 128
                and data[i + r] == data[i]
            ):
                r += 1

            if r >= 3 or (i - start) >= 128:
                break

            i += r

        literal_length = i - start

        out.append(literal_length - 1)
        out.extend(data[start:i])

    return out


def convert_png_to_h(input_path: Path, output_path: Path):
    print("=" * 60)
    print("E1003 PNG -> RLE 4bpp Header Converter")
    print("=" * 60)

    print(f"\nInput : {input_path}")
    print(f"Output: {output_path}")

    # ------------------------------------------------------------
    # 1. Load
    # ------------------------------------------------------------
    img = Image.open(input_path)

    print(f"\nOriginal size: {img.width} x {img.height}")
    print(f"Original mode: {img.mode}")

    # Handle transparency correctly:
    # transparent pixels become white.
    if img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    ):
        rgba = img.convert("RGBA")

        white_bg = Image.new(
            "RGBA",
            rgba.size,
            (255, 255, 255, 255)
        )

        img = Image.alpha_composite(
            white_bg,
            rgba
        ).convert("RGB")
    else:
        img = img.convert("RGB")

    # ------------------------------------------------------------
    # 2. Resize exactly to E1003 resolution
    # ------------------------------------------------------------
    if img.size != (TARGET_WIDTH, TARGET_HEIGHT):
        print(
            f"Resize: {img.width}x{img.height}"
            f" -> {TARGET_WIDTH}x{TARGET_HEIGHT}"
        )

        img = img.resize(
            (TARGET_WIDTH, TARGET_HEIGHT),
            Image.Resampling.LANCZOS
        )

    # ------------------------------------------------------------
    # 3. Grayscale
    # ------------------------------------------------------------
    gray = img.convert("L")

    pixels = list(gray.getdata())

    # Optional white clipping.
    if WHITE_CLIP is not None:
        pixels = [
            255 if p >= WHITE_CLIP else p
            for p in pixels
        ]

        print(f"White clip enabled: >= {WHITE_CLIP} -> 255")
    else:
        print("White clip: disabled")

    # ------------------------------------------------------------
    # 4. Quantize to 16 grayscale levels
    #
    # 0  = black
    # 15 = white
    # ------------------------------------------------------------
    levels = [
        round(p * 15 / 255)
        for p in pixels
    ]

    # ------------------------------------------------------------
    # 5. Pack 4bpp
    #
    # One byte:
    #
    #   [ pixel A ][ pixel B ]
    #      4 bit      4 bit
    #
    # ------------------------------------------------------------
    packed = bytearray()

    for i in range(0, len(levels), 2):
        high = levels[i] & 0x0F

        if i + 1 < len(levels):
            low = levels[i + 1] & 0x0F
        else:
            low = 0x0F

        packed.append(
            (high << 4) | low
        )

    # ------------------------------------------------------------
    # 6. RLE
    # ------------------------------------------------------------
    compressed = packbits_encode(packed)

    # ------------------------------------------------------------
    # 7. Generate C++ header
    # ------------------------------------------------------------
    lines = [
        "#pragma once",
        "#include <cstdint>",
        "",
        "// ============================================================",
        "// AUTO GENERATED FILE",
        "//",
        "// E1003 Dashboard Bitmap",
        "// 1872 x 1404",
        "// 16-level grayscale",
        "// 4bpp",
        "// PackBits-style RLE",
        "// ============================================================",
        "",
        f"static constexpr int DASHBOARD_V4_WIDTH = {TARGET_WIDTH};",
        f"static constexpr int DASHBOARD_V4_HEIGHT = {TARGET_HEIGHT};",
        f"static constexpr int DASHBOARD_V4_RAW_SIZE = {len(packed)};",
        f"static constexpr int DASHBOARD_V4_RLE_SIZE = {len(compressed)};",
        "",
        "static const uint8_t "
        "dashboard_v4_rle[DASHBOARD_V4_RLE_SIZE] PROGMEM = {",
    ]

    # 20 bytes per source line.
    for i in range(0, len(compressed), 20):
        chunk = compressed[i:i + 20]

        line = "  " + ", ".join(
            f"0x{x:02X}"
            for x in chunk
        ) + ","

        lines.append(line)

    lines.append("};")
    lines.append("")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        "\n".join(lines),
        encoding="ascii"
    )

    # ------------------------------------------------------------
    # 8. Statistics
    # ------------------------------------------------------------
    raw_size = len(packed)
    compressed_size = len(compressed)

    ratio = compressed_size / raw_size
    saved = 1 - ratio

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

    print(
        f"Raw 4bpp       : {raw_size:,} bytes"
    )

    print(
        f"RLE compressed : {compressed_size:,} bytes"
    )

    print(
        f"Compression     : {ratio * 100:.1f}% of raw"
    )

    print(
        f"Space saved     : {saved * 100:.1f}%"
    )

    print(
        f"\nGenerated:\n{output_path}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert PNG/JPG to E1003 "
            "4bpp PackBits RLE C++ header."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input PNG/JPG image"
    )

    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=Path("dashboard_static_v4.h"),
        help="Output .h file"
    )

    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(
            f"Input image not found: {args.input}"
        )

    convert_png_to_h(
        args.input,
        args.output
    )


if __name__ == "__main__":
    main()