#!/usr/bin/env bash
# Source-derived version-pinned distribution: copy only engine-managed assets.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY=0
REF_ARG=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --*) echo "Unknown option: $arg" >&2; exit 1 ;;
    *) [ -z "$REF_ARG" ] || { echo "Only one ref is accepted" >&2; exit 1; }; REF_ARG="$arg" ;;
  esac
done
[ -f "$ROOT/.engine-source" ] || { echo "Missing .engine-source" >&2; exit 1; }
SOURCE="$(head -1 "$ROOT/.engine-source")"
REF="$REF_ARG"
if [ -z "$REF" ]; then
  [ -f "$ROOT/.engine-version" ] || { echo "Missing .engine-version" >&2; exit 1; }
  REF="$(head -1 "$ROOT/.engine-version")"
fi
[ -n "$SOURCE" ] && [ -n "$REF" ] || { echo "Source and ref must be set" >&2; exit 1; }
case "$REF" in -*) echo "Invalid ref" >&2; exit 1 ;; esac
CACHE="$(mktemp -d "${TMPDIR:-/tmp}/conference-engine.XXXXXX")"
trap 'rm -rf "$CACHE"' EXIT
git clone --quiet --no-checkout -- "$SOURCE" "$CACHE/repo"
RESOLVED="$(git -C "$CACHE/repo" rev-parse --verify "$REF^{commit}")"
mkdir "$CACHE/export"
git -C "$CACHE/repo" archive "$RESOLVED" | tar -xf - -C "$CACHE/export"
MANAGED=(.claude/skills .claude/commands .claude/workflows .claude/scripts
  .claude/settings.json .agent-skills methodology
  scripts/run-workflow.mjs scripts/workflow-runtime.mjs
  templates/speaker-profile-template.md templates/sponsor-profile-template.md
  templates/prospectus-document.md docs examples)
for path in "${MANAGED[@]}"; do
  [ -e "$CACHE/export/$path" ] || { echo "Missing engine asset: $path" >&2; exit 1; }
  # A local symlink could redirect copying/removal outside the instance.
  parent="$ROOT/$path"
  while [ "$parent" != "$ROOT" ]; do
    [ ! -L "$parent" ] || { echo "Refusing symlink destination: $parent" >&2; exit 1; }
    parent="$(dirname "$parent")"
  done
done
echo "source=$SOURCE ref=$REF commit=$RESOLVED dry-run=$DRY"
for path in "${MANAGED[@]}"; do
  if [ "$DRY" = 1 ]; then
    echo "would-sync $path"
  else
    rm -rf "$ROOT/$path"
    mkdir -p "$(dirname "$ROOT/$path")"
    cp -R "$CACHE/export/$path" "$ROOT/$path"
    echo "synced $path"
  fi
done
if [ "$DRY" = 0 ]; then
  printf '%s\n' "$RESOLVED" > "$ROOT/.engine-version"
fi
