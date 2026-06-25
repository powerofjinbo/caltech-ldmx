# Baseline MIP Calibration

This note records the first clean-muon baseline for the standalone Geant4
active-target prototype. The purpose is to establish the ordinary muon response
before introducing controlled background-like samples or any dark-matter signal
model.

## Geometry

Debug geometry for the first baseline package:

- 25 LYSO layers along the beam direction.
- 10 crystals per layer.
- Each crystal is `1 cm x 1 cm x 10 cm`.
- Adjacent layers have a `0.1 mm` air gap in the scaffold.
- The gun fires one primary `mu-` per Geant4 event.

The proposal geometry is 40 LYSO layers. The 25-layer sample is kept as the
pipeline validation baseline. The current code has now been moved to the
40-layer proposal geometry; see the final section for the 40-layer sanity
check.

## Samples

Two clean-muon samples were generated:

```sh
./build/muon_active_target macros/run_muon.mac
./build/muon_active_target macros/run_muon_15gev.mac
```

Each macro runs 1000 events:

- 25-layer `8 GeV mu-`: plots preserved in `plots/muon_8gev_25layer/`
- 25-layer `15 GeV mu-`: plots preserved in `plots/muon_15gev_25layer/`
- 40-layer `8 GeV mu-`: `output/muon_8gev_40layer_nt_events.csv`
- 40-layer `15 GeV mu-`: `output/muon_15gev_40layer_nt_events.csv`

## Main Calibration Result

The baseline MIP response is:

```text
1 MIP/layer ~= 9.2 MeV
```

This is the anchor number for later threshold and veto studies.

## 8 GeV, 1000 Events

Summary:

- `primary_muon_edep_mev / n_hit_layers`: mean `9.182 MeV/layer`, std `0.140 MeV/layer`
- mean total edep: `307.815 MeV`
- mean extra edep: `78.265 MeV`
- mean outgoing muon KE: `7.681 GeV`
- mean max layer edep: `27.446 MeV`
- mean extra hit crystals: `24.20`

Tail checks:

- `extra_edep_mev`: p50 `47.648 MeV`, p90 `145.782 MeV`, p99 `570.710 MeV`, max `2608.600 MeV`
- `max_layer_edep_mev`: p50 `21.556 MeV`, p90 `44.779 MeV`, p99 `124.482 MeV`, max `409.045 MeV`
- `n_extra_hit_crystals`: p50 `21`, p90 `41`, p99 `76`, max `176`

Representative event displays:

- typical event: event `955`, `extra_edep = 47.822 MeV`, `n_extra_hit_crystals = 19`, `plots/muon_8gev_25layer/typical_event_display.svg`
- high-extra event: event `882`, `extra_edep = 2608.600 MeV`, `n_extra_hit_crystals = 176`, `plots/muon_8gev_25layer/high-extra_event_display.svg`

Plots:

- `plots/muon_8gev_25layer/mip_per_layer_distribution.svg`
- `plots/muon_8gev_25layer/total_edep_distribution.svg`
- `plots/muon_8gev_25layer/extra_edep_distribution.svg`
- `plots/muon_8gev_25layer/extra_edep_tail.svg`
- `plots/muon_8gev_25layer/out_muon_ke_distribution.svg`
- `plots/muon_8gev_25layer/max_layer_edep_distribution.svg`
- `plots/muon_8gev_25layer/n_extra_hit_crystals_distribution.svg`
- `plots/muon_8gev_25layer/average_layer_profile.svg`

## 15 GeV, 1000 Events

Summary:

- `primary_muon_edep_mev / n_hit_layers`: mean `9.251 MeV/layer`, std `0.136 MeV/layer`
- mean total edep: `319.880 MeV`
- mean extra edep: `88.616 MeV`
- mean outgoing muon KE: `14.655 GeV`
- mean max layer edep: `29.925 MeV`
- mean extra hit crystals: `26.32`

Tail checks:

- `extra_edep_mev`: p50 `51.780 MeV`, p90 `164.250 MeV`, p99 `712.166 MeV`, max `1819.540 MeV`
- `max_layer_edep_mev`: p50 `22.946 MeV`, p90 `47.789 MeV`, p99 `125.965 MeV`, max `544.366 MeV`
- `n_extra_hit_crystals`: p50 `22`, p90 `43`, p99 `84`, max `122`

