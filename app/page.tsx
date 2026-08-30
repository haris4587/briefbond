"use client";

import { useMemo, useState } from "react";
import {
  ArrowUpRight,
  BadgeCheck,
  BanknoteArrowDown,
  CircleDollarSign,
  Clock3,
  FileCheck2,
  Fingerprint,
  Link2,
  LoaderCircle,
  LockKeyhole,
  Megaphone,
  RefreshCw,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Upload,
  WalletCards,
} from "lucide-react";
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";

const CONTRACT_ADDRESS = "0x3c38550CCF41685c1DF1d07A9823A70Df5998A91";
const CONTRACT_READY = CONTRACT_ADDRESS !== "0x0000000000000000000000000000000000000000";
const EXPLORER_BASE = "https://explorer-studio.genlayer.com";

type WalletAddress = `0x${string}`;
type BusyAction = "connect" | "fund" | "submit" | "inspect" | null;

type CampaignRecord = {
  campaign_id?: string;
  campaign_title?: string;
  brand_name?: string;
  creator_wallet?: string;
  brief_hash?: string;
  status?: string;
  settlement_action?: string;
  current_score?: number;
  current_version?: number;
  current_post_hash?: string;
  escrow_deposited_wei?: string;
  escrow_remaining_wei?: string;
};

const sampleCampaign = {
  id: "northstar-summer-2026-01",
  title: "Northstar Summer Hydration Launch",
  brand: "Northstar Drinks",
  creator: "0x0000000000000000000000000000000000000000",
  briefUrl: "https://github.com/haris4587/briefbond/blob/main/examples/campaign-brief.md",
  briefHash: "",
  brief:
    "Publish one bright sponsored post using the line ‘Summer starts with a sip.’ The tone must feel energetic, unmistakably summery, and suitable for a general audience.",
  disclosure: "Paid partnership with Northstar Drinks",
  cta: "Tap the link to discover the summer collection",
  threshold: "82",
  payout: "1",
};

function compactAddress(address: string) {
  if (address.length < 12) return address;
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

function genToWei(value: string) {
  const clean = value.trim();
  if (!/^\d+(\.\d{0,18})?$/.test(clean)) {
    throw new Error("Enter a valid GEN amount with up to 18 decimal places.");
  }
  const [whole, fraction = ""] = clean.split(".");
  return BigInt(whole) * BigInt(10) ** BigInt(18) + BigInt(fraction.padEnd(18, "0"));
}

function weiToGen(value?: string) {
  if (!value) return "0";
  const wei = BigInt(value);
  const unit = BigInt(10) ** BigInt(18);
  const whole = wei / unit;
  const fraction = (wei % unit).toString().padStart(18, "0").slice(0, 3);
  return `${whole}.${fraction}`;
}

async function sha256(file: File) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint ? <span className="field-hint">{hint}</span> : null}
    </label>
  );
}

