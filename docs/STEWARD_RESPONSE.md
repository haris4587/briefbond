# BriefBond response to steward review

## Steward request

> The stored hashes are not verified against the brief or rendered post, so the
> proof record cannot authenticate what validators judged. Bind fetched evidence
> to its digest and add a retry or review path before an inaccessible post
> triggers an irreversible refund.

## Implemented response

| Review concern | v2 correction | Verification |
| --- | --- | --- |
| Brief hash was caller-declared only | Consensus fetches the brief, recomputes SHA-256, and rejects a mismatch before accepting campaign funding | `test_campaign_funding_requires_digest_matching_brief` |
| Post hash was caller-declared only | Jury fetches response bytes and requires fetched SHA-256 to equal the declared digest | `test_compliant_post_binds_fetched_digest_and_releases_payout` |
| Proof did not authenticate rendered evidence | Contract stores SHA-256 of the exact screenshot bytes passed to the jury | Same compliant test checks the rendered digest |
| Validator only approved the leader | Validator independently fetches, renders, hashes, classifies, and scores; exact digest and outcome agreement is required | Compliant test runs the validator and rejects a tampered fetched digest |
| Inaccessible post could cause irreversible refund | Access, size, digest, and render failures produce `EVIDENCE_REVIEW` / `HOLD_FOR_RETRY` | `test_inaccessible_post_holds_escrow_then_retry_can_recover` |
| No recovery after temporary access failure | Either brand or creator can call `retry_review`; a one-hour grace window protects retry near expiry | Recovery test plus `test_retry_window_blocks_immediate_expiry_refund` |
| One `INVALID` verdict immediately refunded | First verified invalid holds in `REVIEW_REQUIRED`; second consensus-confirmed invalid refunds | `test_invalid_requires_second_consensus_review_before_refund` |
| Evidence history was incomplete | Append-only proofs store declared, fetched, and rendered digests plus review status and settlement action | Digest, mismatch, recovery, and invalid tests |

## Evidence status rules

- `VERIFIED`: 2xx response, within size limit, fetched digest matches, and render succeeds.
- `INACCESSIBLE`: request failure or non-2xx response.
- `HASH_MISMATCH`: fetched response does not match the creator commitment.
- `TOO_LARGE`: response exceeds the 2 MB evidence limit.
- `RENDER_FAILED`: raw bytes match but the jury cannot render the evidence.

Only `VERIFIED` evidence can receive `COMPLIANT`, `FIX_REQUIRED`, or `INVALID`.
All other statuses are stored as `UNREVIEWED` and keep the payout locked.

## Local verification result

```text
GenVM lint: passed
Contract tests: 8 passed
Application lint: passed
Application tests: 5 passed
Production build: passed
```

The remaining external step is to deploy this exact v2 contract to Studionet,
run a full-consensus campaign, and add the new address and transaction links to
this repository before resubmission.
