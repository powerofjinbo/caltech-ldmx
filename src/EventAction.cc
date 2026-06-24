#include "EventAction.hh"

#include "G4AnalysisManager.hh"
#include "G4Event.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"

#include <algorithm>

EventAction::EventAction(G4int numberOfLayers, G4int crystalsPerLayer)
    : fNumberOfLayers(numberOfLayers), fCrystalsPerLayer(crystalsPerLayer) {}

void EventAction::Reset() {
  fCrystalEdep.clear();
  fLayerEdep.clear();
  fExtraCrystalEdep.clear();
  fExtraLayerEdep.clear();
  fTotalEdep = 0.0;
  fPrimaryMuonEdep = 0.0;
  fExtraEdep = 0.0;
  fMaxLayerEdep = 0.0;
  fOutgoingMuonKineticEnergy = -1.0;
  fSecondaries = 0;
  fChargedSecondaries = 0;
  fGammaSecondaries = 0;
}

void EventAction::BeginOfEventAction(const G4Event* event) {
  Reset();
  fEventId = event->GetEventID();
}

void EventAction::AddCrystalEdep(G4int copyNumber, G4double edep,
                                  G4bool fromPrimaryMuon) {
  if (edep <= 0.0) {
    return;
  }

  const G4int layer = copyNumber / fCrystalsPerLayer;

  fTotalEdep += edep;
  fCrystalEdep[copyNumber] += edep;
  fLayerEdep[layer] += edep;

  if (fromPrimaryMuon) {
    fPrimaryMuonEdep += edep;
  } else {
    fExtraEdep += edep;
    fExtraCrystalEdep[copyNumber] += edep;
    fExtraLayerEdep[layer] += edep;
  }
}

void EventAction::CountSecondary(
    const G4ParticleDefinition* particleDefinition) {
  if (particleDefinition == nullptr) {
    return;
  }

  ++fSecondaries;
  if (particleDefinition->GetPDGCharge() != 0.0) {
    ++fChargedSecondaries;
  }
  if (particleDefinition->GetParticleName() == "gamma") {
    ++fGammaSecondaries;
  }
}

void EventAction::SetOutgoingMuonKineticEnergy(G4double kineticEnergy) {
  if (fOutgoingMuonKineticEnergy < 0.0) {
    fOutgoingMuonKineticEnergy = kineticEnergy;
  }
}

void EventAction::EndOfEventAction(const G4Event* event) {
  const G4int eventId = event->GetEventID();

  G4int nHitCrystals = 0;
  for (const auto& [copyNumber, edep] : fCrystalEdep) {
    if (edep >= fHitThreshold) {
      ++nHitCrystals;
    }
  }

  G4int nHitLayers = 0;
  for (const auto& [layer, edep] : fLayerEdep) {
    if (edep >= fHitThreshold) {
      ++nHitLayers;
    }
    fMaxLayerEdep = std::max(fMaxLayerEdep, edep);
  }

  G4int nExtraHitCrystals = 0;
  for (const auto& [copyNumber, edep] : fExtraCrystalEdep) {
    if (edep >= fHitThreshold) {
      ++nExtraHitCrystals;
    }
  }

  G4int nExtraHitLayers = 0;
  for (const auto& [layer, edep] : fExtraLayerEdep) {
    if (edep >= fHitThreshold) {
      ++nExtraHitLayers;
    }
  }

  auto* analysis = G4AnalysisManager::Instance();
  analysis->FillNtupleIColumn(0, 0, eventId);
  analysis->FillNtupleDColumn(0, 1, fTotalEdep / MeV);
  analysis->FillNtupleDColumn(0, 2, fPrimaryMuonEdep / MeV);
  analysis->FillNtupleDColumn(0, 3, fExtraEdep / MeV);
  analysis->FillNtupleIColumn(0, 4, nHitCrystals);
  analysis->FillNtupleIColumn(0, 5, nHitLayers);
  analysis->FillNtupleIColumn(0, 6, nExtraHitCrystals);
  analysis->FillNtupleIColumn(0, 7, nExtraHitLayers);
  analysis->FillNtupleDColumn(0, 8, fMaxLayerEdep / MeV);
  analysis->FillNtupleDColumn(0, 9, fOutgoingMuonKineticEnergy / GeV);
  analysis->FillNtupleIColumn(0, 10, fSecondaries);
  analysis->FillNtupleIColumn(0, 11, fChargedSecondaries);
  analysis->FillNtupleIColumn(0, 12, fGammaSecondaries);
  analysis->AddNtupleRow(0);

  for (G4int layer = 0; layer < fNumberOfLayers; ++layer) {
    G4double layerEdep = 0.0;
    if (const auto found = fLayerEdep.find(layer); found != fLayerEdep.end()) {
      layerEdep = found->second;
    }

    G4double extraLayerEdep = 0.0;
    if (const auto found = fExtraLayerEdep.find(layer);
        found != fExtraLayerEdep.end()) {
      extraLayerEdep = found->second;
    }

    G4int layerHitCrystals = 0;
    G4int layerExtraHitCrystals = 0;
    for (G4int crystal = 0; crystal < fCrystalsPerLayer; ++crystal) {
      const G4int copyNumber = layer * fCrystalsPerLayer + crystal;
      if (const auto found = fCrystalEdep.find(copyNumber);
          found != fCrystalEdep.end() && found->second >= fHitThreshold) {
        ++layerHitCrystals;
      }
      if (const auto found = fExtraCrystalEdep.find(copyNumber);
          found != fExtraCrystalEdep.end() && found->second >= fHitThreshold) {
        ++layerExtraHitCrystals;
      }
    }

    analysis->FillNtupleIColumn(1, 0, eventId);
    analysis->FillNtupleIColumn(1, 1, layer);
    analysis->FillNtupleDColumn(1, 2, layerEdep / MeV);
    analysis->FillNtupleDColumn(1, 3, extraLayerEdep / MeV);
    analysis->FillNtupleIColumn(1, 4, layerHitCrystals);
    analysis->FillNtupleIColumn(1, 5, layerExtraHitCrystals);
    analysis->AddNtupleRow(1);
  }

  for (G4int copyNumber = 0; copyNumber < fNumberOfLayers * fCrystalsPerLayer;
       ++copyNumber) {
    G4double crystalEdep = 0.0;
    if (const auto found = fCrystalEdep.find(copyNumber);
        found != fCrystalEdep.end()) {
      crystalEdep = found->second;
    }

    G4double extraCrystalEdep = 0.0;
    if (const auto found = fExtraCrystalEdep.find(copyNumber);
        found != fExtraCrystalEdep.end()) {
      extraCrystalEdep = found->second;
    }

    if (crystalEdep <= 0.0 && extraCrystalEdep <= 0.0) {
      continue;
    }

    analysis->FillNtupleIColumn(2, 0, eventId);
    analysis->FillNtupleIColumn(2, 1, copyNumber / fCrystalsPerLayer);
    analysis->FillNtupleIColumn(2, 2, copyNumber % fCrystalsPerLayer);
    analysis->FillNtupleDColumn(2, 3, crystalEdep / MeV);
    analysis->FillNtupleDColumn(2, 4, extraCrystalEdep / MeV);
    analysis->AddNtupleRow(2);
  }
}
