#include "ActionInitialization.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "SteppingAction.hh"
#include "TrackingAction.hh"

ActionInitialization::ActionInitialization(const DetectorConstruction* detector)
    : fDetector(detector) {}

void ActionInitialization::Build() const {
  auto* eventAction =
      new EventAction(fDetector->GetNumberOfLayers(),
                      fDetector->GetCrystalsPerLayer());
  auto* runAction = new RunAction("output/muon_5gev_40layer");

  SetUserAction(new PrimaryGeneratorAction());
  SetUserAction(runAction);
  SetUserAction(eventAction);
  SetUserAction(new SteppingAction(eventAction, fDetector));
  SetUserAction(new TrackingAction(eventAction, runAction));
}
