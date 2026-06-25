#!/usr/bin/env python3
"""Create basic SVG plots from the active-target CSV ntuples.

This intentionally avoids matplotlib so the first Geant4 workflow can run on a
plain Python install.
"""

import argparse
import csv
import math
from pathlib import Path


def read_geant4_csv(path):
    columns = []
    data_lines = []
    with Path(path).open(newline="") as handle:
        for line in handle:
            if line.startswith("#column"):
                columns.append(line.strip().split()[-1])
            elif line.startswith("#") or not line.strip():
                continue
            else:
                data_lines.append(line)
    return list(csv.DictReader(data_lines, fieldnames=columns))


def f(row, key):
    return float(row[key])


def i(row, key):
    return int(float(row[key]))


def svg_text(x, y, text, size=13, anchor="middle", weight="normal"):
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
        f'font-family="Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="#202124">{text}</text>'
    )


def scale(value, old_min, old_max, new_min, new_max):
    if old_max <= old_min:
        return 0.5 * (new_min + new_max)
    return new_min + (value - old_min) * (new_max - new_min) / (old_max - old_min)


def quantile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * fraction
    low = int(math.floor(position))
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def mean_std(values):
    if not values:
        return 0.0, 0.0
    average = sum(values) / len(values)
    variance = sum((value - average) ** 2 for value in values) / len(values)
    return average, math.sqrt(variance)


def histogram_plot(title, values, path, x_label, y_label="events", bins=40, color="#2563eb"):
    width, height = 860, 420
    left, right, top, bottom = 82, 28, 48, 82
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_min = min(values) if values else 0.0
    x_max = max(values) if values else 1.0
    if x_max <= x_min:
        x_max = x_min + 1.0
    bin_width = (x_max - x_min) / bins
    counts = [0 for _ in range(bins)]
    for value in values:
        index = int((value - x_min) / bin_width)
        if index == bins:
            index -= 1
        counts[index] += 1
    y_max = max(counts) * 1.15 if counts and max(counts) > 0 else 1.0
    average, width_std = mean_std(values)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(width / 2, 26, title, 18, weight="700"),
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#444"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#444"/>',
        svg_text(left + plot_w / 2, height - 28, x_label, 13),
        svg_text(22, top + plot_h / 2, y_label, 13),
        svg_text(
            left + plot_w - 4,
            top + 16,
            f"mean={average:.3g}, std={width_std:.3g}, p90={quantile(values, 0.90):.3g}",
            12,
            anchor="end",
        ),
    ]

    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        y_val = frac * y_max
        y = scale(y_val, 0, y_max, top + plot_h, top)
        parts.append(f'<line x1="{left - 4}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#e5e7eb"/>')
        parts.append(svg_text(left - 9, y + 4, f"{y_val:.0f}", 11, anchor="end"))

    for tick in range(6):
        x_val = x_min + tick * (x_max - x_min) / 5
        x = scale(x_val, x_min, x_max, left, left + plot_w)
        parts.append(f'<line x1="{x}" y1="{top + plot_h}" x2="{x}" y2="{top + plot_h + 4}" stroke="#444"/>')
        parts.append(svg_text(x, top + plot_h + 19, f"{x_val:.3g}", 10))

    for index, count in enumerate(counts):
        x0 = left + index * plot_w / bins
        x1 = left + (index + 1) * plot_w / bins
        y = scale(count, 0, y_max, top + plot_h, top)
        parts.append(
            f'<rect x="{x0 + 0.5:.2f}" y="{y:.2f}" width="{max(x1 - x0 - 1.0, 0.5):.2f}" '
            f'height="{top + plot_h - y:.2f}" fill="{color}" opacity="0.86"/>'
        )

    parts.append("</svg>")
    Path(path).write_text("\n".join(parts))


