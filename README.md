# cv-pipeline

Batch-generate tailored one-page CVs (+ Gmail-ready mail bodies) for spontaneous PFE applications.

## Setup
```bash
pip install -r requirements.txt     # pyyaml
curl -fsSL https://claude.ai/install.sh | bash   # Claude Code CLI -> ~/.local/bin/claude
# pdflatex + pdfinfo: texlive-latex-extra, poppler-utils (apt)
# Roboto without root (instead of the 1.7 GB texlive-fonts-extra):
curl -fsSLO https://mirrors.ctan.org/install/fonts/roboto.tds.zip
unzip -oq roboto.tds.zip -d "$(kpsewhich -var-value TEXMFHOME)" && updmap-user --enable Map=roboto.map
```

## Use
1. Fill `companies.csv` (`company,website,city,contact`; contact optional).
2. `./run.sh companies.csv 3`   (3 companies in parallel; re-running skips finished ones)
3. Read `out/report.md` (variant chosen, why, keywords added, flags), then check `out/<slug>/`.

Interactive single company: open Claude Code in this folder and run `/tailor <slug>`.

### Applying to a specific job posting (CV + cover letter)
```bash
./apply.sh                    # paste the job description (or its link), Enter, Ctrl-D
./apply.sh https://...        # job link
./apply.sh -c                 # clipboard (sudo apt install xclip)
./apply.sh jobs 3             # every jobs/*.md, 3 in parallel (file format: jobs/_template.md, front matter optional)
```
Company, role and city are read from the posting; the output folder is named after them,
e.g. `out/jobs/Acme-Backend-Engineer-Intern/` with `CV_Hsan_Ellouze_<slug>.pdf` and `Cover_Letter_Hsan_Ellouze_<slug>.pdf`.
Then read `out/jobs/report.md` (ATS coverage, variant, requirements with no evidence, flags).

Interactive: `/apply <slug>` in Claude Code. The cover letter (`templates/cover_letter.tex`) is checked like the CV:
locked header, no invented numbers or tools, exactly 1 page, names the company and the February 2027 start; warnings for
clichés, length outside 250-450 words, tools the posting names that the CV omits, and posting requirements not flagged as gaps.

## How it stays honest
- `templates/{general,ai,sre}.tex` are your three CVs; only `% >>> EDIT-ZONE` blocks may change.
- `facts.yaml` lists the technologies you really used. `scripts/check.py` fails a CV that:
  changes locked content, mentions a tool from the forbidden lexicon, contains a number not already
  in your CV (invented metric), is not exactly 1 page, or uses the old portfolio domain / Applicare in Tunis.
- A failed check triggers one automatic repair attempt; otherwise the company is marked FAILED in the report.

## Notes
- Corrections applied to the imported CVs: Applicare is "Canada", portfolio is hsanellouze.site.
- Add a technology to `facts.yaml > technologies` only when it is true; extend `forbidden_lexicon` freely.
- Sandbox without Roboto: `CV_FONT_FALLBACK=1 python3 scripts/check.py out <slug>` (page count approximate).
- Not included yet: FR templates (the FR .tex files are in your project; same zone markers can be added).
