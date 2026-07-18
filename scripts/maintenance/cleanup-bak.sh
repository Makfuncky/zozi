#!/usr/bin/env bash
# Remove backup files from workspace to avoid git stress and local clutter
# Usage: ./scripts/cleanup-bak.sh

target_dir="${1:-.}"

echo "Cleaning up .bak files under ${target_dir}..."
find "$target_dir" -type f -name "*.bak" -print -delete
find "$target_dir" -type f -name "*.backup" -print -delete

echo "Done."
