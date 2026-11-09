#!/usr/bin/env bash
# file: admin/deploy/release.sh
# importable: nothing, run from any folder:
#
#   bash admin/deploy/release.sh
#
# Needs the vps host in the SSH settings.
#
# description: Builds the committed admin panel and puts it on the server in one step.

# NOTE: Every release is a complete folder and the live address is a link to one of them, so a
# visitor sees either the old panel or the new one and never a mix of the two.

set -euo pipefail

# The whole body sits in main, so editing this file while it runs can not change what runs.
main() {
  cd "$(dirname "$(readlink -f "$0")")/.."
  [ -z "$(git status --porcelain -- .)" ] || { echo "Commit the panel changes first." >&2; exit 1; }

  # Not local, the cleanup runs after main has returned and still needs this name.
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT

  npm run --silent build > "$work/build.log" 2>&1 || { tail -30 "$work/build.log"; echo "Build failed, nothing was sent." >&2; exit 1; }
  tar -czf "$work/panel.tar.gz" -C dist .

  local id
  id="admin-$(date -u +%Y%m%d-%H%M%S)-$(git rev-parse --short=7 HEAD)"
  scp -q "$work/panel.tar.gz" deploy/security-headers.conf vps:/root/
  ssh vps bash -s -- "$id" < <(install_remote)
  echo "Live with panel $id."
}

# Prints the steps that run on the server.
install_remote() {
  cat <<'REMOTE'
set -euo pipefail
trap 'rm -f /root/panel.tar.gz /root/security-headers.conf' EXIT
root=/var/www/bitpulse-admin-releases
snippet=/etc/nginx/snippets/bitpulse-admin-headers.conf
target="$root/$1"
install -d -m 755 "$root" "$target"
tar -xzf /root/panel.tar.gz -C "$target" --no-same-owner
chmod -R a+rX "$target"
if ! cmp -s /root/security-headers.conf "$snippet"; then
  saved="$(mktemp)"
  cp "$snippet" "$saved"
  install -m 644 /root/security-headers.conf "$snippet"
  if ! nginx -t -q 2> /dev/null; then
    cp "$saved" "$snippet"
    rm -f "$saved"
    echo "The nginx settings were refused, nothing changed." >&2
    exit 1
  fi
  rm -f "$saved"
  systemctl reload nginx
fi
ln -sfn "$target" "$root/.current.next"
mv -T "$root/.current.next" "$root/current"
now="$(basename "$(readlink "$root/current")")"
ls -1dt "$root"/admin-* | tail -n +4 | while read -r old; do
  [ "$(basename "$old")" = "$now" ] || rm -rf "$old"
done
REMOTE
}

main "$@"
