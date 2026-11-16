"""Animate snk's single-position output without changing contribution cells."""

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def animate_idle(path):
    svg = path.read_text()
    frames = re.findall(r"@keyframes s(\d+)\{(.*?)\}\}", svg, re.S)
    if not frames:
        raise ValueError(f"{path}: no snake keyframes found")
    if "@keyframes idle-s" in svg:
        return
    positions = [body.count("translate(") for _, body in frames]
    if any(count > 1 for count in positions):
        print(f"{path}: contribution animation already moves")
        return
    if any(count != 1 for count in positions):
        raise ValueError(f"{path}: unrecognized snake animation")

    root = ET.fromstring(svg)
    cells = [
        rect for rect in root.iter("{http://www.w3.org/2000/svg}rect")
        if "c" in rect.get("class", "").split()
    ]
    if not cells or any(rect.get("class") != "c" for rect in cells):
        raise ValueError(f"{path}: expected an empty contribution grid")

    # snk uses 16 px cells with a 2 px inset. Patrol the grid's border.
    step = 16
    left = int(min(float(cell.get("x")) for cell in cells)) - 2 - step
    right = int(max(float(cell.get("x")) for cell in cells)) - 2 + step
    top = int(min(float(cell.get("y")) for cell in cells)) - 2 - step
    bottom = int(max(float(cell.get("y")) for cell in cells)) - 2 + step
    route = (
        [(left, y) for y in range(top, bottom, step)]
        + [(x, bottom) for x in range(left, right, step)]
        + [(right, y) for y in range(bottom, top, -step)]
        + [(x, top) for x in range(right, left, -step)]
    )
    start = route.index((left + step, top))
    css = []
    for segment, _ in frames:
        index = int(segment)
        keyframes = []
        for tick in range(len(route) + 1):
            x, y = route[(start + tick - index) % len(route)]
            keyframes.append(
                f"{tick * 100 / len(route):.6f}%"
                f"{{transform:translate({x}px,{y}px)}}"
            )
        css.append(f"@keyframes idle-s{index}{{{''.join(keyframes)}}}")
        css.append(
            f".s.s{index}{{animation:idle-s{index} "
            f"{len(route) * 100}ms linear infinite}}"
        )
    path.write_text(svg.replace("</style>", "".join(css) + "</style>", 1))
    print(f"{path}: added {len(route)} idle positions; contribution cells unchanged")


if __name__ == "__main__":
    for filename in sys.argv[1:]:
        animate_idle(Path(filename))
