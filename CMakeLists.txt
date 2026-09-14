cmake_minimum_required(VERSION 3.17)
project(bsonjs LANGUAGES C)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# Read the package version from pyproject.toml for BSONJS_VERSION.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/pyproject.toml" _pyproject)
string(REGEX MATCH "version = \"([^\"]*)\"" _ "${_pyproject}")
set(_package_version "${CMAKE_MATCH_1}")

# --- libbson static library via FetchContent ---
include(FetchContent)

FetchContent_Declare(
  mongo-c-driver
  URL https://github.com/mongodb/mongo-c-driver/archive/refs/tags/2.5.3.tar.gz
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

# We only need libbson, not libmongoc, which requires a TLS/crypto library.
# Turning mongoc off also keeps the build C-only and the driver's dependencies
# out of the picture. Build libbson as a static library.
set(ENABLE_MONGOC OFF)
set(ENABLE_SHARED OFF)
set(ENABLE_STATIC ON)
# The driver builds a C++ test gated on BUILD_TESTING; keep the build C-only.
set(BUILD_TESTING OFF)
set(ENABLE_TESTS OFF)
FetchContent_MakeAvailable(mongo-c-driver)

# bson:static (alias bson_static) propagates BSON_STATIC already, but the
# driver does not export its include dirs on the target, so add them here so
# both #include <bson.h> and #include <bson/...> resolve. The generated
# config.h/version.h live in the binary dir, and the common/mlib headers come
# from the common tree.
set(_bson_src "${mongo-c-driver_SOURCE_DIR}/src/libbson")
set(_bson_bin "${mongo-c-driver_BINARY_DIR}/src/libbson")
set(_common_src "${mongo-c-driver_SOURCE_DIR}/src/common")
set(_common_bin "${mongo-c-driver_BINARY_DIR}/src/common")

# --- Build the extension module ---
Python_add_library(bsonjs MODULE WITH_SOABI "${CMAKE_CURRENT_SOURCE_DIR}/bsonjs/bsonjs.c")

target_include_directories(bsonjs PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/bsonjs"
  "${_bson_src}/src"
  "${_bson_src}/src/bson"
  "${_bson_bin}/src"
  "${_common_src}/src"
  "${_common_bin}/src"
)

target_compile_definitions(bsonjs PRIVATE
  Py_LIMITED_API=0x03090000
  BSONJS_VERSION="${_package_version}"
  BSON_STATIC
)

if(WIN32)
  target_link_libraries(bsonjs PRIVATE bson_static ws2_32)
elseif(APPLE)
  target_link_libraries(bsonjs PRIVATE bson_static)
else()
  target_link_libraries(bsonjs PRIVATE bson_static rt)
endif()

install(TARGETS bsonjs DESTINATION .)
