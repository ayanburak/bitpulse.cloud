#!/usr/bin/env bash
# file: radar/deploy/release-code.sh
# importable: nothing, run from any folder:
#
#   bash radar/deploy/release-code.sh
#
# Needs the vps host in the SSH settings and uv.
#
# description: Sends the committed radar code to the server and restarts the radar on it.

# NOTE: Each release is a complete virtual environment, and /opt/bitpulse/radar/.venv is a link to the
# one in use. The services and the timers keep using that one path. New columns are added by the
# radar when it opens its database and older code ignores them, so undoing a release never needs the
# database copy. The copy is there for a mistake in the new code.

set -euo pipefail

# The whole body sits in main, so editing this file while it runs can not change what runs.
main() {
  cd "$(dirname "$(readlink -f "$0")")/.."
  [ -z "$(git status --porcelain -- .)" ] || { echo "Commit the radar changes first." >&2; exit 1; }

  # Not local, the cleanup runs after main has returned and still needs this name.
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT

  uv run --isolated --locked --python 3.10 pytest > "$work/test.log" 2>&1 ||
    { tail -30 "$work/test.log"; echo "Tests failed, nothing was sent." >&2; exit 1; }
  uv build --quiet --wheel --out-dir "$work/release"
  uv export --quiet --locked --no-dev --no-emit-project --format requirements-txt -o "$work/release/requirements.txt"
  cp sources.toml "$work/release/"

  local id
  id="radar-$(date -u +%Y%m%d-%H%M%S)-$(git rev-parse --short=7 HEAD)"
  ssh vps 'rm -rf /root/radar-release'
  scp -q -r "$work/release" vps:/root/radar-release
  old="$(ssh vps bash -s -- "$id" < <(install_remote))"
  echo "Live with radar code $id, the previous one was ${old##*/}"
}

# Prints the steps that run on the server. The old release is the only line on the output.
install_remote() {
  cat <<'REMOTE'
set -euo pipefail
trap 'rm -rf /root/radar-release' EXIT
id="$1"
src=/root/radar-release
root=/opt/bitpulse/radar
data=/var/lib/bitpulse/radar
target="$root/releases/$id"

install -d -m 755 "$root/releases"
python3 -m venv --copies "$target"
"$target/bin/pip" install --quiet --disable-pip-version-check --require-hashes -r "$src/requirements.txt"
"$target/bin/pip" install --quiet --disable-pip-version-check --no-deps "$src"/bitpulse_radar-*.whl
chmod -R a+rX "$target"

"$target/bin/python" - "$data/radar.db" "$data/pre-$id.db" <<'PY'
import sqlite3, sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
copy = sqlite3.connect(sys.argv[2])
source.backup(copy)
copy.close()
PY
chown bitpulse-radar:bitpulse-radar "$data/pre-$id.db"
chmod 600 "$data/pre-$id.db"

# The very first release finds a real folder here. It becomes the release to return to.
if [ ! -L "$root/.venv" ]; then
  mv -T "$root/.venv" "$root/releases/radar-first"
  ln -s "releases/radar-first" "$root/.venv"
fi
old="$(readlink "$root/.venv")"

point() {
  ln -sfn "$1" "$root/.venv.next"
  mv -T "$root/.venv.next" "$root/.venv"
}

saved="$(mktemp)"
cp "$root/sources.toml" "$saved"
install -m 644 "$src/sources.toml" "$root/sources.toml"
point "releases/$id"
systemctl restart bitpulse-radar-poll.service

healthy() {
  sleep 8
  systemctl is-active --quiet bitpulse-radar-poll.service &&
    runuser -u bitpulse-radar -- env RADAR_DB="$data/radar.db" "$root/.venv/bin/radar" --sources "$root/sources.toml" sources > /dev/null
}

if ! healthy; then
  point "$old"
  cp "$saved" "$root/sources.toml"
  rm -f "$saved"
  systemctl restart bitpulse-radar-poll.service
  echo "The new radar did not start. The previous code is back." >&2
  exit 1
fi
rm -f "$saved"

# Keeps the last three releases and two database copies, never the release in use.
ls -1dt "$root"/releases/radar-* | tail -n +4 | while read -r item; do
  [ "$(basename "$item")" = "$id" ] || [ "$item" = "$root/$old" ] || rm -rf "$item"
done
ls -1t "$data"/pre-radar-*.db | tail -n +3 | xargs -r rm -f
echo "$old"
REMOTE
}

main "$@"
