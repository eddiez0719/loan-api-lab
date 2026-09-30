# loan-api-lab — Friday 4:45 PM: A Bad Release Reaches Production

**loan-api** powers the repayment calculator brokers and customers use to quote loans (`GET /api/quote`).

| Branch | Meaning | On push |
|---|---|---|
| `main` | Reviewed, tested code | Tests only |
| `prod` | What is live | Tests, then **automatic deploy to production** |

At 4:45 PM on Friday, to hit a promotion deadline (0.5% off the interest rate for loans of $400,000 or more), the release manager merged **PR #142 straight into `prod`** (the promo PR, merged with `Merge pull request ... from feature/promo-rate`). It is not in `main`. The pipeline is **green**. Ten minutes later, brokers call: *"The calculator is quoting repayments of hundreds of thousands of dollars a month."* You are the on-call engineer.

Endpoints: `/health`, `/version` (running 7-character git SHA), `/api/quote`.
Known-good result before the promo PR: `curl -s "http://<PROD_ALB_DNS>/api/quote?amount=500000&rate=6.5&years=30"` → `{"monthly_repayment":3160.34}`

## Rules
1. Restore first, investigate second. Do not debug on the live service.
2. Freeze `prod`: nobody merges into it until the fix is out.
3. Not allowed: force-push, rewriting history, changing ECS or task definitions in the AWS console.
4. All code changes go through a Pull Request. Hotfix branches are named `hotfix/<description>`.

## Repository variables (Settings → Environments → `production`)
`AWS_ROLE_ARN`, `AWS_REGION`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`, and (LAB-4) `BASE_URL`. Edit `.aws/task-definition.json` (`<ACCOUNT_ID>`) for your account.

---

## LAB-1 – Stabilise production (target: under 10 minutes)
- [ ] Confirm the impact: record the HTTP status of `/health` and the `monthly_repayment` returned.
- [ ] One sentence: why `/health` and the pipeline both looked healthy.
- [ ] Prove `main` is clean and behind `prod`: `git log --oneline main..prod` shows only PR #142's changes; note the SHA of `main`.
- [ ] Restore production using **GitHub Actions only**: run `loan-api CI/CD` manually with **Use workflow from: `main`**. No console changes, no commits.
- [ ] `/version` returns the SHA of `main` and the reference request returns `3160.34`.
- [ ] Post a stakeholder update and record time-to-recover.

```
[HH:MM] Incident update – loan-api
Impact:   repayment quotes incorrect since HH:MM
Action:   production redeployed from main (SHA xxxxxxx), the last reviewed release
Status:   recovered at HH:MM, monitoring
Note:     the prod branch still contains the faulty change – merge freeze in place
Next update: HH:MM
```

## LAB-2 – Find the root cause without touching production
- [ ] Create `hotfix/quote-rate-calc` from the current **`prod`** branch.
- [ ] `git diff main..prod` shows the lines changed by PR #142; paste them in your notes.
- [ ] Run the app locally from your branch and reproduce the wrong quote.
- [ ] `make test` passes. Write 3 sentences: what broke, why tests and the pipeline did not catch it, and what the correct results should be.

## LAB-3 – Ship the hotfix through a Pull Request
Business rules (ticket LEND-231): loans of **$400,000 or more** get **0.5 percentage points** off the annual rate; smaller loans use the normal rate.

| Request | Expected `monthly_repayment` |
|---|---|
| `amount=500000&rate=6.5&years=30` (promo applies) | `2997.75` |
| `amount=300000&rate=6.5&years=30` (no promo) | `1896.2` |

- [ ] Bug fixed in `app.py` on `hotfix/quote-rate-calc`.
- [ ] Two pytest regression tests (one per table row) fail on the PR #142 code and pass on your fix.
- [ ] PR into **`prod`**: title starts with `HOTFIX:`; description states impact, root cause, how you tested. The `test` job passes.
- [ ] After merge, the pipeline deploys automatically; `/version` returns the merge SHA and the reference request returns `2997.75`.
- [ ] A second PR merges `prod` into `main` so both branches match.
- [ ] Lift the merge freeze.

## LAB-4 – Make sure customers are never the first to find out
- [ ] New Makefile target `smoke` takes `BASE_URL`. It exits non-zero if `/health` fails, or if `/api/quote?amount=500000&rate=6.5&years=30` does not return `monthly_repayment` equal to `2997.75`.
- [ ] `ci-cd.yml` runs `make smoke` as the last step of the `deploy` job, using the GitHub environment variable `BASE_URL`.
- [ ] Proof: `make smoke` failed against a local container built from the PR #142 code (paste the output).
- [ ] Delivered by a PR into `prod` and deployed by the pipeline.

**Bonus:** In 3 sentences, explain why it is risky that `prod` was ahead of `main`. Propose one team rule and name the GitHub setting that enforces it.

## LAB-5 – Post-incident review (one page)
Timeline with timestamps, customer impact, root cause, why tests and the pipeline did not catch it, what went well, and **3 action items with an owner and due date**.

## Deliverables
1. Run URLs: the bad deploy, the redeploy from `main`, the hotfix deploy
2. Links to the hotfix PR, the `prod` → `main` PR, and the smoke-test PR
3. Reproduction evidence (`git diff main..prod` lines, wrong quote output)
4. Stakeholder update text
5. Post-incident review
