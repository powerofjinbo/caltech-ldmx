# Muon-beam LDMX-like Active Target: Technical Framework

## One-Sentence Goal

This standalone Geant4 study asks how a 40-layer LYSO active target responds to
a 5 GeV muon beam in an LDMX-like missing-momentum setup.

## Current Scope

The current code is intentionally restricted to a clean baseline:

```text
5 GeV primary mu- -> 40-layer LYSO active target -> edep/hits/tracks/plots
```

Each Geant4 event starts with exactly one primary `mu-`. There are no manual
extra-particle generator modes or dark-matter particles. Any extra tracks in
the output come from Geant4 physics processes during the muon transport.

## Detector Model

- Beam direction: `+z`.
- LYSO stack: 40 layers, each `1 cm` thick.
- Per layer: 10 LYSO crystal bars.
- Crystal size: `1 cm x 1 cm x 10 cm`.
- Even layers have bars along `x`; odd layers have bars along `y`.
- Temporary inter-layer air gap: `0.1 mm`, used as a Geant4 navigation/debug
  scaffold rather than a final detector-design statement.
- Beam spot: `(0.1 mm, 0.1 mm)` to avoid starting exactly on crystal
  boundaries.
- LYSO material: approximate `Lu1.8Y0.2SiO5`, density `7.10 g/cm3`.
- Not modeled yet: scintillation photons, SiPM response, electronics
  thresholds, timing, dead channels, ECal/HCal.

## Pipeline

```text
CMake/Geant4 build
  -> 5 GeV muon gun
  -> Geant4 physics list
  -> stepping-level LYSO scoring
  -> event/layer/crystal/track CSV files
  -> SVG plots and event displays
```

## Main Observables

- `primary_muon_edep_mev / n_hit_layers`: MIP/layer calibration.
- `total_edep_mev`: total visible energy in LYSO.
- `extra_edep_mev`: non-primary energy deposition.
- `n_hit_layers`, `n_hit_crystals`: active-target occupancy.
- `n_extra_hit_layers`, `n_extra_hit_crystals`: non-primary activity.
- `max_layer_edep_mev`: local shower-like burst proxy.
- `out_muon_ke_gev`: outgoing muon kinetic energy.
- Track truth: particle name, PDG code, parent id, creator process, and
  start/end positions for debugging.

## Immediate Plan

1. Keep only the 5 GeV clean-muon baseline.
2. Rebuild and rerun 1000 events.
3. Refresh the baseline plots and event displays.
4. Use the result to answer: what is `1 MIP/layer`, how broad is it, and how
   large is the natural non-primary tail?
5. Decide the next real-background-generation strategy with Bertrand before
   adding any new generator modes.

## Why Manual Extra-Particle Modes Were Removed

The previous extra-particle modes were debugging topology probes, not realistic
rate calculations. Since the current project direction is to establish a clean
5 GeV baseline first, those modes and macros have been removed to avoid mixing
baseline calibration with artificial event content.
