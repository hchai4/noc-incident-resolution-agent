SOP-NET-19: Customer CPE Unreachable Protocol
1. Scope & Symptoms
Applies when the provider edge sees the customer attachment down (interface protocol down, BFD to CPE dead, or no ARP/ND) and the rest of the core and the access ring are healthy.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 4 Hours to restore the CPE or confirm the fault is on the customer side.

Primary Cause: Customer router crash, local power, or last-mile handoff — not a core fiber or IX outage.

3. Immediate Technical Actions
Confirm the PE interface and the access NID. If the ring and PE are up, do not open a metro-cut ticket.

Bounce the attachment circuit once after checking optics. Open a customer smart-hands ticket for the CPE.

If the NID is down and it is our last-mile, dispatch access tech to the building, not a long-haul splice team.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes of confirmed CPE/NID down.

Progress Status Updates: Every 60 minutes until the customer LAN is reachable or the customer accepts local ownership.

Tone Requirement: Last-mile / CPE. Core and long-haul are out of scope unless proven otherwise.
