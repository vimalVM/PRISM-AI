# Sovereign AI Workbench — Network Verification & Offline Evidence Archive

This folder stores cryptographic, network, and system evidence proving the core guarantee:
**Nothing leaves the premises. Zero runtime external network dependencies.**

This conforms to **03_SECURITY_AND_ACCESS.md §15** and **04_ANTIGRAVITY_BUILD_PLAN.md Phase 12**.

---

## Evidence Checklist (E1 – E8)

| Item | Description | Evidence File / Location | How Captured |
|---|---|---|---|
| **E1** | Local models verification | `docs/evidence/models.txt` | `ollama list` & `ollama show <model>` output showing local models with SHA-256 digests. |
| **E2** | Loopback binding proof | `docs/evidence/e2_listeners.txt` / screenshot | Windows: `netstat -ano \| findstr "8000 11434"`; Linux: `ss -tlnp`. Verifies binding exclusively to `127.0.0.1`. |
| **E3** | Firewall outbound block rules | `docs/evidence/e3_firewall_rules.txt` | Windows: `netsh advfirewall firewall show rule name="SAW block python"`. Per-process blocking rules. |
| **E4** | Wireshark network capture | `docs/evidence/e4_traffic_capture.pcapng` & screenshots | Wireshark capture on physical Wi-Fi/Ethernet adapter during Demo A/B/C runs with filters: `dns`, `tls`, `tcp.port == 443`, `!(ip.addr == 127.0.0.1)`. |
| **E5** | Sovereignty Panel UI screenshot | `docs/evidence/e5_sovereignty_panel.png` | Screenshot of Workbench UI `/sovereignty` showing `0 Non-Loopback Connections`, `127.0.0.1 ONLY`, and clean status. |
| **E6** | Static egress scan report | `logs/egress_scan.json` (copied to `docs/evidence/e6_egress_scan.json`) | Output of `python scripts/scan_egress.py` confirming 0 outbound URLs, 0 cloud AI SDKs, and 0 forbidden technologies. |
| **E7** | Offline live demonstration proof | Live demo record / video | Wi-Fi / Ethernet physically disabled; Demo A/B/C workflow completes end-to-end. |
| **E8** | Cryptographic audit trail export | `docs/evidence/e8_audit_export.jsonl` | Append-only hash-chained ledger verifying `prev_hash` to `hash` chain integrity with zero missing links. |

---

## Instructions for Re-generating Evidence

Run the automated verification helper script:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\offline_proof.ps1
```
Or follow the step-by-step procedure detailed in [`scripts/offline_proof.md`](file:///c:/Users/Abhiraj/OneDrive/Desktop/sovereign-ai-workbench/scripts/offline_proof.md).
