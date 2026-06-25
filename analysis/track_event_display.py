#!/usr/bin/env python3
"""Draw 2D x-z and y-z event displays from the track-truth CSV."""

import argparse
import csv
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


def read_plain_csv(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def f(row, key):
    return float(row[key])


def i(row, key):
    return int(float(row[key]))


def select_event(events, mode):
    if mode == "high-extra":
        return max(events, key=lambda row: f(row, "extra_edep_mev"))
    if mode == "typical":
        ordered = sorted(f(row, "extra_edep_mev") for row in events)
        median = ordered[len(ordered) // 2]
        expected_layers = max(i(row, "n_hit_layers") for row in events)
        return min(
            events,
            key=lambda row: (
                abs(f(row, "extra_edep_mev") - median),
                abs(i(row, "n_hit_layers") - expected_layers),
            ),
        )
    raise ValueError(f"Unknown selection mode: {mode}")


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


def track_color(track):
    particle = track["particle_name"].strip('"')
    parent_id = i(track, "parent_id")
    charge = f(track, "charge_e")
    if parent_id == 0 and particle == "mu-":
        return "#e11d48", 4.0
    if particle == "gamma":
        return "#22c55e", 1.8
    if charge != 0.0:
        return "#ef4444", 1.7
    return "#64748b", 1.5


def draw_projection(parts, tracks, panel, projection, title, x_range, y_range, layer_count):
    x0, y0, width, height = panel
    left, right, top, bottom = x0 + 72, x0 + width - 28, y0 + 54, y0 + height - 58
    plot_w = right - left
    plot_h = bottom - top
    axis_label = "x [mm]" if projection == "xz" else "y [mm]"

    parts.append(f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" fill="#ffffff" stroke="#cbd5e1"/>')
    parts.append(svg_text(x0 + width / 2, y0 + 28, title, 18, weight="700"))
    parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#334155"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#334155"/>')
    parts.append(svg_text(left + plot_w / 2, y0 + height - 18, "z beam direction [mm]", 13))
    parts.append(svg_text(x0 + 22, top + plot_h / 2, axis_label, 13))

    for tick in range(7):
        z = x_range[0] + tick * (x_range[1] - x_range[0]) / 6
        x = scale(z, x_range[0], x_range[1], left, right)
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" stroke="#e2e8f0"/>')
        parts.append(svg_text(x, bottom + 18, f"{z:.0f}", 10))

    for tick in range(5):
        value = y_range[0] + tick * (y_range[1] - y_range[0]) / 4
        y = scale(value, y_range[0], y_range[1], bottom, top)
        parts.append(f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#e2e8f0"/>')
        parts.append(svg_text(left - 8, y + 4, f"{value:.0f}", 10, anchor="end"))

    layer_width = 10.0
    layer_gap = 0.1
    target_start = -0.5 * (layer_count * layer_width + (layer_count - 1) * layer_gap)
    for layer in range(layer_count):
        z_low = target_start + layer * (layer_width + layer_gap)
        z_high = z_low + layer_width
        x_low = scale(z_low, x_range[0], x_range[1], left, right)
        x_high = scale(z_high, x_range[0], x_range[1], left, right)
        y_low = scale(-50, y_range[0], y_range[1], bottom, top)
        y_high = scale(50, y_range[0], y_range[1], bottom, top)
        color = "#dbeafe" if layer % 2 == 0 else "#fed7aa"
        parts.append(
            f'<rect x="{x_low:.2f}" y="{y_high:.2f}" width="{x_high - x_low:.2f}" '
            f'height="{y_low - y_high:.2f}" fill="{color}" opacity="0.35" stroke="#94a3b8" stroke-width="0.4"/>'
        )

    for track in tracks:
        z1 = f(track, "start_z_mm")
        z2 = f(track, "end_z_mm")
        if projection == "xz":
            v1 = f(track, "start_x_mm")
            v2 = f(track, "end_x_mm")
        else:
            v1 = f(track, "start_y_mm")
            v2 = f(track, "end_y_mm")
        color, width_px = track_color(track)
        x_start = scale(z1, x_range[0], x_range[1], left, right)
        x_end = scale(z2, x_range[0], x_range[1], left, right)
        y_start = scale(v1, y_range[0], y_range[1], bottom, top)
        y_end = scale(v2, y_range[0], y_range[1], bottom, top)
        parts.append(
            f'<line x1="{x_start:.2f}" y1="{y_start:.2f}" x2="{x_end:.2f}" y2="{y_end:.2f}" '
            f'stroke="{color}" stroke-width="{width_px}" stroke-linecap="round" opacity="0.88"/>'
        )

    legend_x = right - 220
    legend_y = top + 18
    for index, (label, color, width_px) in enumerate(
        [
            ("primary muon", "#e11d48", 4.0),
            ("gamma", "#22c55e", 1.8),
            ("charged secondary", "#ef4444", 1.7),
            ("neutral secondary", "#64748b", 1.5),
        ]
    ):
        y = legend_y + 21 * index
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 32}" y2="{y}" stroke="{color}" stroke-width="{width_px}"/>')
        parts.append(svg_text(legend_x + 40, y + 4, label, 11, anchor="start"))


def draw_event(events, tracks, event_id, path, title):
    event = next(row for row in events if i(row, "event_id") == event_id)
    event_tracks = [row for row in tracks if i(row, "event_id") == event_id]
    if not event_tracks:
        raise SystemExit(f"No tracks found for event {event_id}")

    width, height = 1100, 860
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        svg_text(width / 2, 32, title, 22, weight="700"),
        svg_text(
            width / 2,
            58,
            (
                f"event {event_id}: total_edep={f(event, 'total_edep_mev'):.3f} MeV, "
                f"primary_muon_edep={f(event, 'primary_muon_edep_mev'):.3f} MeV, "
                f"extra_edep={f(event, 'extra_edep_mev'):.3f} MeV, "
                f"n_extra_hit_crystals={i(event, 'n_extra_hit_crystals')}"
            ),
            12,
        ),
    ]

    layer_count = max(i(row, "n_hit_layers") for row in events)
    target_half_z = 0.5 * (layer_count * 10.0 + (layer_count - 1) * 0.1)
    z_values = [f(track, key) for track in event_tracks for key in ("start_z_mm", "end_z_mm")]
    transverse_values = [
        f(track, key)
        for track in event_tracks
        for key in ("start_x_mm", "end_x_mm", "start_y_mm", "end_y_mm")
    ]
    x_range = (
        min(-260.0, min(z_values) - 40.0, -target_half_z - 30.0),
        max(target_half_z + 120.0, max(z_values) + 40.0),
    )
    transverse_extent = max(70.0, max(abs(value) for value in transverse_values) + 20.0)
    y_range = (-transverse_extent, transverse_extent)
    draw_projection(
        parts,
        event_tracks,
        (30, 84, 1040, 360),
        "xz",
        "Event display projection: x-z",
        x_range,
        y_range,
        layer_count,
    )
    draw_projection(
        parts,
        event_tracks,
        (30, 470, 1040, 360),
        "yz",
        "Event display projection: y-z",
        x_range,
        y_range,
        layer_count,
    )
    parts.append("</svg>")
    Path(path).write_text("\n".join(parts))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default="output/muon_8gev_40layer_nt_events.csv")
    parser.add_argument("--tracks", default="output/muon_8gev_40layer_tracks.csv")
    parser.add_argument("--out-dir", default="plots/muon_8gev_40layer")
    parser.add_argument("--event-id", type=int)
    parser.add_argument("--select", choices=["typical", "high-extra"], default="typical")
    args = parser.parse_args()

    events = read_geant4_csv(args.events)
    tracks = read_plain_csv(args.tracks)
    event = next((row for row in events if i(row, "event_id") == args.event_id), None) if args.event_id is not None else None
    if event is None:
        event = select_event(events, args.select)
    event_id = i(event, "event_id")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = args.select if args.event_id is None else f"event_{event_id}"
    output = out_dir / f"{suffix}_event_display.svg"
    draw_event(events, tracks, event_id, output, f"{args.select.replace('-', ' ').title()} Event Display")
    print(f"selected event_id={event_id}")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
