#!/usr/bin/env python3
"""Convert Geant4 VRML2FILE output into compact JSON for the web display."""

import argparse
import csv
import json
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
                points.append([float(match.group(axis)) for axis in range(1, 4)])
        index += 1
    return points, index


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
    return [
        float(row[f"{prefix}_x_mm"]),
        float(row[f"{prefix}_y_mm"]),
        float(row[f"{prefix}_z_mm"]),
    ]


def attach_track_truth(tracks, truth_rows, event_id):
    truth_rows = [row for row in truth_rows if int(float(row["event_id"])) == event_id]
    unmatched = set(range(len(truth_rows)))

    for track in sorted(tracks, key=lambda item: item["length"], reverse=True):
        best = None
        start = track["points"][0]
        for truth_idx in unmatched:
            row = truth_rows[truth_idx]
            start_score = math.dist(start, truth_position(row, "start"))
            length_score = abs(track["length"] - float(row["track_length_mm"]))
            score = start_score + 0.03 * length_score
            if best is None or score < best[0]:
                best = (score, truth_idx)
        if best is not None and best[0] < 8.0:
            row = truth_rows[best[1]]
            track["truth"] = {
                "eventId": int(float(row["event_id"])),
                "trackId": int(float(row["track_id"])),
                "parentId": int(float(row["parent_id"])),
                "particleName": row["particle_name"],
                "pdg": int(float(row["pdg"])),
                "chargeE": float(row["charge_e"]),
                "creatorProcess": row["creator_process"],
                "initialKeMev": float(row["initial_ke_mev"]),
                "finalKeMev": float(row["final_ke_mev"]),
                "trackLengthMm": float(row["track_length_mm"]),
            }
            unmatched.remove(best[1])


def parse_vrml(path, truth_rows=None, event_id=0):
    lines = Path(path).read_text().splitlines()
    boxes = []
    tracks = []
    current_color = [0.7, 0.7, 0.7]

    index = 0
    while index < len(lines):
        line = lines[index]
        color_match = COLOR_RE.match(line)
        if color_match:
            current_color = [float(color_match.group(i)) for i in range(1, 4)]

        if "#---------- SOLID:" in line:
            points, index = parse_points(lines, index)
            if points:
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                zs = [point[2] for point in points]
                boxes.append(
                    {
                        "center": [
                            0.5 * (min(xs) + max(xs)),
                            0.5 * (min(ys) + max(ys)),
                            0.5 * (min(zs) + max(zs)),
                        ],
                        "size": [
                            max(xs) - min(xs),
                            max(ys) - min(ys),
                            max(zs) - min(zs),
                        ],
                        "color": current_color,
                    }
                )
        elif "#---------- POLYLINE" in line:
            color = current_color
            search = index
            while search < len(lines) and "geometry IndexedLineSet" not in lines[search]:
                color_match = COLOR_RE.match(lines[search])
                if color_match:
                    color = [float(color_match.group(i)) for i in range(1, 4)]
                search += 1
            points, index = parse_points(lines, search)
            if len(points) >= 2:
                tracks.append({"points": points, "color": color, "length": path_length(points)})
        index += 1

    if not boxes:
        raise SystemExit(f"No detector boxes found in {path}")
    if not tracks:
        raise SystemExit(f"No tracks found in {path}")

    primary_index = max(range(len(tracks)), key=lambda idx: (tracks[idx]["length"], len(tracks[idx]["points"])))
    for idx, track in enumerate(tracks):
        track["role"] = "primary" if idx == primary_index else "secondary"

    if truth_rows:
        attach_track_truth(tracks, truth_rows, event_id)

    return {
        "source": str(path),
        "units": "mm",
        "detector": boxes,
        "tracks": tracks,
        "primaryTrackIndex": primary_index,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vrml", nargs="?", default="../g4_01.wrl")
    parser.add_argument("--out", default="../event-display-3d/public/event.json")
    parser.add_argument("--tracks", default="output/base_muon_nt_tracks.csv")
    parser.add_argument("--event-id", type=int, default=0)
    args = parser.parse_args()

    data = parse_vrml(args.vrml, read_geant4_csv(args.tracks), args.event_id)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))
    print(f"wrote {out_path}")
    print(f"detector boxes: {len(data['detector'])}")
    print(f"tracks: {len(data['tracks'])}")
    print(f"tracks with truth: {sum(1 for track in data['tracks'] if 'truth' in track)}")
    print(f"primary track index: {data['primaryTrackIndex']}")


if __name__ == "__main__":
    main()
