# Synthetic GitHub Activity Experiment

> **This repository intentionally generates synthetic commits. It should not
> be presented as evidence of real engineering work. Its purpose is to
> demonstrate that contribution counts are easy to automate and should not be
> treated as a meaningful measure of developer quality.**

Every event, data entry, commit message, workflow name, and Git identity in
this repository is deliberately labeled as automated or synthetic. This is a
small measurement experiment, not a software product and not real development
activity.

## Why this exists

GitHub contribution graphs show counts and timing, not the difficulty, value,
or quality of the underlying work. A short workflow can manufacture many
valid commits without creating a feature, helping a user, reviewing a design,
or solving a meaningful problem. The resulting squares may look active while
communicating almost nothing about engineering ability.

A strong developer profile is better evaluated through:

- project quality and real outcomes;
- code clarity, documentation, and testing;
- sound technical decisions and trade-offs;
- collaboration;
- issue and pull-request quality.

## How the experiment works

At `00:17 UTC` each day, one GitHub Actions job:

1. targets the previous completed UTC day;
2. randomly chooses an integer from 0 through 10;
3. generates that many unique, sorted timestamps and explicit synthetic event
   records using only the Python standard library;
4. appends one event to [`data/activity_log.jsonl`](data/activity_log.jsonl)
   per commit;
5. sets `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` to the event timestamp; and
6. pushes all new commits to the default branch in one network operation.

Using yesterday avoids creating commits dated in the future. GitHub schedules
can be delayed, so running at the end of a day is less robust than processing a
day that has fully completed. This approach randomizes recorded commit times;
it does not pretend the workflow actually ran at each time and does not keep a
runner alive with long sleeps.

The generator writes a temporary JSONL plan and prints a JSON summary for the
workflow. The workflow then appends each planned line to the persistent log,
creating a real file change for every commit. A selection of zero is a normal,
successful no-op.

## Repository layout

```text
.
├── .github/workflows/
│   ├── generate-activity.yml
│   └── tests.yml
├── data/activity_log.jsonl
├── scripts/generate_activity.py
├── tests/test_generate_activity.py
├── .gitignore
├── LICENSE
└── README.md
```

## Setup

1. Create a **public** GitHub repository with a transparent name such as
   `synthetic-github-activity`. Do not initialize it with generated files.
2. Add this project, commit it, and push it to the repository's default branch.
3. In **Settings → Actions → General → Workflow permissions**, select
   **Read and write permissions**, then save. The workflow also declares the
   narrower `contents: write` permission explicitly.
4. Open the **Actions** tab and enable workflows if GitHub asks.
5. Select **Generate clearly synthetic activity** and use **Run workflow** for
   an immediate manual test, or wait for the daily schedule.

The built-in `GITHUB_TOKEN` is used automatically. No personal access token,
API key, server, paid service, locally running computer, or second repository
is needed.

Branch protection or repository rules may reject direct pushes from
`github-actions[bot]`. For this isolated demonstration, either allow that bot
to push to the default branch or leave the scheduled workflow disabled. Do not
weaken protections on a real project merely to run this experiment.

## Manual use

From the workflow's **Run workflow** menu, optional inputs can select a
completed UTC date, fixed minimum and maximum counts, and a deterministic
integer seed. Leave the date blank to use yesterday. For example, setting both
counts to `3` always creates three events; setting both to `0` tests the
successful no-op path.

The generator can also be exercised locally without making Git commits:

```bash
python scripts/generate_activity.py \
  --date 2026-07-22 \
  --min-commits 0 \
  --max-commits 10 \
  --output /tmp/synthetic-events.jsonl \
  --seed 42
```

It requires Python 3.11 or newer and no third-party packages. Run the tests
with:

```bash
python -m unittest discover -s tests -v
```

## Git timestamps and contribution-graph limitations

Git stores author and committer timestamps in commit objects. This experiment
sets both timestamps to an artificial event time, so a later workflow run can
create commits whose metadata falls on the previous day. The commit objects
are still created and pushed together during the workflow run.

Whether GitHub displays a commit as a profile contribution depends on GitHub's
rules, including:

- the commit email must be associated with the profile being credited;
- the repository must be standalone rather than a fork;
- commits generally need to be on the repository's default branch (or another
  qualifying branch);
- repository visibility and the user's profile privacy settings affect what
  other people can see;
- scheduled workflows run only from the default branch and can be delayed or
  disabled by GitHub;
- repository rules can prevent the workflow from pushing.

GitHub deliberately does not start another workflow run from a push
authenticated with the built-in `GITHUB_TOKEN`. Consequently, synthetic log
commits do not recursively launch `tests.yml`; ordinary pushes and pull
requests still do. Qualifying contributions can also take time to appear on a
profile.

This project intentionally uses the clearly identified
`github-actions[bot]` name and noreply email. It does not impersonate the
repository owner, so its commits should not be presented as that person's
work. Changing the email to one associated with a personal account could
alter attribution, but doing so would undermine the transparency and ethics of
this demonstration.

For private repositories, GitHub users can choose to show anonymized private
contribution counts from their profile's **Contribution settings → Private
contributions**. This demonstration should remain public so reviewers can see
exactly how the activity was generated.

## Disabling the experiment

Disable **Generate clearly synthetic activity** from its page in the
repository's **Actions** tab, or delete
`.github/workflows/generate-activity.yml`. Existing commits remain in Git
history; disabling the workflow only stops new ones.

## Ethics and transparency

This repository demonstrates a weakness in a simplistic metric; it is not a
template for deceiving employers, clients, or collaborators. It never creates
fake issues, pull requests, reviews, releases, or collaborations, and it makes
no claims about features, fixes, customers, security, or production work.

Keep the repository public, keep the disclosure intact, and link to the
automation when discussing its graph. Contribution volume should be treated
as context at most—not as proof of competence, productivity, effort, or work
quality.
