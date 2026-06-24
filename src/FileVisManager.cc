#include "FileVisManager.hh"

#include "G4TrajectoryDrawByCharge.hh"
#include "G4VRML2File.hh"

FileVisManager::FileVisManager() : G4VisManager("warnings") {}

void FileVisManager::RegisterGraphicsSystems() {
  RegisterGraphicsSystem(new G4VRML2File);
}

void FileVisManager::RegisterModelFactories() {
  RegisterModel(new G4TrajectoryDrawByCharge("drawByCharge"));
  SelectTrajectoryModel("drawByCharge");
}

