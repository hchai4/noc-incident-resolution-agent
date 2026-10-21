SOP-NET-10: Recursive DNS Resolver Outage Protocol
1. Scope & Symptoms
Applies to recursive resolver clusters that stop answering, return SERVFAIL at scale, or show query latency above 500 ms. Authoritative zones we host may still be healthy.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 1 Hour to restore recursive service or fail clients to the anycast backup.

Primary Cause: Resolver software crash, cache poisoning mitigation overload, or anycast node drain.

3. Immediate Technical Actions
Check recursive vs authoritative separately. Do not treat this as a fiber or BGP event.

Fail the sick anycast node out of the DNS anycast prefix and confirm the remaining nodes answer.

If all recursive nodes are down, announce the backup resolver anycast and point stub resolvers at it.

4. Mandatory Client Notification Cadence
Initial Alert: Within 10 minutes of recursive failure.

Progress Status Updates: Every 20 minutes until query success rate is back above 99%.

Tone Requirement: Naming recursive DNS, not "the whole internet is down."
