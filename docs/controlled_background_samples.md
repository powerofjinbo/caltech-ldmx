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

Add a macro-controlled generator mode, for example:

```text
/muonActiveTarget/generator/extraMode gamma
/muonActiveTarget/generator/extraEnergy 1 GeV
/muonActiveTarget/generator/extraZ 50 mm
/muonActiveTarget/generator/extraAngle 5 deg
```

The generator should always fire the baseline primary muon first, then add the
controlled extra particle or particle pair in the same Geant4 event. The scoring
already treats any non-track-1 muon energy deposition as extra activity, so
these injected particles can be compared directly against the clean-muon
baseline distributions.

