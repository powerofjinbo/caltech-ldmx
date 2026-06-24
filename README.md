# Muon LDMX-like Active Target

Minimal Geant4 pipeline for a muon-beam LDMX-like active-target study.

The first detector model is intentionally small and inspectable:

- 25 LYSO layers along the beam axis, for `25 cm` total LYSO thickness.
- 10 crystals per layer.
- Each crystal is `1 cm x 1 cm x 10 cm`.
- Beam direction is `+z`.
- The default beam spot is offset by `0.1 mm` in `x` and `y` so the track does
  not lie exactly on a crystal boundary.
- Even layers use bars along `x`; odd layers use bars along `y`, giving a simple 2D hodoscope-like active target.
- Adjacent layers have a `0.1 mm` air gap in the scaffold to avoid idealized
  coincident-boundary navigation issues during early development, so the
  current outer z-extent is `25.24 cm`.
- LYSO is approximated as `Lu1.8Y0.2SiO5`, density `7.10 g/cm3`; Ce doping and optical photons are not modeled yet.

## Build

From this directory:

```sh
source ../setup_geant4_11_4_1.sh
cmake -S . -B build
cmake --build build -j
```

## Run A Smoke Test

```sh
./build/muon_active_target macros/run_muon.mac
python3 analysis/summarize_events.py output/base_muon_nt_events.csv
python3 analysis/plot_basic.py
```

## Write A 3D Geant4 View

The default executable registers the file-based `VRML2FILE` visualization
driver. It avoids the OpenGL/XQuartz dependency and writes a `.wrl` 3D scene
file:

```sh
./build/muon_active_target macros/vis_vrml.mac
```

Geant4 writes files named like `g4_00.wrl` and `g4_01.wrl` in the run
directory. In this macro, `g4_01.wrl` is the flushed accumulated scene with the
detector geometry and one stored muon event. Open it with a VRML viewer, or
convert it with another 3D tool if needed:

```sh
open g4_01.wrl
```

If macOS does not know what app to use, install/use a VRML-capable viewer such
as FreeWRL, view3dscene, MeshLab, or Blender. The current Geant4 build avoids
OpenGL/XQuartz because this machine is missing the `/opt/X11` runtime libraries.

The default macro fires 10 `8 GeV` `mu-` particles through the target. A
`15 GeV` M3-like smoke macro is also included:

```sh
./build/muon_active_target macros/run_muon_15gev.mac
```

The optional second executable argument changes the reference physics list:

```sh
./build/muon_active_target macros/run_muon.mac FTFP_BERT
./build/muon_active_target macros/run_muon.mac QGSP_BERT
```

The executable defaults to a lightweight `EM` physics list
(`G4EmStandardPhysics + Decay`, `1 mm` default cut) for fast geometry, scoring,
and CSV smoke tests. Use a Geant4 reference list such as `FTFP_BERT` for actual
background-production studies.

## Current Event Output

The CSV ntuple records one row per event:

- `total_edep_mev`: total LYSO energy deposition.
- `primary_muon_edep_mev`: energy deposition from the primary muon track.
- `extra_edep_mev`: energy deposition from all non-primary tracks.
- `n_hit_crystals`, `n_hit_layers`: active channels/layers above `0.1 MeV`.
- `n_extra_hit_crystals`, `n_extra_hit_layers`: non-primary activity above `0.1 MeV`.
- `max_layer_edep_mev`: largest layer energy deposition.
- `out_muon_ke_gev`: primary muon kinetic energy after leaving the active target, or `-1` if not recorded.
- `n_secondaries`, `n_charged_secondaries`, `n_gamma_secondaries`: secondary-particle counters.

The run also writes:

- `output/base_muon_nt_layers.csv`: one row per event and layer.
- `output/base_muon_nt_crystals.csv`: one row per event and hit crystal.
- `output/base_muon_nt_tracks.csv`: one row per Geant4 track, including
  `track_id`, `parent_id`, `particle_name`, `pdg`, `creator_process`, start/end
  position, kinetic energy, and track length.

`analysis/plot_basic.py` creates dependency-free SVG plots in `plots/`:

- `plots/event_total_edep.svg`
- `plots/average_layer_profile.svg`
- `plots/event_0_hitmap.svg`

For a clearer event display than MeshLab's default VRML rendering, convert the
Geant4 VRML trajectories to 2D projection views:

```sh
python3 analysis/vrml_event_display.py g4_01.wrl
open plots/event_display_tracks.svg
```

If `output/base_muon_nt_tracks.csv` comes from the same event, the SVG labels
long tracks with truth information:

```sh
python3 analysis/vrml_event_display.py g4_07.wrl \
  --tracks output/base_muon_nt_tracks.csv \
  --out plots/event_display_tracks_labeled.svg
```

## Dynamic 3D Event Displays

Two dynamic viewers are included.

The browser/Three.js viewer is lightweight and reads the Geant4 VRML output:

```sh
python3 event-display-3d/scripts/vrml_to_event_json.py g4_07.wrl \
  --tracks output/base_muon_nt_tracks.csv \
  --out event-display-3d/public/event.json
cd event-display-3d
npm install
npm run build
python3 -m http.server 4173 --bind 127.0.0.1 -d dist
```

Then open `http://127.0.0.1:4173/`.

The native VTK viewer is closer to a standard scientific event-display tool:

```sh
/opt/homebrew/bin/python3.14 analysis/vtk_event_display.py g4_05.wrl
```

Controls: mouse rotate/zoom/pan, space pause/resume, `r` reset, `+/-` speed.
On a normal desktop terminal, you can also ask VTK to write a static PNG check:

```sh
/opt/homebrew/bin/python3.14 analysis/vtk_event_display.py g4_05.wrl --screenshot plots/vtk_event_display.png
```

The separate `muon_active_target_gui` binary is linked against the standard
Geant4 GUI/Qt visualization stack:

```sh
./build/muon_active_target_gui macros/vis_qt.mac
```

On this Mac, Geant4 has `qt[yes]`, Homebrew has `qt` and `vtk`, but the
current Geant4 install still reports `vtk[no]`. Enabling Geant4's VTK driver
requires rebuilding Geant4 with VTK support. The Qt/OpenGL binary also expects
the XQuartz runtime files under `/opt/X11`; if those files are missing, rerun
the XQuartz package installer and enter the macOS administrator password.

## Next Engineering Steps

1. Confirm beam energy, beam spot, and layer/bar orientation with Bertrand.
2. Add macro-driven geometry parameters if the 25-layer design changes.
3. Add event displays for high-extra-activity events.
4. Generate dedicated SM background samples: muon bremsstrahlung, pair production, and muon-nuclear interactions.
5. Build cut scans: outgoing-muon energy loss plus active-target veto variables.
6. Cross-check `FTFP_BERT` against at least one alternate physics list.
