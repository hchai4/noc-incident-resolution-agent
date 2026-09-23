SOP-NET-04: Distributed Denial of Service (DDoS) Volumetric Attack Mitigation
1. Scope & Symptoms
Applies to aggregate ingress interface saturation exceeding 50 Gbps, volumetric SYN floods, DNS amplification attacks, or distributed botnet targeting client IP prefixes.

2. Standard Service Level Agreement (SLA)
Standard Mitigation Objective: 30 Minutes to divert and cleanse traffic via scrubbing center.

Primary Cause: Malicious external volumetric targeting.

3. Immediate Technical Actions
Analyze ingress traffic distribution via NetFlow telemetry to identify targeted destination prefixes.

Announce BGP community strings to trigger Border Gateway BGP FlowSpec or BGP divert to regional scrubbing centers.

If volumetric threshold threatens edge peering links, implement selective Remotely Triggered Blackhole (RTBH) routing on attacked non-essential subnets.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes of anomaly diversion.

Progress Status Updates: Every 30 minutes until attack traffic subsides below baseline threshold.

Tone Requirement: Security-focused, analytical, confirming perimeter protection and scrubbing status.
