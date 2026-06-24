#include "SteppingAction.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"

#include "G4LogicalVolume.hh"
#include "G4ParticleDefinition.hh"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4SystemOfUnits.hh"
#include "G4TouchableHandle.hh"
#include "G4Track.hh"
#include "G4VPhysicalVolume.hh"

namespace {
bool IsMuon(const G4ParticleDefinition* particle) {
  if (particle == nullptr) {
    return false;
  }
  const auto name = particle->GetParticleName();
  return name == "mu-" || name == "mu+";
}
}  // namespace

SteppingAction::SteppingAction(EventAction* eventAction,
                               const DetectorConstruction* detector)
    : fEventAction(eventAction), fDetector(detector) {}

void SteppingAction::UserSteppingAction(const G4Step* step) {
  auto* track = step->GetTrack();
  auto* particle = track->GetDefinition();
  const G4bool fromPrimaryMuon =
      track->GetTrackID() == 1 && IsMuon(particle);

  const auto* preStepPoint = step->GetPreStepPoint();
  const auto touchable = preStepPoint->GetTouchableHandle();
  const auto* volume = touchable->GetVolume();

  if (volume != nullptr) {
    if (volume->GetName() == "LYSOCrystal") {
      const G4int copyNumber = touchable->GetCopyNumber();
      fEventAction->AddCrystalEdep(copyNumber, step->GetTotalEnergyDeposit(),
                                   fromPrimaryMuon);
    }
  }

  const auto* secondaries = step->GetSecondaryInCurrentStep();
  for (const auto* secondary : *secondaries) {
    fEventAction->CountSecondary(secondary->GetDefinition());
  }

  if (fromPrimaryMuon) {
    const auto* postStepPoint = step->GetPostStepPoint();
    const auto preZ = preStepPoint->GetPosition().z();
    const auto postZ = postStepPoint->GetPosition().z();
    if (preZ <= fDetector->GetTargetHalfZ() &&
        postZ > fDetector->GetTargetHalfZ() &&
        track->GetMomentumDirection().z() > 0.0) {
      fEventAction->SetOutgoingMuonKineticEnergy(
          postStepPoint->GetKineticEnergy());
    }
  }
}
