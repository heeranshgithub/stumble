# Guard bake-off: Jev vs openai/gpt-oss-safeguard-20b (reasoning effort medium)

Same 96 learner lines and 12 replies, same scene context, a policy generated from the same questions and boundary cases. Jev's numbers are its stored classifier runs (v2, heldout, unnamed, unnamed-heldout).

| | Jev (jev-1.13.0) | gpt-oss-safeguard-20b |
|---|---|---|
| Every learner line, action as the policy says | 96 of 96 | 96 of 96 |
| Harmful lines blocked | 37 of 37 | 37 of 37 |
| Distress sent to support | 6 of 6 | 6 of 6 |
| Clean lines wrongly stopped | 0 of 40 | 0 of 40 |
| Replies judged right | 12 of 12 | 12 of 12 |
| Latency per call, median / p90 | 349 / 581 ms | 363 / 803 ms |
| Cost of both checks, per thousand turns | about $0.085 | about $0.248 |

Tokens per learner-line check: 1020 in, 246 out (reasoning included). Actions: {'block': 37, 'support': 6, 'deflect': 6, 'ignore': 6, 'pass': 46, 'replace': 7}

## Where they differ

| Case | Expect | Jev | Safeguard | Safeguard's reason |
|---|---|---|---|---|
