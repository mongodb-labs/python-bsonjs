project(
  'bsonjs',
  'c',
  version: '0.8.0.dev0',
  meson_version: '>=1.3',
  default_options: ['c_std=c99', 'warning_level=1'],
)

py = import('python').find_installation(pure: false)
fs = import('fs')
cc = meson.get_compiler('c')
threads = dependency('threads')

# libbson's mlib selects its POSIX clock primitives from _POSIX_C_SOURCE or
# _DEFAULT_SOURCE, and error.c uses strerror_l only when _XOPEN_SOURCE >= 700.
# glibc derives both from _GNU_SOURCE; musl derives neither, so define them
# explicitly. Windows has its own code path (guarded on _WIN32), so leave it out
# entirely there. The feature probes below compile with the same macros so they
# test the environment libbson is actually compiled in.
if host_machine.system() == 'darwin'
  feature_args = ['-D_POSIX_C_SOURCE=200809L']
elif host_machine.system() != 'windows'
  feature_args = ['-D_GNU_SOURCE', '-D_DEFAULT_SOURCE', '-D_XOPEN_SOURCE=700']
else
  feature_args = []
endif
if feature_args.length() > 0
  add_project_arguments(feature_args, language: 'c')
endif

# --- libbson from source ------------------------------------------------
# Meson has no FetchContent, so the mongo-c-driver release tarball is
# extracted to .mongo-c-driver/: the CI action pre-fetches it, and meson
# fetches it here when absent. We compile only libbson (static), never
# libmongoc, by listing its sources explicitly.
#
# The pinned release, read by scripts/fetch_mongo_c_driver.py. The SHA256 of
# that tarball is updated by scripts/bump_libbson.py alongside the version.
mcd_version = '2.5.3'
mcd_sha256 = '5eb6f2297f5fbfcf0bf79942623b84f883e9223f008f24497ae60937802a6315'

mcd_src = get_option('mongo-c-driver-dir')
if mcd_src == ''
  # Fallback: the CI action pre-fetches and extracts the release tarball here.
  fallback = meson.project_source_root() / '.mongo-c-driver' / 'mongo-c-driver-@0@'.format(mcd_version)
  if not fs.is_dir(fallback)
    # Nothing pre-fetched, so fetch the pinned release now. This lets an
    # sdist install build itself without a separate setup step.
    fetch = run_command(
      py,
      meson.project_source_root() / 'scripts' / 'fetch_mongo_c_driver.py',
      check: false,
    )
    if fetch.returncode() != 0
      error('Failed to fetch mongo-c-driver:\n' + fetch.stdout() + fetch.stderr())
    endif
  endif
  if fs.is_dir(fallback)
    mcd_src = fallback
  endif
endif
if mcd_src == '' or not fs.is_dir(mcd_src)
  error('mongo-c-driver source dir not found. Set -Dmongo-c-driver-dir or extract the tarball to .mongo-c-driver/mongo-c-driver-@0@.'.format(mcd_version))
endif

bson_src_dir = mcd_src / 'src' / 'libbson' / 'src'
common_src_dir = mcd_src / 'src' / 'common' / 'src'

# Generated headers (config.h, version.h) from the CMake templates. The
# feature probes mirror upstream's src/libbson/CMakeLists.txt, which runs
# CMake's check_include_file/check_symbol_exists/check_struct_has_member on
# every platform; cc.has_header()/cc.has_function()/cc.has_member() are the
# Meson equivalents.
mcd_ver_comps = mcd_version.split('.')
libbson_major = mcd_ver_comps[0].to_int()
libbson_minor = mcd_ver_comps[1].to_int()
libbson_patch = mcd_ver_comps[2].to_int()
conf = configuration_data()
if host_machine.endian() == 'little'
  conf.set('BSON_BYTE_ORDER', 1234)
else
  conf.set('BSON_BYTE_ORDER', 4321)
