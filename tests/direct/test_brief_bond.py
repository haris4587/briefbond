import hashlib
import json

from PIL import Image


BRIEF_BODY = b"Northstar immutable campaign brief v2"
POST_BODY_V1 = b"Northstar sponsored creator post version one"
POST_BODY_V2 = b"Northstar sponsored creator post version two"
BRIEF_HASH = hashlib.sha256(BRIEF_BODY).hexdigest()
POST_HASH_V1 = hashlib.sha256(POST_BODY_V1).hexdigest()
POST_HASH_V2 = hashlib.sha256(POST_BODY_V2).hexdigest()


def wallet(address_bytes):
    return "0x" + address_bytes.hex()


def stub_screenshot_decoder(monkeypatch):
    monkeypatch.setattr(
        Image,
        "open",
        lambda *_args, **_kwargs: Image.new("RGB", (2, 2), "white"),
    )


def mock_brief(direct_vm, body=BRIEF_BODY, status=200):
    direct_vm.mock_web(
        r"https://example\.com/brief-v2",
        {"status": status, "body": body},
    )


def mock_verdict(direct_vm, url_pattern, body, outcome, scores, status=200):
    direct_vm.mock_web(
        url_pattern,
        {"status": status, "body": body},
    )
    direct_vm.mock_llm(
        r".*lead validator settling a creator sponsorship escrow.*",
        json.dumps(
            {
                "outcome": outcome,
                "brief_match": scores[0],
                "disclosure_compliance": scores[1],
                "cta_delivery": scores[2],
                "brand_safety": scores[3],
                "reason": "The authenticated sponsored post was checked against the locked brief.",
                "evidence": "The required product, disclosure, and call to action are visible.",
                "required_fix": "Add the missing campaign requirement and submit a new version.",
            }
        ),
    )
    direct_vm.mock_llm(
        r".*independent GenLayer validator\. Reproduce the creator campaign.*",
        json.dumps(
            {
                "outcome": outcome,
                "brief_match": scores[0],
                "disclosure_compliance": scores[1],
                "cta_delivery": scores[2],
                "brand_safety": scores[3],
            }
        ),
    )


def open_campaign(
    contract,
    direct_vm,
    brand,
    creator,
    campaign_id,
    payout=10**18,
    brief_hash=BRIEF_HASH,
):
    direct_vm.sender = brand
    direct_vm.value = payout
    mock_brief(direct_vm)
    contract.open_campaign(
        campaign_id,
        "Summer hydration launch",
        "Northstar Drinks",
        wallet(creator),
        "https://example.com/brief-v2",
        brief_hash,
        "Publish one bright product post showing the bottle in an outdoor summer setting.",
        "Paid partnership with Northstar Drinks",
        "Tap the link to discover the summer collection",
        80,
        2_000_000_000,
    )