def tail_plot(title, values, path, x_label):
    width, height = 860, 420
    left, right, top, bottom = 82, 28, 48, 82
    plot_w = width - left - right
    plot_h = height - top - bottom
    ordered = sorted(value for value in values if value >= 0.0)
    if not ordered:
        ordered = [0.0]
    max_value = max(ordered)
    thresholds = []
    for index in range(80):
        t = index / 79
        thresholds.append(max_value * t * t)
    fractions = [
        sum(1 for value in ordered if value >= threshold) / len(ordered)
        for threshold in thresholds
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(width / 2, 26, title, 18, weight="700"),
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#444"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#444"/>',
        svg_text(left + plot_w / 2, height - 28, x_label, 13),
        svg_text(22, top + plot_h / 2, "fraction of events above threshold", 13),
        svg_text(
            left + plot_w - 4,
            top + 16,
            f"p90={quantile(ordered, 0.90):.3g}, p99={quantile(ordered, 0.99):.3g}, max={max_value:.3g}",
            12,
            anchor="end",
        ),
    ]

    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        y = scale(frac, 0, 1, top + plot_h, top)
        parts.append(f'<line x1="{left - 4}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#e5e7eb"/>')
        parts.append(svg_text(left - 9, y + 4, f"{frac:.2f}", 11, anchor="end"))

    for tick in range(6):
        x_val = max_value * tick / 5
        x = scale(x_val, 0, max_value, left, left + plot_w)
        parts.append(f'<line x1="{x}" y1="{top + plot_h}" x2="{x}" y2="{top + plot_h + 4}" stroke="#444"/>')
        parts.append(svg_text(x, top + plot_h + 19, f"{x_val:.3g}", 10))

    points = []
    for threshold, fraction in zip(thresholds, fractions):
        x = scale(threshold, 0, max_value, left, left + plot_w)
        y = scale(fraction, 0, 1, top + plot_h, top)
        points.append(f"{x:.2f},{y:.2f}")
    parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#dc2626" stroke-width="2.5"/>')

    parts.append("</svg>")
    Path(path).write_text("\n".join(parts))


def line_plot(title, xs, series, path, x_label, y_label):
    width, height = 860, 420
    left, right, top, bottom = 82, 24, 48, 72
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_y = [y for _, ys, _ in series for y in ys]
    y_min = 0.0
    y_max = max(all_y) * 1.15 if all_y and max(all_y) > 0 else 1.0
    x_min, x_max = min(xs), max(xs)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(width / 2, 26, title, 18, weight="700"),
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#444"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#444"/>',
        svg_text(left + plot_w / 2, height - 24, x_label, 13),
        svg_text(20, top + plot_h / 2, y_label, 13, anchor="middle"),
    ]

    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        y_val = y_min + frac * (y_max - y_min)
        y = scale(y_val, y_min, y_max, top + plot_h, top)
        parts.append(f'<line x1="{left - 4}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#e5e7eb"/>')
        parts.append(svg_text(left - 9, y + 4, f"{y_val:.1f}", 11, anchor="end"))

    for label, ys, color in series:
        points = []
        for x_val, y_val in zip(xs, ys):
            x = scale(x_val, x_min, x_max, left, left + plot_w)
            y = scale(y_val, y_min, y_max, top + plot_h, top)
            points.append(f"{x:.2f},{y:.2f}")
        parts.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.5"/>'
        )
        for x_val, y_val in zip(xs, ys):
            x = scale(x_val, x_min, x_max, left, left + plot_w)
            y = scale(y_val, y_min, y_max, top + plot_h, top)
            parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}"/>')

    legend_x = left + plot_w - 220
    for idx, (label, _, color) in enumerate(series):
        y = top + 20 + 22 * idx
        parts.append(f'<rect x="{legend_x}" y="{y - 10}" width="16" height="4" fill="{color}"/>')
        parts.append(svg_text(legend_x + 24, y - 5, label, 12, anchor="start"))

    parts.append("</svg>")
    Path(path).write_text("\n".join(parts))


