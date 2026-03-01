cmake_minimum_required(VERSION 3.16)
project(InTheBeginning VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# --- Compiler flags ---
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    add_compile_options(-Wall -Wextra -Wpedantic -O2)
endif()

# --- Find SDL2 ---
# Try pkg-config first (Linux), then CMake config, then manual
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(SDL2 QUIET sdl2)
endif()

if(NOT SDL2_FOUND)
    find_package(SDL2 QUIET CONFIG)
endif()

if(NOT SDL2_FOUND)
    # Manual fallback for common install locations
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
        "SDL2 not found. Install with:\n"
        "  Ubuntu/Debian: sudo apt install libsdl2-dev\n"
        "  Fedora:        sudo dnf install SDL2-devel\n"
        "  Arch:          sudo pacman -S sdl2\n"
        "  macOS:         Download from https://libsdl.org (framework install)\n"
    )
endif()

# --- Find OpenGL ---
find_package(OpenGL REQUIRED)

# --- Source files ---
set(SIMULATOR_SOURCES
    simulator/quantum.cpp
    simulator/atomic.cpp
    simulator/chemistry.cpp
    simulator/biology.cpp
    simulator/environment.cpp
    simulator/universe.cpp
)

set(APP_SOURCES
    main.cpp
    renderer.cpp
)

# --- Executable ---
add_executable(inthebeginning ${APP_SOURCES} ${SIMULATOR_SOURCES})

target_include_directories(inthebeginning PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${SDL2_INCLUDE_DIRS}
    ${OPENGL_INCLUDE_DIR}
)

target_link_libraries(inthebeginning PRIVATE
    ${SDL2_LIBRARIES}
    OpenGL::GL
)

# On Linux, we also need dl and pthread
if(UNIX AND NOT APPLE)
    target_link_libraries(inthebeginning PRIVATE dl pthread m)
endif()

# On macOS with framework SDL2
if(APPLE)
    target_link_libraries(inthebeginning PRIVATE "-framework Cocoa")
endif()

# --- Copy shaders to build directory ---
file(GLOB SHADER_FILES "${CMAKE_CURRENT_SOURCE_DIR}/shaders/*.glsl")
foreach(SHADER ${SHADER_FILES})
    get_filename_component(SHADER_NAME ${SHADER} NAME)
    configure_file(${SHADER} "${CMAKE_CURRENT_BINARY_DIR}/shaders/${SHADER_NAME}" COPYONLY)
endforeach()

# Also install shaders alongside executable
add_custom_command(TARGET inthebeginning POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_CURRENT_SOURCE_DIR}/shaders"
        "$<TARGET_FILE_DIR:inthebeginning>/shaders"
)
