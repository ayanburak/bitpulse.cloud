#!/usr/bin/env bash
# file: scripts/package-render.sh
# importable: nothing, run from the site folder:
#
#   bash scripts/package-render.sh /path/to/render-package.tar.gz
#
# description: Compiles the site code and packs everything the publishing worker runs.

# NOTE: The compiler and the bundler run here and never on the server. The package holds the
# browser files, the page renderer and only the libraries needed at run time.

set -euo pipefail

# The whole body sits in main, so editing this file while it runs can not change what runs.
main() {
  local output="${1:?usage: package-render.sh output.tar.gz}"
  # Not local, the cleanup runs after main has returned and still needs this name.
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT

  npx tsc --noEmit
  npx vite build --logLevel warn
  npx vite build --ssr src/render.tsx --outDir "$work/ssr" --logLevel warn

  mkdir -p "$work/scripts"
  cp -r dist "$work/template"
  cp scripts/prerender.ts scripts/publish.ts "$work/scripts/"
  cp package.json package-lock.json .node-version "$work/"
  # dist is emptied again so a later local build does not mistake this one for its own output.
  rm -rf dist

  npm ci --omit=dev --ignore-scripts --silent --prefix "$work"
  # sharp and pagefind arrive as ready binaries in their own packages, nothing needs compiling.
  tar -czf "$output" -C "$work" template ssr scripts node_modules package.json .node-version
  echo "Package: $output"
}

main "$@"
