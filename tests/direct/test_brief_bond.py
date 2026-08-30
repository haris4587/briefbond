import json

from PIL import Image


BRIEF_HASH = "a" * 64
POST_HASH_V1 = "b" * 64
POST_HASH_V2 = "c" * 64


def wallet(address_bytes):
    return "0x" + address_bytes.hex()


def stub_screenshot_decoder(monkeypatch):
    monkeypatch.setattr(
        Image,
        "open",
        lambda *_args, **_kwargs: Image.new("RGB", (2, 2), "white"),
    )


def mock_verdict(direct_vm, url_pattern, outcome, scores):
    direct_vm.mock_web(
        url_pattern,
        {"status": 200, "body": "mock sponsored post screenshot"},
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
                "reason": "The visible sponsored post was checked against the locked brief.",
                "evidence": "The required product, disclosure, and call to action are visible.",
                "required_fix": "Add the missing campaign requirement and resubmit a new version.",
            }
        ),
    )
    direct_vm.mock_llm(
        r".*independent GenLayer validator checking a proposed creator campaign.*",
        json.dumps(
            {
                "acceptable": True,
                "reason": "The assessment is supported by the submitted evidence.",
            }
        ),
    )


def open_campaign(contract, direct_vm, brand, creator, campaign_id, payout=10**18):
    direct_vm.sender = brand
    direct_vm.value = payout
    contract.open_campaign(
        campaign_id,
        "Summer hydration launch",
        "Northstar Drinks",
        wallet(creator),
        "https://example.com/brief-v1",
        BRIEF_HASH,
        "Publish one bright product post showing the bottle in an outdoor summer setting.",
        "Paid partnership with Northstar Drinks",
        "Tap the link to discover the summer collection",
        80,
        2_000_000_000,
    )


def test_compliant_post_releases_campaign_payout(
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
    assert funded["escrow_remaining_wei"] == str(10**18)

    direct_vm.sender = direct_bob
    direct_vm.value = 0
    mock_verdict(
        direct_vm,
        r"https://example\.com/post-v1",
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
    assert proof["post_hash"] == POST_HASH_V1
    assert proof["final_outcome"] == "COMPLIANT"
    assert totals["released_wei"] == str(10**18)
    assert totals["locked_wei"] == "0"


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
    assert proof_v1["post_hash"] == POST_HASH_V1
    assert proof_v1["status_after_verdict"] == "FIX_REQUIRED"
    assert proof_v2["post_hash"] == POST_HASH_V2
    assert proof_v2["status_after_verdict"] == "PAID"


def test_invalid_evidence_refunds_brand(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    monkeypatch,
):
    contract = direct_deploy("contracts/brief_bond.py")
    stub_screenshot_decoder(monkeypatch)
    open_campaign(contract, direct_vm, direct_alice, direct_bob, "campaign-003")

    direct_vm.sender = direct_bob
    direct_vm.value = 0
    mock_verdict(
        direct_vm,
        r"https://example\.com/unrelated-post",
        "INVALID",
        (2, 0, 0, 10),
    )
    contract.submit_and_settle(
        "campaign-003",
        "https://example.com/unrelated-post",
        POST_HASH_V1,
    )

    settled = json.loads(contract.get_campaign("campaign-003"))
    totals = json.loads(contract.get_totals())
    assert settled["status"] == "REFUNDED"
    assert settled["settlement_action"] == "REFUND_BRAND"
    assert settled["escrow_remaining_wei"] == "0"
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
    deadline = 1_788_094_800
    contract.open_campaign(
        "campaign-004",
        "One-hour launch activation",
        "Northstar Drinks",
        wallet(direct_bob),
        "https://example.com/brief-v1",
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
    contract.settle_expired("campaign-004")

    expired = json.loads(contract.get_campaign("campaign-004"))
    assert expired["status"] == "EXPIRED_REFUNDED"
    assert expired["settlement_action"] == "REFUND_BRAND"
    assert expired["escrow_remaining_wei"] == "0"