function HashUpload({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const [fileName, setFileName] = useState("");

  async function handleFile(file?: File) {
    if (!file) return;
    setFileName(file.name);
    onChange(await sha256(file));
    toast.success(`${label} fingerprint created`);
  }

  return (
    <div className="hash-box">
      <div className="hash-topline">
        <div>
          <span className="field-label">{label} SHA-256</span>
          <p>{fileName || "Choose the exact public file you are committing to."}</p>
        </div>
        <label className="upload-button">
          <Upload aria-hidden="true" />
          Hash file
          <input
            type="file"
            onChange={(event) => handleFile(event.target.files?.[0])}
            aria-label={`Upload ${label.toLowerCase()} file to calculate SHA-256`}
          />
        </label>
      </div>
      <Input
        value={value}
        onChange={(event) => onChange(event.target.value.toLowerCase())}
        placeholder="64-character SHA-256 fingerprint"
        className="mono-input"
        maxLength={64}
      />
    </div>
  );
}

export default function Home() {
  const [wallet, setWallet] = useState<WalletAddress | "">("");
  const [busy, setBusy] = useState<BusyAction>(null);
  const [txHash, setTxHash] = useState("");
  const [campaign, setCampaign] = useState(sampleCampaign);
  const [deadline, setDeadline] = useState(() => {
    const future = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    return future.toISOString().slice(0, 16);
  });
  const [submission, setSubmission] = useState({
    campaignId: sampleCampaign.id,
    postUrl: "",
    postHash: "",
  });
  const [lookupId, setLookupId] = useState(sampleCampaign.id);
  const [record, setRecord] = useState<CampaignRecord | null>(null);

  const client = useMemo(() => {
    if (!wallet) return null;
    return createClient({ chain: studionet, account: wallet });
  }, [wallet]);

  async function connectWallet() {
    setBusy("connect");
    try {
      const ethereum = (window as unknown as { ethereum?: { request: (args: { method: string }) => Promise<string[]> } }).ethereum;
      if (!ethereum) throw new Error("Open BriefBond in a browser with MetaMask installed.");
      const accounts = await ethereum.request({ method: "eth_requestAccounts" });
      if (!accounts[0]) throw new Error("No wallet account was selected.");
      const address = accounts[0] as WalletAddress;
      const networkClient = createClient({ chain: studionet, account: address });
      await networkClient.connect("studionet");
      setWallet(address);
      setCampaign((current) => ({
        ...current,
        creator: current.creator.includes("000000") ? address : current.creator,
      }));
      toast.success("Wallet connected to GenLayer Studionet");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Wallet connection failed.");
    } finally {
      setBusy(null);
    }
  }

  function requireClient() {
    if (!CONTRACT_READY) throw new Error("The new BriefBond contract is being deployed.");
    if (!client || !wallet) throw new Error("Connect your wallet first.");
    return client;
  }

  async function fundCampaign() {
    setBusy("fund");
    try {
      const activeClient = requireClient();
      if (campaign.briefHash.length !== 64) throw new Error("Create the brief SHA-256 fingerprint first.");
      const deadlineUnix = Math.floor(new Date(deadline).getTime() / 1000);
      if (!Number.isFinite(deadlineUnix)) throw new Error("Choose a valid campaign deadline.");

      const hash = await activeClient.writeContract({
        address: CONTRACT_ADDRESS as WalletAddress,
        functionName: "open_campaign",
        args: [
          campaign.id,
          campaign.title,
          campaign.brand,
          campaign.creator,
          campaign.briefUrl,
          campaign.briefHash,
          campaign.brief,
          campaign.disclosure,
          campaign.cta,
          Number(campaign.threshold),
          deadlineUnix,
        ],
        value: genToWei(campaign.payout),
      });
      setTxHash(hash);
      toast.success("Campaign submitted. GEN will lock after consensus.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Campaign transaction failed.");
    } finally {
      setBusy(null);
    }
  }

  async function submitProof() {
    setBusy("submit");
    try {
      const activeClient = requireClient();
      if (submission.postHash.length !== 64) throw new Error("Create the post SHA-256 fingerprint first.");
      const hash = await activeClient.writeContract({
        address: CONTRACT_ADDRESS as WalletAddress,
        functionName: "submit_and_settle",
        args: [submission.campaignId, submission.postUrl, submission.postHash],
        value: BigInt(0),
      });
      setTxHash(hash);
      toast.success("Proof submitted to the validator jury.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Proof submission failed.");
    } finally {
      setBusy(null);
    }
  }

  async function inspectCampaign() {
    setBusy("inspect");
    try {
      const activeClient = requireClient();
      const result = await activeClient.readContract({
        address: CONTRACT_ADDRESS as WalletAddress,
        functionName: "get_campaign",
        args: [lookupId],
      });
      const parsed = JSON.parse(String(result || "{}")) as CampaignRecord;
      if (!parsed.campaign_id) throw new Error("No campaign was found with that ID.");
      setRecord(parsed);
      toast.success("Campaign record loaded");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not load the campaign.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="site-shell">
      <Toaster position="top-center" richColors />
      <div className="background-grid" aria-hidden="true" />

      <header className="topbar">
        <a className="brand-lockup" href="#top" aria-label="BriefBond home">
          <span className="brand-mark"><Megaphone /></span>
          <span>
            <strong>BriefBond</strong>
            <small>CREATOR ESCROW</small>
          </span>
        </a>
        <div className="header-actions">
          <span className="network-pill"><span /> Studionet</span>
          <Button className="wallet-button" onClick={connectWallet} disabled={busy === "connect"}>
            {busy === "connect" ? <LoaderCircle className="spin" /> : <WalletCards />}
            {wallet ? compactAddress(wallet) : "Connect wallet"}
          </Button>
        </div>
      </header>

      <section className="intro" id="top">
        <div className="eyebrow"><Sparkles /> Sponsorship terms that actually settle</div>
        <h1>BRIEF. PROOF.<br /><span>PAID.</span></h1>
        <p>
          Lock a creator campaign brief and its GEN payout. GenLayer validators inspect the
          public post, reach neutral consensus, and enforce the result.
        </p>
        <div className="trust-row">
          <span><Fingerprint /> SHA-256 anchored</span>
          <span><ShieldCheck /> Validator judged</span>
          <span><CircleDollarSign /> Binding payout</span>
        </div>
      </section>

      <section className="workspace" aria-label="BriefBond campaign workspace">
        <div className="control-panel">
          <div className="panel-heading">
            <div>
              <span className="section-kicker">Campaign console</span>
              <h2>Move a deal on-chain</h2>
            </div>
            <a
              className={`contract-state ${CONTRACT_READY ? "ready" : "deploying"}`}
              href={`${EXPLORER_BASE}/address/${CONTRACT_ADDRESS}`}
              target="_blank"
              rel="noreferrer"
              title="Open the deployed BriefBond contract in GenLayer Explorer"
            >
              <span /> {CONTRACT_READY ? "Contract live" : "Deploying v1"}
              <ArrowUpRight aria-hidden="true" />
            </a>
          </div>

          <Tabs defaultValue="fund" className="campaign-tabs">
            <TabsList className="tab-list">
              <TabsTrigger value="fund">1. Fund</TabsTrigger>
              <TabsTrigger value="prove">2. Prove</TabsTrigger>
              <TabsTrigger value="inspect">3. Inspect</TabsTrigger>
            </TabsList>

            <TabsContent value="fund" className="tab-content">
              <div className="step-intro">
                <span className="step-icon coral"><LockKeyhole /></span>
                <div><h3>Lock the campaign</h3><p>The brief fingerprint and payout cannot be quietly changed later.</p></div>
              </div>
              <div className="form-grid two">
                <Field label="Campaign ID"><Input value={campaign.id} onChange={(e) => setCampaign({ ...campaign, id: e.target.value })} /></Field>
                <Field label="Campaign title"><Input value={campaign.title} onChange={(e) => setCampaign({ ...campaign, title: e.target.value })} /></Field>
                <Field label="Brand name"><Input value={campaign.brand} onChange={(e) => setCampaign({ ...campaign, brand: e.target.value })} /></Field>
                <Field label="Creator wallet"><Input value={campaign.creator} onChange={(e) => setCampaign({ ...campaign, creator: e.target.value })} className="mono-input" /></Field>
              </div>
              <Field label="Public brief URL" hint="Use a permanent, publicly readable HTTPS link.">
                <div className="icon-input"><Link2 /><Input value={campaign.briefUrl} onChange={(e) => setCampaign({ ...campaign, briefUrl: e.target.value })} /></div>
              </Field>
              <HashUpload label="Brief" value={campaign.briefHash} onChange={(briefHash) => setCampaign({ ...campaign, briefHash })} />
              <Field label="Campaign brief"><Textarea value={campaign.brief} onChange={(e) => setCampaign({ ...campaign, brief: e.target.value })} rows={4} /></Field>
              <div className="form-grid two">
                <Field label="Required disclosure"><Input value={campaign.disclosure} onChange={(e) => setCampaign({ ...campaign, disclosure: e.target.value })} /></Field>
                <Field label="Required call to action"><Input value={campaign.cta} onChange={(e) => setCampaign({ ...campaign, cta: e.target.value })} /></Field>
                <Field label="Approval score"><Input type="number" min="60" max="95" value={campaign.threshold} onChange={(e) => setCampaign({ ...campaign, threshold: e.target.value })} /></Field>
                <Field label="Submission deadline"><Input type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)} /></Field>
              </div>
              <div className="payout-strip">
                <div><span>Campaign payout</span><strong>{campaign.payout || "0"} GEN</strong></div>
                <Input aria-label="Campaign payout in GEN" value={campaign.payout} onChange={(e) => setCampaign({ ...campaign, payout: e.target.value })} inputMode="decimal" />
                <Button className="primary-action" onClick={fundCampaign} disabled={busy === "fund" || !CONTRACT_READY}>
                  {busy === "fund" ? <LoaderCircle className="spin" /> : <LockKeyhole />}
                  Lock terms + GEN
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="prove" className="tab-content">
              <div className="step-intro">
                <span className="step-icon yellow"><FileCheck2 /></span>
                <div><h3>Submit creator proof</h3><p>The assigned creator commits one exact post version for neutral review.</p></div>
              </div>
              <Field label="Campaign ID"><Input value={submission.campaignId} onChange={(e) => setSubmission({ ...submission, campaignId: e.target.value })} /></Field>
              <Field label="Public sponsored-post URL" hint="The validator jury must be able to open it without signing in.">
                <div className="icon-input"><Link2 /><Input value={submission.postUrl} onChange={(e) => setSubmission({ ...submission, postUrl: e.target.value })} placeholder="https://…" /></div>
              </Field>
              <HashUpload label="Post" value={submission.postHash} onChange={(postHash) => setSubmission({ ...submission, postHash })} />
              <div className="proof-warning"><BadgeCheck /><p><strong>Version lock:</strong> revisions are welcome, but each revision needs a new fingerprint. Every previous verdict remains auditable.</p></div>
              <Button className="primary-action wide" onClick={submitProof} disabled={busy === "submit" || !CONTRACT_READY}>
                {busy === "submit" ? <LoaderCircle className="spin" /> : <ScanSearch />}
                Submit to validator jury
              </Button>
            </TabsContent>

            <TabsContent value="inspect" className="tab-content">
              <div className="step-intro">
                <span className="step-icon blue"><ScanSearch /></span>
                <div><h3>Inspect the settlement</h3><p>Read the accepted campaign state directly from the intelligent contract.</p></div>
              </div>
              <div className="lookup-row">
                <Input value={lookupId} onChange={(e) => setLookupId(e.target.value)} placeholder="Campaign ID" />
                <Button onClick={inspectCampaign} disabled={busy === "inspect" || !CONTRACT_READY}>
                  {busy === "inspect" ? <LoaderCircle className="spin" /> : <RefreshCw />} Load record
                </Button>
              </div>
              {record ? (
                <div className="record-card">
                  <div className="record-top"><span>{record.status}</span><strong>{record.current_score ?? 0}/100</strong></div>
                  <h3>{record.campaign_title}</h3>
                  <p>{record.brand_name} → {compactAddress(record.creator_wallet || "")}</p>
                  <div className="record-grid">
                    <div><small>Action</small><strong>{record.settlement_action}</strong></div>
                    <div><small>Version</small><strong>v{record.current_version}</strong></div>
                    <div><small>Deposited</small><strong>{weiToGen(record.escrow_deposited_wei)} GEN</strong></div>
                    <div><small>Still locked</small><strong>{weiToGen(record.escrow_remaining_wei)} GEN</strong></div>
                  </div>
                  <div className="hash-readout"><Fingerprint /> {record.current_post_hash || record.brief_hash}</div>
                </div>
              ) : (
                <div className="empty-record"><ScanSearch /><p>No record loaded yet.</p></div>
              )}
            </TabsContent>
          </Tabs>

          {txHash ? (
            <a className="tx-banner" href={`${EXPLORER_BASE}/tx/${txHash}`} target="_blank" rel="noreferrer">
              <BadgeCheck /> Transaction submitted <span>{compactAddress(txHash)}</span><ArrowUpRight />
            </a>
          ) : null}
        </div>

        <aside className="settlement-panel">
          <span className="section-kicker">Settlement rail</span>
          <h2>Consensus has consequences.</h2>
          <p className="rail-copy">The jury cannot leave optional advice. Its accepted verdict moves the money.</p>

          <div className="outcome-stack">
            <article className="outcome-card paid">
              <span className="outcome-number">01</span>
              <div><strong>COMPLIANT</strong><p>Brief + score threshold passed</p></div>
              <span className="outcome-result"><BanknoteArrowDown /> Pay creator</span>
            </article>
            <article className="outcome-card held">
              <span className="outcome-number">02</span>
              <div><strong>FIX REQUIRED</strong><p>Material fixable gap remains</p></div>
              <span className="outcome-result"><Clock3 /> Hold escrow</span>
            </article>
            <article className="outcome-card refund">
              <span className="outcome-number">03</span>
              <div><strong>INVALID</strong><p>Unrelated or deceptive evidence</p></div>
              <span className="outcome-result"><RefreshCw /> Refund brand</span>
            </article>
          </div>

          <div className="proof-ledger">
            <div className="ledger-heading"><Fingerprint /><span>Immutable proof ledger</span></div>
            <div className="ledger-line"><span>Brief identity</span><strong>SHA-256</strong></div>
            <div className="ledger-line"><span>Post versions</span><strong>Append-only</strong></div>
            <div className="ledger-line"><span>Payout timing</span><strong>Finalized</strong></div>
            <div className="ledger-line"><span>Decision makers</span><strong>AI validators</strong></div>
          </div>

          <a className="learn-link" href="https://docs.genlayer.com/" target="_blank" rel="noreferrer">
            Built on GenLayer <ArrowUpRight />
          </a>
        </aside>
      </section>

      <footer>
        <span>BRIEFBOND / GENLAYER BUILDER PROJECT</span>
        <span>IMMUTABLE TERMS · NEUTRAL REVIEW · BINDING SETTLEMENT</span>
      </footer>
    </main>
  );
}
