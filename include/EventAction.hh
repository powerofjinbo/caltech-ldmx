#ifndef EVENT_ACTION_HH
#define EVENT_ACTION_HH

#include "G4SystemOfUnits.hh"
#include "G4UserEventAction.hh"
#include "globals.hh"

#include <map>

class G4Event;
class G4ParticleDefinition;

class EventAction : public G4UserEventAction {
 public:
  EventAction(G4int numberOfLayers, G4int crystalsPerLayer);
  ~EventAction() override = default;

  void BeginOfEventAction(const G4Event* event) override;
  void EndOfEventAction(const G4Event* event) override;

  G4int GetEventId() const { return fEventId; }

  void AddCrystalEdep(G4int copyNumber, G4double edep, G4bool fromPrimaryMuon);
  void CountSecondary(const G4ParticleDefinition* particleDefinition);
  void SetOutgoingMuonKineticEnergy(G4double kineticEnergy);

 private:
  void Reset();

  const G4int fNumberOfLayers;
  const G4int fCrystalsPerLayer;
  const G4double fHitThreshold = 0.1 * MeV;

  G4int fEventId = -1;

  std::map<G4int, G4double> fCrystalEdep;
  std::map<G4int, G4double> fLayerEdep;
  std::map<G4int, G4double> fExtraCrystalEdep;
  std::map<G4int, G4double> fExtraLayerEdep;

  G4double fTotalEdep = 0.0;
  G4double fPrimaryMuonEdep = 0.0;
  G4double fExtraEdep = 0.0;
  G4double fMaxLayerEdep = 0.0;
  G4double fOutgoingMuonKineticEnergy = -1.0;

  G4int fSecondaries = 0;
  G4int fChargedSecondaries = 0;
  G4int fGammaSecondaries = 0;
};

#endif