def event_bars(events, path):
    width, height = 860, 420
    left, right, top, bottom = 76, 26, 48, 72
    plot_w = width - left - right
    plot_h = height - top - bottom
    ids = [i(row, "event_id") for row in events]
    totals = [f(row, "total_edep_mev") for row in events]
    ymax = max(totals) * 1.15 if totals else 1.0
    bar_w = plot_w / max(len(totals), 1) * 0.68

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(width / 2, 26, "Total LYSO energy deposition per event", 18, weight="700"),
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#444"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#444"/>',
        svg_text(left + plot_w / 2, height - 24, "event id", 13),
        svg_text(20, top + plot_h / 2, "MeV", 13),
    ]

    for idx, value in enumerate(totals):
        x_center = left + (idx + 0.5) * plot_w / len(totals)
        y = scale(value, 0, ymax, top + plot_h, top)
        parts.append(
            f'<rect x="{x_center - bar_w / 2:.2f}" y="{y:.2f}" width="{bar_w:.2f}" '
            f'height="{top + plot_h - y:.2f}" fill="#3b82f6"/>'
        )
        parts.append(svg_text(x_center, top + plot_h + 18, str(ids[idx]), 11))

    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        y_val = frac * ymax
        y = scale(y_val, 0, ymax, top + plot_h, top)
        parts.append(f'<line x1="{left - 4}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#e5e7eb"/>')
        parts.append(svg_text(left - 9, y + 4, f"{y_val:.0f}", 11, anchor="end"))

    parts.append("</svg>")
    Path(path).write_text("\n".join(parts))


def event_distributions(events, out_dir):
    total_edep = [f(row, "total_edep_mev") for row in events]
    primary_edep = [f(row, "primary_muon_edep_mev") for row in events]
    extra_edep = [f(row, "extra_edep_mev") for row in events]
    hit_layers = [max(i(row, "n_hit_layers"), 1) for row in events]
    out_muon_ke = [
        f(row, "out_muon_ke_gev")
        for row in events
        if f(row, "out_muon_ke_gev") >= 0.0
    ]
    mip_per_layer = [
        primary / layers for primary, layers in zip(primary_edep, hit_layers)
    ]

    histogram_plot(
        "Primary muon energy deposition per hit layer",
        mip_per_layer,
        out_dir / "mip_per_layer_distribution.svg",
        "primary_muon_edep / n_hit_layers [MeV/layer]",
        color="#16a34a",
    )
    histogram_plot(
        "Total LYSO energy deposition distribution",
        total_edep,
        out_dir / "total_edep_distribution.svg",
        "total_edep [MeV]",
        color="#2563eb",
    )
    histogram_plot(
        "Extra activity energy deposition distribution",
        extra_edep,
        out_dir / "extra_edep_distribution.svg",
        "extra_edep [MeV]",
        color="#dc2626",
    )
    tail_plot(
        "Extra activity tail",
        extra_edep,
        out_dir / "extra_edep_tail.svg",
        "extra_edep threshold [MeV]",
    )
    histogram_plot(
        "Outgoing primary muon kinetic energy distribution",
        out_muon_ke,
        out_dir / "out_muon_ke_distribution.svg",
        "out_muon_ke [GeV]",
        color="#7c3aed",
    )


