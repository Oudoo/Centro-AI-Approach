# Centro CDX GEO/AEO Program — Implementation Playbook

**What this is:** the leaner, buildable version of the Centro CDX operating-system
brief (now at **v3.0**), plus a step-by-step build guide for Claude Code and
Claude Cowork. Follow it top to bottom to ship the program. The full v3.0 brief is
condensed in the skill at `references/operating-system-v3.md`; facts live in
`references/entity-facts.md`.

**Two artifacts ship with this playbook:**
1. `centro-geo-aeo/` — a Claude Code skill (your house GEO/AEO toolkit, with tested scripts).
2. The `claude-seo` open-source plugin (the generic SEO/GEO audit engine) — MIT, by AgriciDaniel.

---

## Live audit findings — centrocdx.com (run May 2026)

I ran the toolkit against the live site. Two results to act on:

- **robots.txt — PASS.** It's a WordPress site; robots.txt only blocks `/wp-admin/`
  and exposes `sitemap.xml`. Every critical AI/search bot is allowed. No fix needed.
- **Finding 0 (priority zero) — the homepage 307-redirects into a JavaScript-gated
  interstitial ("JavaScript is required").** A plain HTTP fetch gets no HTML and no
  JSON-LD. Google (which renders JS) indexes the site, but **AI retrieval bots that
  don't execute JavaScript — including some used by ChatGPT/Perplexity/Claude search
  — may see nothing.** This undercuts the entire GEO effort. **Fix rendering first:**
  serve real HTML + JSON-LD server-side (SSR/prerender) to bots, or remove the JS
  gate for crawler user-agents. Re-test with `validate_schema.py <url>` until it
  returns JSON-LD instead of the redirect error.

Everything below assumes Finding 0 is on the top of the backlog.

---

## Part 0 — The reframe (what changed, and v3.0 vs v2.0)

The original brief was a strong strategy written as one autonomous "agent" with
targets it could never measure on its own. Four fixes make it real:

1. **It's a project, not one prompt.** No single model can "maximize citations
   across ChatGPT, Gemini, Perplexity." Those are external systems. We split the
   work into a *technical engine* (Claude Code) and a *content/research engine*
   (Cowork), each doing what it's actually good at.
2. **The headline metrics need real data.** AI Citation Frequency, Share of
   Voice, Commercial Visibility can only come from actually querying the engines
   and logging results — not from an LLM's self-assessment. That testing lives
   in Cowork (or a paid AI-visibility tool) and feeds back into the scorecard.
3. **The scores are now defined.** The brief said "GEO Score above 90" with no
   formula. `geo_score.py` makes it a reproducible weighted number you run monthly.
4. **Volume targets become quality ceilings.** "10 FAQs/service" is a *limit for
   genuinely useful Q&As*, not a quota to hit with filler — thin mass content is
   exactly what AI engines discard.

**What v3.0 changed (and is now reflected in the toolkit):**
- Revenue prioritization tiers (70/20/10) — see Part 1.5.
- Expanded regions: GCC broken out into Saudi Arabia, UAE, Qatar, Kuwait, Bahrain,
  Oman (in `entity-facts.md` and the Organization schema).
- **AI Transformation Services elevated to its own flagship pillar** — see Part 1.5.
- Query bank target raised from 100 to **250 prompts**.
- New **Commercial Visibility** scorecard category (weight 10); scorecard weights
  re-balanced to v3.0 (AI Citations 20→15, Entity SoV 10→5). `geo_score.py` updated.
- Atomic paragraphs widened to **40-80 words**; fuller per-page content model
  (10 paragraphs, 10 FAQs, 3 definitions, 2 comparisons, 2 case studies, etc.).
  `passage_lint.py` and `geo-rules.md` updated.

---

## Part 1 — Architecture: who does what

| Layer | Tool | Owns |
| --- | --- | --- |
| Generic audit engine | **`claude-seo` plugin** | Broad technical SEO, E-E-A-T scoring, sitemaps, link graph, GEO/AEO audit, reporting |
| House GEO/AEO toolkit | **`centro-geo-aeo` skill** | Centro entity facts, schema templates + validation, crawler-access gate, citability lint, GEO score |
| Content + research | **Claude Cowork** | Writing pages/FAQs/case studies, AI-visibility testing, competitor share-of-voice, monthly report |
| Source of truth | `references/entity-facts.md` | The one set of names/descriptions/metrics everything else must match |

**Rule of thumb:** anything that runs as code or touches the repo → Claude Code.
Anything that is a written deliverable or research → Cowork. The `entity-facts.md`
file is shared by both so the brand stays consistent.

---

## Part 1.5 — Revenue priorities & the AI Transformation pillar

**Spend effort by revenue tier (v3.0):**

