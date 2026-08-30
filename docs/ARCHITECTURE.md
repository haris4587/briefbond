# BriefBond architecture

BriefBond is a creator-campaign escrow in which GenLayer is central to both the
judgment and the settlement.

The deployed Studionet contract is
[`0xC83882792dFd41948C4eC4CF74c7a477EDccd549`](https://explorer-studio.genlayer.com/address/0xC83882792dFd41948C4eC4CF74c7a477EDccd549).

## Binding workflow

1. A brand opens a campaign and deposits GEN through `open_campaign`.
2. The public brief URL, SHA-256 fingerprint, creator wallet, deadline, scoring
   threshold, disclosure, and call to action are stored as immutable terms.
3. Only the assigned creator may call `submit_and_settle`.
4. The creator supplies a public post URL and a SHA-256 fingerprint for one
   exact post version.
5. GenLayer validators independently render the public post, compare it to the
   locked terms, and reach consensus on a structured scorecard.
6. Deterministic contract logic applies the accepted verdict:
   - `COMPLIANT` plus the score threshold releases GEN to the creator.
   - `FIX_REQUIRED` keeps GEN locked and permits a new hash-anchored version.
   - `INVALID` refunds the brand.
7. If the deadline expires before settlement, anyone may trigger a deterministic
   refund to the brand.

Every proof version remains readable from `get_proof`; revisions never overwrite
the evidence or verdict that came before them.
