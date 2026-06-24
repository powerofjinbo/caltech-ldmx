#include "RunAction.hh"

#include "G4AnalysisManager.hh"
#include "G4Run.hh"

#include <filesystem>
#include <fstream>

RunAction::RunAction(G4String outputBaseName)
    : fOutputBaseName(std::move(outputBaseName)) {
  auto* analysis = G4AnalysisManager::Instance();
  analysis->SetDefaultFileType("csv");
  analysis->SetVerboseLevel(1);
  analysis->SetNtupleMerging(false);

  analysis->CreateNtuple("events", "Event-level active-target observables");
  analysis->CreateNtupleIColumn("event_id");
  analysis->CreateNtupleDColumn("total_edep_mev");
  analysis->CreateNtupleDColumn("primary_muon_edep_mev");
  analysis->CreateNtupleDColumn("extra_edep_mev");
  analysis->CreateNtupleIColumn("n_hit_crystals");
  analysis->CreateNtupleIColumn("n_hit_layers");
  analysis->CreateNtupleIColumn("n_extra_hit_crystals");
  analysis->CreateNtupleIColumn("n_extra_hit_layers");
  analysis->CreateNtupleDColumn("max_layer_edep_mev");
  analysis->CreateNtupleDColumn("out_muon_ke_gev");
  analysis->CreateNtupleIColumn("n_secondaries");
  analysis->CreateNtupleIColumn("n_charged_secondaries");
  analysis->CreateNtupleIColumn("n_gamma_secondaries");
  analysis->FinishNtuple();

  analysis->CreateNtuple("layers", "Per-layer active-target observables");
  analysis->CreateNtupleIColumn("event_id");
  analysis->CreateNtupleIColumn("layer_id");
  analysis->CreateNtupleDColumn("layer_edep_mev");
  analysis->CreateNtupleDColumn("extra_layer_edep_mev");
  analysis->CreateNtupleIColumn("n_hit_crystals");
  analysis->CreateNtupleIColumn("n_extra_hit_crystals");
  analysis->FinishNtuple();

  analysis->CreateNtuple("crystals", "Per-crystal active-target observables");
  analysis->CreateNtupleIColumn("event_id");
  analysis->CreateNtupleIColumn("layer_id");
  analysis->CreateNtupleIColumn("crystal_id");
  analysis->CreateNtupleDColumn("crystal_edep_mev");
  analysis->CreateNtupleDColumn("extra_crystal_edep_mev");
  analysis->FinishNtuple();

}

void RunAction::BeginOfRunAction(const G4Run*) {
  std::filesystem::create_directories("output");
  std::ofstream tracks("output/base_muon_nt_tracks.csv");
  tracks << "event_id,track_id,parent_id,particle_name,pdg,charge_e,"
            "creator_process,start_x_mm,start_y_mm,start_z_mm,end_x_mm,"
            "end_y_mm,end_z_mm,initial_ke_mev,final_ke_mev,track_length_mm\n";
  G4AnalysisManager::Instance()->OpenFile(fOutputBaseName);
}

void RunAction::EndOfRunAction(const G4Run*) {
  auto* analysis = G4AnalysisManager::Instance();
  analysis->Write();
  analysis->CloseFile();
}
