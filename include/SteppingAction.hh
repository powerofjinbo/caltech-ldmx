#ifndef STEPPING_ACTION_HH
#define STEPPING_ACTION_HH

#include "G4UserSteppingAction.hh"

class DetectorConstruction;
class EventAction;
class G4Step;

class SteppingAction : public G4UserSteppingAction {
 public:
  SteppingAction(EventAction* eventAction, const DetectorConstruction* detector);
  ~SteppingAction() override = default;

  void UserSteppingAction(const G4Step* step) override;

 private:
  EventAction* fEventAction;
  const DetectorConstruction* fDetector;
};

#endif

