#include "PhysicsList.hh"

#include "G4DecayPhysics.hh"
#include "G4EmParameters.hh"
#include "G4EmStandardPhysics.hh"
#include "G4SystemOfUnits.hh"

PhysicsList::PhysicsList() {
  SetVerboseLevel(0);
  G4EmParameters::Instance()->SetVerbose(0);
  G4EmParameters::Instance()->SetWorkerVerbose(0);
  defaultCutValue = 1.0 * mm;

  RegisterPhysics(new G4EmStandardPhysics());
  RegisterPhysics(new G4DecayPhysics());
}

void PhysicsList::SetCuts() { SetCutsWithDefault(); }
