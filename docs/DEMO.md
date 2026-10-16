# Live demo script — M10 (3 points)

The rubric asks you to **commit a change, watch the pipeline run, and see the
deployment update**. That is the whole DevOps loop in one minute: a developer's
edit becomes a tested, scanned, versioned artefact running in a cluster, with
no human touching a server.

Rehearse it once before you present. Total runtime: about 4 minutes, most of it
waiting for the pipeline.

---

## Before you start

Have these open in tabs:

1. The app — <http://localhost:8080>
2. GitHub Actions — <https://github.com/ChampDeepak/todo/actions>
3. A terminal in `/Users/deepak/sst/todo`
4. Grafana — <http://grafana.localtest.me:8080/d/taskr-app>

Confirm the cluster is alive:

```bash
kind export kubeconfig --name taskr
kubectl get pods -n taskr
```

---

## Step 1 — Make a visible change (15 seconds)

Edit the heading in `frontend/src/App.jsx` so the audience can see the change
land. Something unmistakable:

```bash
grep -n "Taskr" frontend/src/App.jsx | head -3
```

Change the visible title to e.g. `Taskr — live demo`.

**Say while doing it:** "This is an ordinary code change. I am not going to
touch a server, a registry, or the cluster by hand."

---

## Step 2 — Commit and push (15 seconds)

```bash
git add frontend/src/App.jsx
git commit -m "Change the app heading to demonstrate the deployment pipeline"
git push origin main
```

**Say:** "The push is the trigger. Nothing else starts this pipeline."

---

## Step 3 — Watch the pipeline (about 2–3 minutes)

Switch to the Actions tab. Narrate the gates as they go green:

| Job | What to say |
|---|---|
| **Lint and test** | "32 tests against a real PostgreSQL. If any fail, nothing below runs — no image is even built." |
| **Build frontend** | "Runs in parallel. Independent of the tests." |
| **Build, scan and push** | "Only reached because both gates passed. The image is built locally first, then Trivy scans it for HIGH and CRITICAL CVEs. It is pushed **only** if the scan passes." |

When it's green, show the tag:

```bash
gh run view --log | grep -oE 'ghcr\.io/champdeepak/todo-frontend:sha-[a-f0-9]+' | head -1
```

**Say:** "The tag is the commit SHA, not `latest`. The commit, the CI run, the
image and the pod about to run it all carry one identifier. That is what makes
a rollback a single command."

---

## Step 4 — Deploy the new image (about 45 seconds)

```bash
SHA=$(git rev-parse HEAD)
docker build -t todo-frontend:$SHA ./frontend
kind load docker-image todo-frontend:$SHA --name taskr
helm upgrade --install taskr ./helm --namespace taskr \
  --set frontend.image.tag=$SHA --wait
```

Watch the rollout replace pods one at a time:

```bash
kubectl get pods -n taskr -w
```

**Say:** "Two replicas, replaced one at a time. The readiness probe has to pass
before the old pod is removed, so the app keeps serving through the deploy."

Refresh <http://localhost:8080> — the new heading is live.

> **Note for the audience, and an honest one:** in a cloud cluster this step is
> `helm upgrade --set image.tag=<sha>` and nothing else — the cluster pulls
> straight from GHCR. We build and `kind load` here only because this is a
> local kind cluster with no registry credentials configured.

---

## Step 5 — Show the rollback (20 seconds)

This is the part that lands.

```bash
helm history taskr -n taskr
helm rollback taskr -n taskr
```

**Say:** "Because every image is tagged with its commit, going back is one
command. With `latest` there would be no previous version to go back to."

---

## Step 6 — Show it in monitoring (20 seconds)

Switch to Grafana. Point at the **request rate** panel and the **pods being
scraped** stat.

**Say:** "Both replicas are being scraped individually. During that rollout the
scraped-pod count dipped and recovered — that is the deploy, visible in
metrics."

---

## Questions you should expect, with the honest answer

| Question | Answer |
|---|---|
| "Why is the database inside the cluster?" | It shouldn't be. Production uses RDS so backups, failover and patching are managed. This is a demo shortcut, and it's listed in the README. |
| "Why are migrations in the entrypoint?" | Simplicity. At scale it's a separate Job that must complete before the Deployment rolls, so N replicas don't race. |
| "Why public subnets for EKS?" | A NAT Gateway costs ~$32/month and adds minutes to apply and destroy. Security groups do the access control. Production uses private subnets. |
| "Where is Terraform state?" | Local, tonight. Production uses S3 with a DynamoDB lock so two engineers can't corrupt it. |
| "Did Trivy actually find anything?" | Yes — 43 HIGH/CRITICAL in `nginx:1.27-alpine`, including CVE-2026-31789 (critical OpenSSL heap overflow). The pipeline blocked the push; we moved to `nginx:1.29-alpine`. |

---

## After the demo — do not skip this

```bash
cd terraform && AWS_PROFILE=project terraform destroy
```

EKS bills $0.10/hour for the control plane alone, whether or not you use it.
