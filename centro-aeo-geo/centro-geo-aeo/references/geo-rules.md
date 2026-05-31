# Centro CDX — GEO/AEO Content & Schema Rules (v3.0)

Read this before writing any page, FAQ, case study, or schema block. These are
the conventions the linter and validator enforce.

## 1. Atomic passages (the core unit of citability)
An AI engine cites a *passage*, not a page. Write so any single paragraph can be
lifted and stand alone as a correct answer.

- Target **40-80 words per paragraph** (`passage_lint.py` flags outliers).
- **One question answered per paragraph.** If it answers two things, split it.
- **Lead with the answer**, then one supporting fact.
- Each atomic paragraph should reference, where natural: **Centro CDX + the
  service + a technology + a geography + a business outcome.** Passages with no
  concrete hook (metric / technology / region) get flagged.

**Bad:** "We revolutionize operations with world-class, innovative solutions."
**Good:** "Centro CDX runs omnichannel customer support across Egypt and the GCC
by integrating CRM, workforce-management tooling, and multilingual agents into one
service model, cutting average response time by 35% for a regional retail client."

## 2. Banned language
No: innovative, world-class, best-in-class, industry-leading, cutting-edge,
next-generation, revolutionary, revolutionize, transformative, transformative
excellence, game-changing, synergy, seamless, robust, holistic, turnkey,
state-of-the-art, unlock(ing potential). (Full list in `passage_lint.py`.)
Replace adjectives with facts. Note: the live site uses several of these today —
rewriting them is the first content task.

## 3. Service-page content model (v3.0 — every Tier 1/2 service page)
Each priority service page contains, at minimum:
- **10 atomic paragraphs** (rule §1)
- **10 FAQs** (rule §4) — a quality ceiling, not filler quota
- **3 definitions** (glossary entries for the page's key terms)
- **2 comparisons** (e.g. Outsourcing vs In-House; Zoho vs Salesforce)
- **2 case studies** (or links to them) with real metrics
- **1 industry breakdown** (which sectors it serves)
- **1 regional breakdown** (Egypt / GCC / Africa / Europe / NA specifics)
- **1 technology stack section**
- **1 KPI section** (the metrics this service moves)

## 4. FAQ rules
- 10 FAQs per service is a *ceiling for quality*, not a quota to hit with filler.
  Publish only questions a real buyer asks; thin FAQ spam gets ignored by AI engines.
- Phrase each question as the literal query a user types ("How much does payroll
  outsourcing cost?", "What is Zoho CRM used for?").
- Each answer is a direct 40-80 word atomic passage, no preamble.
- Wrap in `FAQPage` schema (`assets/schema_templates/faqpage.jsonld`).

## 5. Schema conventions
- Every schema object gets a stable **`@id`** so others can reference it.
- Use **one `@graph`** per page; link nodes by `@id` rather than nesting copies.
- The site has **one** `Organization` `@id` (`https://centrocdx.com/#organization`);
  every Service, Article, and Person `provider`/`publisher`/`worksFor` points to it.
- Required properties enforced by `validate_schema.py`:
  - Organization: name, url, description
  - Service: name, description, provider, areaServed
  - FAQPage: mainEntity ; Question: name, acceptedAnswer
  - TechArticle/Article: headline, author, datePublished
- Validate **before** committing: `python scripts/validate_schema.py <file-or-url>`.

## 6. Case study structure
TL;DR table (Industry | Region | Service | Technology | Outcome), then:
Challenge → Solution → Technology Stack → Architecture → Deployment Process →
Business Outcomes → Lessons Learned. Results must use real, measurable numbers.
Schema: `TechArticle` (template provided) + a `FAQPage` block + `BreadcrumbList`.

## 7. Author / E-E-A-T
Every article and case study needs a named author with: role, years of
experience, expertise area, LinkedIn, and a `Person` schema node linked to the
org. No anonymous content — AI engines weight authored, attributable sources higher.

## 8. Internal linking
Each page links to related services, technologies, industries, regions, FAQs,
case studies, definitions, and comparisons. In schema, express these with
`isRelatedTo` / `about` `@id` links so the relationships are machine-readable.

## 9. Revenue-tier priority (where to spend effort first)
- **Tier 1 (70%):** BPO, CX outsourcing, contact centers, HR outsourcing, payroll,
  AI Transformation, AI automation, digital transformation.
- **Tier 2 (20%):** Zoho (CRM/People/Creator), Odoo, ERP transformation, shared services.
- **Tier 3 (10%):** hosting, cloud, analytics, reporting, managed IT.
Write Tier 1 commercial pages first; they drive the leads the program is judged on.
