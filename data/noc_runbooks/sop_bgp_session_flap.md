SOP-NET-08: BGP Neighbor Session Flap Protocol
1. Scope & Symptoms
Applies to a single BGP neighbor oscillating Idle/Established without evidence of a new origin or an unintended full-table leak. Prefixes we originate are unchanged. Packet loss is limited to that peering, not a global hijack.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 2 Hours from first flap after damping.

Primary Cause: Unstable far-end session, BFD timeout, or a peering interface error — not an AS-path policy leak.

3. Immediate Technical Actions
Inspect session state and last-error on that neighbor only. Do not apply a network-wide leak prefix-filter as the first step.

Enable or tighten BFD; bounce the session once after damping if the far-end is clean.

If the neighbor keeps flapping, shut that session and shift traffic to the backup peer for the same ASN. Do not treat this as a route leak or hijack.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes of persistent flap (three or more resets).

Progress Status Updates: Every 30 minutes until the neighbor stays Established for 15 minutes.

Tone Requirement: Technical, naming the neighbor ASN and that originated prefixes were not leaked.