| Tier | Effort | Topics to build first |
| --- | --- | --- |
| **Tier 1** | 70% | BPO, CX outsourcing, contact centers, HR outsourcing, payroll, **AI transformation**, AI automation, digital transformation |
| **Tier 2** | 20% | Zoho (CRM/People/Creator), Odoo, ERP transformation, shared services |
| **Tier 3** | 10% | Hosting, cloud, analytics, reporting, managed IT |

Build Tier 1 **commercial** pages first ("best BPO company Egypt", "payroll
outsourcing GCC cost") — those queries drive the leads the program is judged on,
and they feed the new Commercial Visibility score.

### AI Transformation Services — treat it as its own pillar
Per your recommendation (and v3.0), build **AI Transformation Services as a
dedicated, top-level pillar — not a sub-section of Digital Transformation.**

- **Why:** over a 3–5 year horizon, AI Transformation is likely to become a larger
  lead source than traditional BPO and Zoho/Odoo implementation. Establishing the
  entity category early — a clean URL hub, consistent naming, schema, and authored
  content — is a durable, compounding advantage before competitors claim it.
- **How to structure it:** a top-level hub (e.g. `/ai-transformation/`) with child
  pages for each sub-topic to own: AI customer support, AI contact centers, AI
  agents, AI HR helpdesks, AI ticket routing, AI document processing, AI knowledge
  bases, AI process automation, AI analytics/forecasting, and AI governance.
- **Entity treatment:** in `entity-facts.md` it is listed as a flagship pillar; in
  schema, model it as a `Service` with its own `@id`, `provider` → the org, and
  `isRelatedTo` links to CX, contact-center, and HR services so the graph shows AI
  Transformation *connected to* — but distinct from — the rest.
- **Honesty check:** the public site currently lists AI only under technology
  consulting. Confirm the real, deliverable AI offerings with the business before
  publishing pages as live services (don't claim capabilities that aren't real).

---

## Part 2 — Claude Code: detailed how-to (the technical engine)

You'll do this in a terminal with the Claude Code CLI. Each step gives the
**exact command or prompt**.

### Step 0 — Prerequisites
Install if you don't have them:
- **Node.js** (for the Claude Code CLI) and the **Claude Code CLI** itself.
- **Python 3.10+** and **Git**.

Verify:
```bash
claude --version
python3 --version
git --version
```

### Step 1 — Create the project workspace
This is where the website repo (or a content repo) and your GEO assets live.
```bash
mkdir -p ~/centro-geo-program && cd ~/centro-geo-program
git init            # or: git clone <your Centro website repo>
```

### Step 2 — Install the generic engine (`claude-seo`)
Start Claude Code in the folder, then inside Claude Code run the plugin install
(recommended path, Claude Code 1.0.33+):
```text
/plugin marketplace add AgriciDaniel/claude-seo
/plugin install claude-seo@agricidaniel-seo
```
Manual alternative (Unix/macOS/Linux), from a normal shell:
```bash
git clone --depth 1 https://github.com/AgriciDaniel/claude-seo.git
bash claude-seo/install.sh
```
Verify inside Claude Code:
```text
/seo
```
You should get a help prompt. (Installs to `~/.claude/skills/seo/`. Optional
Playwright adds screenshots; skip it to start.)

> Note: install commands are from the repo's INSTALLATION.md as of late May 2026.
> If a command 404s, check the repo README for the current plugin slug.

### Step 3 — Install the house toolkit (`centro-geo-aeo` skill)
Copy the skill folder shipped with this playbook into your Claude Code skills
directory, then install its one dependency:
```bash
cp -r centro-geo-aeo ~/.claude/skills/centro-geo-aeo
pip install --user pyyaml          # only needed for the YAML scorecard
chmod +x ~/.claude/skills/centro-geo-aeo/scripts/*.py
```
Claude Code auto-discovers it. Confirm by asking, inside Claude Code:
```text
What does the centro-geo-aeo skill do, and list its scripts?
```

### Step 4 — Confirm the entity facts (do this once, before any content)
`~/.claude/skills/centro-geo-aeo/references/entity-facts.md` is **already filled
with verified data** (domain, 2009 founding, founder, Winchester VA HQ, delivery
sites, LinkedIn/Crunchbase/Clutch, the four lines of business, contact, regions).
Two things to do: (1) replace the few `REPLACE` items (e.g. logo URL); (2) review
every `CONFIRM` item — the Zoho/Odoo/payroll/AI-Transformation services from the
v3.0 brief are listed as *targets*, not yet asserted as live offerings. Sign them
off with the business before publishing pages that claim them. This file is the
source of truth — consistency here prevents a fractured entity later.

### Step 5 — Crawlability gate (Phase 1)
Confirm AI/search bots can fetch the site *before* anything else:
```bash
python ~/.claude/skills/centro-geo-aeo/scripts/check_ai_crawlers.py https://YOUR-DOMAIN.com
```
If any critical bot (OAI-SearchBot, PerplexityBot, Claude-SearchBot, Googlebot,
Google-Extended, Bingbot) shows **BLOCKED**, fix `robots.txt` (and any Cloudflare
WAF / Bot Fight Mode rule) until this passes. Re-run until it says PASS. *(For
centrocdx.com this already PASSES — see the findings box.)*

Crawl access is necessary but not sufficient: also confirm **rendering**. Fetch a
key page without JavaScript and check real content + JSON-LD are present:
```bash
python ~/.claude/skills/centro-geo-aeo/scripts/validate_schema.py https://YOUR-DOMAIN.com
```
If it returns the redirect/JS-gate error instead of schema (Finding 0), the page
isn't machine-readable to non-JS bots — fix SSR/prerendering before content work.

### Step 6 — Baseline audit with the generic engine
Inside Claude Code:
```text
/seo https://YOUR-DOMAIN.com
```
Let the agents fan out. Save the prioritized action plan it produces — that's
your technical backlog (status codes, canonicals, Core Web Vitals, broad schema
gaps, internal links). Work the high-priority items first.

### Step 7 — Schema, per key page
For each important page (home, each service, each case study), inside Claude Code:
```text
Using the centro-geo-aeo skill: build JSON-LD for /services/cx-outsourcing from the
Service template. Pull names and the description style from entity-facts.md and
geo-rules.md, reuse the Organization @id, then validate it.
```
Claude will fill the template and run the validator. You can also run it directly:
```bash
python ~/.claude/skills/centro-geo-aeo/scripts/validate_schema.py https://YOUR-DOMAIN.com/services/cx-outsourcing
```
Resolve every **ERROR** (missing required field, dangling `@id`) before you ship
the page.

### Step 8 — Make the prose citable
For each page's copy (as a `.md` or pasted text), inside Claude Code:
```text
Rewrite services/cx-outsourcing.md to follow geo-rules.md: 40-60 word atomic
passages, one answer each, concrete hooks, no banned words. Then lint it.
```
Or run the linter directly and fix what it flags:
```bash
python ~/.claude/skills/centro-geo-aeo/scripts/passage_lint.py services/cx-outsourcing.md
```
Push the citability pass rate toward 100% before publishing.

### Step 9 — Score the program (monthly)
Fill `~/.claude/skills/centro-geo-aeo/assets/geo_scorecard.yml` (pull AI-citation and
share-of-voice numbers from the Cowork tracker — Part 3), then:
```bash
python ~/.claude/skills/centro-geo-aeo/scripts/geo_score.py ~/.claude/skills/centro-geo-aeo/assets/geo_scorecard.yml
```
Log the GEO score + sub-scores with the date. Watch the trend month over month.

### Step 10 — (Optional) Put the gates in CI
Add the crawler check, schema validation, and passage lint with `--strict` to a
CI job (GitHub Actions) so a regression — a bad robots.txt edit, broken schema,
or fluffy copy — fails the build before it reaches production.

---

## Part 3 — Claude Cowork: detailed how-to (content + research engine)

Cowork is the desktop knowledge-work app. Here you write deliverables and run the
measurement the scripts can't. Each step gives the **exact prompt** to paste.

### Step 0 — Set up the Cowork project
Create a project named "Centro CDX GEO". Connect the tools you'll use (e.g.
Google Drive for storing reports, and any analytics you have access to). Keep all
GEO work in this one project so context persists.

