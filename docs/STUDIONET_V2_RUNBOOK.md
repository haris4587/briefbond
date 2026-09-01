# BriefBond v2 Studionet runbook

Use this checklist to produce the final on-chain evidence for the steward
resubmission.

## Verified v2 deployment

- **Contract:** [`0x37620B14f49069616cD1c24A286a94f0A18E7831`](https://explorer-studio.genlayer.com/address/0x37620B14f49069616cD1c24A286a94f0A18E7831)
- **Deployment transaction:** [`0xdaa1376eabceebe87b646ceef6cafde418b000137ad02fbb9311d83035392c7f`](https://explorer-studio.genlayer.com/tx/0xdaa1376eabceebe87b646ceef6cafde418b000137ad02fbb9311d83035392c7f)
- **Status:** `FINALIZED`; five validator commits and five reveals.
- **Source SHA-256:** `96223c65b46f05991ab9ba2fc6f2791266001ba3c7eee3c4f6ffa5be8bc4c1f4`
  for both the deployed source and `contracts/brief_bond.py`.

## 1. Deploy the exact v2 contract — completed

1. Open [GenLayer Studio](https://studio.genlayer.com/) on Studionet.
2. Create or open the BriefBond contract editor.
3. Replace the editor contents with the exact current
   [`contracts/brief_bond.py`](../contracts/brief_bond.py) source.
4. Confirm Studio shows no constructor inputs; `BriefBond.__init__` takes none.
5. Click **Deploy** and wait for the deployment transaction to finalize.
6. Record the new contract address and deployment transaction hash. Completed
   with the verified values above.

Do not reuse the v1 address. This upgrade changes storage fields, public methods,
and settlement behavior and therefore requires a fresh deployment.

## 2. Open the verified demonstration campaign

Call `open_campaign` with **Normal / Full Consensus** and attach a small GEN
payout (for example 1 GEN).

| Input | Exact demonstration value |
| --- | --- |
| `campaign_id` | `briefbond-v2-2026-001` |
| `campaign_title` | `Northstar Summer Hydration v2` |
| `brand_name` | `Northstar Drinks` |
| `creator` | Your connected Studionet wallet address |
| `brief_url` | `https://briefbond.ansaf1st33.chatgpt.site/demo-campaign-brief-v2.txt` |
| `brief_hash` | `33f746b711c6ce5c60432984fb165a6388340d7dc502ac61f6ba2f0d4958fba5` |
| `campaign_brief` | `Publish one public sponsored post for Northstar Drinks. It must visibly include the campaign line "Summer starts with a sip.", use a bright energetic summer tone, include the required disclosure and call-to-action, and use language suitable for a general audience.` |
| `required_disclosure` | `Paid partnership with Northstar Drinks` |
| `required_cta` | `Tap the link to discover the summer collection` |
| `approval_threshold` | `82` |
| `deadline_unix` | `1788479940` (September 3, 2026, 23:59 UTC) |

The transaction must finalize with campaign state `FUNDED`,
`brief_hash_verified: true`, and identical `brief_hash` and
`brief_fetched_hash` values.

## 3. Submit digest-bound creator evidence

Using the wallet entered as `creator`, call `submit_and_settle` with **Normal /
Full Consensus**:

| Input | Exact demonstration value |
| --- | --- |
| `campaign_id` | `briefbond-v2-2026-001` |
| `post_url` | `https://briefbond.ansaf1st33.chatgpt.site/demo-sponsored-post-v4.txt` |
| `post_hash` | `4ed35eade773e34c5e4474a500ae07715b438c300c38944e39dc9304fe4aa65e` |

The `.txt` evidence is intentional. The host serves these bytes unchanged,
whereas the historical HTML page may receive dynamic anti-bot markup and is not
suitable for exact response-digest verification.

## 4. Capture final proof

After finalization, record:

- new contract address;
- deployment transaction;
- `open_campaign` transaction;
- `submit_and_settle` transaction;
- `get_campaign("briefbond-v2-2026-001")` result;
- `get_proof("briefbond-v2-2026-001", 1)` result;
- Explorer links showing Full Consensus and final state.

For a compliant result, the campaign should show `PAID` and
`RELEASE_TO_CREATOR`. The proof must show:

- `evidence_status: VERIFIED`;
- `hash_verified: true`;
- identical `declared_post_hash` and `fetched_post_hash`;
- a non-empty `rendered_post_hash`;
- the accepted validator scorecard and settlement action.

## 5. Final repository and website update

Replace the v2 deployment placeholders in `README.md`, `docs/ARCHITECTURE.md`,
and `app/page.tsx`, add all Explorer links, redeploy the website, and then use
those already-submitted GitHub/site evidence links for steward resubmission.
