# Generated libbson headers (config.h, version.h).
#
# libbson's sources do `#include <bson/config.h>` and `<bson/version.h>`, so
# these must land in <build>/bson/ (the root adds <build> to the include
# path). output cannot contain a path segment, so this lives in a `bson/`
# subdir whose build dir is <build>/bson/.
configure_file(
  input: mcd_src / 'src' / 'libbson' / 'src' / 'bson' / 'config.h.in',
  output: 'config.h',
  configuration: conf,
)
configure_file(
  input: mcd_src / 'src' / 'libbson' / 'src' / 'bson' / 'version.h.in',
  output: 'version.h',
  configuration: version_conf,
)
