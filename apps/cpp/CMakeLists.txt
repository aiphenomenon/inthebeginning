cmake_minimum_required(VERSION 3.16)
project(InTheBeginning VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# --- Options ---
option(BUILD_GUI "Build the SDL2+OpenGL GUI target (inthebeginning-gui)" OFF)

# --- Compiler flags ---
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    add_compile_options(-Wall -Wextra -Wpedantic -O2)
endif()

# --- Shared simulator sources (used by both CLI and GUI) ---
set(SIMULATOR_SOURCES
    simulator/quantum.cpp
    simulator/atomic.cpp
    simulator/chemistry.cpp
    simulator/biology.cpp
    simulator/environment.cpp
    simulator/universe.cpp
)

# =============================================================
# CLI target: inthebeginning (no external dependencies)
# =============================================================
add_executable(inthebeginning
    simulator/main.cpp
    ${SIMULATOR_SOURCES}
)

target_include_directories(inthebeginning PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/simulator
)

# On Linux, link math and pthread
if(UNIX AND NOT APPLE)
    target_link_libraries(inthebeginning PRIVATE m pthread)
endif()

# =============================================================
# GUI target: inthebeginning-gui (requires SDL2 + OpenGL)
# =============================================================
if(BUILD_GUI)
    # --- Find SDL2 ---
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(SDL2 QUIET sdl2)
    endif()

    if(NOT SDL2_FOUND)
        find_package(SDL2 QUIET CONFIG)
    endif()

    if(NOT SDL2_FOUND)
        find_path(SDL2_INCLUDE_DIRS
            NAMES SDL.h
            PATH_SUFFIXES SDL2 include/SDL2
            PATHS
                /usr/include
                /usr/local/include
                /opt/homebrew/include
                /Library/Frameworks/SDL2.framework/Headers
        )
        find_library(SDL2_LIBRARIES
            NAMES SDL2
            PATHS
                /usr/lib
                /usr/local/lib
                /opt/homebrew/lib
                /Library/Frameworks
        )
        find_library(SDL2_MAIN_LIBRARY
            NAMES SDL2main
            PATHS
                /usr/lib
                /usr/local/lib
                /opt/homebrew/lib
        )
        if(SDL2_INCLUDE_DIRS AND SDL2_LIBRARIES)
            set(SDL2_FOUND TRUE)
            if(SDL2_MAIN_LIBRARY)
                list(APPEND SDL2_LIBRARIES ${SDL2_MAIN_LIBRARY})
            endif()
        endif()
    endif()

    if(NOT SDL2_FOUND)
        message(FATAL_ERROR
            "SDL2 not found (required for GUI build). Install with:\n"
            "  Ubuntu/Debian: sudo apt install libsdl2-dev\n"
            "  Fedora:        sudo dnf install SDL2-devel\n"
            "  Arch:          sudo pacman -S sdl2\n"
            "  macOS:         Download from https://libsdl.org (framework install)\n"
            "Or disable GUI: cmake .. -DBUILD_GUI=OFF\n"
        )
    endif()

    # --- Find OpenGL ---
    find_package(OpenGL REQUIRED)

    set(GUI_SOURCES
        main.cpp
        renderer.cpp
    )

    add_executable(inthebeginning-gui ${GUI_SOURCES} ${SIMULATOR_SOURCES})

    target_include_directories(inthebeginning-gui PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/simulator
        ${SDL2_INCLUDE_DIRS}
        ${OPENGL_INCLUDE_DIR}
    )

    target_link_libraries(inthebeginning-gui PRIVATE
        ${SDL2_LIBRARIES}
        OpenGL::GL
    )

    if(UNIX AND NOT APPLE)
        target_link_libraries(inthebeginning-gui PRIVATE dl pthread m)
    endif()

    if(APPLE)
        target_link_libraries(inthebeginning-gui PRIVATE "-framework Cocoa")
    endif()

    # --- Copy shaders to build directory ---
    file(GLOB SHADER_FILES "${CMAKE_CURRENT_SOURCE_DIR}/shaders/*.glsl")
    foreach(SHADER ${SHADER_FILES})
        get_filename_component(SHADER_NAME ${SHADER} NAME)
        configure_file(${SHADER} "${CMAKE_CURRENT_BINARY_DIR}/shaders/${SHADER_NAME}" COPYONLY)
    endforeach()

    add_custom_command(TARGET inthebeginning-gui POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
            "${CMAKE_CURRENT_SOURCE_DIR}/shaders"
            "$<TARGET_FILE_DIR:inthebeginning-gui>/shaders"
    )
endif()
