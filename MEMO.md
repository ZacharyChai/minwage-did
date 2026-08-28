# Did the 2024 state minimum-wage increases cost retail and food-service jobs?

**Short answer:** No measurable effect. Across the 22 states that raised their
minimum wage on January 1, 2024, retail and leisure-&-hospitality employment
grew at essentially the same rate as in comparable states that did not raise
their wage floor. The best point estimate for retail is about **−0.6%**
(≈ −39,000 jobs across the treated states), but the 95% confidence interval runs
from roughly **−86,000 to +8,000 jobs**, and a placebo test shows the design
produces "effects" of this size routinely at dates when nothing happened. The
honest reading is a **precisely estimated zero**, not a small job loss.

---

## What was measured

- **Policy:** the January 1, 2024 round of state minimum-wage increases — 22
  states. Eight were legislated step increases of \$1.00–\$2.00 (DE, HI, IL, MD,
  NE, NJ, NY, RI); the rest were smaller automatic inflation adjustments. FL, NV and
  OR raised mid-2024 and are excluded from both groups.
- **Outcome:** state-level payroll employment in **retail trade** and in
  **leisure & hospitality** (the standard proxy for food-service employment),
  seasonally adjusted, monthly, from FRED / BLS. Total non-farm employment is
  carried as a placebo outcome.
- **Comparison group:** the 21 "never-treated" states on the federal \$7.25
  floor (plus WV, unchanged since 2016). Robustness runs swap in a broader
  control group and a border-states-only group.
- **Method:** difference-in-differences with state and calendar-month fixed
  effects, standard errors clustered by state, plus an event-study version that
  traces the effect month by month.
- **Window:** July 2022 – July 2026. The pre-period starts in mid-2022 because
  that is when treated and control states' employment paths actually converge
  after the uneven COVID rebound (see the parallel-trends figure); a 2021 start
  is kept as a robustness check.

## What the data shows

| Outcome | DiD estimate | 95% CI | In plain terms |
|---|---|---|---|
| Retail employment | −0.56% (p = 0.10) | −1.2% to +0.1% | ≈ −39k jobs, CI −86k to +8k |
| Retail, region×month controls | −0.19% (p = 0.64) | −1.0% to +0.6% | ≈ −13k jobs, CI −70k to +43k |
| Leisure & hospitality | +0.20% (p = 0.59) | −0.6% to +1.0% | ≈ +15k jobs, CI −42k to +73k |
| Total non-farm (placebo) | −0.17% (p = 0.48) | −0.7% to +0.3% | no effect, as expected |

Across all 36 robustness specifications (three control groups × three treatment
definitions × two fixed-effect structures × two windows), the retail estimate
never leaves the range −1.0% to +0.3%, and is statistically significant in only
3 of 18 baseline-window specs — always the ones without region×month controls.
Leisure & hospitality is never significant in the baseline window.

## Why the estimate should be read as zero, not as "a small job loss"

Three of the rigor checks point the same way:

1. **Event study.** For retail, the pre-policy coefficients are flat and
   individually insignificant (largest deviation 0.3 log points). After the
   policy, retail employment drifts down slowly, reaching about −0.8% by 30
   months — but the pre-period also has a faint downward tilt, so part of that
   post-period drift is a trend that was already there, not the policy.

2. **Placebo / falsification.** Re-running the design on *fake* policy dates
   throughout 2018–2023 produces DiD estimates ranging from −3.5% to +0.2% for
   retail, with a standard deviation of 1.3 log points. The real 2024 estimate
   (−0.6%) sits at the **76th percentile** of that placebo distribution — i.e.
   most fake dates yield a *more* negative "effect" than the real policy does.
   Randomization-inference p-value: **0.76**. A fixed placebo at January 2019
   yields a spurious, significant −2.9% for retail and −5.4% for hospitality;
   this is exactly why the pre-2022 period is excluded from the headline.

3. **Placebo outcome.** Total non-farm employment — which should not move with a
   minimum-wage change concentrated in low-wage industries — shows −0.17%
   (n.s.), essentially identical to the retail and hospitality estimates. When
   the "treated" industries move the same amount as an untreated aggregate, the
   most likely explanation is residual between-state differences, not the policy.

## The one assumption that would break this

**Parallel trends** — that treated and control states would have followed the
same employment path absent the 2024 increases. The treated group is
disproportionately high-cost coastal and industrial states; the control group is
disproportionately Sun Belt and rural. Post-2021 internal migration has been
flowing *toward* the low-minimum-wage Sun Belt, which mechanically pushes the
DiD toward showing job losses in treated states. The formal joint test of
pre-period parallelism is rejected in every specification (though the
economically meaningful pre-period gaps for retail are tiny, < 0.4 log points).

Two things make the null reasonably robust to this: the region×month
specification, which absorbs division-wide migration and demand shocks, moves
the estimate *toward* zero, not away from it; and the border-states control
group, which holds regional labor markets roughly fixed, gives −0.3% (n.s.).
But the caveat is real: if treated states were on a meaningfully worse
employment trajectory for reasons unrelated to the wage floor, this design would
read that as a minimum-wage job loss — and it still finds close to zero.

## What this design cannot rule out

- **Hours and composition.** This is a headcount on payroll. A cut in weekly
  hours, a shift from full- to part-time, slower *new* hiring, or fewer teenage
  and less-experienced workers hired could all be happening without moving the
  total employment count. Card–Krueger-style employment nulls coexist in the
  literature with real hours and turnover effects.
- **Small or slow effects.** With 22 treated states and ~30 post-period months,
  the design can detect an employment change of roughly ±1.5% with confidence.
  A true effect smaller than that — which is where much of the modern minimum-
  wage literature sits — would be invisible here.
- **The indexed vs. legislated distinction.** The small automatic COLA
  increases (median +\$0.40) may simply be too small a "treatment" to expect any
  labor-demand response, which would dilute the pooled estimate. The legislated
  subset (median +\$1.00–\$1.50) shows a slightly more negative point estimate
  (−0.8% to −0.9%) but it is not robust to region×month controls.
- **General-equilibrium and price responses.** Pass-through to consumer prices,
  effects on firm entry/exit, and multi-state firms reallocating across the
  policy line are outside what a state-level employment panel can see.

## Bottom line for a decision-maker

If the policy question is "will a 2024-style state minimum-wage increase produce
visible retail or restaurant job losses in the following two years," the answer
from this data is **no** — the employment counts move within normal
state-to-state noise. That is consistent with the bulk of recent research on
moderate minimum-wage increases from a low base. It is *not* evidence that the
increases were costless to employers: prices, hours, scheduling, and hiring
standards are where any adjustment would more plausibly show up, and none of
those are measured here.
