# Controlled Background-Like Samples

These samples are not rare-background rate calculations. They are topology
studies: inject visible particles in addition to the primary muon and check
whether the active LYSO target records vetoable activity.

The current clean-muon baseline should be treated as the reference:

```text
1 MIP/layer ~= 9.2 MeV
```

## Sample A: Muon Plus Photon

Target topology:

```text
mu- + gamma
```

Physics analogy:

```text
mu N -> mu N gamma
```

The photon is a controlled stand-in for hard muon bremsstrahlung. If a hard
photon escapes unseen it can mimic missing energy; if it converts or showers in
the active target or downstream calorimetry it should be vetoable.

Initial scan:

- `E_gamma = 0.5, 1, 3, 5 GeV`
- injection layer `5, 15, 25, 35`
- angle relative to beam `0, 5, 10 deg`

Observables:

- `extra_edep_mev`
- `n_extra_hit_crystals`
- `n_extra_hit_layers`
- `max_layer_edep_mev`
- crystal hitmap width
- event display topology

## Sample B: Muon Plus Electron-Positron Pair

Target topology:

```text
mu- + e+ + e-
```

Physics analogy:

```text
mu N -> mu N e+ e-
```

The pair is a controlled stand-in for pair-production-like activity. The active
target should see additional charged tracks beyond the primary muon MIP line.

Initial scan:

- total pair energy `0.5, 1, 3 GeV`
- injection layer `5, 15, 25, 35`
- opening angle `5, 10, 20 deg`

Observables:

- increase in `n_extra_hit_crystals`
- increase in `n_extra_hit_layers`
- widening of hitmap relative to clean muon
- two additional charged track segments in event display

## Sample C: Muon Plus Hadrons

Target topology:

```text
mu- + hadron
```

Physics analogy:

```text
mu N -> mu + hadrons
```

Initial single-hadron probes:

- `pi+`
- `pi-`
- `proton`
- `neutron`

Initial scan:

- hadron kinetic energy `0.2, 0.5, 1, 3 GeV`
- injection layer `5, 15, 25, 35`
- angle relative to beam `0, 10, 30 deg`

Observables:

- `extra_edep_mev`
- `n_extra_hit_crystals`
- `n_extra_hit_layers`
- `max_layer_edep_mev`
- delayed or diffuse hit topology for neutral particles

The neutron probe is especially important. Charged pions and protons should
leave direct ionization, while neutrons can travel before interacting and are
more likely to escape an active target. This is one of the motivations for
downstream hadronic calorimetry in a fuller detector.

## Implementation Plan

The standalone app now has a macro-controlled generator mode, for example:

```text
/muonActiveTarget/generator/generatorMode muGamma
/muonActiveTarget/generator/secondaryEnergy 1 GeV
/muonActiveTarget/generator/secondaryAngle 5 deg
/muonActiveTarget/generator/emissionLayer 20
```

Supported modes:

- `cleanMuon`: baseline one-muon mode.
- `muGamma`: primary `mu-` plus one injected `gamma`.
- `muPair`: primary `mu-` plus injected `e-` and `e+`.
- `muHadron`: primary `mu-` plus one injected hadron.

Additional controls:

- `/muonActiveTarget/generator/secondaryEnergy`: kinetic energy assigned to
  each injected particle.
- `/muonActiveTarget/generator/secondaryAngle`: angle relative to the beam axis.
- `/muonActiveTarget/generator/emissionLayer`: layer index used as the emission
  point.
- `/muonActiveTarget/generator/emissionZ`: explicit z position, if a layer index
  should not be used.
- `/muonActiveTarget/generator/hadronSpecies`: `pi+`, `pi-`, `proton`, or
  `neutron` for `muHadron`.

The generator always fires the baseline primary muon first, then adds the
controlled extra particle or particle pair in the same Geant4 event. The scoring
already treats any non-track-1 muon energy deposition as extra activity, so
these injected particles can be compared directly against the clean-muon
baseline distributions.

Example macros:

- `macros/run_mu_gamma_15gev.mac`
- `macros/run_mu_pair_15gev.mac`
- `macros/run_mu_hadron_15gev.mac`

These macros each start with 100 events for debugging. They are topology
studies, not realistic rate calculations.

## Debug Run Results

The first implementation check ran the following 100-event samples:

```sh
./build/muon_active_target macros/run_mu_gamma_15gev.mac
./build/muon_active_target macros/run_mu_pair_15gev.mac
./build/muon_active_target macros/run_mu_hadron_15gev.mac
```

Generated output prefixes:

- `output/mu_gamma_15gev_40layer_*`
- `output/mu_pair_15gev_40layer_*`
- `output/mu_neutron_15gev_40layer_*`

Generated plot directories:

- `plots/mu_gamma_15gev_40layer/`
- `plots/mu_pair_15gev_40layer/`
- `plots/mu_neutron_15gev_40layer/`

Initial 100-event summary:

| sample | mean total edep [MeV] | mean extra edep [MeV] | p90 extra edep [MeV] | max extra edep [MeV] | mean extra hit crystals |
|---|---:|---:|---:|---:|---:|
| `muGamma`, 1 GeV gamma, layer 20, 5 deg | 1464.169 | 1093.891 | 1244.025 | 2168.100 | 128.90 |
| `muPair`, 0.5 GeV per lepton, layer 20, 10 deg | 1519.739 | 1148.628 | 1290.830 | 4031.440 | 133.38 |
| `muHadron`, 1 GeV neutron, layer 20, 10 deg | 503.314 | 133.258 | 233.160 | 798.254 | 42.65 |

Representative event displays:

- `plots/mu_gamma_15gev_40layer/typical_event_display.svg`
- `plots/mu_gamma_15gev_40layer/high-extra_event_display.svg`
- `plots/mu_pair_15gev_40layer/typical_event_display.svg`
- `plots/mu_pair_15gev_40layer/high-extra_event_display.svg`
- `plots/mu_neutron_15gev_40layer/typical_event_display.svg`
- `plots/mu_neutron_15gev_40layer/high-extra_event_display.svg`

The gamma and pair samples produce large visible activity by construction. The
neutron sample is much closer to the clean-muon baseline in mean extra energy,
which is qualitatively consistent with the concern that neutral hadrons can be
harder to veto in an active target alone.
