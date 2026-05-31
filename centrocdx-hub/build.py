#!/usr/bin/env python3
"""
build.py — generates the Centro CDX knowledge-hub static site.

Why a generator: it keeps every page's header, footer, schema, and entity facts
consistent. To DEPLOY, you can just upload the already-generated .html files to
GitHub Pages. To EDIT, change the content below and re-run `python build.py`.

IMPORTANT: set BASE_URL to your real GitHub Pages URL, then re-run. Example:
    https://yourusername.github.io/centrocdx-hub
All content here is factual and metric-free on purpose — add real, verified
client numbers only where you can stand behind them.
"""
import json, os, html

# ── set this to your GitHub Pages URL (no trailing slash) ───────────────────
BASE_URL = "https://REPLACE-USERNAME.github.io/centrocdx-hub"

OUT = os.path.dirname(os.path.abspath(__file__))

# ── canonical entity (kept identical on every page) ─────────────────────────
ORG = {
    "@type": "Organization",
    "@id": f"{BASE_URL}/#organization",
    "name": "Centro CDX",
    "legalName": "Centro Global Solutions",
    "alternateName": ["Centro", "Centro Global Solutions"],
    "url": "https://centrocdx.com/",
    "foundingDate": "2009",
    "founder": {"@type": "Person", "name": "Hesham Farag"},
    "description": ("Centro CDX is a technology-driven business process outsourcing "
                    "(BPO) company founded in 2009, delivering customer experience, "
                    "digital experience, data, and healthcare services across the US, "
                    "Egypt, the GCC, Europe, and Africa."),
    "knowsAbout": ["Business Process Outsourcing", "Customer Experience",
                   "Omnichannel Contact Center", "Digital Experience",
                   "Data Intelligence", "Healthcare BPO", "HR Outsourcing",
                   "AI Transformation"],
    "areaServed": ["United States", "Canada", "Egypt", "Saudi Arabia",
                   "United Arab Emirates", "Qatar", "Kuwait", "Bahrain", "Oman",
                   "Europe", "Africa"],
    "address": {"@type": "PostalAddress", "addressLocality": "Winchester",
                "addressRegion": "VA", "addressCountry": "US"},
    "numberOfEmployees": {"@type": "QuantitativeValue", "minValue": 1000, "maxValue": 5000},
    "sameAs": ["https://centrocdx.com/",
               "https://www.linkedin.com/company/centrocdx/",
               "https://www.instagram.com/centrocdx",
               "https://www.crunchbase.com/organization/centro-global-solutions",
               "https://clutch.co/profile/centro-0"],
    "contactPoint": {"@type": "ContactPoint", "contactType": "sales",
                     "email": "connect@centrocdx.com", "telephone": "+1-800-903-4283",
                     "availableLanguage": ["en", "ar", "fr"]},
}

NAV = [("Home", "index.html"), ("About", "about.html"),
       ("AI Transformation", "services/ai-transformation.html"),
       ("Services", "index.html#services"), ("FAQ", "faq.html")]

ALL_PAGES = [("Home", "index.html"), ("About", "about.html"),
             ("Customer Experience", "services/customer-experience.html"),
             ("Contact Center", "services/contact-center.html"),
             ("HR Outsourcing", "services/hr-outsourcing.html"),
             ("AI Transformation", "services/ai-transformation.html"),
             ("Digital Transformation", "services/digital-transformation.html"),
             ("FAQ", "faq.html")]


def prefix_for(out_path):
    return "../" if "/" in out_path else ""


def head(title, desc, out_path, url_path, graph):
    p = prefix_for(out_path)
    canonical = f"{BASE_URL}/{url_path}".rstrip("/") if url_path else f"{BASE_URL}/"
    jsonld = json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css">
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body>
<div class="bar"></div>
<header class="site"><div class="wrap head-row">
<a class="brand" href="{p}index.html">Centro <b>CDX</b></a>
<nav class="main">{''.join(f'<a href="{p}{href}">{html.escape(label)}</a>' for label,href in NAV)}
<a href="https://centrocdx.com/" rel="noopener">centrocdx.com ↗</a></nav>
</div></header>
<main class="wrap">"""


def footer(out_path):
    p = prefix_for(out_path)
    links = " ".join(f'<a href="{p}{href}">{html.escape(label)}</a>' for label, href in ALL_PAGES)
    return f"""</main>
