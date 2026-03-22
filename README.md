# Zenith Active Solutions: External Strategy Audit
Candidate Briefing & Task Directives
## Executive Summary & Context
Welcome. Your consulting group has been engaged by the executive board of Zenith Active Solutions, a mid-sized, direct-to-consumer (D2C) fitness equipment and apparel brand.

Zenith experienced hyper-growth between 2021 and 2023, expanding from a handful of products to over 200 SKUs. However, while top-line revenue remains high, the company is experiencing a profitability crisis. EBITDA has collapsed to near-zero. The board suspects the company is leaking profit across multiple departments due to fractured data, inefficient processes, and undisciplined growth strategies.

**Your Mission: You have ~3 hours to process a raw data room, identify the structural leaks destroying the company’s margins, and present a data-backed turnaround strategy.**

## How You Should Work
**Your team must cover at least 2 of the 4 tracks.** Choose based on your team's strengths. Our preference is a combination that includes Track A + B (data + strategy), but a team that delivers a strong C+D or B+C solution will be evaluated equally.

- 🟢 Data Engineering & Analytics
- 🔵 Business Intelligence & Strategy
- 🟠 Marketing & Brand Strategy
- 🔴 UX/UI & Design

⚠️ A shallow attempt at all 4 tracks is worse than a deep, connected solution across 2–3.

## 🟢 Track A: Data Engineering & Analytics

    “Turn chaos into something usable—and scalable.”

Zenith's leadership cannot make data-informed decisions. Their data lives in 7 incompatible formats across databases, spreadsheets, JSON blobs, and mystery files. Nobody in the company can answer basic questions like "which customers are actually profitable?" or "which products should we stop selling?" Your job is to build the data foundation that makes answers possible — and explain to the board why this infrastructure investment is critical to the turnaround.

#### Your Role:

You are not just cleaning data—you are laying the foundation for how this company should work with data going forward.

>We suggest using:  Python (Pandas, SQLAlchemy, JSON parsing), SQL, Data Visualization libraries.


#### What You Should Produce:

1. A “Single Source of Truth” Dataset:
    - Merged dataset (SQLite + JSON)
    - Clean structure (user / transaction / time level)
    - Exported and usable by other teams

2. Business-Ready Data Outputs:
    - Provide at least 3 structured datasets, e.g.:
    - Customers per month by acquisition channel
    - Revenue / orders per SKU
    - Repeat purchase or cohort metrics

3. Exploratory Visual Proof (2–4 charts)
    - Clear, labeled charts that highlight:
    - An anomaly
    - A cost driver
    - A behavioral issue

4. ETL / Data Pipeline Attempt (Key Differentiator)

    Go one step beyond analysis:

    Design (or partially implement) a simple data pipeline or warehouse concept.

    This can be:

    - A script that:

        - Loads raw data

        - Cleans it

        - Outputs a final dataset automatically

    - OR a small “analytics database” (e.g., SQLite/Postgres) with cleaned tables

    - OR a structured ETL flow (even if not fully complete)

    What we’re looking for:

    - Clear structure (raw → cleaned → final)

    - Reproducibility mindset

    - An attempt to automate or systematize the process

    > It does not need to be perfect or fully finished—we want to see how you think about scaling data workflows.

Your presentation must connect your work to the company's core problem. Don't just show what you built — explain what problem it solves, why that problem matters, and what impact your solution would have.


### 🔵 Track B: Business Intelligence & Strategy (BI Team)

    “Explain where the money goes—and why.”

The board knows EBITDA collapsed from healthy margins to near-zero, but they don't know where the money is going. Costs are rising faster than revenue, but nobody can point to the specific leaks. Your job is to follow every dollar from revenue to cost, identify which operational and strategic decisions are destroying profit, and present the board with clear levers to pull — backed by numbers, not opinions.

#### Your Role:

You own the business narrative and translate data into decisions.


