SOP-NET-02: BGP Flapping and Route Leak Mitigation Protocol
1. Scope & Symptoms
Applies to Border Gateway Protocol (BGP) neighbor state changes, route flapping, AS-Path hijacking, or unintended route leak anomalies causing prefix withdrawal and packet drops.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 1 Hour from anomaly detection.

Primary Cause: Upstream peer misconfiguration, peering router memory overflow, or autonomous system policy mismatches.

3. Immediate Technical Actions
Inspect BGP route-flap damping counters on border edge routers (AS-Level peering interfaces).

Apply ingress prefix-filter policies to discard leaked announcements.

If peering neighbor fails to stabilize, shut down the primary BGP session and divert transit traffic through secondary Tier-1 upstream transit provider.

4. Mandatory Client Notification Cadence
Initial Alert: Within 10 minutes of peering flap detection.

Progress Status Updates: Every 20 minutes until routing tables converge globally.

Tone Requirement: Urgent, technical, highlighting autonomous routing isolation and active traffic rerouting.