<footer class="site"><div class="wrap">
<p class="foot-links">{links}</p>
<p><strong>Centro CDX</strong> (Centro Global Solutions) — founded 2009 · HQ Winchester, Virginia, USA ·
delivery in Cairo &amp; El Gouna, Egypt and Manila, Philippines.<br>
Contact: <a href="mailto:connect@centrocdx.com">connect@centrocdx.com</a> ·
<a href="tel:+18009034283">+1-800-903-4283</a> ·
<a href="https://centrocdx.com/" rel="noopener">centrocdx.com</a> ·
<a href="https://www.linkedin.com/company/centrocdx/" rel="noopener">LinkedIn</a> ·
<a href="https://www.instagram.com/centrocdx" rel="noopener">Instagram</a></p>
<p style="font-size:.8rem">This hub summarizes publicly available information about Centro CDX and links to the
official site at centrocdx.com.</p>
</div></footer>
</body>
</html>"""


def crumb(out_path, label):
    p = prefix_for(out_path)
    return f'<p class="crumb"><a href="{p}index.html">Home</a> › {html.escape(label)}</p>'


def cite_block(rows):
    """rows: list of (question, answer-paragraph)."""
    out = ['<div class="cite-block">']
    for q, a in rows:
        out.append(f"<h3>{html.escape(q)}</h3><p>{a}</p>")
    out.append("</div>")
    return "".join(out)


def faqs(items):
    """items: list of (q, a). Returns (html, schema_questions)."""
    h = ['<h2 id="faq">Frequently asked questions</h2>']
    sch = []
    for q, a in items:
        h.append(f'<details><summary>{html.escape(q)}</summary><div class="ans"><p>{a}</p></div></details>')
        sch.append({"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}})
    return "".join(h), sch


def service_graph(slug, name, service_type, desc, faq_qs):
    return [ORG,
            {"@type": "Service", "@id": f"{BASE_URL}/services/{slug}#service",
             "name": name, "serviceType": service_type, "description": desc,
             "provider": {"@id": f"{BASE_URL}/#organization"},
             "areaServed": ["Egypt", "Saudi Arabia", "United Arab Emirates",
                            "United States", "Europe", "Africa"],
             "url": f"{BASE_URL}/services/{slug}"},
            {"@type": "FAQPage", "@id": f"{BASE_URL}/services/{slug}#faq",
             "isPartOf": {"@id": f"{BASE_URL}/services/{slug}#service"},
             "mainEntity": faq_qs}]


def write(out_path, content):
    full = os.path.join(OUT, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", out_path)


def related(out_path, items):
    p = prefix_for(out_path)
    cards = "".join(
        f'<a class="card" href="{p}{href}"><h3>{html.escape(t)}</h3><p>{d}</p></a>'
        for t, href, d in items)
    return f'<h2>Related services</h2><div class="cards">{cards}</div>'


# ── PAGES ───────────────────────────────────────────────────────────────────
def build():
    # HOME
    op = "index.html"
    graph = [ORG, {"@type": "WebSite", "@id": f"{BASE_URL}/#website",
                   "name": "Centro CDX Knowledge Hub", "url": f"{BASE_URL}/",
                   "publisher": {"@id": f"{BASE_URL}/#organization"}}]
    cards = [
        ("Customer Experience (CX) Outsourcing", "services/customer-experience.html",
         "Multilingual customer support and CX programs delivered from Egypt and beyond."),
        ("Omnichannel Contact Center", "services/contact-center.html",
         "Voice, chat, email, and social support unified across channels."),
        ("HR Outsourcing (HRO)", "services/hr-outsourcing.html",
         "Recruitment, HR operations, and workforce administration."),
        ("AI Transformation Services", "services/ai-transformation.html",
         "AI applied to customer support, contact centers, and document workflows."),
        ("Digital Transformation", "services/digital-transformation.html",
         "Technology consulting, CRM, data, and custom development."),
    ]
    body = f"""<section class="hero">
