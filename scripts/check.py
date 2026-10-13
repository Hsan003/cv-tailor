#!/usr/bin/env python3
"""Verify a tailored CV (and, in job mode, its cover letter). Usage: check.py <out_dir> <slug>

Reads  <out_dir>/<slug>/CV_Hsan_Ellouze_<slug>.tex and <out_dir>/<slug>/decision.json
Writes <out_dir>/<slug>/check.json and exits 0 (ok) / 1 (violations).

Checks on the CV (all must pass):
  1. every EDIT-ZONE marker present, once, in order
  2. everything OUTSIDE the zones is byte-identical to the chosen template
  3. no forbidden string (old portfolio domain, Applicare/Tunis)
  4. no technology from forbidden_lexicon in the output
  5. every number in the zones already exists in the template (no invented metrics)
  6. pdflatex compiles and the PDF is exactly 1 page
  7. decision.json is well-formed and its keywords_added all appear in the CV

Job mode (decision.json has "mode": "job", written by /apply) adds:
  8. Cover_Letter_Hsan_Ellouze_<slug>.tex passes 1-4 and 6 against templates/cover_letter.tex,
     numbers only from the CV template, facts.yaml or the job description, no @@placeholder@@ left,
     names the company and the February 2027 start
  9. job-description coverage: every tool the posting names that is in facts.yaml appears in the CV;
     warning for tools it names that Hsan has not used and no flag mentions
 10. ATS keywords: every decision.jd_keywords entry with evidence appears in the CV (plural tolerated,
     LaTeX stripped); new items in the skills zone must be jd_keywords with evidence
"""
import json, os, re, subprocess, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = {"general", "ai", "sre"}
ZONE_RE = re.compile(
    r"^% >>> EDIT-ZONE (?P<name>\w+)\n(?P<body>.*?)^% <<< EDIT-ZONE (?P=name)\n",
    re.S | re.M,
)
NUM_RE = re.compile(r"\d[\d,.]*")
CLICHES = (
    "I am writing to express", "passionate", "dynamic team", "hard-working", "hardworking",
    "team player", "fast-paced", "synergy", "go-getter", "outside the box", "perfect fit",
    "dream job", "perfect candidate", "ideal candidate",
)


def zones(text):
    return [(m.group("name"), m.group("body")) for m in ZONE_RE.finditer(text)]


def locked(text):
    """Template with every zone body replaced by a placeholder."""
    return ZONE_RE.sub(lambda m: f"@@ZONE:{m.group('name')}@@\n", text)


def numbers(text):
    return {n.rstrip(".,") for n in NUM_RE.findall(text)}


def term_present(term, text):
    pat = r"(?<![\w#+.])" + re.escape(term) + r"(?![\w#+])"
    return re.search(pat, text, re.I) is not None


def check_tex(label, out, tpl, facts, known, skip_number_zones=()):
    """Rules 1-5 for one LaTeX file. Returns (errors, warnings, zone_text)."""
    errors, warnings = [], []
    tz, oz = zones(tpl), zones(out)
    if [n for n, _ in tz] != [n for n, _ in oz]:
        errors.append(f"{label}: EDIT-ZONE markers differ from template: expected {[n for n,_ in tz]}, got {[n for n,_ in oz]}")
    elif locked(tpl) != locked(out):
        a, b = locked(tpl).splitlines(), locked(out).splitlines()
        diff = next(((x, y) for x, y in zip(a, b) if x != y), (None, None))
        errors.append(f"{label}: locked (non-zone) content was modified, first difference: template={diff[0]!r} output={diff[1]!r}")

    zone_text = "\n".join(body for _, body in oz)

    for bad in ("hsanellouze.me", "Applicare, Tunis", "Applicare -- Tunis"):
        if bad.lower() in out.lower():
            errors.append(f"{label}: forbidden string present: {bad!r}")
    if "Applicare" in zone_text and "Applicare, Canada" not in zone_text and "Applicare -- Canada" not in zone_text:
        warnings.append(f"{label}: Applicare is mentioned but not as 'Applicare, Canada'")

    allowed = {t.lower() for t in facts["technologies"]}
    for term in facts["forbidden_lexicon"]:
        if term.lower() not in allowed and term_present(term, zone_text):
            errors.append(f"{label}: technology not in facts.yaml appears: {term}")

    counted = "\n".join(body for name, body in oz if name not in skip_number_zones)
    invented = sorted(numbers(counted) - known)
    if invented:
        errors.append(f"{label}: numbers not found in template/facts (invented metrics?): {invented}")

    left = sorted(set(re.findall(r"@@\w+@@", zone_text)))
    if left:
        errors.append(f"{label}: placeholders not replaced: {left}")
    return errors, warnings, zone_text


