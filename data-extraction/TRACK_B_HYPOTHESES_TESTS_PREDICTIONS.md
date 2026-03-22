# Track B: Hypotheses, Tests, and Predictions (Sales + Marketing)

## Objective
Board hypothesis: profit is leaking due to fragmented data, inefficient marketing mix, and undisciplined growth.

This plan focuses on sales outcomes and four paid/acquisition channels:
- Organic
- Search
- Paid Social
- Influencer

## Baseline Evidence (from merged outputs)
Data sources:
- encoded_data/track_b_channel_cac_ltv.csv
- encoded_data/track_b_customer_behavior_enriched.csv
- encoded_data/track_b_monthly_merged_table.csv

Channel baseline snapshot:
- Organic: CAC 24.50, Avg LTV 1043.24, LTV/CAC 42.58
- Search: CAC 155.88, Avg LTV 1040.88, LTV/CAC 6.68
- Paid Social: CAC 148.10, Avg LTV 1041.30, LTV/CAC 7.03
- Influencer: CAC 1058.34, Avg LTV 654.64, LTV/CAC 0.62

Spend mix:
- Influencer 51.58% of total spend
- Paid Social 29.40%
- Search 15.42%
- Organic 3.60%

Problem signal:
- The largest spend bucket (Influencer) is the least efficient channel by far.

## Hypothesis 1: Marketing Mix Leak
Hypothesis:
- Profit leak is driven by over-allocation to Influencer relative to channel quality.

Test design:
- Type: controlled budget reallocation test (geo or audience split).
- Horizon: 6-8 weeks.
- Variant A (control): current allocation.
- Variant B (test): move 20% of Influencer spend into Organic + Search (70/30 split).
- Guardrail: keep total spend constant.

Primary KPIs:
- CAC by channel
- Blended CAC
- LTV/CAC
- New customers per euro
- Incremental gross profit proxy

Pass criteria:
- Blended CAC down at least 12%
- Blended LTV/CAC up at least 20%
- No more than 5% decline in total new customers in first 2 weeks

Prediction:
- Theoretical upper bound from current CACs for 20% Influencer reallocation:
  - Spend shifted: 104,564
  - Expected customers if kept in Influencer: 98.8
  - Expected customers if moved to Organic-equivalent CAC: 4,267.2
- Capacity-adjusted realistic range (5-20% of theoretical lift):
  - Incremental customers: +208 to +834
  - Revenue uplift proxy: +246,474 to +985,896

## Hypothesis 2: Influencer Quality Leak
Hypothesis:
- Influencer traffic quality is weak because spend is broad and conversion intent is low.

Test design:
- Type: creative + audience quality test within Influencer.
- Horizon: 4 weeks.
- Variant A: current influencer mix.
- Variant B: strict creator whitelist (top 20%), conversion-focused creative, remove low-intent placements.

Primary KPIs:
- Influencer CAC
- First-order conversion rate
- 30-day repeat rate
- Refund/return proxy rate

Pass criteria:
- Influencer CAC down at least 25%
- 30-day repeat rate up at least 10%
- Return-risk proxy down at least 10%

Prediction:
- Influencer CAC can improve from ~1058 toward 750-850 range if low-yield creators are removed.
- LTV/CAC should move from 0.62 toward 0.9-1.2 in initial phase.

## Hypothesis 3: Paid Social and Search Under-Scaled
Hypothesis:
- Search and Paid Social are efficient enough to absorb more budget with better unit economics than Influencer.

Test design:
- Type: stepwise budget ramp test.
- Horizon: 6 weeks.
- Increase Paid Social and Search budgets by +15% each, funded by Influencer reduction.
- Keep bids and attribution model stable to isolate spend effect.

Primary KPIs:
- Marginal CAC (not average CAC)
- Incremental revenue per additional euro
- Contribution margin per order

Pass criteria:
- Marginal CAC stays within +20% of current average CAC
- Incremental contribution margin positive in both channels

Prediction:
- Paid Social and Search should retain LTV/CAC above 4.5 under moderate scaling.
- Net effect likely: lower blended CAC and higher EBITDA proxy margin by 1.0-2.5 points.

## Hypothesis 4: Sales Leak from Channel-Blind Growth
Hypothesis:
- Sales teams optimize for volume, not profitable demand; low-quality acquisition erodes contribution.

Test design:
- Type: channel-quality sales governance experiment.
- Horizon: 8 weeks.
- Introduce channel-level revenue quality scorecard into weekly sales planning.
- Scorecard dimensions: CAC, AOV, repeat, return-risk proxy, contribution proxy.

Primary KPIs:
- Contribution margin per customer
- Share of new customers from channels with LTV/CAC > 3
- EBITDA proxy trend in monthly merged table

Pass criteria:
- At least 15% increase in profitable-customer share
- Contribution margin per customer up at least 8%

Prediction:
- Sales quality mix shifts toward Organic/Search/Paid Social segments.
- EBITDA proxy margin improvement likely 1-3 points over 1 quarter if discipline is maintained.

## Test Execution Governance
- Weekly review: channel spend, CAC, new customers, LTV/CAC, contribution proxy.
- Bi-weekly decision rule: pause channels/tests missing pass criteria for 2 consecutive periods.
- Monthly board pack: include waterfall and margin-killer deltas using track_b_monthly_merged_table.csv.

## Structural Leak Summary (Sales + Marketing)
- Leak 1: Spend concentration in lowest-quality channel (Influencer).
- Leak 2: Growth measured by customer count, not channel-adjusted contribution.
- Leak 3: Missing fast budget reallocation loop based on marginal CAC and LTV/CAC.

## Board Message (Short Form)
- The margin problem is not a single cost line; it is a channel-allocation and quality-control failure.
- Rebalancing spend away from Influencer and enforcing contribution-based sales governance is the fastest path to margin recovery.
- First 90 days should focus on reallocations, strict test gates, and weekly operating rhythm.
