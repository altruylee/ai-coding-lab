# Experiment 007 — Prompt-context comparison campaign

## Question

On Task 002, does including public test descriptions change the observed result
relative to supplying the task specification alone?

## Configurations

- **public-test-descriptions** — task requirements plus descriptions of all
  public tests.
- **spec-only** — the same task requirements without test descriptions.

Both configurations used isolated Codex sub-agents with no inherited
conversation, no follow-up prompts, zero human interventions, and the same
no-tool/no-reference policy. Each configuration has two recorded attempts.

## Reproduce

```bash
python -m benchmarks.campaigns \
  --campaign benchmark_runs/campaigns/task002-prompt-context-001/campaign.json \
  --output experiments/007-prompt-context-campaign/results.json \
  --repo-root . \
  --verify
```

## Observed results

| Configuration | Solved | Eligible | Elapsed values | Median |
| --- | ---: | ---: | --- | ---: |
| public-test-descriptions | 2/2 | 2/2 | 195,648 ms; 149,231 ms | 172,439.5 ms |
| spec-only | 2/2 | 2/2 | 169,795 ms; 163,629 ms | 166,712 ms |

All four candidates passed the public checks without correction.

## Interpretation

Within this four-run sample, removing the public test descriptions did not
change task success. The median wall-clock difference is too small and the
sample too limited to support a performance conclusion.

## Limitations

- Two attempts per configuration are not enough to estimate a stable success
  rate or latency distribution.
- The exact model deployment, token usage, and cost were unavailable.
- Tests were public for configuration A and withheld by prompt for
  configuration B; there was no separate hidden suite.
- No-tool and no-reference boundaries were prompt-enforced and attested, not
  container-enforced.
- Wall-clock measurements include scheduling and orchestration overhead.
- All attempts used the same disclosed model family, so this is a prompt
  context comparison, not a cross-model comparison.
