# Counterfactual plan for targeting strategy

## Why the current files cannot identify lift

The supplied `daily_targeting.csv` contains target records, recommended channels, priority, status and campaign IDs. It does not identify randomized treatment/control assignment, a stable exposure log for every strategy, intervention costs, or a reliable month-opening eligible-balance denominator. A payment occurring within seven days after a targeting event is only a temporal association. It is not proof that the touch caused the payment. Accounts can receive multiple contacts, and treatment choice may reflect risk/DPD or agent judgment.

## Recommended pilot

1. **Population:** define eligible accounts before assignment, excluding legal holds, active disputes, invalid contacts and policy-restricted cases. Freeze eligibility before randomization.
2. **Stratification:** randomize within DPD band, risk segment, loan type, current status, balance band and prior-contact intensity. Randomize at account level; if treatments can spill across linked accounts, randomize at borrower level instead.
3. **Arms:** current business-as-usual strategy vs. candidate strategy. Keep all other policies equal. Use a persistent assignment table and log every delivered/attempted treatment.
4. **Primary outcome:** net cash recovered per eligible account within a prespecified 30-day window, after refunds/reversals and with one approved payment-ledger definition. Report both amount and recovery rate using month-opening eligible balance.
5. **Guardrails:** complaints, harassment complaints, wrong-party contacts, opt-outs, cost per incremental rupee, promise-to-pay breakage, and operational capacity.
6. **Analysis:** intent-to-treat difference in mean net recovery per eligible account, with confidence interval and stratified estimates. Pre-register exclusions, missing-data rules, stopping rules and multiplicity policy. Do not switch to per-protocol results because they look better.
7. **Decision rule:** scale only if the lower confidence bound for incremental net benefit clears the approved hurdle and all customer-protection guardrails pass. Finance must provide intervention cost, funding cost and risk-adjustment assumptions before ROI or break-even is calculated.

## Investment choice and planning scenario (assumptions, not observed causal results)

**Leading area to test: better borrower targeting.** It is selected as the first hypothesis because it is testable with an account-level randomized holdout and can prioritize existing collection capacity. The observational channel table is not evidence that targeting has already won.

The reproducible scenario model is `src/investment_business_case.py`; its outputs are `data/processed/investment_roi_scenarios.csv` and `reports/investment_business_case.html`.

- Baseline: mean recovered cash in seven completed months, annualized by multiplying by 12; this is a planning proxy, not a forecast.
- Targetable cash share assumption: 70%.
- Incremental lift scenarios: 5% downside, 10% base, 15% upside.
- Economic-benefit realization factor: 85% assumption to haircut gross incremental cash for displacement/timing/variable-cost uncertainty.
- Total investment: ₹10 Cr; illustrative allocation is in the business-case report.
- Base scenario: about ₹12.79 Cr gross incremental recovery; ₹10.87 Cr realized economic benefit; ₹0.87 Cr net benefit after investment; 8.7% planning ROI.
- Downside/base/upside planning ROI: approximately −45.7% / +8.7% / +63.0%.
- Break-even: approximately ₹11.76 Cr gross incremental recovery, or 9.19% lift on the assumed targetable cash base.

These are sensitivity scenarios, not a measured causal effect, probability-weighted forecast, statistical confidence interval, or audited ROI. Replace all assumptions with Finance-approved inputs and randomized pilot estimates before release.

## Causal identification and actual ROI measurement

Randomize eligible accounts 50/50 to current business-as-usual vs. targeting treatment, stratified by DPD, risk, loan type, balance band and prior-contact intensity. Freeze eligibility before assignment; use borrower-level assignment if linked accounts create spillover. Analyze intent-to-treat with 30-day net cash per eligible account after reversals/refunds. Record per-arm operating costs and report treatment-minus-control effect with a 95% confidence interval. The existing observational dataset cannot identify this effect; causal lift is **not yet measured**.

Scale only if the lower 95% confidence bound on net benefit is positive, the approved ROI hurdle is met, and complaints, opt-outs, wrong-party contact, PTP breakage and fairness guardrails pass.


## Sample-size and uncertainty plan (must be completed before launch)

The supplied observational data do not provide a valid randomized treatment effect or a reliable variance estimate for the prespecified 30-day outcome. Therefore this package intentionally does **not** claim a powered sample size. Before randomization:

1. Use a blinded historical/initial baseline sample to estimate the standard deviation (σ) of 30-day net cash per eligible account and its zero-payment mass; validate the outcome distribution and heavy-tail handling.
2. Finance and Collections must define the minimum economically meaningful treatment-control difference (δ) per eligible account from the approved investment hurdle.
3. For a two-arm, two-sided 5% test with 80% power and a continuous outcome, an initial equal-arm approximation is `n_per_arm ≈ 2 × (z(0.975) + z(0.80))² × σ² / δ²`. Use simulation/bootstrap or a suitable robust method if the cash distribution is highly skewed or zero-inflated.
4. Inflate for expected missing outcome records, borrower/account clustering and treatment contamination. Pre-register the final calculation and stopping rule; do not repeatedly peek without a sequential-testing plan.
5. Report the intention-to-treat difference, 95% confidence interval, net ROI confidence interval and guardrail intervals. A positive point estimate alone is not sufficient for scale.

This makes the experiment design operationally testable while honestly leaving the numeric sample size pending the missing variance, minimum detectable effect and Finance cost assumptions.
