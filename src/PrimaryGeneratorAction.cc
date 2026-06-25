#include "PrimaryGeneratorAction.hh"

#include "DetectorConstruction.hh"

#include "G4Event.hh"
#include "G4Exception.hh"
#include "G4GenericMessenger.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"

#include <algorithm>
#include <cmath>

PrimaryGeneratorAction::PrimaryGeneratorAction(
    const DetectorConstruction* detector)
    : fDetector(detector), fParticleGun(std::make_unique<G4ParticleGun>(1)) {
  auto* particleTable = G4ParticleTable::GetParticleTable();
  auto* muon = particleTable->FindParticle("mu-");

  fParticleGun->SetParticleDefinition(muon);
  fParticleGun->SetParticleEnergy(8.0 * GeV);
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0.0, 0.0, 1.0));
  fParticleGun->SetParticlePosition(G4ThreeVector(0.1 * mm, 0.1 * mm,
                                                  -25.0 * cm));
  fSecondaryEnergy = 1.0 * GeV;

  fMessenger = std::make_unique<G4GenericMessenger>(
      this, "/muonActiveTarget/generator/",
      "Controlled topology generator controls");
  auto& modeCommand = fMessenger->DeclareProperty(
      "generatorMode", fGeneratorMode,
      "Generator mode: cleanMuon, muGamma, muPair, or muHadron");
  modeCommand.SetParameterName("generatorMode", false);
  modeCommand.SetStates(G4State_Idle);

  auto& energyCommand = fMessenger->DeclarePropertyWithUnit(
      "secondaryEnergy", "GeV", fSecondaryEnergy,
      "Kinetic energy of each controlled injected particle");
  energyCommand.SetParameterName("secondaryEnergy", false);
  energyCommand.SetStates(G4State_Idle);

  auto& angleCommand = fMessenger->DeclarePropertyWithUnit(
      "secondaryAngle", "deg", fSecondaryAngle,
      "Angle of the controlled injected particle relative to +z");
  angleCommand.SetParameterName("secondaryAngle", false);
  angleCommand.SetStates(G4State_Idle);

  auto& layerCommand = fMessenger->DeclareMethod(
      "emissionLayer", &PrimaryGeneratorAction::SetEmissionLayer,
      "Layer index used as controlled emission point");
  layerCommand.SetParameterName("emissionLayer", false);
  layerCommand.SetStates(G4State_Idle);

  auto& zCommand = fMessenger->DeclareMethodWithUnit(
      "emissionZ", "mm", &PrimaryGeneratorAction::SetEmissionZ,
      "Explicit controlled emission z position");
  zCommand.SetParameterName("emissionZ", false);
  zCommand.SetStates(G4State_Idle);

  auto& hadronCommand = fMessenger->DeclareProperty(
      "hadronSpecies", fHadronSpecies,
      "Hadron species for muHadron: pi+, pi-, proton, or neutron");
  hadronCommand.SetParameterName("hadronSpecies", false);
  hadronCommand.SetStates(G4State_Idle);
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() = default;

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
  auto* primaryParticle = fParticleGun->GetParticleDefinition();
  const auto primaryEnergy = fParticleGun->GetParticleEnergy();
  const auto primaryPosition = fParticleGun->GetParticlePosition();
  const auto primaryDirection = fParticleGun->GetParticleMomentumDirection();

  // Always fire the baseline muon first so track id 1 remains the primary
  // muon used by the existing scoring code.
  fParticleGun->GeneratePrimaryVertex(event);

  if (fGeneratorMode == "cleanMuon") {
    return;
  }
  if (fGeneratorMode == "muGamma") {
    GenerateExtraParticle(event, "gamma", fSecondaryEnergy, fSecondaryAngle);
  } else if (fGeneratorMode == "muPair") {
    GenerateExtraParticle(event, "e-", fSecondaryEnergy, fSecondaryAngle,
                          +1.0);
    GenerateExtraParticle(event, "e+", fSecondaryEnergy, fSecondaryAngle,
                          -1.0);
  } else if (fGeneratorMode == "muHadron") {
    GenerateExtraParticle(event, fHadronSpecies, fSecondaryEnergy,
                          fSecondaryAngle);
  } else {
    G4ExceptionDescription description;
    description << "Unknown /muonActiveTarget/generator/generatorMode: "
                << fGeneratorMode
                << ". Supported modes are cleanMuon, muGamma, muPair, "
                   "and muHadron.";
    G4Exception("PrimaryGeneratorAction::GeneratePrimaries",
                "MuonLDMXGenerator001", FatalException, description);
  }

  fParticleGun->SetParticleDefinition(primaryParticle);
  fParticleGun->SetParticleEnergy(primaryEnergy);
  fParticleGun->SetParticlePosition(primaryPosition);
  fParticleGun->SetParticleMomentumDirection(primaryDirection);
}

void PrimaryGeneratorAction::SetEmissionLayer(G4int layer) {
  fEmissionLayer = layer;
  fUseExplicitEmissionZ = false;
}

void PrimaryGeneratorAction::SetEmissionZ(G4double z) {
  fEmissionZ = z;
  fUseExplicitEmissionZ = true;
}

G4double PrimaryGeneratorAction::GetEmissionZ() const {
  if (fUseExplicitEmissionZ) {
    return fEmissionZ;
  }

  const auto nLayers = fDetector->GetNumberOfLayers();
  const auto layer = std::clamp(fEmissionLayer, 0, nLayers - 1);
  if (nLayers <= 1) {
    return 0.0;
  }

  const auto layerThickness = fDetector->GetLayerThickness();
  const auto targetHalfZ = fDetector->GetTargetHalfZ();
  const auto layerPitch = (2.0 * targetHalfZ - layerThickness) /
                          static_cast<G4double>(nLayers - 1);
  return -targetHalfZ + 0.5 * layerThickness + layer * layerPitch;
}

void PrimaryGeneratorAction::GenerateExtraParticle(
    G4Event* event, const G4String& particleName, G4double energy,
    G4double angle, G4double yDirectionSign) {
  auto* particle =
      G4ParticleTable::GetParticleTable()->FindParticle(particleName);
  if (particle == nullptr) {
    G4ExceptionDescription description;
    description << "Unknown controlled injected particle: " << particleName;
    G4Exception("PrimaryGeneratorAction::GenerateExtraParticle",
                "MuonLDMXGenerator002", FatalException, description);
  }

  const auto primaryPosition = fParticleGun->GetParticlePosition();
  const G4ThreeVector emissionPosition(primaryPosition.x(), primaryPosition.y(),
                                       GetEmissionZ());
  G4ThreeVector direction(std::sin(angle), 0.0, std::cos(angle));
  if (yDirectionSign != 0.0) {
    direction = G4ThreeVector(0.0, yDirectionSign * std::sin(angle),
                              std::cos(angle));
  }
  direction = direction.unit();

  fParticleGun->SetParticleDefinition(particle);
  fParticleGun->SetParticleEnergy(energy);
  fParticleGun->SetParticlePosition(emissionPosition);
  fParticleGun->SetParticleMomentumDirection(direction);
  fParticleGun->GeneratePrimaryVertex(event);
}
