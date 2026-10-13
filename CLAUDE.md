# CV pipeline: PFE applications for Hsan Ellouze

You tailor ONE company (or ONE job posting) at a time. Two modes:
- **Spontaneous** (`/tailor <slug>`, `run.sh`): inputs from `companies.csv` (company, website, city, contact); CV + mail.
- **Job description** (`/apply <slug>`, `apply.sh`): input `jobs/<slug>.md`; CV + cover letter tailored to that posting (see the end of this file).
Target: end-of-studies internship (PFE), February 2027, 4-6 months, Europe. Language: English.

## Hard rules (scripts/check.py enforces most of them and fails the run otherwise)
1. **Never invent.** Employers, dates, tools, metrics, results: only what is in `facts.yaml` and the templates. If a number is not already there, do not write it.
2. **Never add a technology that is not in `facts.yaml > technologies`.** If the company's key tool is not listed, highlight the nearest real equivalent (Pinecone/Qdrant for another vector DB, Prometheus/Loki for another observability stack, Docker/GitHub Actions for another CI) and put the gap in `flags`.
3. **Edit only inside `% >>> EDIT-ZONE name` ... `% <<< EDIT-ZONE name` blocks.** Keep the marker lines. Preamble, name, contact line, Education are locked.
4. **Exactly one page.** Cut the least relevant bullets/projects/activities; never shrink fonts or margins.
5. Applicare is **Canada**. Portfolio is **hsanellouze.site**.
6. Calm, sober tone. No buzzword stuffing: a keyword goes in only where a real bullet supports it (ATS-friendly vocabulary of the company's domain, in the same words the company uses).

## Choosing the variant (templates/general.tex, ai.tex, sre.tex)
Score the company from its website, careers page and engineering blog:
- `ai`: LLM/RAG/ML platform, vector search, document AI, data/AI products, AI-first startups.
- `sre`: infrastructure, cloud/platform, observability, Kubernetes, DevOps tooling, reliability, security-ops, hosting.
- `general`: product companies, SaaS, fintech, e-commerce, consulting/ESN, anything backend/fullstack-centric, or when the signal is mixed.
If two variants are close, prefer the one matching the *team Hsan would join* (what the careers page says), then `general`.
Write the reasoning in `decision.json` (2-3 sentences, cite what you saw on the site).

## What tailoring may change (inside zones only)
- `title`: the muted subtitle line, adapted to the company's domain (keep the `|` style and one line).
- `seeking`: may add the city, e.g. `Open to relocation (Berlin)`. Keep one line.
- `summary`: 2-3 sentences, lead with the strengths matching the company, using its vocabulary.
- `experience`, `projects`: reorder bullets, rewrite wording to surface company-relevant keywords (bold with `\textbf{}` sparingly: 4-6 per CV at most), drop the least relevant bullets or whole project to fit one page. Keep each fact true.
- `skills`: reorder lines/items so the relevant group comes first. Do not add items.
- `activities`: keep or drop for space.

## Output files per company (slug = company name, letters/digits/hyphens only)
`out/<slug>/CV_Hsan_Ellouze_<slug>.tex` (+ `.pdf` once check.py compiles it)
`out/<slug>/decision.json`:
```json
{"company": "...", "variant": "general|ai|sre", "reason": "...",
 "keywords_added": ["RAG", "observability"], "flags": ["Company uses Weaviate; CV highlights Qdrant/Pinecone instead"]}
```
`out/<slug>/mail_<slug>.html` (Gmail-ready body, see /tailor).

Then run `python3 scripts/check.py out <slug>` and fix every reported error until it prints `CHECK OK`.

## Job-description mode (/apply)
All hard rules above apply to the CV **and** to the cover letter (`templates/cover_letter.tex`, same zone rules, numbers only from the CV/facts/posting, no tool outside `facts.yaml`).
- **Keywords**: put as many of the posting's keywords in the CV as possible, in its exact words, but only those with real evidence (`decision.json > jd_keywords`); check.py fails if a keyword with evidence is missing. In this mode only, a posting keyword with evidence may be added as a skills item (never a tool outside `facts.yaml`).
- The posting drives the tailoring: map each requirement to real evidence (`decision.json > requirements`, `evidence: null` when there is none) and use the posting's own words where a fact supports them.
- The cover letter answers: why this company (researched facts), why this job fits the profile (2-3 requirements -> concrete evidence), motivation (what Hsan wants to learn there, what he brings), availability (PFE from February 2027, 4-6 months, relocation to the city).
- Output in `out/jobs/<slug>/`: `CV_Hsan_Ellouze_<slug>.tex/.pdf`, `Cover_Letter_Hsan_Ellouze_<slug>.tex/.pdf`, `decision.json` (with `"mode": "job"`, `job_title`, `job_file`, `requirements`).
- Check with `python3 scripts/check.py out/jobs <slug>` until `CHECK OK`; every gap the checker lists must be in `flags`.