### Step 1 — Load the shared rules as project knowledge
Upload `entity-facts.md` and `geo-rules.md` (the same files from the skill) into
the project's knowledge. Prompt:
```text
These two files are our source of truth. For everything in this project, use
the exact service names, descriptions, regions, and metrics from entity-facts.md,
and follow the writing rules in geo-rules.md. Confirm you've loaded both.
```

### Step 2 — Build the AI query bank (target: 250 prompts)
```text
Draft 250 buyer-intent prompts a real person would ask an AI assistant where
Centro CDX should ideally appear — across BPO, CX, contact centers, HR
outsourcing, payroll, AI transformation, digital transformation, Zoho/Odoo, and
shared services, for Egypt, the GCC (Saudi/UAE/Qatar/Kuwait/Bahrain/Oman),
Africa, Europe, and North America. Weight the mix toward Tier-1 revenue topics
(~70%). Tag each prompt "commercial" (buyer-ready, e.g. cost/best/provider) or
"informational". Group by topic and save as a table I can reuse weekly.
```

### Step 3 — Run the AI-visibility test (weekly)
This is the real measurement. For each engine you can reach (ChatGPT, Claude,
Gemini, Perplexity, Copilot, Grok), ask the query-bank prompts and log the result.
```text
Take a 25-40 prompt slice from the query bank (include all the "commercial" ones
this rotation). For each, record: was Centro CDX mentioned (yes/no), its position
in the answer, which competitors appeared, the source URL cited, and answer
confidence. Put it in a table and compute: overall mention rate, average position,
mention rate on COMMERCIAL prompts specifically, and top competitors by mentions.
```
Notes:
- Where an engine has no API, run the prompt in that engine's app and paste the
  answer back to Cowork to score — or use a dedicated AI-visibility tool
  (Profound, Peec, Otterly, etc.) and import its export. Either way, **the
  numbers must come from real answers, not estimates.**
