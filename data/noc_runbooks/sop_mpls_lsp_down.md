SOP-NET-18: MPLS LSP Down Protocol
1. Scope & Symptoms
Applies to an RSVP or LDP LSP that is down, tail-end unreachable in MPLS, or L3VPN labels missing, while IGP and BGP sessions to the PE may still be up.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 2 Hours to re-signal the LSP or move the VPN to a backup PE.

Primary Cause: RSVP bandwidth admission, mid-point LSR down, or LDP session drop.

3. Immediate Technical Actions
Check the LSP at head-end (show mpls lsp / rsvp session). Do not treat this as a customer CPE outage.

Resignal the LSP on an alternate path or enable facility backup if Fast Reroute is configured.

If the mid-point LSR is down, detour around it; do not bounce the customer attachment circuit first.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes if the L3VPN is down.

Progress Status Updates: Every 30 minutes until the LSP is up and labels are programmed.

Tone Requirement: MPLS/LSP specific. Underlay fiber may still be up.
