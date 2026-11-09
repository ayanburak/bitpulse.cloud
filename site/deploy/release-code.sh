#!/usr/bin/env bash
# file: site/deploy/release-code.sh
# importable: nothing, run from any folder:
#
#   bash site/deploy/release-code.sh
#
# Needs the vps host in the SSH settings and the bitpulse command.
#
# description: Sends the committed site code to the publishing worker and rebuilds the live site.

# NOTE: Only committed code can leave, so the name of a code release always points to a real commit.
# The policy goes first because a broken nginx setting then stops the run before anything else
# changed. When the theme script changed, its old pages are blocked for the seconds until the
# rebuild ends, and the theme falls back to light for that moment.

set -euo pipefail

# The whole body sits in main, so editing this file while it runs can not change what runs.
main() {
  cd "$(dirname "$(readlink -f "$0")")/.."
  [ -z "$(git status --porcelain -- .)" ] || { echo "Commit the site changes first." >&2; exit 1; }

  # Not local, the cleanup runs after main has returned and still needs this name.
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT

  BITPULSE_STORIES=tests/fixtures/stories npm test --silent > "$work/test.log" 2>&1 ||
    { tail -30 "$work/test.log"; echo "Tests failed, nothing was sent." >&2; exit 1; }
  bash scripts/package-render.sh "$work/render.tar.gz"

  local id
  id="render-$(date -u +%Y%m%d-%H%M%S)-$(git rev-parse --short=7 HEAD)"
  scp -q "$work/render.tar.gz" deploy/csp.conf vps:/root/
  old="$(ssh vps bash -s -- "$id" < <(install_remote))"
  echo "Code release: $id, the previous one was ${old##*/}"

  if ! bitpulse rebuild; then
    ssh vps bash -s -- "$old" < <(point_remote)
    echo "The rebuild failed. The code release was undone and the live site did not change." >&2
    exit 1
  fi
  ssh vps bash -s < <(prune_remote)
  echo "Live with code $id."
}

# Prints the steps that run on the server. The old code release is the only line on the output.
install_remote() {
  cat <<'REMOTE'
set -euo pipefail
trap 'rm -f /root/render.tar.gz /root/csp.conf' EXIT
root=/opt/bitpulse/render
snippet=/etc/nginx/snippets/bitpulse-csp.conf
if ! cmp -s /root/csp.conf "$snippet"; then
  saved="$(mktemp)"
  cp "$snippet" "$saved"
  install -m 644 /root/csp.conf "$snippet"
  if ! nginx -t -q 2> /dev/null; then
    cp "$saved" "$snippet"
    rm -f "$saved"
    echo "The nginx settings were refused, nothing changed." >&2
    exit 1
  fi
  rm -f "$saved"
  systemctl reload nginx
fi
target="$root/releases/$1"
install -d -m 755 "$target"
tar -xzf /root/render.tar.gz -C "$target" --no-same-owner
chmod -R a+rX "$target"
(cd "$target" && runuser -u bitpulse-render -- "$root/node/bin/node" -e "import('sharp').catch(() => process.exit(1))")
readlink "$root/current"
ln -sfn "releases/$1" "$root/.current.next"
mv -T "$root/.current.next" "$root/current"
REMOTE
}

# Prints the steps that point the worker at another code release, in one rename.
point_remote() {
  cat <<'REMOTE'
set -euo pipefail
root=/opt/bitpulse/render
ln -sfn "$1" "$root/.current.next"
mv -T "$root/.current.next" "$root/current"
REMOTE
}

# Prints the steps that keep the last three code releases and never the one in use.
prune_remote() {
  cat <<'REMOTE'
set -euo pipefail
root=/opt/bitpulse/render
now="$(basename "$(readlink "$root/current")")"
ls -1dt "$root"/releases/render-* | tail -n +4 | while read -r old; do
  [ "$(basename "$old")" = "$now" ] || rm -rf "$old"
done
REMOTE
}

main "$@"
