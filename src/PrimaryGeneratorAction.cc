#include "PrimaryGeneratorAction.hh"

#include "G4Event.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction()
    : fParticleGun(std::make_unique<G4ParticleGun>(1)) {
  auto* particleTable = G4ParticleTable::GetParticleTable();
  auto* muon = particleTable->FindParticle("mu-");

  fParticleGun->SetParticleDefinition(muon);
  fParticleGun->SetParticleEnergy(5.0 * GeV);
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0.0, 0.0, 1.0));
  fParticleGun->SetParticlePosition(G4ThreeVector(0.1 * mm, 0.1 * mm,
                                                  -25.0 * cm));
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() = default;

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
  fParticleGun->GeneratePrimaryVertex(event);
}