>We suggest using: Excel / PowerBI, Process Mapping (BPMN / Flowcharts), Strategic Frameworks (Value Driver Trees, Unit Economics).

Expected Deliverables:

1. Financial Model / Dashboard

    A working Excel file with:

    - CAC (ideally by channel)
    - Revenue & cost breakdown
    - Unit economics (LTV or proxy)
    - SKU / category performance

    **Important:**

    - At least part of the model should be dynamic/configurable
    (e.g., changing CAC assumptions or storage costs updates outputs)


2. Inventory & Cost Insight

    Clear identification of:

    - High-performing vs low-performing SKUs

    - Visual or table showing:

    - Cost impact (e.g., storage burden)


3. Process Analysis (Current vs Future)

    - Current process (visual or structured)

    -  At least 2 concrete inefficiencies

    - Improved process design

4. Scenario / Impact View

    - At least 2 strategic recommendations

    - Rough estimate of financial impact

    - Clear assumptions

5. Cost Waterfall Analysis

    - Show where each dollar of gross revenue gets consumed before reaching EBITDA

    - Identify the top 3 cost categories destroying margin and quantify each

    - Make it clear which costs are structural vs. addressable

Your presentation must connect your work to the company's core problem. Don't just show what you built — explain what problem it solves, why that problem matters, and what financial impact your solution would have.


### 🟠 Track C: Marketing & Brand Strategy

    “Fix growth so it actually creates value.”

Marketing spend has increased every quarter for two years, yet profitability is going down. The board suspects the growth engine is actually destroying value — acquiring the wrong customers, at the wrong price, through the wrong channels. Your job is to diagnose what's broken in the growth model, identify which channels and strategies are value-destroying, and redesign marketing to focus on profitable retention over vanity volume.

#### The Role:

You are responsible for resetting how the company grows.

Right now, marketing is optimized for volume—not profitability. Your job is to:

- Identify which channels and strategies are destroying value

- Redesign marketing to focus on retention, efficiency, and brand integrity

- Translate insights into executable campaigns you can actually show us

You can use data from:

- Track A (if available) for channel and customer data

- Track B (if available) for CAC, LTV, and profitability insights

- Folder 2: marketing_spend_history.xlsx is directly usable without coding

- Folder 3: Several internal documents contain critical marketing clues

>We suggest using: Google Docs / Notion, PowerPoint, Canva, your phone — whatever you'd use to actually build a campaign.

#### Expected Deliverables:

1. Channel Audit & Strategy Pivot

    Diagnose the current marketing spend across channels. Use the spend data and internal documents to answer:

    - Which channels are generating value and which are destroying it?

    - What's the evidence? (Spend trends, document clues, customer behavior signals)

    - What should the new channel mix look like, and why?

    Output: A clear 1-2 page analysis or set of slides with a specific recommendation and the reasoning behind it.

2. Campaign Concept with Mockups

    Design a concrete campaign for one of the following (pick the one that fits your diagnosis):

    - A "Bundle & Save" launch to move dead inventory while protecting margin

    - A retention/win-back campaign targeting high-value customer segments

    - A brand repositioning campaign shifting away from discount-first messaging

    **Show us what you'd actually post.** Create 2-3 real mockups: social media posts, stories, short video storyboards, email designs, or ad concepts. Use Canva, Figma, your phone, hand sketches — whatever works. We want to see execution, not just a written description of a campaign.

    Output: 2-3 campaign assets (images, storyboards, or drafts) + a short explanation of the strategy behind them.

3. 2-Week Content Calendar

    Build a realistic 2-week content plan for Zenith's social channels that supports your campaign concept.

    - What gets posted where (Instagram, TikTok, Email, etc.) and when?

    - What's the mix of content types (product, lifestyle, educational, promo)?

    - How does this calendar reflect your strategic pivot away from what's currently broken?

    Output: A simple calendar (spreadsheet, table, or slide) showing the plan + a brief rationale.

