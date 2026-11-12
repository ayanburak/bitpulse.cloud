#!/usr/bin/env bash
# file: api/deploy/release-code.sh
# importable: nothing, run from any folder:
#
#   bash api/deploy/release-code.sh
#
# Needs the vps host in the SSH settings and uv.
#
# description: Sends the committed API code to the server and restarts the API on it.

# NOTE: Each release is a complete virtual environment, and /opt/bitpulse/api/.venv is a link to the
# one in use. The service, the backup and the server commands keep using that one path. Migrations
# only add tables or widen rules, so older code still runs on a migrated database and undoing a
# release never needs the database copy. The copy is there for a mistake in a migration.

set -euo pipefail

# The whole body sits in main, so editing this file while it runs can not change what runs.
main() {
  cd "$(dirname "$(readlink -f "$0")")/.."
  [ -z "$(git status --porcelain -- .)" ] || { echo "Commit the API changes first." >&2; exit 1; }

  # Not local, the cleanup runs after main has returned and still needs this name.
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT

  uv run --isolated --locked --python 3.14 pytest > "$work/test.log" 2>&1 ||
    { tail -30 "$work/test.log"; echo "Tests failed, nothing was sent." >&2; exit 1; }
  uv build --quiet --wheel --out-dir "$work/release"
  uv export --quiet --locked --no-dev --no-emit-project --format requirements-txt -o "$work/release/requirements.txt"
  cp deploy/bitpulse-api.service deploy/notify.py "$work/release/"

  local id
  id="api-$(date -u +%Y%m%d-%H%M%S)-$(git rev-parse --short=7 HEAD)"
  ssh vps 'rm -rf /root/api-release'
  scp -q -r "$work/release" vps:/root/api-release
  old="$(ssh vps bash -s -- "$id" < <(install_remote))"
  echo "Live with API code $id, the previous one was ${old##*/}"
}

# Prints the steps that run on the server. The old release is the only line on the output.
install_remote() {
  cat <<'REMOTE'
set -euo pipefail
trap 'rm -rf /root/api-release' EXIT
id="$1"
src=/root/api-release
root=/opt/bitpulse/api
data=/var/lib/bitpulse/api
target="$root/releases/$id"

install -d -m 755 "$root/releases"
/opt/bitpulse/python/current/bin/python3 -m venv --copies "$target"
"$target/bin/pip" install --quiet --disable-pip-version-check --require-hashes -r "$src/requirements.txt"
"$target/bin/pip" install --quiet --disable-pip-version-check --no-deps "$src"/bitpulse_api-*.whl
chmod -R a+rX "$target"

install -m 644 "$src/notify.py" /opt/bitpulse/notify/notify.py

# The migration runs first on a throwaway copy, so a bad one stops here with the API untouched.
check="$(mktemp -d)"
trap 'rm -rf /root/api-release "$check"' EXIT
"$target/bin/python" - "$data/bitpulse.db" "$check/copy.db" <<'PY'
import sqlite3, sys
from pathlib import Path
from bitpulse_api.db import connect
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
copy = sqlite3.connect(sys.argv[2])
source.backup(copy)
copy.close()
connect(Path(sys.argv[2])).close()
PY
"$target/bin/python" - "$data/bitpulse.db" "$data/pre-$id.db" <<'PY'
import sqlite3, sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
copy = sqlite3.connect(sys.argv[2])
source.backup(copy)
copy.close()
PY
chown bitpulse-api:bitpulse-api "$data/pre-$id.db"
chmod 600 "$data/pre-$id.db"

# The very first release finds a real folder here. It becomes the release to return to.
if [ ! -L "$root/.venv" ]; then
  mv -T "$root/.venv" "$root/releases/api-first"
  ln -s "releases/api-first" "$root/.venv"
fi
old="$(readlink "$root/.venv")"

point() {
  ln -sfn "$1" "$root/.venv.next"
  mv -T "$root/.venv.next" "$root/.venv"
}

healthy() {
  for _ in $(seq 1 30); do
    "$root/.venv/bin/python" -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8010/health', timeout=2)" 2> /dev/null && return 0
    sleep 1
  done
  return 1
}

unit=/etc/systemd/system/bitpulse-api.service
saved="$(mktemp)"
cp "$unit" "$saved"
if ! cmp -s "$src/bitpulse-api.service" "$unit"; then
  install -m 644 "$src/bitpulse-api.service" "$unit"
  systemctl daemon-reload
fi

point "releases/$id"
systemctl restart bitpulse-api.service
if ! healthy; then
  point "$old"
  cp "$saved" "$unit"
  rm -f "$saved"
  systemctl daemon-reload
  systemctl restart bitpulse-api.service
  echo "The new API did not answer. The previous code is back." >&2
  exit 1
fi
rm -f "$saved"

# Keeps the last three releases and two database copies, never the release in use.
ls -1dt "$root"/releases/api-* | tail -n +4 | while read -r item; do
  [ "$(basename "$item")" = "$id" ] || [ "$item" = "$root/$old" ] || rm -rf "$item"
done
ls -1t "$data"/pre-api-*.db | tail -n +3 | xargs -r rm -f
echo "$old"
REMOTE
}

main "$@"
