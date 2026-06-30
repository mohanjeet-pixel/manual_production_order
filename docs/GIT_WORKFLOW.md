# Git Workflow — end to end

Repo: `https://github.com/mohanjeet-pixel/manual_production_order.git`

---

## ⚠️ READ FIRST — leaked credentials

The file `.env` (containing a **real Gmail app password** and SAP password) was
committed in earlier history and pushed to GitHub. Removing it now stops *future*
leaks but the old commits still contain it on GitHub.

**Do these two things before anything else:**

1. **Rotate the exposed credentials now** — treat them as public:
   - Revoke the Gmail app password (`EMAIL=kaliraj.b@bullmachine.com`) at
     https://myaccount.google.com/apppasswords and generate a new one.
   - Change the SAP password (`SAP_PASSWORD`).
   - Put the new values in your local `.env` only.
2. **Scrub `.env` from history** (Section 4) so the secret is gone from GitHub,
   then force-push.

If you skip step 2, anyone with repo access can read the old secret in history.

---

## 1. One-time setup (per machine)

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@bullmachine.com"
```

If cloning fresh:

```bash
git clone https://github.com/mohanjeet-pixel/manual_production_order.git
cd manual_production_order
```

GitHub no longer accepts account passwords over HTTPS — when prompted, use a
**Personal Access Token** (https://github.com/settings/tokens) as the password,
or set up SSH keys.

---

## 2. Pre-push safety check (always)

Confirm secrets and junk are NOT staged:

```bash
git status                       # review what will be committed
git check-ignore .env            # must print ".env"  (i.e. it's ignored)
git ls-files | grep -E "\.env$|node_modules"   # must print NOTHING
```

If `.env` still shows as tracked, run once:

```bash
git rm --cached .env
git rm -r --cached frontend/node_modules
```

(These are already done in the current working tree.)

---

## 3. Normal change → push cycle

Work on a branch, not directly on `main`:

```bash
# 1. start from an up-to-date main
git checkout main
git pull origin main

# 2. create a feature branch
git checkout -b feature/short-description

# 3. make changes, then stage + review
git add -A
git status
git diff --cached            # read exactly what you're committing

# 4. commit
git commit -m "Short summary of the change"

# 5. push the branch
git push -u origin feature/short-description
```

Then open a Pull Request on GitHub (`Compare & pull request`), review, and
**Merge** into `main`. After merge:

```bash
git checkout main
git pull origin main
git branch -d feature/short-description
```

### Quick path (small solo project, push straight to main)

```bash
git add -A
git commit -m "Make app production-ready: env config, DB bootstrap, docs"
git push origin main
```

---

## 4. Scrub the leaked `.env` from history (do once)

This rewrites history to remove `.env` from **every** commit. Coordinate with
anyone else using the repo — they must re-clone afterwards.

### Using git-filter-repo (recommended)

```bash
# install once
uv tool install git-filter-repo        # or: pip install git-filter-repo

# from the repo root, with a clean working tree
git filter-repo --path .env --invert-paths --force

# filter-repo removes the remote; re-add and force-push
git remote add origin https://github.com/mohanjeet-pixel/manual_production_order.git
git push origin --force --all
git push origin --force --tags
```

### Alternative: BFG Repo-Cleaner

```bash
bfg --delete-files .env
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push origin --force --all
```

After scrubbing:
- The secret is removed from future clones of the repo.
- **It may still exist in GitHub caches / forks / anyone's old clone** — which is
  exactly why rotating the credentials (top of this doc) is mandatory, not
  optional.

---

## 5. Commit hygiene

Before each commit:

- `git diff --cached` — never commit something you haven't read.
- Never `git add .env`, `.venv/`, `frontend/node_modules/`, `frontend/dist/`,
  `logs/*.log` — all are git-ignored; keep them that way.
- Keep `.env.example` up to date when you add a new setting (but never put real
  values in it).

---

## 6. Handy commands

| Goal | Command |
|------|---------|
| See current branch / state | `git status` |
| Discard unstaged changes to a file | `git checkout -- path` |
| Unstage a file | `git restore --staged path` |
| Amend last commit message | `git commit --amend` |
| See recent history | `git log --oneline -10` |
| Update local main | `git checkout main && git pull origin main` |
| Throw away a bad local commit (keep changes) | `git reset --soft HEAD~1` |
