cmake_minimum_required(VERSION 3.17)
project(bsonjs LANGUAGES C)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# Read the package version from pyproject.toml for BSONJS_VERSION.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/pyproject.toml" _pyproject)
string(REGEX MATCH "version = \"([^\"]*)\"" _ "${_pyproject}")
set(_package_version "${CMAKE_MATCH_1}")

# --- libbson static library detection ---
set(LIBBSON_INSTALL_DIR "$ENV{LIBBSON_INSTALL_DIR}")
if(NOT LIBBSON_INSTALL_DIR)
  set(LIBBSON_INSTALL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libbson")
endif()
get_filename_component(LIBBSON_INSTALL_DIR "${LIBBSON_INSTALL_DIR}" ABSOLUTE)

# Auto-build libbson if the install dir does not contain a lib directory.
if(NOT EXISTS "${LIBBSON_INSTALL_DIR}/lib")
  message(STATUS "libbson not found, building from source...")
  execute_process(
    COMMAND bash ${CMAKE_CURRENT_SOURCE_DIR}/build-libbson.sh
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE _build_result
  )
  if(NOT _build_result EQUAL 0)
    message(FATAL_ERROR "Failed to build libbson via build-libbson.sh")
  endif()
endif()

# Find headers: libbson 2.x installs to include/bson-X.Y.Z/bson/
file(GLOB _bson_include_dirs "${LIBBSON_INSTALL_DIR}/include/bson-*/bson")
if(NOT _bson_include_dirs)
  message(FATAL_ERROR "Could not find bson headers under ${LIBBSON_INSTALL_DIR}/include")
endif()
list(GET _bson_include_dirs 0 LIBBSON_INCLUDE_DIR)

# Find static library
if(WIN32)
  file(GLOB _bson_libs
    "${LIBBSON_INSTALL_DIR}/lib/bson2-static.lib"
    "${LIBBSON_INSTALL_DIR}/lib/bson2.lib"
    "${LIBBSON_INSTALL_DIR}/lib/*/bson2-static.lib"
    "${LIBBSON_INSTALL_DIR}/lib/*/bson2.lib"
  )
else()
  file(GLOB _bson_libs
    "${LIBBSON_INSTALL_DIR}/lib/libbson2.a"
    "${LIBBSON_INSTALL_DIR}/lib*/libbson2.a"
  )
endif()
if(NOT _bson_libs)
  message(FATAL_ERROR "Could not find libbson2.a static library under ${LIBBSON_INSTALL_DIR}/lib")
endif()
list(GET _bson_libs 0 LIBBSON_STATIC_LIB)

# --- Build the extension module ---
Python_add_library(bsonjs MODULE WITH_SOABI "${CMAKE_CURRENT_SOURCE_DIR}/bsonjs/bsonjs.c")

target_include_directories(bsonjs PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}/bsonjs"
  "${LIBBSON_INCLUDE_DIR}"
)

target_compile_definitions(bsonjs PRIVATE
  Py_LIMITED_API=0x03090000
  BSONJS_VERSION="${_package_version}"
  BSON_STATIC
)

if(WIN32)
  target_link_libraries(bsonjs PRIVATE ${LIBBSON_STATIC_LIB} ws2_32)
elseif(APPLE)
  target_link_libraries(bsonjs PRIVATE ${LIBBSON_STATIC_LIB})
else()
  target_link_libraries(bsonjs PRIVATE ${LIBBSON_STATIC_LIB} rt)
endif()

install(TARGETS bsonjs DESTINATION .)