endif
conf.set('BSON_OS', host_machine.system() == 'windows' ? 2 : 1)
conf.set('BSON_HAVE_STRINGS_H', cc.has_header('strings.h') ? 1 : 0)
conf.set('BSON_HAVE_STRNLEN', cc.has_function('strnlen', prefix: '#include <string.h>', args: feature_args) ? 1 : 0)
conf.set('BSON_HAVE_CLOCK_GETTIME', cc.has_function('clock_gettime', prefix: '#include <time.h>', args: feature_args) ? 1 : 0)
conf.set('BSON_HAVE_GMTIME_R', cc.has_function('gmtime_r', prefix: '#include <time.h>', args: feature_args) ? 1 : 0)
conf.set('BSON_HAVE_RAND_R', cc.has_function('rand_r', prefix: '#include <stdlib.h>', args: feature_args) ? 1 : 0)
conf.set('BSON_HAVE_TIMESPEC', cc.has_member('struct timespec', 'tv_sec', prefix: '#include <time.h>', args: feature_args) ? 1 : 0)
conf.set('BSON_HAVE_STRLCPY', cc.has_function('strlcpy', prefix: '#include <string.h>', args: feature_args) ? 1 : 0)
conf.set('BSON_HAVE_STDBOOL_H', cc.has_header('stdbool.h') ? 1 : 0)
conf.set('BSON_HAVE_SNPRINTF', cc.has_function('snprintf', prefix: '#include <stdio.h>', args: feature_args) ? 1 : 0)
# aligned_alloc is C11 and is not declared under -std=c99.
conf.set('BSON_HAVE_ALIGNED_ALLOC', 0)
version_conf = configuration_data()
version_conf.set('libbson_VERSION_MAJOR', libbson_major)
version_conf.set('libbson_VERSION_MINOR', libbson_minor)
version_conf.set('libbson_VERSION_PATCH', libbson_patch)
version_conf.set('libbson_VERSION_FULL', mcd_version)
version_conf.set('libbson_VERSION_PRERELEASE', '')
subdir('bson')
# common-config.h is included by the common/ sources; the build dir is on the
# include path (via inc_flags), so this generated header resolves as <common-config.h>.
common_conf = configuration_data()
common_conf.set('MONGOC_ENABLE_DEBUG_ASSERTIONS', 0)
configure_file(input: common_src_dir / 'common-config.h.in',
               output: 'common-config.h', configuration: common_conf)

# --- libbson static library --------------------------------------------
# Meson rejects absolute source-tree paths in include_directories, and the
# libbson tree lives in .mongo-c-driver/ (or an externally supplied dir), so
# pass the include dirs as -I flags in c_args.
bson_incs = [
  bson_src_dir,
  bson_src_dir / 'bson',
  common_src_dir,
  meson.current_build_dir(),
]
inc_flags = []
foreach d : bson_incs
  inc_flags += '-I' + d
endforeach
libbson_src = [
  common_src_dir / 'common-atomic.c',
  common_src_dir / 'common-b64.c',
  common_src_dir / 'common-json.c',
  common_src_dir / 'common-md5.c',
  common_src_dir / 'common-oid.c',
  common_src_dir / 'common-string.c',
  common_src_dir / 'common-thread.c',
  bson_src_dir / 'bson' / 'bson.c',
  bson_src_dir / 'bson' / 'bson-bcon.c',
  bson_src_dir / 'bson' / 'bson-clock.c',
  bson_src_dir / 'bson' / 'bson-context.c',
  bson_src_dir / 'bson' / 'bson-decimal128.c',
  bson_src_dir / 'bson' / 'bson-iso8601.c',
  bson_src_dir / 'bson' / 'bson-iter.c',
  bson_src_dir / 'bson' / 'bson-json.c',
  bson_src_dir / 'bson' / 'bson-keys.c',
  bson_src_dir / 'bson' / 'bson-oid.c',
  bson_src_dir / 'bson' / 'bson-reader.c',
  bson_src_dir / 'bson' / 'bson-string.c',
  bson_src_dir / 'bson' / 'bson-timegm.c',
  bson_src_dir / 'bson' / 'bson-utf8.c',
  bson_src_dir / 'bson' / 'bson-value.c',
  bson_src_dir / 'bson' / 'bson-vector.c',
  bson_src_dir / 'bson' / 'bson-version-functions.c',
  bson_src_dir / 'bson' / 'error.c',
  bson_src_dir / 'bson' / 'memory.c',
  bson_src_dir / 'bson' / 'validate.c',
  bson_src_dir / 'jsonsl' / 'jsonsl.c',
]
libbson = static_library('bson',
  libbson_src,
  c_args: ['-DBSON_COMPILATION', '-DBSON_STATIC', '-DJSONSL_PARSE_NAN'] + inc_flags,
)

# --- Python extension module (Limited API / abi3) ------------------------
# libbson's bson-context.c calls gethostname, which lives in ws2_32.lib on
# Windows; find_library resolves it to the import library (a bare 'ws2_32'
# link arg would be treated as an .obj and fail with LNK1181).
ws2_32 = cc.find_library('ws2_32', required: false)
# bsonjs.__version__ comes from this macro. The project version is also the
# wheel metadata version: pyproject.toml declares the version dynamically and
# meson-python feeds it from here, so meson.build is the single source.
bsonjs_version = meson.project_version()

py.extension_module(
  'bsonjs',
  'bsonjs/bsonjs.c',
  c_args: ['-DBSON_STATIC', '-DBSONJS_VERSION="@0@"'.format(bsonjs_version)] + inc_flags,
  link_with: libbson,
  dependencies: ws2_32.found() ? [ws2_32] : [],
  install: true,
  limited_api: '3.11',
)
