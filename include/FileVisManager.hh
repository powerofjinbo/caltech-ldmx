#ifndef FILE_VIS_MANAGER_HH
#define FILE_VIS_MANAGER_HH

#include "G4VisManager.hh"

class FileVisManager : public G4VisManager {
 public:
  FileVisManager();
  ~FileVisManager() override = default;

 private:
  void RegisterGraphicsSystems() override;
  void RegisterModelFactories() override;
};

#endif

