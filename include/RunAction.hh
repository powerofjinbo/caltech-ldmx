#ifndef RUN_ACTION_HH
#define RUN_ACTION_HH

#include "G4String.hh"
#include "G4UserRunAction.hh"

#include <memory>

class G4GenericMessenger;
class G4Run;

class RunAction : public G4UserRunAction {
 public:
  explicit RunAction(G4String outputBaseName);
  ~RunAction() override;

  void BeginOfRunAction(const G4Run* run) override;
  void EndOfRunAction(const G4Run* run) override;
  const G4String& GetOutputBaseName() const { return fOutputBaseName; }

 private:
  G4String fOutputBaseName;
  std::unique_ptr<G4GenericMessenger> fMessenger;
};

#endif
