---
description: Tailor Hsan's CV + spontaneous mail for one company (usage: /tailor <slug>)
---
Process the company with slug `$ARGUMENTS` from `companies.csv` (columns: company, website, city, contact).
Follow CLAUDE.md strictly. Steps:

1. **Research** (WebFetch the website and its careers/engineering pages; WebSearch if needed). Collect: what the company builds, its domain, its stack, 2-3 concrete verifiable facts. Do not guess anything you did not see.
2. **Choose the variant** (general / ai / sre) with the rubric in CLAUDE.md.
3. **Create the CV**: copy `templates/<variant>.tex` to `out/<slug>/CV_Hsan_Ellouze_<slug>.tex` and edit only the EDIT-ZONE blocks. Write `out/<slug>/decision.json`.
4. **Check**: `python3 scripts/check.py out <slug>`. Fix every error and re-run until `CHECK OK`. Max 4 attempts; if still failing, stop and say why.
5. **Write the mail** `out/<slug>/mail_<slug>.html` (only after CHECK OK):
   - Subject on its own first line: `Spontaneous Application – End-of-Study Internship`.
   - Body in `font-family: Arial, Helvetica, sans-serif; font-size: 14px`, one `<p>` per paragraph, `<b>` on 5-8 keywords max (never whole sentences), portfolio as a real link to https://hsanellouze.site/. No emojis, no lists, no colors.
   - Greeting: `Hi FIRSTNAME,` using the contact column (if empty: `Hello,`). Never guess gender or role.
   - Paragraph 1: genuine interest in what the company really builds (1-2 researched facts), linked to Hsan's closest real project. Say he wanted to reach out directly rather than wait for a matching opening.
   - Paragraph 2: `I'm Hsan, a final-year Software Engineering student at INSAT (Tunisia), seeking an end-of-studies internship (PFE) starting in February 2027 at <Company>.` + 1-2 production systems from the CV most relevant to them + wants a team where he keeps learning while contributing real work.
   - Paragraph 3: open to relocating (name the city if known), available from February 2027, CV attached, portfolio link.
   - Close: `Thanks for your time, and I'd love the chance to talk soon.` / `Best regards,` / `Hsan Ellouze`.
   - Do not claim Hsan used the company's product unless the sheet/notes say so.
6. Final reply: one line with variant + why, the flags, nothing else.
