# BriefBond

**BriefBond is a GenLayer-powered creator campaign escrow.** A brand locks a
campaign brief and GEN payout, a creator submits a hash-anchored public post,
and AI-validator consensus releases, holds, or refunds the payout.

## Live GenLayer deployment

- **Studionet contract:** [`0x3c38550CCF41685c1DF1d07A9823A70Df5998A91`](https://explorer-studio.genlayer.com/address/0x3c38550CCF41685c1DF1d07A9823A70Df5998A91)
- **Finalized deployment transaction:** [`0x3cf7…3e27`](https://explorer-studio.genlayer.com/tx/0x3cf79baa1d99cfd3f43558bf036f39ccb558201badf035127faddba7717a3e27)
- **Network:** GenLayer Studionet

## Verified full-consensus settlement

Campaign `briefbond-live-2026-003` completed the complete escrow workflow on
Studionet using Normal (Full Consensus) execution:

- **Funded escrow:** [`0x7b10…5614`](https://explorer-studio.genlayer.com/tx/0x7b1091428a8a4d01525e41dd25fc08a9860928f5425faea4062066e68a9f5614)
- **Judged and settled:** [`0xd3a7…147b`](https://explorer-studio.genlayer.com/tx/0xd3a71955879bd4bc885752c675eb1808b72d4255e65498d5359cba24decf147b)
- **Validator verdict:** `COMPLIANT` — `100/100`
- **Binding result:** `PAID` — `RELEASE_TO_CREATOR`
- **Public post:** [creator evidence v3](https://briefbond.ansaf1st33.chatgpt.site/demo-sponsored-post-v3.html)
- **Post SHA-256:** `c44cb21d61a3626a963464679acc7fc0f8080cd3c0c5818ca24ef097bc83d58f`

## Why GenLayer is central

Traditional smart contracts cannot reliably judge whether a sponsored post
actually follows a natural-language campaign brief. BriefBond lets GenLayer
validators inspect the public post and agree on a structured verdict. The
contract then turns that accepted judgment into a binding financial consequence.

| Verdict | Contract consequence |
| --- | --- |
| `COMPLIANT` and score ≥ threshold | Release escrow to creator |
| `FIX_REQUIRED` or score below threshold | Keep escrow locked for a revision |
| `INVALID` | Refund the brand |
| Deadline expired | Refund the brand |

## Immutable evidence

- The campaign brief is committed by public URL and SHA-256 fingerprint.
- Every creator submission is committed by public URL and SHA-256 fingerprint.
- Revisions create append-only versions; prior evidence and verdicts remain readable.
- External GEN transfers are emitted only after transaction finalization.
- **Validator-readable demo post:** [open creator post v3](https://briefbond.ansaf1st33.chatgpt.site/demo-sponsored-post-v3.html)

## Repository map

- `contracts/brief_bond.py` — intelligent contract and escrow settlement logic
- `tests/direct/test_brief_bond.py` — release, revision, refund, and expiry tests
- `app/` — mobile-first GenLayer application
- `examples/` — public campaign brief and creator-post evidence
- `public/demo-*` — validator-readable copies of the demonstration evidence
- `docs/ARCHITECTURE.md` — full workflow and settlement model

## Local checks

```bash
npm run lint
npm run build
pytest tests/direct -v
```

## Contract methods

- `open_campaign(...)` — locks immutable terms and GEN payout
- `submit_and_settle(...)` — judges a post version and enforces the verdict
- `settle_expired(campaign_id)` — refunds an expired campaign
- `get_campaign(campaign_id)` — reads the current campaign state
- `get_proof(campaign_id, version)` — reads any immutable proof version
- `get_totals()` — reads aggregate escrow statistics