- Feed the results into the GEO scorecard (Part 2, Step 9): overall →
  `ai_citation_frequency`, commercial-prompt rate → `commercial_visibility`,
  competitor share → `entity_share_of_voice`.
- Also log the business outcomes v3.0 cares about — consultation requests,
  discovery calls, opportunities — so you can tie GEO movement to pipeline.

### Step 4 — Produce content (Phases 5-6)
Service page:
```text
Write the /services/payroll-management page following geo-rules.md. Include the
six-question citation block, each answer a 40-60 word atomic passage with a real
metric from entity-facts.md. Then list 10 genuine buyer FAQs with direct answers.
```
Case study:
```text
Turn this deployment [paste notes] into a case study using the geo-rules.md
structure: TL;DR table, Challenge, Solution, Architecture, Tech Stack, Deployment,
Results (real numbers only), Lessons Learned. Name an author with role and
expertise.
```
Then run each through the Claude Code linter/validator (Part 2, Steps 7-8) before
publishing — Cowork writes, the scripts verify.

### Step 5 — Competitor share-of-voice report (Phase 3, monthly)
```text
For the topics "best BPO Egypt", "HR outsourcing GCC", "Zoho implementation
partner", and "digital transformation Egypt", summarize how often Centro CDX vs
[Teleperformance, Concentrix, Foundever, TTEC, TaskUs] appear in AI answers, and
list the content gaps where competitors are cited and we are not.
```

### Step 6 — Monthly executive report
```text
Build a one-page monthly GEO report: the GEO score and sub-scores [paste from
geo_score.py], AI mention rate and average position trend, top content gaps, and
the 5 highest-leverage actions for next month. Save it to the project's Drive folder.
```

---

## Part 4 — The operating loop

**Weekly (≈2-3 hrs):**
- Cowork: run the AI-visibility test on a 25-prompt slice (Part 3, Step 3).
- Cowork: write 1-2 content assets (Part 3, Step 4).
- Claude Code: validate schema + lint the new content (Part 2, Steps 7-8).

**Monthly (≈half a day):**
- Claude Code: re-run `/seo` audit + crawler gate (Steps 5-6).
- Cowork: competitor share-of-voice + exec report (Part 3, Steps 5-6).
- Claude Code: update the scorecard, run `geo_score.py`, log the trend (Step 9).

**Definition of done (the product is "finalized" when):**
- **Finding 0 fixed:** bots get real HTML + JSON-LD without executing JS
  (`validate_schema.py <url>` returns schema, not the redirect error).
- Crawler gate PASSES for all critical bots.
- Every key page: schema validates with 0 errors + citability pass rate ≥90%.
- Entity facts are confirmed (no `CONFIRM`/`REPLACE` left) and consistent across the site.
- AI Transformation pillar hub is live with its core child pages.
- The 250-prompt query bank exists; at least one real measurement is logged,
  including a commercial-prompt mention rate.
- A monthly GEO score (v3.0 weighting, incl. Commercial Visibility) is recorded
  with a baseline to trend against.

---

## Part 5 — Honest limitations (keep these in view)

- **No tool observes other AIs for free.** The visibility numbers are only as
  good as the real query testing behind them. Budget time for Step 3 (or a paid
  tool). Don't let the scorecard be filled with guesses.
- **GEO is a young, shifting discipline.** Bot user-agents and AI-answer behavior
  change; treat the bot list and tactics as living, and re-check quarterly.
- **Volume ≠ authority.** A handful of accurate, well-structured, authored pages
  beats hundreds of thin ones. The rules and linter exist to enforce that.

---

### Appendix — quick command reference
```bash
# crawlability gate
python ~/.claude/skills/centro-geo-aeo/scripts/check_ai_crawlers.py https://DOMAIN

# validate a page's JSON-LD
python ~/.claude/skills/centro-geo-aeo/scripts/validate_schema.py https://DOMAIN/page

# lint prose for citability
python ~/.claude/skills/centro-geo-aeo/scripts/passage_lint.py page.md

# monthly GEO score
python ~/.claude/skills/centro-geo-aeo/scripts/geo_score.py .../assets/geo_scorecard.yml
```
Generic engine, inside Claude Code: `/seo https://DOMAIN`
