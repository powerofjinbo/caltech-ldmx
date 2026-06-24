#ifndef RUN_ACTION_HH
#define RUN_ACTION_HH

#include "G4String.hh"
#include "G4UserRunAction.hh"

class G4Run;

class RunAction : public G4UserRunAction {
 public:
  explicit RunAction(G4String outputBaseName);
  ~RunAction() override = default;

  void BeginOfRunAction(const G4Run* run) override;
  void EndOfRunAction(const G4Run* run) override;

 private:
  G4String fOutputBaseName;
};

#endif

