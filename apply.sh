#!/usr/bin/env bash
# Tailor the CV + cover letter to a job posting. Fastest ways:
#   ./apply.sh                      paste the job description (or its link), then Ctrl-D
#   ./apply.sh https://...          job link
#   ./apply.sh -c                   use the clipboard (needs xclip or wl-paste)
# Batch / files:
#   ./apply.sh jobs/<slug>.md ...   job files (optional front matter: see jobs/_template.md)
#   ./apply.sh jobs [parallel=2]    every jobs/*.md not starting with _
# Each job: headless Claude Code run (/apply) -> check.py -> one repair attempt -> report.
# Outputs go to out/jobs/<Company>-<Role>/ (CV + cover letter .tex/.pdf, decision.json, check.json).
# Skips jobs that already have a passing check.json (delete it to redo). Needs: claude CLI, pdflatex, python3 + pyyaml.
set -uo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
command -v claude >/dev/null || { echo "claude CLI not found (install: curl -fsSL https://claude.ai/install.sh | bash)"; exit 1; }
mkdir -p jobs out/jobs logs/jobs

# Quick input (paste / link / clipboard) -> jobs/Job-<timestamp>.md; renamed after the run from the company + role.
new_job_file() {
  local f="jobs/Job-$(date +%Y%m%d-%H%M%S)-$RANDOM.md"
  if [[ "$1" =~ ^https?:// && "$1" != *[[:space:]]* ]]; then
    printf -- '---\nurl: %s\n---\n' "$1" > "$f"
  else
    printf '%s\n' "$1" > "$f"
  fi
  echo "$f"
}

PAR=2
FILES=()
if [[ $# -eq 0 ]]; then
  if [[ -t 0 ]]; then
    echo "Paste the job description or its link, then press Enter and Ctrl-D:"
  fi
  text="$(cat)"
  [[ -n "${text//[[:space:]]/}" ]] || { echo "nothing pasted"; exit 1; }
  text="$(echo "$text" | sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  f="$(new_job_file "$text")"; FILES+=("$f")
fi
for a in "$@"; do
  if [[ "$a" == "-c" ]]; then
    if command -v wl-paste >/dev/null; then text="$(wl-paste)"
    elif command -v xclip >/dev/null; then text="$(xclip -o -selection clipboard)"
    else echo "-c needs a clipboard tool: sudo apt install xclip"; exit 1; fi
    [[ -n "${text//[[:space:]]/}" ]] || { echo "clipboard is empty"; exit 1; }
    f="$(new_job_file "$(echo "$text" | sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//')")"; FILES+=("$f")
  elif [[ "$a" =~ ^https?:// ]]; then
    f="$(new_job_file "$a")"; FILES+=("$f")
  elif [[ -d "$a" ]]; then
    for f in "$a"/*.md; do [[ -e "$f" && "$(basename "$f")" != _* ]] && FILES+=("$f"); done
  elif [[ -f "$a" ]]; then
    FILES+=("$a")
  elif [[ "$a" =~ ^[0-9]+$ ]]; then
    PAR="$a"
  else
    echo "not a link, file or folder: $a"; exit 1
  fi
done
[[ ${#FILES[@]} -gt 0 ]] || { echo "no job description found"; exit 1; }

slugify() { echo "$1" | iconv -f utf8 -t ascii//TRANSLIT | tr -cs 'A-Za-z0-9' '-' | sed 's/^-//;s/-$//'; }
passed() { [[ -f "out/jobs/$1/check.json" ]] && python3 -c "import json,sys;sys.exit(0 if json.load(open('out/jobs/$1/check.json'))['ok'] else 1)"; }

# Job-<timestamp> -> <Company>-<first words of the role>, from decision.json (files, job file, decision.job_file).
rename_quick() {
  local old="$1" new
  new="$(python3 - "$old" <<'PY'
import json, re, sys, unicodedata
from pathlib import Path
old = sys.argv[1]
try:
    d = json.loads(Path(f"out/jobs/{old}/decision.json").read_text())
except Exception:
    sys.exit(0)
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")
title = re.sub(r"\(.*?\)|[-|,/].*", "", d.get("job_title", "")).split()[:3]
base = "-".join(p for p in (slug(d.get("company", "")), slug(" ".join(title))) if p)
if not base:
    sys.exit(0)
new, i = base, 2
while Path(f"out/jobs/{new}").exists() or Path(f"jobs/{new}.md").exists():
    new, i = f"{base}-{i}", i + 1
print(new)
PY
)"
  [[ -n "$new" ]] || { echo "$old"; return; }
  mv "out/jobs/$old" "out/jobs/$new"
  [[ -f "jobs/$old.md" ]] && mv "jobs/$old.md" "jobs/$new.md"
  for f in "out/jobs/$new"/*"$old"*; do [[ -e "$f" ]] && mv "$f" "${f//$old/$new}"; done
  sed -i "s#$old#$new#g" "out/jobs/$new/decision.json"
  mv "logs/jobs/$old.log" "logs/jobs/$new.log" 2>/dev/null
  python3 scripts/check.py out/jobs "$new" > "logs/jobs/$new.check" 2>&1
  rm -f "logs/jobs/$old.check"
  echo "$new"
}

process() {
  local file="$1" slug
  slug="$(slugify "$(basename "$file" .md)")"
  # /apply reads jobs/<slug>.md: bring files from elsewhere into jobs/
  [[ "$(realpath "$file")" == "$(realpath -m "jobs/$slug.md")" ]] || cp "$file" "jobs/$slug.md"
  if passed "$slug"; then echo "[skip] $slug (already done)"; return; fi
  mkdir -p "out/jobs/$slug"
  echo "[run ] $slug -> out/jobs/$slug"
  claude -p "$(python3 scripts/prompt.py "$slug" apply)" \
    --permission-mode acceptEdits \
    --allowedTools "Read" "Write" "Edit" "WebFetch" "WebSearch" "Bash(python3 scripts/check.py:*)" "Bash(mkdir:*)" "Bash(cp:*)" "Bash(date:*)" \
    --max-turns 50 \
    > "logs/jobs/$slug.log" 2>&1

  if ! python3 scripts/check.py out/jobs "$slug" > "logs/jobs/$slug.check" 2>&1; then
    echo "[fix ] $slug (check failed, one repair attempt)"
    claude -p "The CV/cover letter for job slug '$slug' (out/jobs/$slug/, job description jobs/$slug.md) failed verification. Fix it following CLAUDE.md and .claude/commands/apply.md, then re-run python3 scripts/check.py out/jobs $slug until CHECK OK. Errors:
$(cat "logs/jobs/$slug.check")" \
      --permission-mode acceptEdits \
      --allowedTools "Read" "Write" "Edit" "Bash(python3 scripts/check.py:*)" \
      --max-turns 25 >> "logs/jobs/$slug.log" 2>&1
    python3 scripts/check.py out/jobs "$slug" > "logs/jobs/$slug.check" 2>&1
  fi
  [[ "$slug" == Job-* ]] && slug="$(rename_quick "$slug")"
  if passed "$slug"; then echo "[ ok ] $slug -> out/jobs/$slug/"; else echo "[FAIL] $slug (see logs/jobs/$slug.check)"; fi
}
export -f process slugify passed rename_quick

printf '%s\n' "${FILES[@]}" | xargs -d '\n' -P "$PAR" -I{} bash -c 'process "$@"' _ {}

python3 scripts/report.py --jobs
echo "Report: out/jobs/report.md"
