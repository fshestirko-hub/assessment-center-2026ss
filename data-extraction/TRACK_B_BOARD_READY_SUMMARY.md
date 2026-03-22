# Track B: Board-Ready Business Intelligence & Strategy Output

## 1) What Was Built
- Single monthly merged table combining P&L, monthly marketing spend, and warehouse storage-cost proxy from rate card.
- SQLite-driven customer purchase behavior table and cohort views.
- Channel-level CAC vs LTV table.
- SKU contribution proxy and bottom-10 SKU risk list.

## 2) Core Financial Signals
- Total net revenue (period): 4,739,638.77
- EBITDA proxy (period): 32,175.37
- EBITDA proxy margin: 0.68%

## 3) Margin Killers (Quantified)
- Marketing intensity: monthly marketing is now included directly in waterfall-style EBITDA proxy.
- SKU storage + returns drag: bottom 20% SKU set implies 3,081.59 recoverable value (storage + return-loss proxy).
- Contribution upside from SKU rationalization: ~0.07 margin points.

## 4) CAC-LTV Efficiency
- Lowest LTV/CAC channel: Influencer
- Highest LTV/CAC channel: Organic
- If 25% of lowest-efficiency spend is reallocated: estimated savings 127,679.16 and ~2.69 margin points.

## 5) Process Redesign (Current -> Future)
- Current: broad SKU catalog, high return-exposed items, and channel mix not explicitly optimized for LTV/CAC.
- Future: bottom-quintile SKU rationalization, channel-budget reallocation to higher LTV/CAC, monthly monitoring of cohort repeat-rate and EBITDA proxy.

## 6) 30-60-90 Day Plan
- 30 days: freeze long-tail SKU expansion, enforce monthly CAC-LTV review, confirm dead-stock list.
- 60 days: implement SKU delist/bundle actions and channel budget shifts.
- 90 days: complete cohort-driven retention program and lock dashboard governance cadence.

## 7) Data Assumptions
- Warehouse storage cost proxy uses rate card fee per unit mapped by Category + Handling_Type and distributed monthly by gross-revenue weight.
- Return-loss proxy assumes 30% unrecovered value of returned revenue.
- Marketing reallocation scenario assumes 25% spend shift from the lowest to highest LTV/CAC channel.
- SQLite customer purchase behavior derived from table: transactions_master