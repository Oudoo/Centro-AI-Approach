# Centro CDX — POC Deploy Guide + CTO Demo Runbook

This is the proof-of-concept: a fast, fully crawlable knowledge hub on GitHub
Pages (no Sucuri, no WordPress, no security-team approval needed) that AI engines
can actually read. Deploy it, get it indexed, wait ~1–2 weeks, then run the demo.

---

## What you're deploying
A static 8-page site — home, about, FAQ, and 5 service pages (CX, contact center,
HR outsourcing, **AI Transformation**, digital transformation). Every page has
real content in the raw HTML (no JavaScript needed), JSON-LD schema linked to one
Organization entity, a sitemap, and a crawler-friendly robots.txt. All content is
factual and sourced from public information about Centro CDX, with the official
site, email, and phone on every page.

---

## Part A — Deploy to GitHub Pages (≈15 minutes)

### Step 1 — Set your URL and rebuild
Decide your repo name (e.g. `centrocdx-hub`). Your Pages URL will be
`https://YOURUSERNAME.github.io/centrocdx-hub`. Open `build.py`, set:
```python
BASE_URL = "https://YOURUSERNAME.github.io/centrocdx-hub"
```
Then regenerate so canonicals, sitemap, and schema use the real URL:
```bash
cd centrocdx-hub
python3 build.py
```

### Step 2 — Create the repo and push
```bash
cd centrocdx-hub
git init
git add .
git commit -m "Centro CDX knowledge hub (POC)"
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/centrocdx-hub.git
git push -u origin main
```
(No terminal? Use GitHub's web UI: New repo → "uploading an existing file" →
drag in everything from the `centrocdx-hub` folder. The `.nojekyll` file matters —
make sure it uploads.)

### Step 3 — Turn on Pages
GitHub repo → **Settings → Pages** → Source: **Deploy from a branch** →
Branch: **main**, folder: **/ (root)** → Save. Wait 1–2 minutes, then visit your
URL. You should see the site with the terracotta/navy theme.

### Step 4 — Verify it's crawler-readable (the whole point)
```bash
# real HTML to a non-JS client? (should print the headline + content, NOT a JS gate)
curl -sS https://YOURUSERNAME.github.io/centrocdx-hub/ | grep -i "Centro CDX"

# schema present?
python3 ../centro-geo-aeo/scripts/validate_schema.py https://YOURUSERNAME.github.io/centrocdx-hub/
```
Contrast this with `curl https://centrocdx.com/` (the JS gate) — that side-by-side
is itself a slide in your CTO pitch.

---

## Part B — Get it indexed fast (do immediately after deploy)

AI search engines mostly read what classic search engines have indexed, so push
the hub into those indexes:

1. **Bing Webmaster Tools** (powers Copilot + influences others): add the site,
   verify, submit `…/sitemap.xml`. Bing also feeds many AI answers — prioritise it.
2. **Google Search Console**: add the property, submit the sitemap, and use
   **URL Inspection → Request indexing** on the homepage and the AI Transformation page.
3. **IndexNow** (instant ping to Bing/Yandex): optional but fast. Submitting via
   Bing Webmaster Tools is the simple route.
4. **Link to it from profiles you control** so crawlers discover it sooner:
   - LinkedIn company page (https://www.linkedin.com/company/centrocdx/) — add the
     hub URL in the About/website section or post it.
   - Instagram (https://www.instagram.com/centrocdx) — put the link in bio.
   - Any directory listing you can edit (Clutch, Crunchbase) — add it as a link.

**Then wait ~1–2 weeks.** Do not demo the day you deploy — engines need a crawl
cycle. Re-check indexing with `site:YOURUSERNAME.github.io/centrocdx-hub` in Bing
and Google.

---

## Part C — The CTO demo runbook

### Setup before the meeting
- Confirm the hub is indexed (the `site:` check returns pages in Bing/Google).
- On the demo machine, open four tabs: **ChatGPT, Gemini, Perplexity, Claude.**
- **Turn web search/browsing ON in each** — this is critical. Default ChatGPT and
  Claude answer from memory and can't see the hub. Perplexity and Gemini search by
  default. The demo only works in search mode.
- Have your side-by-side ready: `curl https://centrocdx.com/` (JS gate, no content)
  vs `curl https://…github.io/centrocdx-hub/` (full content).

### Run the questions in this order — safe first, ambitious last

**Tier A — near-certain wins (lead with these).** Branded, specific; the hub
answers them directly:
- "What is Centro CDX and what services does it offer?"
- "What is Centro CDX's website and contact information?"
- "Where are Centro CDX's delivery centers located?"
- "Does Centro CDX offer AI transformation services?"
> Expected: the assistant returns the company description, **centrocdx.com**, the
> phone number, regions, and services — citing the hub. This is the proof the CTO
> needs: AI can now read and repeat Centro's information correctly.

**Tier B — good odds (long-tail commercial).** Specific enough that incumbents
don't crowd you out:
- "BPO company with a customer experience center in El Gouna, Egypt"
- "multilingual contact center outsourcing with US HQ and Egypt delivery"
- "Arabic-language customer support outsourcing in the GCC"

**Tier C — upside, do NOT promise.** Broad head terms where big incumbents
dominate; frame as "and here's where we're headed next":
- "best BPO companies in Egypt"
- "top customer experience outsourcing providers in the Middle East"
> If Centro appears, great. If not, that's the set-up for your ask: "this is what
> we win once the content is on our real domain and we've built authority."

**Guaranteed fallback (always works).** Paste the hub URL into any assistant:
- "Summarise this company: https://…github.io/centrocdx-hub/"
> The assistant reads it live and describes Centro accurately — proving the
> content is AI-readable and on-message, even where it didn't surface unprompted.

### The closing ask
Frame it exactly like this:
> "Everything you just saw came from a static microsite an AI could read. Our real
> site, centrocdx.com, returns a JavaScript security gate — so the AI sees nothing
> [show the curl]. The diagnosis is a Sucuri firewall challenging bots. The fix is
> a one-time allowlist of AI crawler user-agents in the Sucuri dashboard — no
> WordPress change, no code. Approve that, and we get these results on our own
> domain instead of a github.io URL."

That's the bridge to Version 2 (the permanent Sucuri fix) — now backed by a live
result instead of a theory.

---

## Honest expectations
- **Branded/specific queries (Tier A/B): high probability** once indexed.
- **Head terms (Tier C): low probability** on this timeline — that's normal, and
  it's the reason for the ask, not a failure of the POC.
- **Memory-mode AI: out of scope.** Only web-search mode can see the hub.
- **Timing matters more than anything** — give it the crawl window before demoing.

## After the POC succeeds
Migrate this content to centrocdx.com (it's plain HTML + JSON-LD, easy to port),
get the Sucuri allowlist done (Version 2 / Finding 0 in the main playbook), and
fold the hub's pages into the full GEO program in `CENTRO-GEO-IMPLEMENTATION.md`.
