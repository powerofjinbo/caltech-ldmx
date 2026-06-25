#include "TrackingAction.hh"

#include "EventAction.hh"
#include "RunAction.hh"

#include "G4AnalysisManager.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"

#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>

namespace {
std::string CsvEscape(const G4String& value) {
  std::string escaped = "\"";
  for (const char character : value) {
    if (character == '"') {
      escaped += "\"\"";
    } else {
      escaped += character;
    }
  }
  escaped += '"';
  return escaped;
}
}  // namespace

TrackingAction::TrackingAction(EventAction* eventAction,
                               const RunAction* runAction)
    : fEventAction(eventAction), fRunAction(runAction) {}

void TrackingAction::PreUserTrackingAction(const G4Track* track) {
  fTrackStart.position = track->GetPosition();
  fTrackStart.kineticEnergy = track->GetKineticEnergy();
}

void TrackingAction::PostUserTrackingAction(const G4Track* track) {
  const auto* particle = track->GetDefinition();
  const auto* creator = track->GetCreatorProcess();

  const G4String particleName =
      particle != nullptr ? particle->GetParticleName() : "unknown";
  const G4int pdg = particle != nullptr ? particle->GetPDGEncoding() : 0;
  const G4double charge =
      particle != nullptr ? particle->GetPDGCharge() / eplus : 0.0;
  const G4String creatorName =
      creator != nullptr ? creator->GetProcessName() : "primary";
  const auto end = track->GetPosition();

  std::ofstream output(fRunAction->GetOutputBaseName() + "_tracks.csv",
                       std::ios::app);
  output << std::setprecision(9) << fEventAction->GetEventId() << ','
         << track->GetTrackID() << ',' << track->GetParentID() << ','
         << CsvEscape(particleName) << ',' << pdg << ',' << charge << ','
         << CsvEscape(creatorName) << ',' << fTrackStart.position.x() / mm
         << ',' << fTrackStart.position.y() / mm << ','
         << fTrackStart.position.z() / mm << ',' << end.x() / mm << ','
         << end.y() / mm << ',' << end.z() / mm << ','
         << fTrackStart.kineticEnergy / MeV << ','
         << track->GetKineticEnergy() / MeV << ','
         << track->GetTrackLength() / mm << '\n';
}