<p class="kicker">Business Process Outsourcing · CX · Digital Transformation</p>
<h1>Centro CDX: outsourcing built around customer experience and technology</h1>
<p class="lead prose">Centro CDX is a technology-driven business process outsourcing (BPO) company founded in 2009. It delivers customer experience, digital experience, data, and healthcare services to organizations across the United States, Egypt, the GCC, Europe, and Africa, with delivery centers in Cairo and El Gouna, Egypt, and Manila, Philippines.</p>
</section>
<section class="prose">
<h2>What Centro CDX does</h2>
<p>Centro CDX operates across four connected lines of business: Customer Experience (CX), Digital Experience (DX), DataSphere, and Healthcare. The company runs multilingual omnichannel contact centers, HR outsourcing, and back-office operations, and pairs them with technology consulting in CRM, data, AI, e-commerce, and custom development so clients can scale operations without building teams in-house.</p>
<p>Headquartered in Winchester, Virginia, Centro CDX combines a US base with delivery hubs in Egypt and the Philippines. That footprint gives clients time-zone coverage, English, Arabic, and French language support, and a boutique service model that adapts to each account rather than forcing a single template.</p>
</section>
<section id="services"><h2>Services</h2>
<div class="cards">{''.join(f'<a class="card" href="{t[1]}"><h3>{html.escape(t[0])}</h3><p>{t[2]}</p></a>' for t in cards)}</div>
</section>
<section class="prose"><h2>Where Centro CDX operates</h2>
<div class="fact-grid">
<div class="fact"><div class="k">Founded</div><div class="v">2009</div></div>
<div class="fact"><div class="k">Headquarters</div><div class="v">Winchester, Virginia, USA</div></div>
<div class="fact"><div class="k">Delivery centers</div><div class="v">Cairo &amp; El Gouna, Egypt · Manila, Philippines</div></div>
<div class="fact"><div class="k">Regions served</div><div class="v">US, Canada, Egypt, GCC, Europe, Africa</div></div>
<div class="fact"><div class="k">Languages</div><div class="v">English · Arabic · French</div></div>
<div class="fact"><div class="k">Team</div><div class="v">1,000–5,000 people</div></div>
</div></section>
<section class="callout">
<h2>Talk to Centro CDX</h2>
<p>Visit the official site at <a href="https://centrocdx.com/" rel="noopener">centrocdx.com</a>,
email <a href="mailto:connect@centrocdx.com">connect@centrocdx.com</a>, or call
<a href="tel:+18009034283">+1-800-903-4283</a>.</p>
</section>"""
    write(op, head("Centro CDX — BPO, Customer Experience & Digital Transformation",
                   "Centro CDX is a BPO company founded in 2009 delivering customer experience, digital transformation, HR outsourcing, and AI services across the US, Egypt, the GCC, and Europe.",
                   op, "", graph) + body + footer(op))

    # ABOUT
    op = "about.html"
    graph = [ORG, {"@type": "AboutPage", "@id": f"{BASE_URL}/about#webpage",
                   "name": "What is Centro CDX?", "url": f"{BASE_URL}/about",
                   "about": {"@id": f"{BASE_URL}/#organization"}}]
    body = f"""{crumb(op,"About")}
