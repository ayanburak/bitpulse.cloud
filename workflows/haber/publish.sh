#!/usr/bin/env bash
# file: workflows/haber/publish.sh
# importable: nothing, run from any folder:
#
#   bash workflows/haber/publish.sh <story folder> [R-number]             publishes and makes the social files
#   bash workflows/haber/publish.sh --dry-run <story folder> [R-number]   checks and social files, the server does not change
#   bash workflows/haber/publish.sh --social <story folder>               makes the social files of a published story again
#
# The story does not enter Git. When the tests or the build fail nothing reaches the server. The
# worker builds the pages and tries them inside the server, and stays on the previous release when
# they do not open.
#
# description: Publishes one story from the device and makes its social files.

# NOTE: A session writing a story may run this file and nothing else that reaches the server. Every
# publish is in the audit log of the API, so nothing has to be written down here.
#
# NOTE: Several writing sessions can work at once. The tests and the build read a private copy with
# the published stories and this one, so an unfinished draft of another session can not stop this
# story. The build writes to one shared folder, so builds wait for each other behind a lock.
#
# XXX: Test and build output goes to a file and the exit code decides. Cutting it with tail would
# hide a failure.

set -euo pipefail

fail() {
  echo "$1" >&2
  exit 1
}

# The whole body sits in main, so editing this file while it runs can not change what runs.
main() {
cd "$(dirname "$(readlink -f "$0")")/../.."
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

mode=publish
case "${1:-}" in
  --dry-run) mode=dry; shift ;;
  --social) mode=social; shift ;;
esac

story="${1:-}"
story="${story%/}"
story="${story##*/}"
[ -n "$story" ] || fail "No story folder given."
link=()
[ -z "${2:-}" ] || link=(--candidate "$2")
dir="site/src/content/stories/$story"
[ -d "$dir" ] || fail "No such story folder: $dir"
for file in en.md tr.md image.jpg social.yaml; do
  [ -f "$dir/$file" ] || fail "Missing file: $dir/$file"
done

# Only this story is copied, the published ones next to it are what its tests compare it with.
copy_stories() {
  local live name
  live="$(bitpulse list | awk '!/^not published/ {print $3}')" || fail "The published stories could not be listed, nothing reached the server."
  mkdir "$work/stories"
  for path in site/src/content/stories/*/; do
    name="$(basename "$path")"
    if [ "$name" = "$story" ] || grep -qxF "${name#[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-}" <<< "$live"; then
      cp -r "$path" "$work/stories/$name"
    fi
  done
}

# The social files go to social-posts/ outside Git. A failure here never affects the published story.
make_social() {
  rm -rf "$work/social"
  mkdir "$work/social"
  cp -r "$dir" "$work/social/$story"
  if BITPULSE_STORIES="$work/social" npm run -s social --prefix site -- "$story" > "$work/social.log" 2>&1; then
    # The post folder carries the publishing time after the day, see postFolder in site/src/social.ts.
    local post
    post="$(basename "$(ls -d "site/social-posts/${story:0:10}"-[0-9][0-9][0-9][0-9]"${story:10}" | head -1)")"
    echo "Social files: $PWD/site/social-posts/$post/"
    find "site/social-posts/$post" -type f -not -path "*/images/*" | sort | sed "s#^site/social-posts/$post/#  #"
  else
    tail -15 "$work/social.log"
    echo "WARNING: the social files could not be made, the story is not affected."
    return 1
  fi
}

# Posts are shared from this folder. After thirty days they are gone, they can always be made again.
prune_social() {
  find site/social-posts -mindepth 1 -maxdepth 1 -type d -name '20[0-9][0-9]-*' -mtime +30 -exec rm -rf {} +
}

social() {
  if make_social; then
    prune_social
    return 0
  fi
  echo "SOCIAL FILES NOT MADE, the story is not affected. To try again: bash workflows/haber/publish.sh --social $story"
  return 1
}

if [ "$mode" = social ]; then
  social
  exit $?
fi

copy_stories
BITPULSE_STORIES="$work/stories" npm test --prefix site > "$work/test.log" 2>&1 || { tail -30 "$work/test.log"; fail "Tests failed, nothing reached the server."; }
BITPULSE_STORIES="$work/stories" flock "${XDG_RUNTIME_DIR:-/tmp}/bitpulse-build.lock" npm run -s build --prefix site > "$work/build.log" 2>&1 || { tail -30 "$work/build.log"; fail "Build failed, nothing reached the server."; }

if [ "$mode" = dry ]; then
  make_social || true
  echo "Trial: every check passed, the server did not change."
  exit 0
fi

# When the text and the image on the server equal the local copy only the social text changed, and
# the site is not built again.
handle="${story#[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-}"
if bitpulse pull "$work/server" "$handle" > /dev/null 2>&1 && [ -d "$work/server/$story" ] &&
  cmp -s "$work/server/$story/en.md" "$dir/en.md" &&
  cmp -s "$work/server/$story/tr.md" "$dir/tr.md" &&
  cmp -s "$work/server/$story/image.jpg" "$dir/image.jpg"; then
  cmp -s "$work/server/$story/social.yaml" "$dir/social.yaml" && fail "Nothing to publish: $story"
  bitpulse draft "$PWD/$dir" "${link[@]}"
  echo "Only the social post changed, the site was not built again."
  social || true
  return 0
fi

bitpulse publish "$PWD/$dir" "${link[@]}" | tee "$work/publish.log"

# The server decides the date, so the final name of the folder is read from here.
final="$(sed -n 's/^folder: //p' "$work/publish.log")"
story="${final##*/}"
dir="site/src/content/stories/$story"

field() {
  sed -n "s/^$1: *//p" "$2" | head -1 | sed "s/^['\"]\(.*\)['\"]$/\1/"
}
slug_en="$(field slug "$dir/en.md")"
slug_tr="$(field slug "$dir/tr.md")"
for path in "/en/stories/$slug_en/" "/tr/stories/$slug_tr/"; do
  curl -fsS --retry 3 --retry-delay 2 -o /dev/null "https://bitpulse.cloud$path" || echo "WARNING: the page did not open from outside, it did open inside the server: $path"
done

social || true
echo "English: https://bitpulse.cloud/en/stories/$slug_en/"
echo "Turkish: https://bitpulse.cloud/tr/stories/$slug_tr/"
}

main "$@"
exit $?