Your presentation must connect your work to the company's core problem. Don't just show what you built — explain what problem it solves, why that problem matters, and what financial impact your solution would have.


### 🔴 Track D: UX/UI & Graphic Design

    “Make the solution tangible and usable.”

Zenith's current customer experience is accidentally suppressing revenue and creating downstream operational chaos. The checkout flow discourages multi-item purchases, the homepage trains customers to expect deep discounts, and the packaging process is so complex it slows down the entire warehouse. Your job is to redesign the customer-facing touchpoints that are quietly bleeding money — and show the board how design changes translate to margin improvements.

#### Important Context

You will be provided with:

- Existing brand/UI guidelines

- Example design assets (in a separate folder)

You are not designing from scratch—you are evolving an existing system.


#### The Role:

You must visually redesign the customer touchpoints to increase Average Order Value (AOV) and reduce warehouse friction.


>We suggest using: Figma, Adobe Creative Cloud, Sketching tools.

#### Expected Deliverables:

1. Bundle Builder Wireframe

    -  Clear UI flow (how users build bundles)

    - Encourages multi-item purchases

    - Can be low- or high-fidelity

2. Packaging Concept

    -  Simple visual sketch or concept

    - Focus on:

        - Reduced complexity

        - Consistent design

        - Operational efficiency

3. Campaign Visual (Optional Bonus)

    - 1–2 assets (e.g., banner, social post)

    - Should align with marketing strategy

Your presentation must connect your work to the company's core problem. Don't just show what you built — explain what problem it solves, why that problem matters, and what financial impact your solution would have.


## 🖼️ Final Presentation (10–12 Slides)
At the end of the assessment, your sub-teams must merge your findings into a unified 10-12 Slide Executive Pitch to the Zenith Board (your assessors).

Your presentation MUST include:

- The Problem (1–2 slides): What is broken at Zenith? Root causes, not symptoms.

- Your Evidence (2–3 slides): Data, process analysis, document findings, or design audits that prove your diagnosis. This can be charts, financial models, process maps, document quotes, UX teardowns — whatever your tracks produced.

- Your Solution (3–4 slides): Concrete, implementable changes. Systems, not ideas. Show re-engineered processes, new frameworks, redesigned flows, or restructured strategies.

- Expected Impact (1–2 slides): Rough financial estimate. What does this save or earn? State your assumptions clearly.

- Next Steps (1 slide): 30–60–90 day implementation plan.

Optional but encouraged:

- Value Driver Tree connecting operations → costs → EBITDA

- Process maps (current vs. future state)

- Live demo of a dashboard or data pipeline



> ❗Presentation template is in Main task folder.

## 📁 The Data Room Manifest
You have been granted access to a secure, unorganized data dump.

### Folder 1: Raw System Data

- zenith_core_db.sqlite (Core transaction ledger)

- customer_profiles_v2.json (Deeply nested user telemetry and segment data)

- sys_ops_log_archive.sys (A non-standard, un-headered operational shift log)

### Folder 2: Business & Finance Files

- sku_summary.csv (High-level product catalog data)

- monthly_pnl_summary.csv (Monthly profit & loss summary)

- marketing_spend_history.xlsx (Monthly ad spend by channel)

- warehouse_rate_card.xlsx (Vendor storage costs based on product category)

### Folder 3: Internal Communications (18 documents)

A collection of internal emails, Slack threads, HR surveys, legal memos, meeting notes, maintenance logs, and warehouse SOPs. Warning: Treat these like real-world corporate communications. Some contain vital strategic clues; others are pure corporate noise and distractions.

### Folder 4: Design Assets (Optional)

- UI references

- Example visuals

## What We’re Looking For

Strong teams:

- Focus on high-impact problems

- Connect insights across teams

- Build practical, implementable systems

- Use data as evidence—not decoration

Weak teams:

- Work in silos

- Over-focus on low-impact details

- Provide vague recommendations

- Fail to connect operations to profit

---


Good luck 😊