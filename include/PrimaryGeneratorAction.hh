#ifndef PRIMARY_GENERATOR_ACTION_HH
#define PRIMARY_GENERATOR_ACTION_HH

#include "G4String.hh"
#include "globals.hh"

#include "G4VUserPrimaryGeneratorAction.hh"

#include <memory>

class DetectorConstruction;
class G4Event;
class G4GenericMessenger;
class G4ParticleGun;

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction {
 public:
  explicit PrimaryGeneratorAction(const DetectorConstruction* detector);
  ~PrimaryGeneratorAction() override;

  void GeneratePrimaries(G4Event* event) override;

 private:
  void SetEmissionLayer(G4int layer);
  void SetEmissionZ(G4double z);
  G4double GetEmissionZ() const;
  void GenerateExtraParticle(G4Event* event, const G4String& particleName,
                             G4double energy, G4double angle,
                             G4double yDirectionSign = 0.0);

  const DetectorConstruction* fDetector;
  std::unique_ptr<G4ParticleGun> fParticleGun;
  std::unique_ptr<G4GenericMessenger> fMessenger;
  G4String fGeneratorMode = "cleanMuon";
  G4double fSecondaryEnergy = 1.0;
  G4double fSecondaryAngle = 0.0;
  G4int fEmissionLayer = 20;
  G4double fEmissionZ = 0.0;
  G4bool fUseExplicitEmissionZ = false;
  G4String fHadronSpecies = "neutron";
};

#endif
