from pathlib import Path
import re


CSS = (Path(__file__).resolve().parents[1] / "static" / "app.css").read_text(encoding="utf-8")


def _hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _luminance(value: str) -> float:
    channels = []
    for channel in _hex_rgb(value):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _dark_theme_color(variable: str) -> str:
    match = re.search(rf"{re.escape(variable)}:\s*light-dark\(#[0-9a-f]{{6}},\s*(#[0-9a-f]{{6}})\)", CSS)
    assert match is not None
    return match.group(1)


def test_dark_brand_surfaces_have_readable_normal_text_contrast():
    foreground = re.search(r"--on-brand:\s*(#[0-9a-f]{6})", CSS).group(1)

    assert _contrast(foreground, _dark_theme_color("--brand")) >= 4.5
    assert _contrast(foreground, _dark_theme_color("--brand-strong")) >= 4.5
