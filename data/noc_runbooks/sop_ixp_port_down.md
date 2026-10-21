SOP-NET-20: Internet Exchange Port Down Protocol
1. Scope & Symptoms
Applies to a physical IX switch port or IX VLAN going down (link down, err-disable, or IX-side maintenance) while our core and customer attachments are up. Multiple IX peers on that port go quiet together.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 2 Hours to restore the IX port or shift traffic to transit / other IXs.

Primary Cause: IX switch fault, dirty optic, or IX-side maintenance — not a customer CPE or a long-haul fiber cut.

3. Immediate Technical Actions
Confirm the IX port and the IX NOC ticket. Do not dispatch a metro splice crew for a single IX handoff.

Shift outbound traffic to transit and to other IX fabrics via local-pref.

Replace the optic or move to the spare IX port if the IX NOC confirms their switch is healthy.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes if public-peer destinations are impaired.

Progress Status Updates: Every 30 minutes until the IX port is up or traffic is stable on transit.

Tone Requirement: IX-port specific. Name the exchange (for example Equinix IX). Not a datacenter power event.
