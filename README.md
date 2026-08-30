# BriefBond

**BriefBond is a GenLayer-powered creator campaign escrow.** A brand locks a
campaign brief and GEN payout, a creator submits a hash-anchored public post,
and AI-validator consensus releases, holds, or refunds the payout.

## Live GenLayer deployment

- **Studionet contract:** [`0xC83882792dFd41948C4eC4CF74c7a477EDccd549`](https://explorer-studio.genlayer.com/address/0xC83882792dFd41948C4eC4CF74c7a477EDccd549)
- **Finalized deployment transaction:** [`0x5b3f…fed02`](https://explorer-studio.genlayer.com/tx/0x5b3f8edbf5da64e41b1ec7f85a313f2d841e1f5af0edc8c34ea90d751f6fed02)
- **Network:** GenLayer Studionet

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
