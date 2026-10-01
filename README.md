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

> **Cost:** the ALB and a Fargate task bill by the hour. Apply only during the lesson and always run `terraform destroy` afterwards.

**Prerequisites:** GitHub account; Git, Python 3.12+, curl, Docker; Terraform 1.5+; AWS CLI configured for the lab account (`aws sts get-caller-identity` works) with permission to create ECR, ECS, ALB, security groups and IAM roles in `ap-southeast-2`.

### Step 1 – Fork and clone
1. Click **Fork** on this repo. **Untick "Copy the `main` branch only"** — you need the `prod` branch.
2. In your fork open the *Actions* tab and enable workflows.
3. Ignore any branches named `archive-*` — they are leftovers from preparing the lab. You only need `main` and `prod`.
4. Clone your fork:
```
git clone https://github.com/<your-user>/loan-api-lab.git
cd loan-api-lab
git branch -r        # you must see origin/main and origin/prod
```

### Step 2 – Build production with Terraform (folder `terraform/`, on `main`)
```
git checkout main
cd terraform
terraform init
terraform apply -var github_repo=<your-user>/loan-api-lab
```
If your AWS account already has the GitHub OIDC provider and apply fails with "already exists":
```
terraform apply -var github_repo=<your-user>/loan-api-lab -var create_github_oidc_provider=false
```
Then collect the values:
```
terraform output prod_alb_dns
terraform output github_environment_variables
```

### Step 3 – Configure GitHub
In your fork: *Settings → Environments → New environment* → **`production`**. Under *Environment variables* (not secrets) add: `AWS_REGION`, `AWS_ROLE_ARN`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`, `BASE_URL` (from the Terraform output).

### Step 4 – Put your AWS account ID into the task definition
Get it with `aws sts get-caller-identity --query Account --output text`. In `.aws/task-definition.json` replace `<ACCOUNT_ID>` with it. Make the same small "setup" commit on **both** branches:
```
git checkout main
# edit .aws/task-definition.json
git commit -am "setup: account id" && git push origin main
git checkout prod
# make the same edit
git commit -am "setup: account id" && git push origin prod
```
It is not part of the incident; ignore these commits when you read `git log main..prod` below.

### Step 5 – Start the incident
Actions → `loan-api CI/CD` → *Run workflow* → **Use workflow from: `prod`**. Wait until it finishes. Production now runs the promo release. Note the time — your clock starts when you first see wrong quotes:
```
curl -s "http://<PROD_ALB_DNS>/api/quote?amount=500000&rate=6.5&years=30"
```
You are now the on-call engineer. Continue with LAB-1.

### When the lesson is over
Run `terraform destroy` in the `terraform/` folder with the same `-var` flags you used for apply.

> Tip: to see what the promo PR changed, use the three-dot diff `git diff main...prod` (changes on `prod` since it left `main`). The two-dot form also lists files that exist only on `main` (like `terraform/`).

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
- [ ] `git diff main...prod` shows the lines changed by the promo PR; you pasted them in your notes.
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
