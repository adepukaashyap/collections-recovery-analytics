# Executive memo — Collections recovery claim

**Decision: do not certify the “11% month-on-month recovery improvement” claim yet.** The supplied synthetic dataset supports a descriptive analysis of observed successful payment amounts, but it does not establish a denominator-consistent recovery rate or provide 12 complete months.

## What the supplied data says

- Raw accounts: **30,000**; canonical account IDs: **30,000**.
- Raw payment rows: **25,500**; canonical payment events after event-ID and transaction-reference handling: **21,189**.
- Effective successful payment events under the stated final-status rule: **14,840**.
- Effective recovered amount across the observed period: **₹1,112,566,691**.
- Payment timestamps run from **2026-01-01** through **2026-08-08**. The last observed month (**2026-08**) is partial and is excluded from completed-month MoM comparisons.
- Mean completed-month amount growth: **5.09%**; median: **5.61%**. These are amount-growth descriptors, not recovery-rate growth.
- Month-to-month recovered-amount changes across the six completed comparisons range from **−4.40% to +15.75%**. July was **+11.33%** versus June, but only **one of six** comparisons fell between +10% and +12%; the pattern is not a steady 11% improvement.

## Why the 11% claim is not validated

1. The provided data spans less than the requested ~12 months and the final month is partial.
2. `accounts.csv` provides an account snapshot, not historical month-opening eligible balances. Reusing its current outstanding balance as the historical denominator would create false precision.
3. Payment references repeat and some are missing; event status can change. The pipeline keeps the latest event per reference (missing references use payment_id), prefers a populated reference when duplicate payment IDs have identical timestamps, and counts only final `SUCCESS` events. Same-timestamp conflicts in business fields still need an authoritative source event ID or Finance-approved rule. This rule is auditable but must be reconciled to the source payment ledger before production use.
4. Attribution to calls, SMS, WhatsApp, field visits or targeting cannot be inferred causally from simple temporal proximity. The included channel/segment tables are descriptive only.
5. Mix-adjusted results, cohort maturity and counterfactual lift need a stable historical denominator, treatment assignment/exposure and outcome window. The dataset contains targeting records but no randomized holdout flag.

## Recommendation on ₹10 Cr investment

**Leading investment hypothesis: better borrower targeting, with staged funding and a randomized pilot gate.** The assignment requires a single area; this is the recommended area to test first because it can be evaluated cleanly against business-as-usual and may improve prioritization without presuming one channel is already superior. Observational channel associations do not establish that it wins causally.

A transparent planning model uses seven completed months' mean recovered cash, simply annualized; assumes 70% targetable cash, 5% / 10% / 15% incremental lift scenarios, an 85% economic-benefit realization factor, and ₹10 Cr total investment. These assumptions are not observed facts. The model yields:

- **Downside:** ₹6.39 Cr gross incremental recovery; ₹5.43 Cr realized benefit; −45.7% planning ROI.
- **Base case:** ₹12.79 Cr gross incremental recovery; ₹10.87 Cr realized benefit; ₹0.87 Cr net benefit after investment; **8.7% planning ROI**.
- **Upside:** ₹19.18 Cr gross incremental recovery; ₹16.30 Cr realized benefit; +63.0% planning ROI.
- **Break-even:** approximately ₹11.76 Cr gross incremental recovery, equal to about 9.19% lift on the assumed targetable cash base.

This is an **assumption-based scenario range**, not a measured causal forecast or statistical confidence interval. It is provided to make the assumptions and hurdle explicit—not to certify a return. The 70% targetable share, 85% realization factor, lift, intervention costs and baseline representativeness must be approved/replaced by Finance and validated in a pilot. The illustrative ₹10 Cr allocation is documented in `reports/investment_business_case.html`.

### Counterfactual design to establish actual ROI

1. Freeze eligible accounts and exclusions before assignment.
2. Randomize 50/50 to current strategy vs. targeting, stratified by DPD, risk, loan type, balance band and prior-contact intensity.
3. Measure 30-day net cash per eligible account after refunds/reversals; analyze by intent-to-treat.
4. Capture platform, channel, agent-time, vendor and support costs by arm.
5. Report treatment-minus-control effect with a 95% confidence interval, economic ROI, and complaint/opt-out/wrong-party/PTP-breakage guardrails.
6. Release the remaining investment only if the lower 95% confidence bound on net benefit is positive and the approved ROI/customer-protection gates pass.

The dashboard links to the complete scenario table, illustrative allocation, break-even formula and experiment plan. The full investment should remain gated until the actual randomized effect and Finance-approved economics are available.

**Confidence:** High that the provided files alone do not substantiate a denominator-consistent 11% recovery-rate claim; low for any causal strategy ranking or investment ROI until historical balances and experiment data are available.