def test_campaign_funding_requires_digest_matching_brief(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    contract = direct_deploy("contracts/brief_bond.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 10**18
    mock_brief(direct_vm)

    with direct_vm.expect_revert("Brief evidence must be publicly accessible"):
        contract.open_campaign(
            "campaign-mismatch",
            "Summer hydration launch",
            "Northstar Drinks",
            wallet(direct_bob),
            "https://example.com/brief-v2",
            "0" * 64,
            "Publish one bright product post showing the bottle in an outdoor summer setting.",
            "Paid partnership with Northstar Drinks",
            "Tap the link to discover the summer collection",
            80,
            2_000_000_000,
        )

    assert contract.get_campaign("campaign-mismatch") == ""


def test_compliant_post_binds_fetched_digest_and_releases_payout(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    monkeypatch,
):
    contract = direct_deploy("contracts/brief_bond.py")
    stub_screenshot_decoder(monkeypatch)
    open_campaign(contract, direct_vm, direct_alice, direct_bob, "campaign-001")

    funded = json.loads(contract.get_campaign("campaign-001"))
    assert funded["status"] == "FUNDED"
    assert funded["brief_hash"] == BRIEF_HASH
    assert funded["brief_fetched_hash"] == BRIEF_HASH
    assert funded["brief_hash_verified"] is True
    assert len(funded["terms_hash"]) == 64
    assert funded["escrow_remaining_wei"] == str(10**18)

    direct_vm.sender = direct_bob
    direct_vm.value = 0
    mock_verdict(
        direct_vm,
        r"https://example\.com/post-v1",
        POST_BODY_V1,
        "COMPLIANT",
        (23, 24, 21, 23),
    )
    contract.submit_and_settle(
        "campaign-001",
        "https://example.com/post-v1",
        POST_HASH_V1,
    )

    settled = json.loads(contract.get_campaign("campaign-001"))
    proof = json.loads(contract.get_proof("campaign-001", 1))
    totals = json.loads(contract.get_totals())

    assert settled["status"] == "PAID"
    assert settled["settlement_action"] == "RELEASE_TO_CREATOR"
    assert settled["current_score"] == 91
    assert settled["current_post_hash"] == POST_HASH_V1
    assert settled["current_fetched_post_hash"] == POST_HASH_V1
    assert settled["current_hash_verified"] is True
    assert proof["declared_post_hash"] == POST_HASH_V1
    assert proof["fetched_post_hash"] == POST_HASH_V1
    assert proof["rendered_post_hash"] == hashlib.sha256(b"").hexdigest()
    assert proof["hash_verified"] is True
    assert proof["evidence_status"] == "VERIFIED"
    assert proof["final_outcome"] == "COMPLIANT"
    assert totals["released_wei"] == str(10**18)
    assert totals["locked_wei"] == "0"

    assert direct_vm.run_validator() is True
    tampered = dict(direct_vm._captured_validators[-1][0])
    tampered["fetched_hash"] = "f" * 64
    assert direct_vm.run_validator(leader_result=tampered) is False


def test_fix_required_preserves_v1_then_revision_releases(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    monkeypatch,
):
    contract = direct_deploy("contracts/brief_bond.py")
    stub_screenshot_decoder(monkeypatch)
    open_campaign(
        contract,
        direct_vm,
        direct_alice,
        direct_bob,
        "campaign-002",
        payout=2 * 10**18,
    )

    direct_vm.sender = direct_bob
    direct_vm.value = 0
    mock_verdict(
        direct_vm,
        r"https://example\.com/post-v1",
        POST_BODY_V1,
        "FIX_REQUIRED",
        (21, 10, 14, 22),
    )
    contract.submit_and_settle(
        "campaign-002",
        "https://example.com/post-v1",
        POST_HASH_V1,
    )

    held = json.loads(contract.get_campaign("campaign-002"))
    assert held["status"] == "FIX_REQUIRED"
    assert held["settlement_action"] == "HOLD_IN_ESCROW"
    assert held["escrow_remaining_wei"] == str(2 * 10**18)

    direct_vm.clear_mocks()
    direct_vm.sender = direct_bob
    mock_verdict(
        direct_vm,
        r"https://example\.com/post-v2",
        POST_BODY_V2,
        "COMPLIANT",
        (23, 23, 21, 22),
    )
    contract.submit_and_settle(
        "campaign-002",
        "https://example.com/post-v2",
        POST_HASH_V2,
    )

    settled = json.loads(contract.get_campaign("campaign-002"))
    proof_v1 = json.loads(contract.get_proof("campaign-002", 1))
    proof_v2 = json.loads(contract.get_proof("campaign-002", 2))

    assert settled["current_version"] == 2
    assert settled["status"] == "PAID"
    assert proof_v1["declared_post_hash"] == POST_HASH_V1
    assert proof_v1["status_after_verdict"] == "FIX_REQUIRED"
    assert proof_v2["declared_post_hash"] == POST_HASH_V2
    assert proof_v2["status_after_verdict"] == "PAID"


def test_inaccessible_post_holds_escrow_then_retry_can_recover(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    monkeypatch,
):
    contract = direct_deploy("contracts/brief_bond.py")
    stub_screenshot_decoder(monkeypatch)
    open_campaign(contract, direct_vm, direct_alice, direct_bob, "campaign-003")

    direct_vm.clear_mocks()
    direct_vm.sender = direct_bob
    direct_vm.value = 0
    direct_vm.mock_web(
        r"https://example\.com/temporarily-down",
        {"status": 503, "body": POST_BODY_V1},
    )
    contract.submit_and_settle(
        "campaign-003",
        "https://example.com/temporarily-down",
        POST_HASH_V1,
    )

    held = json.loads(contract.get_campaign("campaign-003"))
    proof_v1 = json.loads(contract.get_proof("campaign-003", 1))
    assert held["status"] == "EVIDENCE_REVIEW"
    assert held["settlement_action"] == "HOLD_FOR_RETRY"
    assert held["escrow_remaining_wei"] == str(10**18)
    assert proof_v1["evidence_status"] == "INACCESSIBLE"
    assert proof_v1["validator_outcome"] == "UNREVIEWED"

    direct_vm.clear_mocks()
    direct_vm.sender = direct_alice
    mock_verdict(
        direct_vm,
        r"https://example\.com/temporarily-down",
        POST_BODY_V1,
        "COMPLIANT",
        (24, 24, 23, 24),
    )
    contract.retry_review("campaign-003")

    recovered = json.loads(contract.get_campaign("campaign-003"))
    proof_v2 = json.loads(contract.get_proof("campaign-003", 2))
    assert recovered["status"] == "PAID"
    assert recovered["review_round"] == 2
    assert proof_v2["evidence_status"] == "VERIFIED"
    assert proof_v2["settlement_action"] == "RELEASE_TO_CREATOR"


def test_retry_window_blocks_immediate_expiry_refund(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    contract = direct_deploy("contracts/brief_bond.py")
    direct_vm.warp("2026-08-30T12:00:00+00:00")
    direct_vm.sender = direct_alice
    direct_vm.value = 10**18
    mock_brief(direct_vm)
    deadline = 1_788_094_800
    contract.open_campaign(
        "campaign-grace",
        "One-hour protected review",
        "Northstar Drinks",
        wallet(direct_bob),
        "https://example.com/brief-v2",
        BRIEF_HASH,
        "Publish one bright product post showing the bottle in an outdoor summer setting.",
        "Paid partnership with Northstar Drinks",
        "Tap the link to discover the summer collection",
        80,
        deadline,
    )

    direct_vm.clear_mocks()
    direct_vm.warp("2026-08-30T12:50:00+00:00")
    direct_vm.sender = direct_bob
    direct_vm.value = 0
    direct_vm.mock_web(
        r"https://example\.com/end-of-window",
        {"status": 503, "body": POST_BODY_V1},
    )
    contract.submit_and_settle(
        "campaign-grace",
        "https://example.com/end-of-window",
        POST_HASH_V1,
    )

    direct_vm.warp("2026-08-30T13:10:00+00:00")
    with direct_vm.expect_revert("protected retry window is still open"):
        contract.settle_expired("campaign-grace")

    protected = json.loads(contract.get_campaign("campaign-grace"))
    assert protected["status"] == "EVIDENCE_REVIEW"
    assert protected["escrow_remaining_wei"] == str(10**18)

    direct_vm.warp("2026-08-30T14:00:00+00:00")
    contract.settle_expired("campaign-grace")
    expired = json.loads(contract.get_campaign("campaign-grace"))
    assert expired["status"] == "EXPIRED_REFUNDED"


def test_hash_mismatch_is_recorded_without_refund(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    contract = direct_deploy("contracts/brief_bond.py")
    open_campaign(contract, direct_vm, direct_alice, direct_bob, "campaign-004")

    direct_vm.clear_mocks()
    direct_vm.sender = direct_bob
    direct_vm.value = 0
    unexpected_body = b"A changed response that does not match the commitment"
    direct_vm.mock_web(
        r"https://example\.com/changed-post",
        {"status": 200, "body": unexpected_body},
    )
    contract.submit_and_settle(
        "campaign-004",
        "https://example.com/changed-post",
        POST_HASH_V1,
    )

    held = json.loads(contract.get_campaign("campaign-004"))
    proof = json.loads(contract.get_proof("campaign-004", 1))
    totals = json.loads(contract.get_totals())
    assert held["status"] == "EVIDENCE_REVIEW"
    assert held["current_hash_verified"] is False
    assert proof["evidence_status"] == "HASH_MISMATCH"
    assert proof["declared_post_hash"] == POST_HASH_V1
    assert proof["fetched_post_hash"] == hashlib.sha256(unexpected_body).hexdigest()
    assert totals["refunded_wei"] == "0"
    assert totals["locked_wei"] == str(10**18)


def test_invalid_requires_second_consensus_review_before_refund(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    monkeypatch,
):
    contract = direct_deploy("contracts/brief_bond.py")
    stub_screenshot_decoder(monkeypatch)
    open_campaign(contract, direct_vm, direct_alice, direct_bob, "campaign-005")

    direct_vm.sender = direct_bob
    direct_vm.value = 0
    mock_verdict(
        direct_vm,
        r"https://example\.com/unrelated-post",
        POST_BODY_V1,
        "INVALID",
        (2, 0, 0, 10),
    )
    contract.submit_and_settle(
        "campaign-005",
        "https://example.com/unrelated-post",
        POST_HASH_V1,
    )

    first_review = json.loads(contract.get_campaign("campaign-005"))
    assert first_review["status"] == "REVIEW_REQUIRED"
    assert first_review["settlement_action"] == "HOLD_FOR_SECOND_REVIEW"
    assert first_review["invalid_confirmations"] == 1
    assert first_review["escrow_remaining_wei"] == str(10**18)

    contract.retry_review("campaign-005")

    settled = json.loads(contract.get_campaign("campaign-005"))
    proof_v2 = json.loads(contract.get_proof("campaign-005", 2))
    totals = json.loads(contract.get_totals())
    assert settled["status"] == "REFUNDED"
    assert settled["settlement_action"] == "REFUND_BRAND_AFTER_REVIEW"
    assert settled["invalid_confirmations"] == 2
    assert settled["escrow_remaining_wei"] == "0"
    assert proof_v2["invalid_confirmations"] == 2
    assert totals["refunded_wei"] == str(10**18)


def test_expired_campaign_refunds_without_subjective_review(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    contract = direct_deploy("contracts/brief_bond.py")
    direct_vm.warp("2026-08-30T12:00:00+00:00")
    direct_vm.sender = direct_alice
    direct_vm.value = 10**18
    mock_brief(direct_vm)
    deadline = 1_788_094_800
    contract.open_campaign(
        "campaign-006",
        "One-hour launch activation",
        "Northstar Drinks",
        wallet(direct_bob),
        "https://example.com/brief-v2",
        BRIEF_HASH,
        "Publish one bright product post showing the bottle in an outdoor summer setting.",
        "Paid partnership with Northstar Drinks",
        "Tap the link to discover the summer collection",
        80,
        deadline,
    )

    direct_vm.warp("2026-08-30T14:00:00+00:00")
    direct_vm.sender = direct_bob
    direct_vm.value = 0
    contract.settle_expired("campaign-006")

    expired = json.loads(contract.get_campaign("campaign-006"))
    assert expired["status"] == "EXPIRED_REFUNDED"
    assert expired["settlement_action"] == "REFUND_BRAND_AFTER_DEADLINE"
    assert expired["escrow_remaining_wei"] == "0"
