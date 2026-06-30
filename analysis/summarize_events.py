#!/usr/bin/env python3
"""Summarize the Geant4 CSV ntuple from the active-target smoke test."""

import argparse
import csv
from pathlib import Path
from statistics import mean


def as_float(row, key):
    return float(row[key])


def as_int(row, key):
    return int(float(row[key]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="output/muon_5gev_40layer_nt_events.csv",
        help="CSV ntuple produced by muon_active_target",
    )
    parser.add_argument(
        "--extra-edep-veto-mev",
        type=float,
        default=1.0,
        help="Toy veto threshold on non-primary-muon energy deposition",
    )
    args = parser.parse_args()

    path = Path(args.csv_file)
    columns = []
    data_lines = []
    with path.open(newline="") as handle:
        for line in handle:
            if line.startswith("#column"):
                parts = line.strip().split()
                columns.append(parts[-1])
            elif line.startswith("#") or not line.strip():
                continue
            else:
                data_lines.append(line)

    rows = list(csv.DictReader(data_lines, fieldnames=columns))

    if not rows:
        raise SystemExit(f"No events found in {path}")

    total_edep = [as_float(row, "total_edep_mev") for row in rows]
    extra_edep = [as_float(row, "extra_edep_mev") for row in rows]
    hit_layers = [as_int(row, "n_hit_layers") for row in rows]
    extra_hit_layers = [as_int(row, "n_extra_hit_layers") for row in rows]
    out_ke = [as_float(row, "out_muon_ke_gev") for row in rows]

    pass_extra_edep = [
        edep < args.extra_edep_veto_mev for edep in extra_edep
    ]
    pass_no_extra_layers = [layers == 0 for layers in extra_hit_layers]
    pass_toy_veto = [
        pass_a and pass_b
        for pass_a, pass_b in zip(pass_extra_edep, pass_no_extra_layers)
    ]

    recorded_out = [energy for energy in out_ke if energy >= 0.0]

    print(f"events: {len(rows)}")
    print(f"mean total Edep [MeV]: {mean(total_edep):.3f}")
    print(f"mean extra Edep [MeV]: {mean(extra_edep):.6f}")
    print(f"max extra Edep [MeV]: {max(extra_edep):.6f}")
    print(f"mean hit layers: {mean(hit_layers):.2f}")
    print(
        "toy veto pass fraction "
        f"(extra_edep < {args.extra_edep_veto_mev:g} MeV and no extra layers): "
        f"{sum(pass_toy_veto) / len(pass_toy_veto):.4f}"
    )
    if recorded_out:
        print(f"mean outgoing muon KE [GeV]: {mean(recorded_out):.4f}")
    else:
        print("mean outgoing muon KE [GeV]: not recorded")


if __name__ == "__main__":
    main()
