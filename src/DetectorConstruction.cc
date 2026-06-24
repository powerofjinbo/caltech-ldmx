#include "DetectorConstruction.hh"

#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4ThreeVector.hh"
#include "G4VisAttributes.hh"

#include <sstream>

G4Material* DetectorConstruction::BuildLYSO() const {
  auto* nist = G4NistManager::Instance();

  auto* lu = nist->FindOrBuildElement("Lu");
  auto* y = nist->FindOrBuildElement("Y");
  auto* si = nist->FindOrBuildElement("Si");
  auto* o = nist->FindOrBuildElement("O");

  auto* lyso = new G4Material("LYSO_approx", 7.10 * g / cm3, 4);
  lyso->AddElement(lu, 0.7144);
  lyso->AddElement(y, 0.0403);
  lyso->AddElement(si, 0.0637);
  lyso->AddElement(o, 0.1816);

  return lyso;
}

G4VPhysicalVolume* DetectorConstruction::Construct() {
  auto* nist = G4NistManager::Instance();
  auto* air = nist->FindOrBuildMaterial("G4_AIR");
  auto* lyso = BuildLYSO();

  auto* worldSolid = new G4Box("WorldSolid", 50.0 * cm, 50.0 * cm, 80.0 * cm);
  auto* worldLogical = new G4LogicalVolume(worldSolid, air, "World");
  auto* worldPhysical =
      new G4PVPlacement(nullptr, G4ThreeVector(), worldLogical, "World", nullptr,
                        false, 0, false);

  auto* crystalXSolid =
      new G4Box("LYSOBarXSolid", 0.5 * fCrystalLength,
                0.5 * fCrystalPitch, 0.5 * fLayerThickness);
  auto* crystalYSolid =
      new G4Box("LYSOBarYSolid", 0.5 * fCrystalPitch,
                0.5 * fCrystalLength, 0.5 * fLayerThickness);

  worldLogical->SetVisAttributes(G4VisAttributes::GetInvisible());

  for (G4int layer = 0; layer < fNumberOfLayers; ++layer) {
    const G4double z = -fTargetHalfZ + 0.5 * fLayerThickness +
                       layer * (fLayerThickness + fLayerGap);
    const G4bool barsAlongX = (layer % 2 == 0);

    for (G4int crystal = 0; crystal < fCrystalsPerLayer; ++crystal) {
      const G4double offset =
          (crystal + 0.5 - 0.5 * fCrystalsPerLayer) * fCrystalPitch;
      const G4int copyNumber = layer * fCrystalsPerLayer + crystal;

      const G4ThreeVector position =
          barsAlongX ? G4ThreeVector(0.0, offset, z)
                     : G4ThreeVector(offset, 0.0, z);
      std::ostringstream logicalName;
      logicalName << "LYSOBar_" << layer << "_" << crystal;
      auto* logical = new G4LogicalVolume(
          barsAlongX ? crystalXSolid : crystalYSolid, lyso,
          logicalName.str());

      const auto layerTint = (layer % 4) * 0.035;
      const G4Colour color =
          barsAlongX ? G4Colour(0.12 + layerTint, 0.58 + layerTint,
                                0.95, 0.35)
                     : G4Colour(1.00, 0.58 + layerTint,
                                0.16 + layerTint, 0.35);
      auto* crystalVis = new G4VisAttributes(color);
      crystalVis->SetVisibility(true);
      crystalVis->SetForceWireframe(true);
      crystalVis->SetForceAuxEdgeVisible(true);
      logical->SetVisAttributes(crystalVis);

      new G4PVPlacement(nullptr, position, logical, "LYSOCrystal",
                        worldLogical, false, copyNumber, false);
    }
  }

  return worldPhysical;
}
