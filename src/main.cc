#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"
#include "FileVisManager.hh"
#include "PhysicsList.hh"

#include "G4PhysListFactory.hh"
#include "G4RunManagerFactory.hh"
#include "G4StepLimiterPhysics.hh"
#include "G4String.hh"
#include "G4UImanager.hh"
#include "G4VModularPhysicsList.hh"

#ifdef MUON_LDMX_USE_STANDARD_VIS
#include "G4UIExecutive.hh"
#include "G4VisExecutive.hh"
#endif

#include <fstream>
#include <string>

namespace {
bool MacroUsesVisualization(const G4String& macroFile) {
  std::ifstream input(macroFile);
  std::string line;
  while (std::getline(input, line)) {
    if (line.find("/vis/") != std::string::npos) {
      return true;
    }
  }
  return false;
}
}  // namespace

int main(int argc, char** argv) {
  const G4String macroFile = argc > 1 ? argv[1] : "macros/run_muon.mac";
  const G4String physicsListName = argc > 2 ? argv[2] : "EM";
#ifdef MUON_LDMX_USE_STANDARD_VIS
  const bool keepInteractiveViewer =
      macroFile.find("vis_tsgqt") != std::string::npos ||
      macroFile.find("vis_ogl") != std::string::npos ||
      macroFile.find("vis_qt") != std::string::npos ||
      macroFile.find("vis_interactive") != std::string::npos;
  G4UIExecutive* ui = nullptr;
  if (keepInteractiveViewer) {
    ui = new G4UIExecutive(argc, argv, "qt");
  }
#endif

  auto* runManager =
      G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

  auto* detector = new DetectorConstruction();
  runManager->SetUserInitialization(detector);

  G4VModularPhysicsList* physicsList = nullptr;
  if (physicsListName == "EM") {
    physicsList = new PhysicsList();
  } else {
    G4PhysListFactory physicsFactory;
    physicsList = physicsFactory.GetReferencePhysList(physicsListName);
    if (physicsList == nullptr) {
      G4cerr << "Unknown Geant4 reference physics list: " << physicsListName
             << G4endl;
      delete runManager;
      return 1;
    }
  }
  physicsList->RegisterPhysics(new G4StepLimiterPhysics());
  runManager->SetUserInitialization(physicsList);

  runManager->SetUserInitialization(new ActionInitialization(detector));

  G4VisManager* visManager = nullptr;
  if (MacroUsesVisualization(macroFile)) {
#ifdef MUON_LDMX_USE_STANDARD_VIS
    visManager = new G4VisExecutive("warnings");
#else
    visManager = new FileVisManager();
#endif
    visManager->Initialize();
  }

  auto* uiManager = G4UImanager::GetUIpointer();
  uiManager->ApplyCommand("/control/execute " + macroFile);

#ifdef MUON_LDMX_USE_STANDARD_VIS
  if (ui != nullptr) {
    ui->SessionStart();
    delete ui;
  }
#endif
  if (visManager != nullptr) {
    delete visManager;
  }
  delete runManager;
  return 0;
}
