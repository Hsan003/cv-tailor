---
description: Tailor Hsan's CV + cover letter to one job description (usage: /apply <slug>, reads jobs/<slug>.md)
---
Apply to the job described in `jobs/$ARGUMENTS.md`: usually the raw pasted job description, or just a front matter with `url:`; optionally a YAML front matter with company, title, city, contact, url.
Follow CLAUDE.md strictly (all hard rules apply to the CV *and* the cover letter). Output folder: `out/jobs/$ARGUMENTS/`. Steps:

1. **Read the posting.** If there is no description (empty body, or the file is only a link), WebFetch the `url`, save the posting's full text to `out/jobs/$ARGUMENTS/job_posting.md` and use that file as `job_file` (if the page is empty or needs a login, stop and say so). Front matter fields win; anything missing (company, title, city, contact) comes from the posting itself, the company's site if needed. Never invent a contact name. Extract: exact job title, team, missions, must-have and nice-to-have skills (in the posting's own words), duration, start date, location, language.
2. **Extract the ATS keywords.** List every term a recruiter's ATS would match on, *in the posting's exact spelling*: tools and languages, concepts and practices ("REST APIs", "microservices", "unit testing", "CI/CD pipelines", "LLM", "observability"), domain words ("fintech", "document processing"), methods and soft skills it names ("Agile", "code reviews", "cross-functional"). Usually 15-35 terms, the repeated or emphasised ones first. For each, the evidence in facts.yaml/the templates that makes it true for Hsan, or `null`. This is `decision.json > jd_keywords`.
3. **Map requirements to facts.** For each must-have / important requirement, find the real evidence in `facts.yaml` and the templates (which experience/project/bullet proves it), or `null` if none. This list goes in `decision.json > requirements` and drives everything below. Never stretch a fact to cover a requirement.
4. **Research the company briefly** (website, about/mission, engineering blog, product pages): 2-3 concrete, verifiable facts about what it builds or how the team works, for the "why this company" part. Do not guess anything you did not see.
5. **Choose the variant** (general / ai / sre) from the *role* in the posting first (missions + must-haves), then the company, with the rubric in CLAUDE.md.
6. **Create the CV**: copy `templates/<variant>.tex` to `out/jobs/$ARGUMENTS/CV_Hsan_Ellouze_$ARGUMENTS.tex` and edit only the EDIT-ZONE blocks, as in CLAUDE.md, but driven by the posting:
   - `title`: may echo the role's domain in the posting's words (e.g. `Software Engineering Student | Backend \& Platform Engineering`). One line.
   - `seeking`: may name the city; keep the February 2027 start.
   - `summary`: lead with the 2-3 strengths that answer the posting's must-haves, in its vocabulary.
   - **Goal: every `jd_keywords` entry with evidence appears in the CV, verbatim** (check.py fails otherwise and reports the coverage). Where the posting's word and the template's word mean the same real thing, use the posting's ("REST APIs" rather than "RESTful API", "LLM" rather than "AI"); "unit tests" replaces "automated testing" only if the fact really is unit tests. Put each keyword where it is proven: in the bullet that is its evidence first, else the summary, else the skills line. Use the most important ones twice (summary + bullet), never more.
   - `experience` / `projects`: put the bullets that are evidence in step 3 first, reword them with the posting's terms (only where the fact supports it), bold 4-6 of the posting's key terms in total, drop what the posting does not care about to stay on one page (keyword-dense bullets win over generic ones).
   - `skills`: reorder so the groups and items the posting names come first; a group label may take the posting's wording (e.g. `Backend \& APIs`). New items only for posting keywords with evidence (a concept or practice a real bullet proves, or a tool already in facts.yaml); never a tool outside facts.yaml.
   - Keywords with `null` evidence never go in the CV, not even as "familiar with" or "basics of": they go in `flags`.
7. **Write the cover letter**: copy `templates/cover_letter.tex` to `out/jobs/$ARGUMENTS/Cover_Letter_Hsan_Ellouze_$ARGUMENTS.tex` and replace every `@@...@@` placeholder, editing only the EDIT-ZONE blocks. English, 300-400 words in the body, calm and specific, every claim traceable to facts.yaml/the CV, numbers only from the CV.
   - `recipient`: contact name if given, else `Hiring Team`; company; city.
   - `date`: today's date, e.g. `12 October 2026`.
   - `subject`: exact job title from the posting (+ reference number if the posting has one).
   - Greeting: `Dear FIRSTNAME LASTNAME,` if a contact is given, else `Dear <Company> Hiring Team,`. Never guess gender.
   - **P1, the role and why this company**: name the position, then why *this* company: 1-2 researched facts (what it builds, its users, its technical approach or mission) and the honest link to Hsan's own work or interests. No flattery, no generic praise.
   - **P2, why this job fits my profile**: take the 2-3 most important requirements from step 3 and, for each, the concrete experience that answers it (role, company, what he built, one CV metric at most per item), using the posting's words. Close with one sentence on how these add up to what the team needs.
   - **P3, motivation**: why he wants this role as his end-of-studies project: what he wants to learn or go deeper in that this team offers (tied to the posting's missions), and what he brings beyond tech (ownership of production systems end-to-end, working with non-technical users at Mazdev, leading a ~40-member team at Junior Enterprise INSAT, only if relevant).
   - **P4, availability**: available for an end-of-studies internship (PFE) starting February 2027 for 4-6 months (if the posting states a duration inside 4-6 months, use it; if it conflicts, keep the truth and flag it), open to relocating to <city>, CV attached, portfolio https://hsanellouze.site as `\href{https://hsanellouze.site}{hsanellouze.site}`, happy to discuss in an interview.
   - Gaps: never claim a skill from a `null` requirement or keyword and never name a tool that is not in `facts.yaml`. The gap goes in `flags`; at most one short, honest clause such as "and I am keen to get up to speed on your stack".
   - Avoid: "I am writing to express", "passionate", "perfect fit", "team player", "fast-paced", repeated "I" sentence openings, restating the whole CV.
8. **Write `out/jobs/$ARGUMENTS/decision.json`**:
   ```json
   {"mode": "job", "company": "...", "job_title": "...", "job_file": "jobs/$ARGUMENTS.md",
    "variant": "general|ai|sre", "reason": "2-3 sentences citing the posting (and site)",
    "keywords_added": ["terms from the posting now in the CV"],
    "jd_keywords": [{"keyword": "REST APIs", "evidence": "Mazdev: React/Next.js + FastAPI API system"},
                    {"keyword": "Kubernetes", "evidence": "KubeMind; skills"},
                    {"keyword": "Terraform", "evidence": null}],
    "requirements": [{"requirement": "Python backend APIs", "evidence": "Mazdev: React/Next.js + FastAPI RESTful API system"},
                     {"requirement": "Terraform", "evidence": null}],
    "flags": ["Posting asks for Terraform (not in facts.yaml); not claimed"]}
   ```
9. **Check**: `python3 scripts/check.py out/jobs $ARGUMENTS`. Fix every error and re-run until `CHECK OK`. Max 4 attempts; if still failing, stop and say why. Read `ats_coverage` and the warnings: every keyword with evidence must be in; add a flag for every gap listed.
10. Final reply: one line with variant + why, the `ats_coverage` line, the requirements with no evidence, the flags, nothing else.
