# loan-api-lab — Friday 4:45 PM: A Bad Release Reaches Production

**What you will practise:** handling a production incident the way a real on-call engineer does.

1. **Deploy** `prod` — the release that goes out looks fine: tests pass, pipeline green, `/health` OK.
2. **Incident** — brokers report wrong quotes. You confirm the impact.
3. **Restore first** — re-run the pipeline from **`main`** (the last reviewed, trusted code) to put production back. No debugging on the live service.
4. **Then fix properly** — reproduce locally, write a hotfix with regression tests, ship it through a Pull Request into `prod`, and bring `main` back in line.
5. **Prevent** — add an automatic post-deploy check so customers are never the first to find out.

## Business context
**loan-api** powers the repayment calculator brokers and customers use to quote loans (`GET /api/quote`).

| Branch | Meaning | On push |
|---|---|---|
| `main` | Reviewed, tested code — the source of truth | Tests only |
| `prod` | What is live | Tests, then **automatic deploy to production** |

At 4:45 PM on Friday, to hit a promotion deadline (0.5% off the interest rate for loans of $400,000 or more), the release manager merged **the promo PR straight into `prod`**. It is not in `main`. The pipeline is **green**. Ten minutes later, brokers call: *"The calculator is quoting repayments of hundreds of thousands of dollars a month."* You are the on-call engineer.

Endpoints: `/health`, `/version` (shows the running 7-character git SHA), `/api/quote`.
Reference request: `curl -s "http://<PROD_ALB_DNS>/api/quote?amount=500000&rate=6.5&years=30"`
Known-good result before the promo PR: `{"monthly_repayment":3160.34}`

## Rules (apply from the moment the incident starts)
1. Restore first, investigate second. Do not debug on the live service.
2. Freeze `prod`: nobody merges into it until the fix is out.
3. Not allowed: force-push, rewriting history, changing ECS or task definitions in the AWS console.
4. All code changes go through a Pull Request. Hotfix branches are named `hotfix/<description>`.

## Setup (before the incident — not part of the exercise)
1. **Fork** this repo. **Untick "Copy the `main` branch only"** — you need the `prod` branch. In your fork open the *Actions* tab and enable workflows.
2. Build the production environment with the Terraform in <https://github.com/eddiez0719/loan-api-lab-infra> (follow its README). It gives you `<PROD_ALB_DNS>` and the values for the GitHub Environment variables.
3. In your fork create the GitHub Environment **`production`** and add the variables from the Terraform output: `AWS_REGION`, `AWS_ROLE_ARN`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`, `BASE_URL`.
4. Replace `<ACCOUNT_ID>` in `.aws/task-definition.json` with your 12-digit AWS account id. Make this one small "setup" commit on **both** `main` and `prod` (same change). It is not part of the incident; ignore it when you read `git log main..prod` below.
5. **Start the incident:** Actions → `loan-api CI/CD` → *Run workflow* → **Use workflow from: `prod`**. Wait until it finishes. Production now runs the promo release. Note the time — your clock starts when you first see wrong quotes.
6. When the lesson is over, run `terraform destroy` (the environment costs money while it runs).

> Tip: `git diff main..prod` also shows README differences if you are reading this on a different branch. Use `git diff main..prod -- app.py tests/` to see only the code changes.

---

## LAB-1 – Stabilise production (target: under 10 minutes)
**As** the on-call engineer, **I want** production back on the last known good code, **so that** customers see correct quotes again.

- [ ] You confirmed the impact: recorded the HTTP status of `/health` and the `monthly_repayment` returned.
- [ ] You wrote one sentence explaining why `/health` and the pipeline both looked healthy.
- [ ] You proved `main` is clean and behind `prod`: `git log --oneline main..prod` shows only the promo PR's changes (plus your setup commit, if you made one); you noted the SHA of `main`.
- [ ] You restored production using **GitHub Actions only**: run `loan-api CI/CD` manually with **Use workflow from: `main`**. No console changes, no commits.
- [ ] `/version` returns the SHA of `main` and the reference request returns `3160.34`.
- [ ] You posted a stakeholder update and recorded time-to-recover.

Stakeholder update template:
```
[HH:MM] Incident update – loan-api
Impact:   repayment quotes incorrect since HH:MM
Action:   production redeployed from main (SHA xxxxxxx), the last reviewed release
Status:   recovered at HH:MM, monitoring
Note:     the prod branch still contains the faulty change – merge freeze in place
Next update: HH:MM
```

## LAB-2 – Find the root cause without touching production
**As** the on-call engineer, **I want** to reproduce the bug locally, **so that** I know which change caused it.

- [ ] You created `hotfix/quote-rate-calc` from the current **`prod`** branch.
- [ ] `git diff main..prod -- app.py tests/` shows the lines changed by the promo PR; you pasted them in your notes.
- [ ] You ran the app locally from your branch and reproduced the wrong quote.
- [ ] `make test` passes. You wrote 3 sentences: what broke, why tests and the pipeline did not catch it, and what the correct results should be.

## LAB-3 – Ship the hotfix through a Pull Request
**As** the on-call engineer, **I want** to fix `prod` through the normal pipeline, **so that** the promotion works and the branches match again.

Business rules (ticket LEND-231): loans of **$400,000 or more** get **0.5 percentage points** off the annual rate; smaller loans use the normal rate.

| Request | Expected `monthly_repayment` |
|---|---|
| `amount=500000&rate=6.5&years=30` (promo applies) | `2997.75` |
| `amount=300000&rate=6.5&years=30` (no promo) | `1896.2` |

- [ ] Bug fixed in `app.py` on `hotfix/quote-rate-calc`.
- [ ] Two pytest regression tests (one per table row) fail on the promo code and pass on your fix.
- [ ] PR into **`prod`**: title starts with `HOTFIX:`; description states impact, root cause, how you tested. The `test` job passes.
- [ ] After merge, the pipeline deploys automatically; `/version` returns the merge SHA and the reference request returns `2997.75`.
- [ ] A second PR merges `prod` into `main` so both branches match.
- [ ] You lifted the merge freeze.

## LAB-4 – Make sure customers are never the first to find out
**As** the platform team, **I want** every production deploy verified automatically, **so that** a wrong quote turns the pipeline red within minutes.

- [ ] New Makefile target `smoke` takes `BASE_URL`. It exits non-zero if `/health` fails, or if `/api/quote?amount=500000&rate=6.5&years=30` does not return `monthly_repayment` equal to `2997.75`.
- [ ] `ci-cd.yml` runs `make smoke` as the last step of the `deploy` job, using the GitHub environment variable `BASE_URL`.
- [ ] Proof: `make smoke` failed against a local container built from the promo (faulty) code (paste the output).
- [ ] Delivered by a PR into `prod` and deployed by the pipeline.

**Bonus:** In 3 sentences, explain why it is risky that `prod` was ahead of `main`. Propose one team rule and name the GitHub setting that enforces it.

## LAB-5 – Post-incident review (one page)
Timeline with timestamps, customer impact, root cause, why tests and the pipeline did not catch it, what went well, and **3 action items with an owner and due date**.

## Deliverables
1. Run URLs: the bad deploy (step 5 of Setup), the redeploy from `main`, the hotfix deploy
2. Links to the hotfix PR, the `prod` → `main` PR, and the smoke-test PR
3. Reproduction evidence (diff lines, wrong quote output)
4. Stakeholder update text
5. Post-incident review
