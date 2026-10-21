SOP-NET-09: Application-Layer (L7) Attack Mitigation Protocol
1. Scope & Symptoms
Applies to HTTP/HTTPS or API abuse (slowloris, credential stuffing, cache-busting GET floods) where the edge link is not saturated. NetFlow shows normal or modest bits-per-second and a spike in requests-per-second against one hostname or URL.

2. Standard Service Level Agreement (SLA)
Standard Mitigation Objective: 45 Minutes to rate-limit or WAF-challenge the abusive requests.

Primary Cause: Application-layer botnet or scripted HTTP clients, not a volumetric SYN or DNS amplification flood.

3. Immediate Technical Actions
Do not announce RTBH or divert the whole prefix to a volumetric scrubbing center as the first step.

Enable WAF challenge / bot score and rate-limit the targeted URI on the load balancer.

If origin CPU is the bottleneck, fail open only the health-check path and keep the rest behind the challenge. Do not blackhole the customer prefix.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes of confirmed L7 abuse.

Progress Status Updates: Every 30 minutes until origin error rate is back under baseline.

Tone Requirement: Application-security focused. Do not describe this as a 50 Gbps volumetric DDoS.