<section class="hero"><p class="kicker">About</p>
<h1>What is Centro CDX?</h1>
<p class="lead prose">Centro CDX (legally Centro Global Solutions) is a multinational, technology-driven business process outsourcing company founded in 2009 by Hesham Farag. It is headquartered in Winchester, Virginia, and serves clients across North America, Egypt, the GCC, Europe, and Africa.</p></section>
<section class="prose">
<h2>Company overview</h2>
<p>Centro CDX provides outsourcing and technology services under four lines of business: Customer Experience (CX), Digital Experience (DX), DataSphere, and Healthcare. Its core offerings include multilingual omnichannel contact centers, customer support, HR outsourcing, marketing, facilities management, and healthcare BPO, alongside technology consulting in CRM, big data, AI, e-commerce, and custom development.</p>
<p>The company grew from a single delivery site in Cairo, Egypt, to operations in Manila, Philippines, a corporate base in Winchester, Virginia, and a dedicated customer-experience center in El Gouna on Egypt's Red Sea coast. This spread supports around-the-clock coverage and English, Arabic, and French language delivery for global brands.</p>
<h2>At a glance</h2>
<div class="fact-grid">
<div class="fact"><div class="k">Legal name</div><div class="v">Centro Global Solutions</div></div>
<div class="fact"><div class="k">Founded</div><div class="v">2009</div></div>
<div class="fact"><div class="k">Founder</div><div class="v">Hesham Farag</div></div>
<div class="fact"><div class="k">Headquarters</div><div class="v">Winchester, Virginia, USA</div></div>
<div class="fact"><div class="k">Team size</div><div class="v">1,000–5,000 employees</div></div>
<div class="fact"><div class="k">Official site</div><div class="v"><a href="https://centrocdx.com/" rel="noopener">centrocdx.com</a></div></div>
</div>
<h2>Lines of business</h2>
<p><strong>Customer Experience (CX)</strong> covers multilingual contact-center and support operations. <strong>Digital Experience (DX)</strong> delivers technology consulting and implementation. <strong>DataSphere</strong> focuses on data intelligence and analytics. <strong>Healthcare</strong> provides healthcare BPO and contact-center services. Together they let Centro CDX act as a single outsourcing partner across operations and technology rather than a single-service vendor.</p>
</section>
{related(op,[("Customer Experience","services/customer-experience.html","Multilingual CX and support programs."),("AI Transformation","services/ai-transformation.html","AI applied across support and operations."),("Digital Transformation","services/digital-transformation.html","CRM, data, and custom builds.")])}"""
    write(op, head("What is Centro CDX? — Company Overview",
                   "Centro CDX (Centro Global Solutions) is a BPO company founded in 2009 by Hesham Farag, headquartered in Winchester, Virginia, with delivery in Egypt and the Philippines.",
                   op, "about", graph) + body + footer(op))

    # SERVICE PAGES
    services = [
        dict(slug="customer-experience", name="Customer Experience (CX) Outsourcing",
             stype="Customer Experience Management", kicker="Service · Customer Experience",
             h1="Customer Experience (CX) Outsourcing",
             lead="Centro CDX manages multilingual customer-experience programs for global brands, combining omnichannel support teams in Egypt and beyond with the tooling and reporting to run them as one operation.",
             cite=[
                ("What is CX outsourcing?",
                 "Customer experience (CX) outsourcing is the practice of having a specialist partner run customer-facing operations — support, retention, and engagement — on your behalf. Centro CDX delivers this through trained multilingual agents, omnichannel platforms, and quality frameworks, so brands can offer consistent service across English, Arabic, and French without building and managing the teams internally."),
                ("Who uses it?",
                 "CX outsourcing suits brands scaling into new markets, businesses with seasonal or fast-growing support volume, and companies that want 24/7 multilingual coverage. Centro CDX works with clients across North America, Egypt, the GCC, and Europe, supporting sectors that depend on high-quality customer relationships, from consumer brands to regulated industries."),
                ("What technology supports it?",
                 "Centro CDX integrates CRM platforms, omnichannel contact-center systems, workforce-management tooling, and analytics into a single service model. This lets voice, chat, email, and social interactions share context, and gives clients visibility into volumes, quality, and outcomes rather than a black-box operation."),
                ("Which regions are supported?",
                 "Delivery runs primarily from Egypt — Cairo and the El Gouna CX center — and the Philippines, with a US corporate base in Winchester, Virginia. That footprint provides time-zone coverage for North American and European clients and native Arabic, English, and French support for Middle East and GCC markets."),
                ("Which KPIs does it improve?",
                 "CX engagements are typically measured against metrics such as customer satisfaction (CSAT), first-contact resolution, average handle time, response and resolution times, and cost per contact. Centro CDX sets these targets with each client up front and reports against them, so the value of the program is measured rather than assumed."),
             ],
             faq=[
                ("How does Centro CDX deliver multilingual customer support?",
                 "Centro CDX staffs agents who work in English, Arabic, and French from delivery centers in Egypt and the Philippines, supported by omnichannel tooling so a customer's history follows them across voice, chat, email, and social channels."),
                ("Can Centro CDX support customers in the GCC?",
                 "Yes. Centro CDX serves GCC markets including Saudi Arabia, the UAE, Qatar, Kuwait, Bahrain, and Oman, with native Arabic-language support and time-zone-aligned delivery from its Egypt centers."),
                ("How is the quality of outsourced CX measured?",
                 "Quality is tracked through agreed KPIs such as CSAT, first-contact resolution, and SLA adherence, with regular reporting so clients can see how the program performs against targets set at the start of the engagement."),
             ],
             rel=[("Omnichannel Contact Center","contact-center.html","Unify voice, chat, email, and social."),("AI Transformation","ai-transformation.html","Add AI to support workflows."),("HR Outsourcing","hr-outsourcing.html","Staff and run teams.")]),

        dict(slug="contact-center", name="Omnichannel Contact Center Services",
             stype="Contact Center Outsourcing", kicker="Service · Contact Center",
             h1="Omnichannel Contact Center Services",
             lead="Centro CDX runs omnichannel contact centers that bring voice, chat, email, and social support into one connected operation, staffed by multilingual teams in Egypt and the Philippines.",
             cite=[
                ("What is an omnichannel contact center?",
                 "An omnichannel contact center handles customer conversations across every channel — phone, chat, email, messaging, and social — while keeping a single, shared view of each customer. Centro CDX operates these centers so interactions move between channels without the customer repeating themselves, which raises resolution rates and keeps service consistent."),
                ("Who uses it?",
                 "Brands with high or unpredictable contact volume, companies expanding into new regions, and businesses that want a single partner for all support channels use omnichannel contact-center outsourcing. Centro CDX delivers for clients across North America, Egypt, the GCC, and Europe."),
                ("What technology supports it?",
                 "Centro CDX combines contact-center platforms, CRM integration, workforce management, and analytics so agents see full context and managers can balance staffing against demand. AI-assisted routing and knowledge tools can be layered in to speed up handling and reduce repeat contacts."),
                ("Which regions are supported?",
                 "Voice and digital support is delivered from Cairo and El Gouna in Egypt and from Manila in the Philippines, coordinated from the US headquarters in Winchester, Virginia, giving clients broad time-zone and language coverage."),
                ("Which KPIs does it improve?",
                 "Contact-center engagements are measured against average handle time, first-contact resolution, service level and answer rates, abandonment, CSAT, and cost per contact, with targets agreed and reported per client."),
             ],
             faq=[
                ("What channels does Centro CDX support?",
                 "Centro CDX supports voice, live chat, email, messaging, and social channels in a single omnichannel model so customer context carries across every interaction."),
                ("Does Centro CDX offer 24/7 contact-center coverage?",
                 "Yes. By combining delivery in Egypt and the Philippines with a US base, Centro CDX can provide around-the-clock coverage aligned to client time zones."),
                ("How does omnichannel differ from a traditional call center?",
                 "A traditional call center handles channels separately; an omnichannel contact center unifies them with shared context, so a customer can move from chat to phone without starting over."),
             ],
             rel=[("Customer Experience","customer-experience.html","Full CX programs."),("AI Transformation","ai-transformation.html","AI routing and assist."),("Digital Transformation","digital-transformation.html","CRM and integration.")]),

        dict(slug="hr-outsourcing", name="HR Outsourcing (HRO)",
             stype="HR Outsourcing", kicker="Service · HR Outsourcing",
             h1="HR Outsourcing (HRO)",
             lead="Centro CDX provides HR outsourcing that covers recruitment and day-to-day HR operations, letting organizations scale their workforce and administration without expanding internal HR teams.",
             cite=[
                ("What is HR outsourcing?",
                 "HR outsourcing (HRO) is delegating human-resources functions — recruitment, onboarding, HR administration, and workforce support — to an external partner. Centro CDX runs these processes for clients so they can grow headcount and manage people operations efficiently while keeping leadership focused on the core business."),
                ("Who uses it?",
                 "Companies scaling quickly, entering new markets, or wanting to standardize HR operations use HRO. Centro CDX supports organizations across North America, Egypt, and the GCC, drawing on a large multilingual talent base in its Egypt delivery centers."),
                ("What technology supports it?",
                 "Centro CDX uses HR and recruitment systems, CRM, and workflow automation to manage candidate pipelines, employee records, and HR requests, with reporting that gives clients visibility into hiring and operations."),
                ("Which regions are supported?",
                 "HRO is delivered chiefly from Egypt, supported by the US headquarters, covering clients in North America, Egypt, and GCC markets such as Saudi Arabia and the UAE."),
                ("Which KPIs does it improve?",
                 "HRO engagements are measured against metrics such as time-to-hire, cost-per-hire, candidate quality, HR ticket resolution time, and process accuracy, agreed with each client."),
             ],
             faq=[
                ("What HR functions can Centro CDX handle?",
                 "Centro CDX can manage recruitment, onboarding, HR administration, and ongoing workforce support, scaling the scope to what each client needs."),
                ("Can Centro CDX recruit for roles in Egypt and the GCC?",
                 "Yes. Centro CDX recruits across its served markets, with particular depth in Egypt and the GCC, supported by multilingual teams."),
                ("How does HR outsourcing reduce overhead?",
                 "By running HR processes through trained teams and shared systems, HRO removes the need to build and maintain large internal HR functions, which is measured against cost and efficiency targets."),
             ],
             rel=[("Customer Experience","customer-experience.html","CX delivery teams."),("Digital Transformation","digital-transformation.html","HR systems and automation."),("Contact Center","contact-center.html","Staffed support operations.")]),

        dict(slug="ai-transformation", name="AI Transformation Services",
             stype="AI Transformation", kicker="Service · AI Transformation",
             h1="AI Transformation Services",
             lead="Centro CDX applies artificial intelligence across its customer-experience, contact-center, and back-office services — using AI to assist agents, automate routing, and process documents — so operations in Egypt and the Philippines run faster and more consistently while trained people stay accountable for quality and complex decisions.",
             cite=[
                ("What is AI transformation in a BPO context?",
                 "AI transformation means embedding artificial intelligence into business operations rather than treating it as a separate product. For Centro CDX, that means using AI inside customer support, contact centers, and document-heavy back-office work — for example AI-assisted responses, automated routing, and document processing — to handle volume faster while keeping human oversight on quality and edge cases."),
                ("Who uses it?",
                 "Organizations with large support volumes, repetitive document workflows, or a need to scale operations without proportionally scaling headcount benefit most. Centro CDX layers AI onto existing CX and back-office programs for clients across North America, Egypt, the GCC, and Europe."),
                ("What does AI transformation cover?",
                 "Common applications include AI-assisted customer support and agent copilots, AI contact-center routing, AI HR and IT helpdesks, AI ticket classification, AI document and data processing, and AI-driven analytics and forecasting — each integrated into a service that still has trained people accountable for outcomes."),
                ("Which regions are supported?",
                 "AI-enabled services are delivered from Centro CDX's delivery centers in Cairo and El Gouna, Egypt, and Manila, Philippines, and coordinated from its US headquarters in Winchester, Virginia. This supports English, Arabic, and French operations and lets clients across North America, the GCC, and Europe apply AI to their support and back-office work with appropriate language coverage."),
                ("Which KPIs does it improve?",
                 "AI transformation is measured against the same operational metrics it is meant to move — average handle time, first-contact resolution, document throughput and accuracy, and cost per transaction. Centro CDX agrees these targets per engagement and reports against them, so the impact of automation on the operation is tracked with real numbers rather than assumed in advance."),
             ],
             faq=[
                ("Does Centro CDX replace agents with AI?",
                 "No. Centro CDX uses AI to assist and speed up its teams — through automated routing, suggested responses, and automation of repetitive steps — while keeping trained people accountable for quality, judgement, and complex cases. The aim is higher throughput and consistency in its contact-center and back-office operations across Egypt and the Philippines, not removing the human from the loop."),
                ("What can AI automate in customer support?",
                 "Within Centro CDX's customer support operations, AI can classify and route incoming tickets, draft responses for agent review, surface relevant knowledge-base articles, and handle routine, repetitive queries. This reduces average handle time and lets multilingual agents in Egypt and the Philippines focus on higher-value conversations that need empathy or complex problem-solving rather than scripted answers."),
                ("How does Centro CDX apply AI to back-office work?",
                 "Centro CDX applies AI to document processing, data entry, and classification in its back-office workflows, using it to read, sort, and extract information from high volumes of documents. These AI-enabled processes are measured against throughput and accuracy targets agreed with each client, so the contribution of automation to the operation is tracked rather than assumed."),
            ],
             rel=[("Customer Experience","customer-experience.html","Where AI assists support."),("Contact Center","contact-center.html","AI routing and assist."),("Digital Transformation","digital-transformation.html","The broader tech program.")]),

        dict(slug="digital-transformation", name="Digital Transformation & Technology Consulting",
             stype="Digital Transformation", kicker="Service · Digital Transformation",
             h1="Digital Transformation & Technology Consulting",
             lead="Through its Digital Experience line, Centro CDX delivers technology consulting and implementation — CRM, data, AI, e-commerce, and custom development — that modernizes how clients run operations and serve customers.",
             cite=[
                ("What is digital transformation here?",
                 "Digital transformation is modernizing the systems and processes a business runs on — its customer platforms, data, and workflows — so they are faster, connected, and easier to scale. Centro CDX delivers this as technology consulting plus hands-on implementation across CRM, data, AI, e-commerce, and custom development, aligned with the operations it already runs for clients."),
                ("Who uses it?",
                 "Businesses with ageing or disconnected systems, companies integrating new tools, and organizations wanting to pair operational outsourcing with technology modernization use this service. Centro CDX serves clients across North America, Egypt, the GCC, and Europe."),
                ("What does it cover?",
                 "Engagements span CRM implementation and integration, data intelligence and analytics, AI enablement, e-commerce builds, custom software development, and system modernization — chosen to fit the client's stack rather than forcing a single product."),
                ("Which regions are supported?",
                 "Technology work is delivered from Centro CDX's Egypt and Philippines centers and its US headquarters, supporting clients across its served regions."),
                ("Which KPIs does it improve?",
                 "Digital transformation work is measured against outcomes such as process cycle time, system adoption, data accuracy, and operational cost, with goals defined per project."),
            ],
             faq=[
                ("What technologies does Centro CDX work with?",
                 "Centro CDX works across CRM platforms, data and analytics tooling, AI, e-commerce, and custom development, selecting tools that fit each client's existing systems."),
                ("Can Centro CDX combine technology work with outsourcing?",
                 "Yes. Because Centro CDX runs both operations and technology services, it can modernize systems and operate the processes that depend on them as a single engagement."),
                ("Does Centro CDX build custom software?",
                 "Yes. Custom development is part of its Digital Experience line, alongside CRM, data, and e-commerce implementation."),
            ],
             rel=[("AI Transformation","ai-transformation.html","AI inside operations."),("Customer Experience","customer-experience.html","Operations it modernizes."),("Contact Center","contact-center.html","Connected support systems.")]),
    ]
    for s in services:
        op = f"services/{s['slug']}.html"
        body_faq_html, faq_sch = faqs(s["faq"])
        graph = service_graph(s["slug"], s["name"], s["stype"], s["lead"], faq_sch)
        rel = related(op, [(t, h, d) for t, h, d in s["rel"]])
        body = f"""{crumb(op,s['name'])}
