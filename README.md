# Muon LDMX-like Active Target

Standalone Geant4 pipeline for a 5 GeV clean-muon baseline through an
LDMX-like LYSO active target.

The current scope is deliberately narrow: one primary `mu-` per event, no
manual extra-particle generator modes, and no dark-matter signal generator yet.
Ordinary secondaries can still be produced by the selected Geant4 physics list.

## Detector Model

- 40 LYSO layers along the beam axis.
- 10 crystals per layer.
- Each crystal is `1 cm x 1 cm x 10 cm`.
- Beam direction is `+z`.
- Beam spot is offset by `0.1 mm` in `x` and `y` so the primary track does not
  lie exactly on a crystal boundary.
- Even layers use bars along `x`; odd layers use bars along `y`.
- Adjacent layers have a temporary `0.1 mm` air gap to avoid idealized
  coincident-boundary navigation issues during early development.
- LYSO is approximated as `Lu1.8Y0.2SiO5`, density `7.10 g/cm3`.
- Optical photons, SiPM response, electronics thresholds, and timing are not
  modeled yet.

## Build

From this directory:

```sh
source ../setup_geant4_11_4_1.sh
cmake -S . -B build
cmake --build build -j
```

## Run 5 GeV Baseline

```sh
./build/muon_active_target macros/run_muon.mac
python3 analysis/summarize_events.py
python3 analysis/plot_basic.py
python3 analysis/track_event_display.py --select typical
python3 analysis/track_event_display.py --select high-extra
```

The baseline macro fires 1000 primary `mu-` particles at 5 GeV and writes:

- `output/muon_5gev_40layer_nt_events.csv`
- `output/muon_5gev_40layer_nt_layers.csv`
- `output/muon_5gev_40layer_nt_crystals.csv`
- `output/muon_5gev_40layer_tracks.csv`

The analysis scripts write SVG plots and event displays under:

- `plots/muon_5gev_40layer/`

## Event Variables

The event ntuple records:

- `total_edep_mev`: total LYSO energy deposition.
- `primary_muon_edep_mev`: energy deposition from the primary muon track.
- `extra_edep_mev`: energy deposition from all non-primary tracks.
- `n_hit_crystals`, `n_hit_layers`: active channels/layers above `0.1 MeV`.
- `n_extra_hit_crystals`, `n_extra_hit_layers`: non-primary activity above
  `0.1 MeV`.
- `max_layer_edep_mev`: largest layer energy deposition.
- `out_muon_ke_gev`: primary muon kinetic energy after leaving the active
  target, or `-1` if not recorded.
- `n_secondaries`, `n_charged_secondaries`, `n_gamma_secondaries`: secondary
  counters from the simulated event.

The track CSV records truth-level Geant4 tracks with particle name, PDG code,
parent id, creator process, start/end positions, kinetic energies, and track
length. This is for debugging and event-display labeling.

## 3D Visualization

For the native Geant4 Qt viewer:

```sh
./build/muon_active_target_gui macros/vis_tsgqt.mac
```

Inside the Geant4 `Session:` prompt, useful commands are:

```text
/run/beamOn 1
/vis/viewer/flush
/vis/viewer/set/style wireframe
/vis/viewer/set/style surface
/vis/viewer/zoom 1.5
```

For file-based VRML output:

```sh
./build/muon_active_target macros/vis_vrml.mac
open g4_01.wrl
```

For a 2D labeled projection from the VRML event:

```sh
python3 analysis/vrml_event_display.py g4_01.wrl \
  --tracks output/muon_5gev_40layer_vis_tracks.csv \
  --out plots/muon_5gev_40layer/event_display_tracks.svg
```

The browser/Three.js viewer can be regenerated from a VRML event:

```sh
python3 event-display-3d/scripts/vrml_to_event_json.py g4_01.wrl \
  --tracks output/muon_5gev_40layer_vis_tracks.csv \
  --out event-display-3d/public/event.json
cd event-display-3d
npm install
npm run build
python3 -m http.server 4173 --bind 127.0.0.1 -d dist
```

Then open `http://127.0.0.1:4173/`.

## Physics List

The executable defaults to a lightweight `EM` physics list
(`G4EmStandardPhysics + Decay`, `1 mm` default cut) for fast geometry, scoring,
and CSV checks. A Geant4 reference physics list can be selected as the optional
second argument:

```sh
./build/muon_active_target macros/run_muon.mac FTFP_BERT
./build/muon_active_target macros/run_muon.mac QGSP_BERT
```

Use reference physics lists for serious background-production studies.

## Current Next Steps

1. Treat 5 GeV clean-muon response as the only baseline.
2. Confirm the MIP/layer calibration and natural extra-activity tails.
3. Discuss with Bertrand which real background generation path to use next.
4. Avoid manual extra-particle generator modes unless they are explicitly
   requested again as a debugging-only topology study.