def heat_color(value, vmax):
    if vmax <= 0:
        return "#f8fafc"
    t = min(max(value / vmax, 0.0), 1.0)
    r = int(248 - 228 * t)
    g = int(250 - 104 * t)
    b = int(252 - 70 * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def hitmap(crystals, event_id, path):
    selected = [row for row in crystals if i(row, "event_id") == event_id]
    if not selected:
        raise SystemExit(f"No crystal rows found for event {event_id}")

    n_layers = max(i(row, "layer_id") for row in selected) + 1
    n_crystals = max(i(row, "crystal_id") for row in selected) + 1
    matrix = [[0.0 for _ in range(n_crystals)] for _ in range(n_layers)]
    for row in selected:
        matrix[i(row, "layer_id")][i(row, "crystal_id")] = f(row, "crystal_edep_mev")

    vmax = max(max(row) for row in matrix)
    cell_w, cell_h = 25, 18
    left, top = 74, 52
    width = left + n_layers * cell_w + 130
    height = top + n_crystals * cell_h + 78

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(width / 2, 26, f"Crystal hit map, event {event_id}", 18, weight="700"),
        svg_text(left + n_layers * cell_w / 2, height - 22, "layer id", 13),
        svg_text(24, top + n_crystals * cell_h / 2, "crystal id", 13),
    ]

    for layer in range(n_layers):
        if layer % 5 == 0:
            parts.append(svg_text(left + layer * cell_w + cell_w / 2, top - 10, str(layer), 10))
        for crystal in range(n_crystals):
            value = matrix[layer][crystal]
            x = left + layer * cell_w
            y = top + crystal * cell_h
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_w - 1}" height="{cell_h - 1}" '
                f'fill="{heat_color(value, vmax)}" stroke="#ffffff" stroke-width="0.5"/>'
            )
    for crystal in range(n_crystals):
        parts.append(svg_text(left - 10, top + crystal * cell_h + 13, str(crystal), 10, anchor="end"))

    legend_x = left + n_layers * cell_w + 26
    parts.append(svg_text(legend_x + 38, top + 2, "MeV", 12, weight="700"))
    for idx in range(8):
        value = vmax * idx / 7
        y = top + 20 + idx * 18
        parts.append(f'<rect x="{legend_x}" y="{y}" width="18" height="16" fill="{heat_color(value, vmax)}"/>')
        parts.append(svg_text(legend_x + 25, y + 12, f"{value:.1f}", 10, anchor="start"))

    parts.append("</svg>")
    Path(path).write_text("\n".join(parts))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default="output/muon_8gev_nt_events.csv")
    parser.add_argument("--layers", default="output/muon_8gev_nt_layers.csv")
    parser.add_argument("--crystals", default="output/muon_8gev_nt_crystals.csv")
    parser.add_argument("--event-id", type=int, default=0)
    parser.add_argument("--out-dir", default="plots")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    events = read_geant4_csv(args.events)
    layers = read_geant4_csv(args.layers)
    crystals = read_geant4_csv(args.crystals)

    event_distributions(events, out_dir)
    event_bars(events, out_dir / "event_total_edep.svg")

    layer_ids = sorted({i(row, "layer_id") for row in layers})
    avg_total = []
    avg_extra = []
    for layer_id in layer_ids:
        rows = [row for row in layers if i(row, "layer_id") == layer_id]
        avg_total.append(sum(f(row, "layer_edep_mev") for row in rows) / len(rows))
        avg_extra.append(sum(f(row, "extra_layer_edep_mev") for row in rows) / len(rows))

    line_plot(
        "Average layer energy deposition",
        layer_ids,
        [
            ("total layer edep", avg_total, "#2563eb"),
            ("extra layer edep", avg_extra, "#dc2626"),
        ],
        out_dir / "average_layer_profile.svg",
        "layer id",
        "MeV/event",
    )
    hitmap(crystals, args.event_id, out_dir / f"event_{args.event_id}_hitmap.svg")

    print(f"wrote {out_dir / 'mip_per_layer_distribution.svg'}")
    print(f"wrote {out_dir / 'total_edep_distribution.svg'}")
    print(f"wrote {out_dir / 'extra_edep_distribution.svg'}")
    print(f"wrote {out_dir / 'extra_edep_tail.svg'}")
    print(f"wrote {out_dir / 'out_muon_ke_distribution.svg'}")
    print(f"wrote {out_dir / 'event_total_edep.svg'}")
    print(f"wrote {out_dir / 'average_layer_profile.svg'}")
    print(f"wrote {out_dir / f'event_{args.event_id}_hitmap.svg'}")


if __name__ == "__main__":
    main()
