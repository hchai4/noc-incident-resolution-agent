SOP-NET-17: OSPF Adjacency Down Protocol
1. Scope & Symptoms
Applies to an OSPF neighbor stuck in Init/ExStart/2-Way, or a FULL adjacency that dropped, inside our IGP. BGP to upstreams may still be up. This is not a public route leak.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 1 Hour to restore the IGP adjacency or isolate the link.

Primary Cause: MTU mismatch, authentication key, area ID, or a Layer-2 fault on the IGP link.

3. Immediate Technical Actions
Check hello/dead timers, area, and MTU on both sides. Do not apply BGP leak filters.

If the link is the problem, cost it out and let SPF use the backup IGP path.

If a key or area mismatch, correct the config on the new side only after change control, then clear the neighbor.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes if customer prefixes are looping or unreachable internally.

Progress Status Updates: Every 20 minutes until the adjacency is FULL.

Tone Requirement: IGP/OSPF specific. Do not call this a BGP hijack.