def compile_one_page(d, tex_path, warnings):
    """pdflatex + page count. Returns (errors, page_count)."""
    errors = []
    compile_name = tex_path.name
    if os.environ.get("CV_FONT_FALLBACK"):
        # Test-only: machines without the roboto package. Page count is APPROXIMATE.
        fb = d / ("_fb_" + tex_path.name)
        fb.write_text(tex_path.read_text().replace(r"\usepackage{roboto}", r"\usepackage{helvet}"))
        compile_name = fb.name
        warnings.append(f"{tex_path.name}: compiled with fallback font (helvet): page count is approximate, re-check with Roboto")
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", compile_name],
        cwd=d, capture_output=True, text=True,
    )
    if compile_name != tex_path.name:
        for ext in (".pdf", ".aux", ".log", ".out", ".tex"):
            src = d / (Path(compile_name).stem + ext)
            if ext == ".pdf" and src.exists():
                src.replace(tex_path.with_suffix(".pdf"))
            else:
                src.unlink(missing_ok=True)
    page_count = None
    if proc.returncode != 0:
        tail = "\n".join(proc.stdout.splitlines()[-15:])
        errors.append(f"{tex_path.name}: pdflatex failed:\n{tail}")
    else:
        info = subprocess.run(["pdfinfo", tex_path.with_suffix(".pdf").name], cwd=d, capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", info)
        page_count = int(m.group(1)) if m else None
        if page_count != 1:
            errors.append(f"{tex_path.name}: PDF has {page_count} pages, must be exactly 1 (cut the least relevant content, do not shrink fonts)")
    for ext in (".aux", ".log", ".out"):
        tex_path.with_suffix(ext).unlink(missing_ok=True)
    return errors, page_count


def read_job(path):
    """Job description text without its YAML front matter."""
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) == 3 else ""
    return text


def latex_plain(latex):
    """CV text as an ATS parser roughly sees it: no comments, commands or braces, single spaces."""
    s = re.sub(r"(?<!\\)%.*", "", latex)
    s = s.replace(r"\&", "&").replace(r"\%", "%").replace(r"\#", "#").replace(r"\_", "_")
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = re.sub(r"[{}\\~$]", " ", s)
    return re.sub(r"\s+", " ", s)


def phrase_present(phrase, plain):
    """Case-insensitive, whitespace-tolerant, singular/plural-tolerant on the last word."""
    words = str(phrase).split()
    if not words:
        return False
    if len(words[-1]) > 3 and words[-1][-1] in "sS":
        words[-1] = words[-1][:-1]
    words = [re.escape(w) for w in words]
    pat = r"(?<![\w#+.])" + r"\s+".join(words) + r"(?:s|es)?(?![\w#+])"
    return re.search(pat, plain, re.I) is not None


def skill_items(skills_zone):
    """Lower-cased items of the skills zone ('Label: a, b (c)' lines separated by \\\\)."""
    items = set()
    for line in skills_zone.split("\\\\"):
        body = latex_plain(line).split(":", 1)[-1]
        for it in re.split(r",|\(|\)", body):
            it = it.strip()
            if it:
                items.add(it.lower())
    return items


def plain_words(latex):
    s = re.sub(r"(?<!\\)%.*", "", latex)
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}\\~$]", " ", s)
    return [w for w in s.split() if re.search(r"\w", w)]


