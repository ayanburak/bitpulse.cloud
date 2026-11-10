#!/usr/bin/env bash
# file: insights/deploy/release-code.sh
# importable: nothing, run from any folder:
#
#   bash insights/deploy/release-code.sh
#
# Needs the vps host in the SSH settings and uv. The first release needs the user, the folders and
# the settings file that the setup steps make.
#
# description: Sends the committed insights code and its systemd files to the server.

# NOTE: Each release is a complete virtual environment, and /opt/bitpulse/insights/.venv is a link to
# the one in use. The timer starts the service through that one path, so a release changes nothing
# for a round that is already running. The service keeps no data, so there is nothing to copy.

set -euo pipefail

# The whole body sits in main, so editing this file while it runs can not change what runs.
main() {
  cd "$(dirname "$(readlink -f "$0")")/.."
  [ -z "$(git status --porcelain -- .)" ] || { echo "Commit the insights changes first." >&2; exit 1; }

  # Not local, the cleanup runs after main has returned and still needs this name.
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT

  uv run --isolated --locked --python 3.10 pytest > "$work/test.log" 2>&1 ||
    { tail -30 "$work/test.log"; echo "Tests failed, nothing was sent." >&2; exit 1; }
  uv build --quiet --wheel --out-dir "$work/release"
  cp deploy/bitpulse-insights.service deploy/bitpulse-insights.timer "$work/release/"

  local id
  id="insights-$(date -u +%Y%m%d-%H%M%S)-$(git rev-parse --short=7 HEAD)"
  ssh vps 'rm -rf /root/insights-release'
  scp -q -r "$work/release" vps:/root/insights-release
  old="$(ssh vps bash -s -- "$id" < <(install_remote))"
  echo "Live with insights code $id, the previous one was ${old##*/}"
}

# Prints the steps that run on the server. The old release is the only line on the output.
install_remote() {
  cat <<'REMOTE'
set -euo pipefail
trap 'rm -rf /root/insights-release' EXIT
id="$1"
src=/root/insights-release
root=/opt/bitpulse/insights
target="$root/releases/$id"

install -d -m 755 "$root/releases"
python3 -m venv --copies "$target"
"$target/bin/pip" install --quiet --disable-pip-version-check --no-deps "$src"/bitpulse_insights-*.whl
chmod -R a+rX "$target"

old="$(readlink "$root/.venv" 2>/dev/null || echo none)"
ln -sfn "releases/$id" "$root/.venv.next"
mv -T "$root/.venv.next" "$root/.venv"

install -m 644 "$src/bitpulse-insights.service" "$src/bitpulse-insights.timer" /etc/systemd/system/
systemctl daemon-reload

if ! runuser -u bitpulse-insights -- "$root/.venv/bin/insights" --help > /dev/null; then
  if [ "$old" != none ]; then
    ln -sfn "$old" "$root/.venv.next"
    mv -T "$root/.venv.next" "$root/.venv"
  fi
  echo "The new insights code does not start. The previous code is back." >&2
  exit 1
fi

# Keeps the last three releases, never the one in use.
ls -1dt "$root"/releases/insights-* | tail -n +4 | while read -r item; do
  [ "$(basename "$item")" = "$id" ] || [ "$item" = "$root/$old" ] || rm -rf "$item"
done
echo "$old"
REMOTE
}

main "$@"
