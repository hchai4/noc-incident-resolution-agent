SOP-NET-13: Public Peering Fabric Congestion Protocol
1. Scope & Symptoms
Applies to a public IX or private-peer interface running above 85% utilization with rising latency and drops in one direction. BGP remains Established. This is not a session flap or a leak.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 3 Hours to shift traffic or raise the port.

Primary Cause: Traffic mix shift, a popular cache, or an undersized 10/100G peer port.

3. Immediate Technical Actions
Confirm drops with interface counters and NetFlow, not with a LOS alarm.

Prepend or MED-shift that peer so traffic moves to a less loaded peer or transit.

If the port is a hard cap, open a capacity ticket. Do not shut the BGP session unless the peer is also erroring.

4. Mandatory Client Notification Cadence
Initial Alert: Within 20 minutes if customer latency is above SLA.

Progress Status Updates: Every 45 minutes until utilization is under 70% or the port is upgraded.

Tone Requirement: Capacity and peering, not a cut or a hijack.
