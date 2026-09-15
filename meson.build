project(
  'bsonjs',
  'c',
  version: '0.8.0',
  default_options: ['c_std=c99', 'warning_level=1'],
)

py = import('python').find_installation(pure: false)
fs = import('fs')
cc = meson.get_compiler('c')
threads = dependency('threads')

# libbson's bundled mlib uses POSIX clock/thread primitives that get selected
# via _POSIX_C_SOURCE; without it the build fails on POSIX hosts. Windows has
# its own code path (guarded on _WIN32), so leave it out there.
if host_machine.system() != 'windows'
  add_project_arguments('-D_POSIX_C_SOURCE=200809L', language: 'c')
endif

# --- libbson from source ------------------------------------------------
# Meson has no FetchContent, so the workflow pre-fetches and extracts the
# mongo-c-driver release tarball and points BSONJS_MCD_SRC at it. We compile
# only libbson (static) — never libmongoc — by listing its sources here.
mcd_src = get_option('mongo-c-driver-dir')
if mcd_src == ''
  # Fallback: the workflow pre-fetches + extracts the release tarball here.
  fallback = meson.project_source_root() / '.mongo-c-driver' / 'mongo-c-driver-2.5.3'
  if fs.is_dir(fallback)
    mcd_src = fallback
  endif
endif
if mcd_src == '' or not fs.is_dir(mcd_src)
  error('mongo-c-driver source dir not found. Set -Dmongo-c-driver-dir or extract the tarball to .mongo-c-driver/mongo-c-driver-2.5.3.')
endif

bson_src_dir = mcd_src / 'src' / 'libbson' / 'src'
common_src_dir = mcd_src / 'src' / 'common' / 'src'

# Generated headers (config.h, version.h) from the CMake templates.
libbson_major = 2
libbson_minor = 5
libbson_patch = 3
conf = configuration_data()
if host_machine.endian() == 'little'
  conf.set('BSON_BYTE_ORDER', 1234)
else
  conf.set('BSON_BYTE_ORDER', 4321)
endif
if host_machine.system() == 'windows'
  conf.set('BSON_OS', 2)
  conf.set('BSON_HAVE_STRINGS_H', 0)
  conf.set('BSON_HAVE_STRNLEN', 0)
  conf.set('BSON_HAVE_CLOCK_GETTIME', 0)
  conf.set('BSON_HAVE_GMTIME_R', 0)
  conf.set('BSON_HAVE_RAND_R', 0)
  conf.set('BSON_HAVE_TIMESPEC', 0)
  conf.set('BSON_HAVE_ALIGNED_ALLOC', 0)
  conf.set('BSON_HAVE_STRLCPY', 0)
else
  conf.set('BSON_OS', 1)
  conf.set('BSON_HAVE_STRINGS_H', 1)
  conf.set('BSON_HAVE_STRNLEN', 1)
  conf.set('BSON_HAVE_CLOCK_GETTIME', 1)
  conf.set('BSON_HAVE_GMTIME_R', 1)
  conf.set('BSON_HAVE_RAND_R', 1)
  conf.set('BSON_HAVE_TIMESPEC', 1)
  # aligned_alloc is C11 and is not declared under -std=c99.
  conf.set('BSON_HAVE_ALIGNED_ALLOC', 0)
  conf.set('BSON_HAVE_STRLCPY', host_machine.system() == 'darwin')
endif
conf.set('BSON_HAVE_STDBOOL_H', 1)
conf.set('BSON_HAVE_SNPRINTF', 1)
version_conf = configuration_data()
version_conf.set('libbson_VERSION_MAJOR', libbson_major)
version_conf.set('libbson_VERSION_MINOR', libbson_minor)
version_conf.set('libbson_VERSION_PATCH', libbson_patch)
version_conf.set('libbson_VERSION_FULL', '2.5.3')
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
# bsonjs.__version__ comes from this macro; keep it in sync with the pyproject
# version (meson.project_version() does not see meson-python's override).
bsonjs_version = run_command(py, '-c',
  'import re,pathlib;print(re.search(r\'version\\s*=\\s*"([^"]+)"\',pathlib.Path("pyproject.toml").read_text()).group(1))',
  check: false).stdout().strip()

py.extension_module(
  'bsonjs',
  'bsonjs/bsonjs.c',
  c_args: ['-DBSON_STATIC', '-DBSONJS_VERSION="@0@"'.format(bsonjs_version)] + inc_flags,
  link_with: libbson,
  link_args: host_machine.system() == 'windows' ? ['ws2_32'] : [],
  install: true,
  limited_api: '3.11',
)