def main():
    out_dir, slug = Path(sys.argv[1]), sys.argv[2]
    d = out_dir / slug
    tex_path = d / f"CV_Hsan_Ellouze_{slug}.tex"
    errors, warnings, extra = [], [], {}

    # decision.json
    try:
        decision = json.loads((d / "decision.json").read_text())
    except Exception as e:
        print(f"FAIL decision.json missing or invalid: {e}")
        sys.exit(1)
    variant = decision.get("variant")
    job_mode = decision.get("mode") == "job"
    if variant not in VARIANTS:
        errors.append(f"decision.variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    required = ["company", "reason", "keywords_added", "flags"]
    if job_mode:
        required += ["job_title", "job_file", "requirements", "jd_keywords"]
    for key in required:
        if key not in decision:
            errors.append(f"decision.json missing key '{key}'")
    job_text = ""
    if job_mode and "job_file" in decision:
        jp = ROOT / decision["job_file"]
        if jp.exists():
            job_text = read_job(jp)
        else:
            errors.append(f"decision.job_file not found: {decision['job_file']}")
    if errors:
        finish(d, errors, warnings, None, extra)

    if not tex_path.exists():
        finish(d, [f"{tex_path.name} not found"], warnings, None, extra)
    out = tex_path.read_text()
    tpl = (ROOT / "templates" / f"{variant}.tex").read_text()
    facts = yaml.safe_load((ROOT / "facts.yaml").read_text())
    known = numbers(tpl) | numbers(yaml.safe_dump(facts))

    e, w, zone_text = check_tex("CV", out, tpl, facts, known)
    errors += e
    warnings += w

    # 7: decision keywords must really be in the CV
    for kw in decision.get("keywords_added", []):
        if not term_present(str(kw), out):
            errors.append(f"decision.keywords_added lists {kw!r} but it is not in the CV")

    letter_path = d / f"Cover_Letter_Hsan_Ellouze_{slug}.tex"
    if job_mode:
        # 8: cover letter
        if not letter_path.exists():
            errors.append(f"{letter_path.name} not found")
        else:
            letter = letter_path.read_text()
            ltpl = (ROOT / "templates" / "cover_letter.tex").read_text()
            e, w, ltext = check_tex("Cover letter", letter, ltpl, facts,
                                    known | numbers(ltpl) | numbers(job_text), skip_number_zones=("date",))
            errors += e
            warnings += w
            if not term_present(decision["company"], ltext):
                errors.append(f"Cover letter: company name {decision['company']!r} does not appear in it")
            if "February 2027" not in ltext:
                errors.append("Cover letter: must state the February 2027 start (availability)")
            n_words = len(plain_words(dict(zones(letter)).get("body", "")))
            extra["letter_words"] = n_words
            if not 250 <= n_words <= 450:
                warnings.append(f"Cover letter: body has {n_words} words (aim for 300-400)")
            for c in CLICHES:
                if c.lower() in ltext.lower():
                    warnings.append(f"Cover letter: cliché {c!r}, say it concretely instead")

        # 9: job-description coverage
        tech = facts["technologies"]
        in_jd = [t for t in tech if term_present(t, job_text)]
        extra["jd_tools_matched"] = [t for t in in_jd if term_present(t, out)]
        missing = [t for t in in_jd if not term_present(t, out)]
        if missing:
            errors.append(f"the posting names {missing} (in facts.yaml) but the CV does not show them: add them where a real bullet or the skills line supports them")
        gaps = [t for t in facts["forbidden_lexicon"]
                if t.lower() not in {x.lower() for x in tech} and term_present(t, job_text)]
        extra["jd_gaps"] = gaps
        flag_text = " ".join(map(str, decision.get("flags", [])))
        unflagged = [g for g in gaps if not term_present(g, flag_text)]
        if unflagged:
            warnings.append(f"the posting asks for {unflagged} (not in facts.yaml) and no flag mentions it")

    # 10: ATS keywords from the posting
    if job_mode:
        plain = latex_plain(out)
        kws = decision.get("jd_keywords", [])
        backed = [str(k.get("keyword", "")) for k in kws if k.get("evidence")]
        unbacked = [str(k.get("keyword", "")) for k in kws if not k.get("evidence")]
        absent = [k for k in backed if not phrase_present(k, plain)]
        if absent:
            errors.append(f"jd_keywords with evidence missing from the CV (use the posting's exact words): {absent}")
        claimed = [k for k in unbacked if phrase_present(k, latex_plain(zone_text))]
        if claimed:
            warnings.append(f"jd_keywords marked without evidence but present in the CV, make sure nothing is overclaimed: {claimed}")
        extra["ats_coverage"] = f"{len(backed) - len(absent)}/{len(kws)} posting keywords in the CV ({len(backed) - len(absent)}/{len(backed)} of those with evidence)"
        extra["ats_missing_no_evidence"] = unbacked
        tz_sk = dict(zones(tpl)).get("skills", "")
        oz_sk = dict(zones(out)).get("skills", "")
        new_items = sorted(skill_items(oz_sk) - skill_items(tz_sk))
        backed_l = {k.lower() for k in backed}
        bad = [i for i in new_items if i not in backed_l]
        if bad:
            errors.append(f"skills: new items {bad} are not jd_keywords with evidence (only reword/reorder, or add a posting term a real bullet supports)")
        elif new_items:
            warnings.append(f"skills: posting terms added {new_items}, double-check each is true")

    # 6: compile + page count
    page_count = None
    if not errors:
        e, page_count = compile_one_page(d, tex_path, warnings)
        errors += e
        if job_mode:
            e, extra["letter_pages"] = compile_one_page(d, letter_path, warnings)
            errors += e

    finish(d, errors, warnings, page_count, extra)


def finish(d, errors, warnings, pages, extra):
    result = {"ok": not errors, "errors": errors, "warnings": warnings, "pages": pages, **extra}
    (d / "check.json").write_text(json.dumps(result, indent=2))
    if errors:
        print("CHECK FAILED")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("CHECK OK", f"({pages} page)")
    for w in warnings:
        print(" warning:", w)
    sys.exit(0)


if __name__ == "__main__":
    main()
