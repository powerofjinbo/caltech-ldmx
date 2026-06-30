#!/usr/bin/env python3
"""Make a clear 2D event display from the Geant4 VRML file.

MeshLab is useful for checking that the exported VRML is valid, but it often
renders VRML lines and transparency in a way that makes particle trajectories
hard to see. This script parses the same VRML file and writes an SVG with
projection views where tracks are deliberately drawn on top of the target.
"""

import argparse
import csv
import math
import re
from pathlib import Path


POINT_RE = re.compile(
    r"^\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+),?\s*$"
)
COLOR_RE = re.compile(
    r"^\s*diffuseColor\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)"
)


def parse_points(lines, start_index):
    points = []
    in_points = False
    index = start_index
    while index < len(lines):
        line = lines[index]
        if "point [" in line:
            in_points = True
            index += 1
            continue
        if in_points and "]" in line:
            break
        if in_points:
            match = POINT_RE.match(line)
            if match:
                points.append(tuple(float(match.group(axis)) for axis in range(1, 4)))
        index += 1
    return points, index


def parse_vrml(path):
    lines = Path(path).read_text().splitlines()
    boxes = []
    polylines = []
    current_color = (0.7, 0.7, 0.7)

    index = 0
    while index < len(lines):
        line = lines[index]
        color_match = COLOR_RE.match(line)
        if color_match:
            current_color = tuple(float(color_match.group(i)) for i in range(1, 4))

        if "#---------- SOLID:" in line:
            points, index = parse_points(lines, index)
            if points:
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                zs = [point[2] for point in points]
                boxes.append(
                    {
                        "xmin": min(xs),
                        "xmax": max(xs),
                        "ymin": min(ys),
                        "ymax": max(ys),
                        "zmin": min(zs),
                        "zmax": max(zs),
                    }
                )
        elif "#---------- POLYLINE" in line:
            color = current_color
            search = index
            while search < len(lines) and "geometry IndexedLineSet" not in lines[search]:
                color_match = COLOR_RE.match(lines[search])
                if color_match:
                    color = tuple(float(color_match.group(i)) for i in range(1, 4))
                search += 1
            points, index = parse_points(lines, search)
            if len(points) >= 2:
                polylines.append({"points": points, "color": color})
        index += 1

    return boxes, polylines


def path_length(points):
    total = 0.0
    for first, second in zip(points, points[1:]):
        total += math.dist(first, second)
    return total


def read_geant4_csv(path):
    path = Path(path)
    if not path.exists():
      return []

    columns = []
    data_lines = []
    with path.open(newline="") as handle:
        for line in handle:
            if line.startswith("#column"):
                columns.append(line.strip().split()[-1])
            elif line.startswith("#") or not line.strip():
                continue
            else:
                data_lines.append(line)
    if columns:
        return list(csv.DictReader(data_lines, fieldnames=columns))

    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def truth_position(row, prefix):
    return (
        float(row[f"{prefix}_x_mm"]),
        float(row[f"{prefix}_y_mm"]),
        float(row[f"{prefix}_z_mm"]),
    )


def match_truth(polylines, truth_rows, event_id):
    truth_rows = [row for row in truth_rows if int(float(row["event_id"])) == event_id]
    unmatched = set(range(len(truth_rows)))
    matches = {}

    for poly_idx in sorted(
        range(len(polylines)),
        key=lambda idx: path_length(polylines[idx]["points"]),
        reverse=True,
    ):
        points = polylines[poly_idx]["points"]
        length = path_length(points)
        start = points[0]

        best = None
        for truth_idx in unmatched:
            row = truth_rows[truth_idx]
            start_score = math.dist(start, truth_position(row, "start"))
            length_score = abs(length - float(row["track_length_mm"]))
            score = start_score + 0.03 * length_score
            if best is None or score < best[0]:
                best = (score, truth_idx)

        if best is not None and best[0] < 8.0:
            matches[poly_idx] = truth_rows[best[1]]
            unmatched.remove(best[1])

    return matches


def svg_text(x, y, text, size=13, anchor="middle", weight="normal"):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="#202124">{text}</text>'
    )


def scale(value, old_min, old_max, new_min, new_max):
    if old_max <= old_min:
        return 0.5 * (new_min + new_max)
    return new_min + (value - old_min) * (new_max - new_min) / (old_max - old_min)


def color_to_svg(color):
    r, g, b = [max(0, min(255, round(component * 255))) for component in color]
    return f"#{r:02x}{g:02x}{b:02x}"


