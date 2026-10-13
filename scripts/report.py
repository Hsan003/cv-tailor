#!/usr/bin/env python3
"""Build out/report.md: one row per company (variant, why, keywords, flags, check status).
With --jobs: build out/jobs/report.md, one row per job description in out/jobs/."""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"


def slugify(name):
    return re.sub(r"-+", "-", re.sub(r"[^A-Za-z0-9]+", "-", name)).strip("-")


def load(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def jobs_report():
    jobs = OUT / "jobs"
    rows = []
    for d in sorted(p for p in jobs.iterdir() if p.is_dir()) if jobs.exists() else []:
        dec, chk = load(d / "decision.json") or {}, load(d / "check.json") or {}
        status = "OK" if chk.get("ok") else ("FAILED" if chk else "not run")
        no_evidence = [r.get("requirement", "") for r in dec.get("requirements", []) if not r.get("evidence")]
        no_evidence += [k.get("keyword", "") for k in dec.get("jd_keywords", []) if not k.get("evidence")]
        flags = list(dec.get("flags", [])) + list(chk.get("warnings", [])) + list(chk.get("errors", []))
        rows.append((d.name, dec, chk, status, no_evidence, flags))
    lines = [
        "# Job applications",
        "",
        f"{sum(1 for r in rows if r[3]=='OK')}/{len(rows)} passed all checks. Read each cover letter and the flags before sending.",
        "",
        "| Job | Status | Role | ATS coverage | Variant | Why | Keywords added | Not evidenced | Flags |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for slug, dec, chk, status, no_ev, flags in rows:
        role = f"{dec.get('job_title', '')} @ {dec.get('company', '')}" if dec else ""
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            cell(slug), status, cell(role), cell(chk.get("ats_coverage", "")), dec.get("variant", ""), cell(dec.get("reason", "")),
            cell(", ".join(dec.get("keywords_added", []))), cell(", ".join(dict.fromkeys(no_ev))), cell("; ".join(flags)),
        ))
    lines += ["", "Files per job: `out/jobs/<slug>/CV_Hsan_Ellouze_<slug>.pdf`, `Cover_Letter_Hsan_Ellouze_<slug>.pdf`, `.tex`, `decision.json`."]
    jobs.mkdir(parents=True, exist_ok=True)
    (jobs / "report.md").write_text("\n".join(lines) + "\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--jobs":
        return jobs_report()
    csv_path = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "companies.csv")
    rows = []
    for r in csv.DictReader(open(csv_path, encoding="utf-8")):
        name = r.get("company", "").strip()
        if not name:
            continue
        slug = slugify(name)
        dec, chk = load(OUT / slug / "decision.json"), load(OUT / slug / "check.json")
        status = "OK" if chk and chk["ok"] else ("FAILED" if chk else "not run")
        rows.append((name, slug, dec or {}, chk or {}, status))

    lines = [
        "# Spontaneous application run",
        "",
        f"{sum(1 for r in rows if r[4]=='OK')}/{len(rows)} passed all checks. Review the flags before sending.",
        "",
        "| Company | Status | Variant | Why | Keywords added | Flags |",
        "|---|---|---|---|---|---|",
    ]
    for name, slug, dec, chk, status in rows:
        flags = list(dec.get("flags", [])) + list(chk.get("warnings", [])) + list(chk.get("errors", []))
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                cell(name), status, dec.get("variant", ""), cell(dec.get("reason", "")),
                cell(", ".join(dec.get("keywords_added", []))), cell("; ".join(flags)),
            )
        )
    lines += ["", "Files per company: `out/<slug>/CV_Hsan_Ellouze_<slug>.pdf`, `.tex`, `mail_<slug>.html`, `decision.json`."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
