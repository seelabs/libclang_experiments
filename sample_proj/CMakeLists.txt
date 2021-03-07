cmake_minimum_required(VERSION 3.1.0)

if (DEFINED ENV{SWD_SDI})
  set(SWD_SDI $ENV{SWD_SDI})
else()
  set(SWD_SDI $ENV{HOME}/projs/sdi)
endif()

if (DEFINED ENV{SWD_PROJS_COMMON})
  set(SWD_PROJS_COMMON $ENV{SWD_PROJS_COMMON})
else()
  set(SWD_PROJS_COMMON $ENV{HOME}/projs/common)
endif()

set(CMAKE_MODULE_PATH "${SWD_SDI}/cmake/module")
include(CMakeFuncs)
set_compiler()

# Project must be set after the compiler is set
project(scratch)

set_linker()

set(CMAKE_CXX_STANDARD 17)

add_executable(main src/main.cpp)
target_link_libraries(main)
nih(main)