Representative event displays:

- typical event: event `152`, `extra_edep = 51.830 MeV`, `n_extra_hit_crystals = 28`, `plots/muon_15gev_25layer/typical_event_display.svg`
- high-extra event: event `997`, `extra_edep = 1819.540 MeV`, `n_extra_hit_crystals = 122`, `plots/muon_15gev_25layer/high-extra_event_display.svg`

Plots:

- `plots/muon_15gev_25layer/mip_per_layer_distribution.svg`
- `plots/muon_15gev_25layer/total_edep_distribution.svg`
- `plots/muon_15gev_25layer/extra_edep_distribution.svg`
- `plots/muon_15gev_25layer/extra_edep_tail.svg`
- `plots/muon_15gev_25layer/out_muon_ke_distribution.svg`
- `plots/muon_15gev_25layer/max_layer_edep_distribution.svg`
- `plots/muon_15gev_25layer/n_extra_hit_crystals_distribution.svg`
- `plots/muon_15gev_25layer/average_layer_profile.svg`

## Interpretation

The MIP response is nearly independent of 8 vs 15 GeV, as expected for
relativistic muons. The primary muon deposits about `9.2 MeV` per crossed LYSO
layer in this geometry.

The broader distributions and the high-side tails come from ordinary muon
interactions in the target: ionization secondaries, bremsstrahlung photons, and
secondary electrons or photons. These are not signal samples. They define the
natural baseline activity that later veto and reconstruction thresholds must
handle.

The tail behavior is the important part for background rejection. A small
fraction of otherwise ordinary muon events can have large `extra_edep`,
high `max_layer_edep`, or large extra-hit multiplicity. Future controlled
background-like studies should focus on whether those hard visible particles
are captured by the active target topology.

## 40-Layer Proposal Geometry Sanity Check

The detector model has been updated to 40 LYSO layers. The basic expectation is
that the primary muon energy deposition should scale from about
`25 x 9.2 MeV ~= 230 MeV` to about `40 x 9.2 MeV ~= 368 MeV`.

The 40-layer rerun confirms this:

### 8 GeV, 1000 Events, 40 Layers

- `n_hit_layers`: mean `40.00`, min `40`, max `40`
- layer ids in the layer ntuple: `0-39`
- `primary_muon_edep_mev / n_hit_layers`: mean `9.185 MeV/layer`, std `0.112 MeV/layer`
- mean primary muon edep: `367.392 MeV`
- mean total edep: `497.566 MeV`
- mean extra edep: `130.174 MeV`
- mean outgoing muon KE: `7.489 GeV`
- `extra_edep_mev`: p50 `88.171 MeV`, p90 `233.464 MeV`, p99 `811.789 MeV`, max `2782.080 MeV`

Representative event displays:

- typical event: event `505`, `extra_edep = 88.275 MeV`, `n_extra_hit_crystals = 30`, `plots/muon_8gev_40layer/typical_event_display.svg`
- high-extra event: event `229`, `extra_edep = 2782.080 MeV`, `n_extra_hit_crystals = 150`, `plots/muon_8gev_40layer/high-extra_event_display.svg`

### 15 GeV, 1000 Events, 40 Layers

- `n_hit_layers`: mean `40.00`, min `40`, max `40`
- layer ids in the layer ntuple: `0-39`
- `primary_muon_edep_mev / n_hit_layers`: mean `9.252 MeV/layer`, std `0.108 MeV/layer`
- mean primary muon edep: `370.063 MeV`
- mean total edep: `521.565 MeV`
- mean extra edep: `151.502 MeV`
- mean outgoing muon KE: `14.453 GeV`
- `extra_edep_mev`: p50 `91.250 MeV`, p90 `283.808 MeV`, p99 `1331.509 MeV`, max `2125.070 MeV`

Representative event displays:

- typical event: event `644`, `extra_edep = 91.275 MeV`, `n_extra_hit_crystals = 47`, `plots/muon_15gev_40layer/typical_event_display.svg`
- high-extra event: event `212`, `extra_edep = 2125.070 MeV`, `n_extra_hit_crystals = 164`, `plots/muon_15gev_40layer/high-extra_event_display.svg`

The per-layer MIP response remains about `9.2 MeV/layer`, while the total
primary muon deposition scales with detector length as expected.
