#!/usr/bin/env bash
# Usage: ./run.sh [companies.csv] [parallel=3]
# For each company: headless Claude Code run (/tailor) -> check.py -> one repair attempt -> report.
# Skips companies that already have a passing check.json (resume). Needs: claude CLI, pdflatex, python3 + pyyaml.
set -uo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
command -v claude >/dev/null || { echo "claude CLI not found (install: curl -fsSL https://claude.ai/install.sh | bash)"; exit 1; }

CSV="${1:-companies.csv}"
PAR="${2:-3}"
mkdir -p out logs

slugify() { echo "$1" | iconv -f utf8 -t ascii//TRANSLIT | tr -cs 'A-Za-z0-9' '-' | sed 's/^-//;s/-$//'; }

process() {
  local name="$1" slug
  slug="$(slugify "$name")"
  if [[ -f "out/$slug/check.json" ]] && python3 -c "import json,sys;sys.exit(0 if json.load(open('out/$slug/check.json'))['ok'] else 1)"; then
    echo "[skip] $name (already done)"; return
  fi
  mkdir -p "out/$slug"
  # custom command text is inlined so headless mode does not depend on slash-command loading
  local prompt
  prompt="$(python3 scripts/prompt.py "$slug")"
  echo "[run ] $name -> out/$slug"
  claude -p "$prompt" \
    --permission-mode acceptEdits \
    --allowedTools "Read" "Write" "Edit" "WebFetch" "WebSearch" "Bash(python3 scripts/check.py:*)" "Bash(mkdir:*)" "Bash(cp:*)" \
    --max-turns 40 \
    > "logs/$slug.log" 2>&1

  if ! python3 scripts/check.py out "$slug" > "logs/$slug.check" 2>&1; then
    echo "[fix ] $name (check failed, one repair attempt)"
    claude -p "The CV for slug '$slug' failed verification. Fix it following CLAUDE.md, then re-run python3 scripts/check.py out $slug until CHECK OK. Errors:
$(cat "logs/$slug.check")" \
      --permission-mode acceptEdits \
      --allowedTools "Read" "Write" "Edit" "Bash(python3 scripts/check.py:*)" \
      --max-turns 20 >> "logs/$slug.log" 2>&1
    python3 scripts/check.py out "$slug" > "logs/$slug.check" 2>&1
  fi
  if [[ -f "out/$slug/check.json" ]] && python3 -c "import json,sys;sys.exit(0 if json.load(open('out/$slug/check.json'))['ok'] else 1)"; then
    echo "[ ok ] $name"
  else
    echo "[FAIL] $name (see logs/$slug.check)"
  fi
}
export -f process slugify

# read companies (first CSV column = company name), skip header
python3 - "$CSV" <<'PY' | xargs -d '\n' -P "$PAR" -I{} bash -c 'process "$@"' _ {}
import csv, sys
for row in csv.DictReader(open(sys.argv[1], encoding="utf-8")):
    if row.get("company", "").strip():
        print(row["company"].strip())
PY

python3 scripts/report.py "$CSV"
echo "Report: out/report.md"
