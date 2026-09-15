cmake_minimum_required(VERSION 3.26)

# Wrap the compiler in ccache when it's available so the repeated libbson
# build in CI is served from the cache. Must be set before project() so the
# launcher applies to the C compiler (and the FetchContent sub-build). Only
# enable it on GNU/Clang platforms: ccache's MSVC launcher hangs CMake's
# compiler detection on Windows.
if(NOT WIN32)
  find_program(CCACHE_PROGRAM ccache)
  if(CCACHE_PROGRAM)
    set(CMAKE_C_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
  endif()
endif()

project(bsonjs LANGUAGES C)

find_package(Python COMPONENTS Interpreter Development.Module Development.SABIModule REQUIRED)

# Read the package version from pyproject.toml for BSONJS_VERSION.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/pyproject.toml" _pyproject)
string(REGEX MATCH "version = \"([^\"]*)\"" _ "${_pyproject}")
set(_package_version "${CMAKE_MATCH_1}")

# --- libbson static library via FetchContent ---
include(FetchContent)

# Small timing helper: logs a phase marker with an elapsed counter so a
# completed or cancelled CI log shows where the build time is going.
string(TIMESTAMP _bsonjs_last "%s")
function(bsonjs_mark msg)
  string(TIMESTAMP _now "%s")
  math(EXPR _elapsed "${_now} - ${_bsonjs_last}")
  message(STATUS "[bsonjs] ${msg} (+${_elapsed}s)")
  set(_bsonjs_last "${_now}" PARENT_SCOPE)
endfunction()
bsonjs_mark("configure begin")

# The mongo-c-driver release tarball is pre-fetched by CI
# (.github/actions/setup-mongo-c-driver) and passed in via BSONJS_MCD_TARBALL,
# so the CI build phase is download-free. Otherwise (dist.yml wheels, sdist,
# local builds) download with hard timeouts so a stalled connection fails fast
# instead of hanging the build for tens of minutes.
set(_mcd_url "https://github.com/mongodb/mongo-c-driver/archive/refs/tags/2.5.3.tar.gz")
set(_mcd_archive "${CMAKE_CURRENT_BINARY_DIR}/mongo-c-driver-2.5.3.tar.gz")
if(DEFINED ENV{BSONJS_MCD_TARBALL})
  # Normalize Windows backslash paths, which would otherwise break the
  # FetchContent subbuild's generated CMakeLists.txt.
  file(TO_CMAKE_PATH "$ENV{BSONJS_MCD_TARBALL}" _mcd_cached)
  if(EXISTS "${_mcd_cached}")
    set(_mcd_archive "${_mcd_cached}")
  endif()
endif()
message(STATUS "[bsonjs] mongo-c-driver BSONJS_MCD_TARBALL=$ENV{BSONJS_MCD_TARBALL}")
message(STATUS "[bsonjs] mongo-c-driver archive=${_mcd_archive}")
if(NOT EXISTS "${_mcd_archive}")
  bsonjs_mark("archive missing -> downloading")
  file(DOWNLOAD
    "${_mcd_url}"
    "${_mcd_archive}"
    TLS_VERIFY ON
    TIMEOUT 300
    INACTIVITY_TIMEOUT 120
    RETRY_COUNT 3
    RETRY_DELAY 5
    STATUS _mcd_status
  )
  list(GET _mcd_status 0 _mcd_code)
  if(NOT _mcd_code EQUAL 0)
    message(FATAL_ERROR "Failed to download mongo-c-driver: ${_mcd_status}")
  endif()
  bsonjs_mark("archive downloaded")
else()
  file(SIZE "${_mcd_archive}" _mcd_size)
  message(STATUS "[bsonjs] mongo-c-driver archive size=${_mcd_size} bytes (cached)")
endif()

FetchContent_Declare(
  mongo-c-driver
  URL "${_mcd_archive}"
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

bsonjs_mark("FetchContent_MakeAvailable begin")
FetchContent_MakeAvailable(mongo-c-driver)
bsonjs_mark("FetchContent_MakeAvailable done")

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
# USE_SABI links Python::SABIModule and sets Py_LIMITED_API from the version,
# producing a module suffix that stays importable across every CPython >= 3.11,
# so a single cp311-abi3 wheel is reused for all of them. (WITH_SOABI would bake
# the build interpreter's SOABI into the name, which newer interpreters can't
# discover.)
Python_add_library(bsonjs MODULE USE_SABI 3.11 "${CMAKE_CURRENT_SOURCE_DIR}/bsonjs/bsonjs.c")

target_include_directories(bsonjs PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/bsonjs"
  "${_bson_src}/src"
  "${_bson_src}/src/bson"
  "${_bson_bin}/src"
  "${_common_src}/src"
  "${_common_bin}/src"
)

target_compile_definitions(bsonjs PRIVATE
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
