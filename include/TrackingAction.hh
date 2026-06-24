#ifndef TRACKING_ACTION_HH
#define TRACKING_ACTION_HH

#include "G4ThreeVector.hh"
#include "G4UserTrackingAction.hh"
#include "globals.hh"

class EventAction;
class G4Track;

class TrackingAction : public G4UserTrackingAction {
 public:
  explicit TrackingAction(EventAction* eventAction);
  ~TrackingAction() override = default;

  void PreUserTrackingAction(const G4Track* track) override;
  void PostUserTrackingAction(const G4Track* track) override;

 private:
  struct TrackStart {
    G4ThreeVector position;
    G4double kineticEnergy = 0.0;
  };

  EventAction* fEventAction;
  TrackStart fTrackStart;
};

#endif
