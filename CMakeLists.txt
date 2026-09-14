cmake_minimum_required(VERSION 3.26)

# Wrap the compiler in ccache when it's available so the repeated libbson
# build in CI is served from the cache. Must be set before project() so the
# launcher applies to the C compiler (and the FetchContent sub-build).
find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
  set(CMAKE_C_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
endif()

project(bsonjs LANGUAGES C)

find_package(Python COMPONENTS Interpreter Development.Module Development.SABIModule REQUIRED)

# Read the package version from pyproject.toml for BSONJS_VERSION.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/pyproject.toml" _pyproject)
string(REGEX MATCH "version = \"([^\"]*)\"" _ "${_pyproject}")
set(_package_version "${CMAKE_MATCH_1}")

# --- libbson static library via FetchContent ---
include(FetchContent)

# A git clone of mongo-c-driver hangs on the Windows CI runners (no output for
# hours), and a bare tarball URL can hit transient HTTP 504s. Download the
# release tarball once with retries and feed the local archive to FetchContent,
# which is deterministic on every platform.
set(_mcd_url "https://github.com/mongodb/mongo-c-driver/archive/refs/tags/2.5.3.tar.gz")
set(_mcd_archive "${CMAKE_CURRENT_BINARY_DIR}/mongo-c-driver-2.5.3.tar.gz")
file(DOWNLOAD
  "${_mcd_url}"
  "${_mcd_archive}"
  TLS_VERIFY ON
  RETRY_COUNT 3
  RETRY_DELAY 5
  STATUS _mcd_status
)
list(GET _mcd_status 0 _mcd_code)
if(NOT _mcd_code EQUAL 0)
  message(FATAL_ERROR "Failed to download mongo-c-driver: ${_mcd_status}")
endif()

FetchContent_Declare(
  mongo-c-driver
  URL "${_mcd_archive}"
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
