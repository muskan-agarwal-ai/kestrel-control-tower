# Kestrel Control Tower

A dashboard showing how Kestrel Provisions' supply chain is performing:
service, cold chain, money, and price position. Built with Streamlit.

**Read `DECISIONS.md` first.** It explains what's real, what was fixed, and
what's still missing, and why. That document is the actual spec this was
built and corrected against.

---

## Quick start

Requires Python 3.9+.

```bash
pip install -r requirements.txt
```

Make sure the database is in place at `data/kestrel_ops.db` (not committed
to version control; supply it separately).

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Six tabs in the sidebar: **Overview**,
**Service**, **Inventory & Returns**, **Cold Chain**, **Freight & Price**,
**Divya's Questions**.

That's the whole cold start. No other setup is required to see real, live
numbers computed from the database.

---

## Seeing live freight and carrier data

Everything on the dashboard reads straight from `data/kestrel_ops.db` and
just works. The one exception is the freight numbers on the **Freight &
Price** tab (and the freight-related question on **Divya's Questions**),
which come from a separate, mock carrier-billing API, not the database,
because that's the only place real freight cost lives (see `DECISIONS.md`
for why `fuel_cost_inr` in the database isn't used instead).

**In a separate terminal, before or after starting the dashboard:**
```bash
python partner_api/server.py
```
Leave this running. Then, in the dashboard, open **Freight & Price** and
click **"Fetch live freight data."**

What happens: it pulls all ~7,100 real invoices for the quarter through the
API's deliberately unreliable connection (expect real rate-limit waits and
occasional retries; the client handles these automatically, and you'll see
them logged in the terminal running `server.py`). Takes about 2 minutes.
Once fetched, both the **cost-per-case-by-warehouse** table and the
**leakage-by-carrier** table populate from that single pull; it doesn't
fetch twice. The freight question on **Divya's Questions** reuses this same
result rather than fetching a third time. If you haven't clicked the button
yet, it'll tell you to do that first instead of hanging.

Refreshing the browser page clears the cached result; you'll need to click
the button again.

The price-position half of the Freight & Price tab (Kestrel MRP vs.
competitor prices) loads automatically. It only reads local files, no
button needed.

---

## What's on each tab

- **Overview**: Q1 FY2026-27 headline numbers (fill rate, two on-time
  metrics, near-expiry, returns value), OTIF by region, and lowest-performing
  routes. Q1-scoped by default because the brief explicitly asks for this.
- **Service**: fill rate by region/warehouse, worst routes and outlets,
  dynamically-computed "last complete month" early-warning outlets, OTIF by
  warehouse plus worst routes/outlets by OTIF, routes exceeding a 10%-late
  threshold, and outlets still ordering discontinued SKUs.
- **Inventory & Returns**: near-expiry stock by warehouse, returns by
  reason, returns by category paired with each category's leading reason
  code, and returns as a percentage of dispatch value by region.
- **Cold Chain**: reefer vs. non-reefer excursion rates, excursions by
  month, and returns specifically caused by cold-chain breach.
- **Freight & Price**: live freight cost per case by warehouse and by
  carrier (button-triggered, see above), and Kestrel MRP vs. the lowest
  validated Mumbai competitor price for the Top-20 SKUs by sales value.
- **Divya's Questions**: the assignment brief's own 8 illustrative
  questions, verbatim, each with a real computed answer behind it. Not a
  free-text "ask anything" box (see `DECISIONS.md`; that pillar isn't
  built), but a fixed set of known questions, each backed by an actual
  query, not a canned response.

---

## Project structure

```
├── app.py                    # The dashboard. This is what you run
├── metrics.py                 # Database-only calculations (fill rate, OTIF
│                               #   at all 4 grains, cold chain, returns,
│                               #   discontinued SKUs, case fill rate for
│                               #   Divya's Questions Q1, etc.)
├── live_metrics.py             # Freight (Partner API) and price position
│                               #   (BazaarPulse): the two things that reach
│                               #   outside the database
├── integrations/
│   └── freight_api.py          # Resilient Partner API client: retries,
│                               #   backoff, paise-to-INR conversion
├── partner_api/
│   └── server.py                # Mock carrier billing API. Must be running
│                               #   separately for live freight data
├── bazaarpulse_site/            # Local static competitor pricing site
├── investigation/                # Scratch scripts used to work out each
│                               #   metric before it went into the app.
│                               #   Not imported by app.py, kept for reference
├── data/kestrel_ops.db          # The database (not committed; supply separately)
├── DECISIONS.md                 # Read this first
└── README.md                    # This file
```

**Important: `app.py` and `metrics.py` do not share code.** `app.py` has
its own inline copies of most queries rather than importing from
`metrics.py` (the newer panels, meaning OTIF, discontinued SKUs, late
routes, monthly excursions, cold-chain returns, returns-by-category,
dispatch-value %, and all of Divya's Questions, do call into `metrics.py`
directly, but the older panels don't). This was found the hard way during
development: a bug fixed in `metrics.py` silently did not take effect in
the dashboard, because `app.py` had its own separate copy of that same
query. **Any future change to a metric's logic needs to be checked in both
files**, not just one. This is flagged as the top near-term refactor in
`DECISIONS.md`.

---

## What's real vs. what's a documented limitation

- **Fill rate (eaches, and cases on Divya's Questions), on-time (both
  definitions), OTIF (all 4 grains), cold chain, returns, near-expiry,
  discontinued SKUs, late routes**: computed live from the database on every
  page load. No caching, no stale snapshots.
- **Freight cost (by warehouse and by carrier)**: real, live data from the
  Partner API, fetched on demand (see above). Not the `fuel_cost_inr` field
  in the database, which is driver-entered and not actual billed cost.
- **Price position**: real, live matching against local BazaarPulse HTML.
  Scoped to Mumbai only and the Top-20 SKUs by Q1 sales value (see
  `DECISIONS.md` for why). Compares against **MRP**, not list price; this
  was a bug in an earlier version, since fixed. Unvalidated matches report
  "no match" rather than a forced, low-confidence comparison; the one
  validated match (Kestrel Atta) carries a visible caveat about match
  strength rather than being presented as certain, and that caveat text is
  generated from the live data, not typed in, so it can't drift out of sync
  with the number in the table again.

## What's not built yet (see `DECISIONS.md` for full reasoning)

- No free-text "ask anything" natural-language query box. Divya's Questions
  answers a fixed, known set of 8 questions, not arbitrary ones.
- No per-region filtered view for regional managers.
- Fill rate shows eaches only on most tabs; cases is shown in exactly one
  place (Divya's Questions, Q1), not as a general second metric everywhere.
- Price matching covers Mumbai only, not all 4 BazaarPulse cities.

These are documented as deliberate scope decisions, not gaps discovered
after the fact.