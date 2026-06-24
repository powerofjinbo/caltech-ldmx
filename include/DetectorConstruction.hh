#ifndef DETECTOR_CONSTRUCTION_HH
#define DETECTOR_CONSTRUCTION_HH

#include "G4SystemOfUnits.hh"
#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class G4LogicalVolume;
class G4Material;
class G4VPhysicalVolume;

class DetectorConstruction : public G4VUserDetectorConstruction {
 public:
  DetectorConstruction() = default;
  ~DetectorConstruction() override = default;

  G4VPhysicalVolume* Construct() override;

  G4int GetNumberOfLayers() const { return fNumberOfLayers; }
  G4int GetCrystalsPerLayer() const { return fCrystalsPerLayer; }
  G4double GetLayerThickness() const { return fLayerThickness; }
  G4double GetTargetHalfZ() const { return fTargetHalfZ; }

 private:
  G4Material* BuildLYSO() const;

  const G4int fNumberOfLayers = 25;
  const G4int fCrystalsPerLayer = 10;
  const G4double fCrystalPitch = 1.0 * cm;
  const G4double fLayerThickness = 1.0 * cm;
  const G4double fLayerGap = 0.1 * mm;
  const G4double fCrystalLength = 10.0 * cm;
  const G4double fTargetHalfZ =
      0.5 * (fNumberOfLayers * fLayerThickness +
             (fNumberOfLayers - 1) * fLayerGap);

};

#endif
