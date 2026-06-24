cmake_minimum_required(VERSION 3.20)

project(MuonLDMXActiveTarget VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(DEFINED ENV{G4INSTALL} AND EXISTS "$ENV{G4INSTALL}/bin/geant4-config")
  set(GEANT4_CONFIG_EXECUTABLE "$ENV{G4INSTALL}/bin/geant4-config" CACHE FILEPATH
      "Geant4 configuration helper" FORCE)
else()
  find_program(GEANT4_CONFIG_EXECUTABLE geant4-config REQUIRED)
endif()
execute_process(
  COMMAND "${GEANT4_CONFIG_EXECUTABLE}" --cflags-without-gui
  OUTPUT_VARIABLE GEANT4_CFLAGS_NO_GUI_RAW
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
  COMMAND "${GEANT4_CONFIG_EXECUTABLE}" --libs-without-gui
  OUTPUT_VARIABLE GEANT4_LIBS_NO_GUI_RAW
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
  COMMAND "${GEANT4_CONFIG_EXECUTABLE}" --cflags
  OUTPUT_VARIABLE GEANT4_CFLAGS_RAW
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
  COMMAND "${GEANT4_CONFIG_EXECUTABLE}" --libs
  OUTPUT_VARIABLE GEANT4_LIBS_RAW
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
  COMMAND "${GEANT4_CONFIG_EXECUTABLE}" --prefix
  OUTPUT_VARIABLE GEANT4_PREFIX
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

separate_arguments(GEANT4_CFLAGS_NO_GUI UNIX_COMMAND "${GEANT4_CFLAGS_NO_GUI_RAW}")
separate_arguments(GEANT4_LIBS_NO_GUI UNIX_COMMAND "${GEANT4_LIBS_NO_GUI_RAW}")
separate_arguments(GEANT4_CFLAGS UNIX_COMMAND "${GEANT4_CFLAGS_RAW}")
separate_arguments(GEANT4_LIBS UNIX_COMMAND "${GEANT4_LIBS_RAW}")
set(GEANT4_FILE_VIS_LIBS
  "-L${GEANT4_PREFIX}/lib"
  "-lG4VRML"
  "-lG4vis_management"
  "-lG4modeling"
)

file(GLOB MUON_ACTIVE_TARGET_SOURCES CONFIGURE_DEPENDS
  "${PROJECT_SOURCE_DIR}/src/*.cc"
)

add_executable(muon_active_target ${MUON_ACTIVE_TARGET_SOURCES})
target_include_directories(muon_active_target PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_options(muon_active_target PRIVATE ${GEANT4_CFLAGS_NO_GUI})
target_link_libraries(muon_active_target PRIVATE ${GEANT4_FILE_VIS_LIBS} ${GEANT4_LIBS_NO_GUI})
set_target_properties(muon_active_target PROPERTIES
  BUILD_RPATH "${GEANT4_PREFIX}/lib"
)

add_executable(muon_active_target_gui ${MUON_ACTIVE_TARGET_SOURCES})
target_include_directories(muon_active_target_gui PRIVATE "${PROJECT_SOURCE_DIR}/include")
target_compile_options(muon_active_target_gui PRIVATE ${GEANT4_CFLAGS})
target_compile_definitions(muon_active_target_gui PRIVATE MUON_LDMX_USE_STANDARD_VIS=1)
target_link_libraries(muon_active_target_gui PRIVATE ${GEANT4_LIBS})
set_target_properties(muon_active_target_gui PROPERTIES
  BUILD_RPATH "${GEANT4_PREFIX}/lib"
)

file(COPY "${PROJECT_SOURCE_DIR}/macros" DESTINATION "${PROJECT_BINARY_DIR}")
