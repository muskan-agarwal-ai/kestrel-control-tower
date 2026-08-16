# DECISIONS.md

## What I built
A Streamlit control tower over Kestrel's operational database: fill rate and
OTIF at every grain (region/warehouse/route/outlet), cold chain (excursions
by month, near-expiry, cold-chain-specific returns), money (freight cost by
warehouse and carrier, live from the Partner API, not a proxy; returns as
% of dispatch value; returns by category with leading reason), price
position (Kestrel MRP vs. Mumbai competitors, Top-20 SKUs), and "Divya's
Questions": the brief's own 8 illustrative questions, each answered by a
real query, as an honest middle ground short of full free-text ask-anything.
Q1 FY2026-27 is on the front page by default, per Rakesh's explicit
instruction. Fill rate is reported in eaches everywhere except one place
(Divya's Questions Q1), per his override of the original cases request.

## What I deliberately did not build
- **Free-text ask-anything.** Divya's Questions answers 8 known questions
  correctly, not arbitrary ones, which is more honest than shipping a
  general NL layer I couldn't fully validate in the time available.
- **Regional-manager-scoped views.** No login/filtering by region exists.
- **Cases as a general second fill-rate metric.** Shown in exactly one place.
- **Price matching beyond Mumbai / beyond the Top-20 SKU cohort.**

## What I assumed, and why
- **OTIF "in full" = 90%, not 100%.** Checked directly: zero of 511,516
  order lines in the dataset ever deliver the exact quantity ordered. A
  literal 100% bar makes OTIF permanently 0% everywhere, not a usable
  metric. Even a 95% bar clears only 1.3% of orders across 18 months. 90% is
  the lowest round threshold producing real differentiation. This is a
  judgement call needing business sign-off, not a discovered fact. OTIF is
  ~13% at region and warehouse grain (near-uniform, pointing to a systemic
  issue, not a regional one) but varies sharply at route/outlet grain, some
  at 0%, which is where the actionable variance actually lives.
- **"On time" reported two ways**, not merged: by 2-hour delay (matches
  Divya's own example, 75.06% in Q1) and by requested delivery date (97.70%).
  The original code silently dropped ~35% of deliveries from the second
  metric, because one telematics vendor's date format wasn't being parsed,
  before this was found and fixed.
- **Returns value uses `credit_note_value_inr` directly.** Checked that it
  isn't simply `qty × price` (the ratio varies 0.3%-39% row to row, no fixed
  scale); it reflects real partial/negotiated credit, the right basis for a
  leakage figure. An earlier reconstruction had overstated returns ~50x.
- **Price comparison uses MRP, not list price.** The brief asks for MRP
  explicitly, twice; an earlier version compared against Kestrel's internal
  trade price instead, understating the real competitive gap (-65% vs. the
  corrected -76%).
- **Near-expiry inventory is scoped to the latest snapshot only.** The
  table holds 78 historical weekly snapshots; summing all of them (the
  original approach) overstated at-risk stock ~78x.

## Two more weeks
1. Extend Divya's Questions toward genuine free-text ask-anything.
2. Refactor so `app.py` and `metrics.py` share one set of queries instead of
   two independently maintained copies (see below).
3. Region-scoped views; cases as a labeled second metric everywhere.
4. Price matching across all 4 BazaarPulse cities, with a maintained
   name-to-SKU mapping table instead of word-overlap matching.
5. Schedule the freight pull as a cached nightly job, not a live per-click one.

## What breaks first in production
- **This runs on SQLite: a single-file, single-writer database with no
  built-in replication or connection pooling.** Fine for a demo at ~820K
  order lines and one user; a real deployment with concurrent users needs a
  proper multi-user database (Postgres) before that becomes a problem, not
  after. Several queries also do full joins with no indexes defined; fine
  today, not at 100x the data.
- **`app.py` and `metrics.py` duplicate queries independently** rather than
  sharing code. Found directly: a bug fix in `metrics.py` didn't take
  effect in the dashboard because `app.py` had its own separate copy of the
  same query, requiring the fix twice. The single most likely source of the
  next silent inconsistency.
- **The freight pull has no cross-session cache**; every click re-walks
  ~7,100 invoices live. Fine at current volume, not at real usage scale.
- **Competitor matching is regex against raw HTML with no schema
  versioning, and test-outlet exclusions are 3 hard-coded IDs**, a snapshot
  of today's data rather than a durable rule.
