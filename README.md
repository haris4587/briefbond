# BriefBond

**BriefBond is a digest-bound GenLayer creator campaign escrow.** A brand locks
a verified public brief and GEN payout, a creator submits an exact public post,
and AI-validator consensus releases, holds, reviews, or refunds the payout.

## v2 steward-request upgrade

The v2 source directly addresses the review request that stored hashes must
authenticate the evidence validators judged and that inaccessible evidence must
have a retry path before any irreversible refund.

- `open_campaign` fetches the public brief under consensus, recomputes SHA-256,
  and rejects funding if the bytes are inaccessible or do not match.
- Every post review records the declared digest, fetched-response digest, and
  rendered-screenshot digest.
- The jury sees only digest-authenticated evidence. A mismatch, oversized
  response, access failure, or render failure produces `EVIDENCE_REVIEW` and
  keeps the GEN locked.
- `retry_review(campaign_id)` lets either campaign party retry the same evidence
  during a protected review window.
- A first authenticated `INVALID` verdict produces `REVIEW_REQUIRED`; only a
  second consensus-confirmed `INVALID` verdict can refund before expiry.
- Validators independently re-fetch, re-render, reproduce the verdict, and
  compare the evidence digests and scorecard.

See the line-by-line [steward response](docs/STEWARD_RESPONSE.md) and the updated
[architecture](docs/ARCHITECTURE.md).

## Upgrade status

- **v2 contract source:** [`contracts/brief_bond.py`](contracts/brief_bond.py)
- **Automated checks:** GenVM lint passed; 8 contract tests passed; application
  lint, build, and 5 interface tests passed.
- **v2 Studionet deployment:** pending final deployment from GenLayer Studio.
- **v2 full-consensus proof:** pending after deployment.

The application deliberately uses the zero-address deployment placeholder until
the v2 address is available, preventing it from presenting the historical v1
contract as the upgraded implementation.

## Historical v1 proof

The earlier build remains useful as proof that BriefBond completed a real
end-to-end Studionet escrow settlement, but it does **not** claim the v2 evidence
protections above.

- **v1 contract:** [`0x3c38550CCF41685c1DF1d07A9823A70Df5998A91`](https://explorer-studio.genlayer.com/address/0x3c38550CCF41685c1DF1d07A9823A70Df5998A91)
- **Deployment transaction:** [`0x3cf7…3e27`](https://explorer-studio.genlayer.com/tx/0x3cf79baa1d99cfd3f43558bf036f39ccb558201badf035127faddba7717a3e27)
- **Funded escrow:** [`0x7b10…5614`](https://explorer-studio.genlayer.com/tx/0x7b1091428a8a4d01525e41dd25fc08a9860928f5425faea4062066e68a9f5614)
- **Judged and settled:** [`0xd3a7…147b`](https://explorer-studio.genlayer.com/tx/0xd3a71955879bd4bc885752c675eb1808b72d4255e65498d5359cba24decf147b)
- **Historical verdict:** `COMPLIANT` — `100/100`
- **Historical result:** `PAID` — `RELEASE_TO_CREATOR`
- **Public post:** [creator evidence v3](https://briefbond.ansaf1st33.chatgpt.site/demo-sponsored-post-v3.html)
- **Post SHA-256:** `c44cb21d61a3626a963464679acc7fc0f8080cd3c0c5818ca24ef097bc83d58f`

## Settlement model

| Accepted result | Contract consequence |
| --- | --- |
| Verified `COMPLIANT`, score ≥ threshold | Release escrow to creator |
| Verified `FIX_REQUIRED` or score below threshold | Hold escrow for a new version |
| Inaccessible, mismatched, oversized, or unrenderable evidence | Hold escrow for protected retry |
| First verified `INVALID` | Hold escrow for second review |
| Second verified `INVALID` | Refund brand |
| Deadline and any protected retry window expired | Refund brand |

## Immutable evidence record

Each proof ledger entry includes:

- public evidence URL;
- creator-declared SHA-256;
- validator-fetched response SHA-256;
- rendered screenshot SHA-256—the exact image supplied to the jury;
- HTTP status, byte length, and evidence-authentication status;
- independent verdict, scorecard, review round, and invalid confirmation count;
- resulting escrow state and settlement action.

Revisions and retries append proof records; prior evidence is never overwritten.

## Repository map

- `contracts/brief_bond.py` — v2 intelligent contract and settlement logic
- `tests/direct/test_brief_bond.py` — digest, jury, retry, review, and payout tests
- `app/` — mobile-first GenLayer application with retry controls
- `examples/campaign-brief-v2.md` — readable v2 demonstration terms
- `public/demo-campaign-brief-v2.txt` — exact hashable public brief bytes
- `public/demo-sponsored-post-v4.txt` — stable digest-bound v2 post evidence
- `public/demo-sponsored-post-v3.html` — validator-readable demonstration post
- `docs/STEWARD_RESPONSE.md` — requested issue mapped to code and tests
- `docs/ARCHITECTURE.md` — v2 workflow and state machine
- `docs/STUDIONET_V2_RUNBOOK.md` — exact deployment and proof inputs

## Local verification

```bash
genvm-lint contracts/brief_bond.py
python3 -m pytest tests/direct -q
npm run lint
npm run test
```

Expected results:

```text
GenVM lint: passed
Contract tests: 8 passed
Application tests: 5 passed
Production build: passed
```

## Contract methods

- `open_campaign(...)` — authenticates the brief, locks canonical terms and GEN
- `submit_and_settle(...)` — authenticates and judges a new post version
- `retry_review(campaign_id)` — retries protected or second-stage review
- `settle_expired(campaign_id)` — refunds only after deadline/retry protections
- `get_campaign(campaign_id)` — reads the current campaign state
- `get_proof(campaign_id, version)` — reads any append-only proof record
- `get_totals()` — reads aggregate escrow statistics