def draw_panel(parts, title, boxes, polylines, primary_index, truth_matches, panel, x0, y0, width, height):
    x_axis = 0 if panel == "xz" else 1
    axis_label = "x [mm]" if panel == "xz" else "y [mm]"

    all_z = [value for box in boxes for value in (box["zmin"], box["zmax"])]
    all_v = []
    for box in boxes:
        if panel == "xz":
            all_v.extend([box["xmin"], box["xmax"]])
        else:
            all_v.extend([box["ymin"], box["ymax"]])
    for polyline in polylines:
        all_z.extend(point[2] for point in polyline["points"])
        all_v.extend(point[x_axis] for point in polyline["points"])

    z_min, z_max = min(all_z) - 10.0, max(all_z) + 10.0
    v_min, v_max = min(all_v) - 10.0, max(all_v) + 10.0

    parts.append(f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" fill="#ffffff" stroke="#d0d7de"/>')
    parts.append(svg_text(x0 + width / 2, y0 + 24, title, 17, weight="700"))

    left = x0 + 74
    right = x0 + width - 24
    top = y0 + 48
    bottom = y0 + height - 54

    parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#444"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#444"/>')
    parts.append(svg_text((left + right) / 2, y0 + height - 18, "z beam direction [mm]", 12))
    parts.append(svg_text(x0 + 22, (top + bottom) / 2, axis_label, 12))

    for tick in range(-250, 151, 50):
        if z_min <= tick <= z_max:
            x = scale(tick, z_min, z_max, left, right)
            parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="#edf2f7"/>')
            parts.append(svg_text(x, bottom + 16, str(tick), 10))

    for tick in range(-60, 61, 20):
        if v_min <= tick <= v_max:
            y = scale(tick, v_min, v_max, bottom, top)
            parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#edf2f7"/>')
            parts.append(svg_text(left - 8, y + 4, str(tick), 10, anchor="end"))

    # Draw the detector as a pale stack, then tracks on top.
    for index, box in enumerate(boxes):
        z1 = scale(box["zmin"], z_min, z_max, left, right)
        z2 = scale(box["zmax"], z_min, z_max, left, right)
        if panel == "xz":
            v1 = scale(box["xmin"], v_min, v_max, bottom, top)
            v2 = scale(box["xmax"], v_min, v_max, bottom, top)
            fill = "#c7ecff" if index % 20 < 10 else "#ffd89a"
        else:
            v1 = scale(box["ymin"], v_min, v_max, bottom, top)
            v2 = scale(box["ymax"], v_min, v_max, bottom, top)
            fill = "#c7ecff" if index % 20 < 10 else "#ffd89a"
        parts.append(
            f'<rect x="{min(z1, z2):.1f}" y="{min(v1, v2):.1f}" '
            f'width="{abs(z2 - z1):.1f}" height="{abs(v2 - v1):.1f}" '
            f'fill="{fill}" fill-opacity="0.22" stroke="#94a3b8" stroke-width="0.35"/>'
        )

    for idx, polyline in enumerate(polylines):
        points = []
        for point in polyline["points"]:
            x = scale(point[2], z_min, z_max, left, right)
            y = scale(point[x_axis], v_min, v_max, bottom, top)
            points.append(f"{x:.1f},{y:.1f}")
        is_primary = idx == primary_index
        color = "#e11d48" if is_primary else color_to_svg(polyline["color"])
        width_px = 4.0 if is_primary else 2.0
        opacity = 0.98 if is_primary else 0.82
        parts.append(
            f'<polyline points="{" ".join(points)}" fill="none" '
            f'stroke="{color}" stroke-width="{width_px}" stroke-opacity="{opacity}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )

    label_count = 0
    for idx in sorted(
        range(len(polylines)),
        key=lambda poly_idx: path_length(polylines[poly_idx]["points"]),
        reverse=True,
    ):
        if label_count >= 7 or idx not in truth_matches:
            continue
        polyline = polylines[idx]
        if path_length(polyline["points"]) < 15.0:
            continue
        row = truth_matches[idx]
        endpoint = polyline["points"][-1]
        label_x = scale(endpoint[2], z_min, z_max, left, right)
        label_y = scale(endpoint[x_axis], v_min, v_max, bottom, top)
        if not (left <= label_x <= right and top <= label_y <= bottom):
            label_x = min(max(label_x, left + 4), right - 118)
            label_y = min(max(label_y, top + 14), bottom - 8)
        text = f'{row["track_id"]}: {row["particle_name"]} ({row["creator_process"]})'
        parts.append(
            f'<text x="{label_x + 6:.1f}" y="{label_y - 4:.1f}" '
            f'font-family="Arial, sans-serif" font-size="10" fill="#334155">{text}</text>'
        )
        label_count += 1

    parts.append(svg_text(right - 218, top + 22, "thick red = primary muon candidate", 12, anchor="start"))
    parts.append(svg_text(right - 218, top + 42, "thin lines = secondaries / other tracks", 12, anchor="start"))
    parts.append(svg_text(right - 218, top + 62, "labels: track_id particle (creator process)", 12, anchor="start"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vrml", nargs="?", default="g4_01.wrl")
    parser.add_argument("--out", default="plots/event_display_tracks.svg")
    parser.add_argument("--tracks", default="output/muon_5gev_40layer_vis_tracks.csv")
    parser.add_argument("--event-id", type=int, default=0)
    args = parser.parse_args()

    boxes, polylines = parse_vrml(args.vrml)
    if not boxes:
        raise SystemExit(f"No detector solids found in {args.vrml}")
    if not polylines:
        raise SystemExit(f"No trajectory polylines found in {args.vrml}")

    primary_index = max(
        range(len(polylines)),
        key=lambda idx: (path_length(polylines[idx]["points"]), len(polylines[idx]["points"])),
    )
    truth_matches = match_truth(polylines, read_geant4_csv(args.tracks), args.event_id)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    width = 1120
    panel_height = 410
    height = 2 * panel_height + 28
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f6f8fa"/>',
    ]
    draw_panel(parts, "Event display projection: x-z", boxes, polylines, primary_index, truth_matches, "xz", 16, 12, width - 32, panel_height)
    draw_panel(parts, "Event display projection: y-z", boxes, polylines, primary_index, truth_matches, "yz", 16, panel_height + 20, width - 32, panel_height)
    parts.append("</svg>")
    out_path.write_text("\n".join(parts))

    print(f"read {len(boxes)} detector boxes and {len(polylines)} trajectories from {args.vrml}")
    print(f"primary trajectory candidate index: {primary_index}")
    print(f"matched truth labels: {len(truth_matches)}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