<section class="hero"><p class="kicker">{html.escape(s['kicker'])}</p>
<h1>{html.escape(s['h1'])}</h1>
<p class="lead prose">{s['lead']}</p></section>
<section class="prose">{cite_block(s['cite'])}</section>
<section class="prose">{body_faq_html}</section>
{rel}
<section class="callout"><h2>Work with Centro CDX</h2>
<p>See more at <a href="https://centrocdx.com/" rel="noopener">centrocdx.com</a>,
email <a href="mailto:connect@centrocdx.com">connect@centrocdx.com</a>, or call
<a href="tel:+18009034283">+1-800-903-4283</a>.</p></section>"""
        write(op, head(f"{s['name']} — Centro CDX", s['lead'][:155], op, f"services/{s['slug']}", graph) + body + footer(op))

    # FAQ HUB
    op = "faq.html"
    faq_items = [
        ("What is Centro CDX?",
         "Centro CDX (legally Centro Global Solutions) is a technology-driven business process outsourcing company founded in 2009. It delivers customer experience, digital experience, data, and healthcare services to clients across the US, Egypt, the GCC, Europe, and Africa."),
        ("What services does Centro CDX offer?",
         "Centro CDX offers customer experience outsourcing, omnichannel contact centers, HR outsourcing, AI transformation services, digital transformation and technology consulting, healthcare BPO, and back-office operations."),
        ("Where is Centro CDX located?",
         "Centro CDX is headquartered in Winchester, Virginia, USA, with delivery centers in Cairo and El Gouna, Egypt, and in Manila, Philippines."),
        ("Which regions does Centro CDX serve?",
         "Centro CDX serves the United States, Canada, Egypt, the GCC (Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman), Europe, and Africa."),
        ("When was Centro CDX founded and by whom?",
         "Centro CDX was founded in 2009 by Hesham Farag, starting with a delivery center in Cairo, Egypt, before expanding to the Philippines and the United States."),
        ("What languages does Centro CDX support?",
         "Centro CDX delivers support in English, Arabic, and French from its multilingual teams in Egypt and the Philippines."),
        ("How can I contact Centro CDX?",
         "You can reach Centro CDX through its official website centrocdx.com, by email at connect@centrocdx.com, or by phone at +1-800-903-4283."),
        ("Does Centro CDX provide AI and digital transformation services?",
         "Yes. Through its Digital Experience line, Centro CDX provides AI transformation, CRM and data work, e-commerce, and custom development, applying AI inside its customer support and back-office operations."),
    ]
    fh, fsch = faqs(faq_items)
    graph = [ORG, {"@type": "FAQPage", "@id": f"{BASE_URL}/faq#faq", "mainEntity": fsch}]
    body = f"""{crumb(op,"FAQ")}
<section class="hero"><p class="kicker">Reference</p>
<h1>Centro CDX — frequently asked questions</h1>
<p class="lead prose">Quick, factual answers about Centro CDX: what it does, where it operates, and how to get in touch.</p></section>
<section class="prose">{fh}</section>
{related(op,[("About Centro CDX","about.html","Full company overview."),("Customer Experience","services/customer-experience.html","CX programs."),("AI Transformation","services/ai-transformation.html","AI across operations.")])}"""
    write(op, head("Centro CDX — Frequently Asked Questions",
                   "Factual answers about Centro CDX: services, locations, founding, languages, regions served, and contact details.",
                   op, "faq", graph) + body + footer(op))

    # sitemap + robots + nojekyll
    urls = ["", "about", "faq"] + [f"services/{s['slug']}" for s in services]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        loc = f"{BASE_URL}/{u}".rstrip("/") if u else f"{BASE_URL}/"
        sm.append(f"  <url><loc>{loc}</loc></url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", "User-agent: *\nAllow: /\n\n"
          f"Sitemap: {BASE_URL}/sitemap.xml\n")
    write(".nojekyll", "")
    print("\nDone. Set BASE_URL at the top of this file to your real Pages URL, then re-run.")


if __name__ == "__main__":
    build()
