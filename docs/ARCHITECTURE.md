# BriefBond v2 architecture

BriefBond uses GenLayer consensus for evidence authentication, subjective
campaign judgment, and the decision that precedes settlement. Storage and GEN
transfers occur only after consensus accepts the non-deterministic result.

## Evidence-bound workflow

1. A brand supplies a public brief URL, declared SHA-256, canonical campaign
   terms, creator, threshold, deadline, and GEN payout.
2. Validators independently fetch the brief response bytes and recompute the
   SHA-256. A campaign cannot open unless the digest matches.
3. The contract stores the verified brief digest and a separate `terms_hash`
   over the canonical brief, disclosure, CTA, threshold, URL, and brief digest.
4. The creator supplies a public post URL and declared SHA-256.
5. In one jury round, each validator:
   - fetches the raw post response and recomputes its SHA-256;
   - rejects non-2xx, oversized, or mismatched evidence from judgment;
   - renders authenticated evidence and hashes the screenshot bytes;
   - independently scores the rendered post against locked terms.
6. Consensus requires exact agreement on HTTP metadata, fetched digest, rendered
   digest, evidence status, and verdict outcome. Limited score tolerance handles
   legitimate subjective variation.
7. Deterministic logic applies the accepted result to escrow.

## State machine

| Current event | New state | GEN action | Allowed next action |
| --- | --- | --- | --- |
| Campaign opens with verified brief | `FUNDED` | Lock | Creator submits evidence |
| Verified post passes threshold | `PAID` | Release to creator | Final |
| Verified post needs changes | `FIX_REQUIRED` | Hold | Creator submits new digest |
| Fetch/digest/render authentication fails | `EVIDENCE_REVIEW` | Hold | Either party retries; creator may revise |
| First verified `INVALID` | `REVIEW_REQUIRED` | Hold | Either party requests second review; creator may revise |
| Second verified `INVALID` | `REFUNDED` | Refund brand | Final |
| Deadline and protected retry window expire | `EXPIRED_REFUNDED` | Refund brand | Final |

The one-hour `review_grace_until` prevents an evidence access failure near the
deadline from becoming an immediate irreversible refund. A retry after the
deadline remains possible while that protected window is open.

## Independent validation

The lead validator cannot self-certify its result. The validator function:

1. independently re-fetches the URL;
2. recomputes response length and SHA-256;
3. independently re-renders and hashes the screenshot;
4. independently asks its model to reproduce the outcome and four scores;
5. requires an identical outcome, no category difference above 6 points, and a
   total score difference no greater than 16 points.

Any evidence digest disagreement rejects the leader proposal.

## Append-only proof ledger

`get_proof(campaign_id, version)` exposes every submission and retry round. Each
record stores:

- `declared_post_hash`
- `fetched_post_hash`
- `rendered_post_hash`
- `hash_verified` and `evidence_status`
- `http_status` and `content_length`
- scorecard, outcome, reason, and required fix
- `review_round` and `invalid_confirmations`
- state and settlement action after the verdict

`current_version` increments for every proof/review entry. New evidence and
same-evidence retries therefore remain auditable without overwriting history.

## Deployment status

The v2 contract is deployed on Studionet at
[`0x37620B14f49069616cD1c24A286a94f0A18E7831`](https://explorer-studio.genlayer.com/address/0x37620B14f49069616cD1c24A286a94f0A18E7831).
Its [deployment transaction](https://explorer-studio.genlayer.com/tx/0xdaa1376eabceebe87b646ceef6cafde418b000137ad02fbb9311d83035392c7f)
is finalized. The deployed source and repository source share SHA-256
`96223c65b46f05991ab9ba2fc6f2791266001ba3c7eee3c4f6ffa5be8bc4c1f4`.
The campaign-opening and settlement proof transactions are the remaining
Studionet evidence.

The historical v1 proof remains at
[`0x3c38550CCF41685c1DF1d07A9823A70Df5998A91`](https://explorer-studio.genlayer.com/address/0x3c38550CCF41685c1DF1d07A9823A70Df5998A91),
but it is not represented as the v2 implementation.
