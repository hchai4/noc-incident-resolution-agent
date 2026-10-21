SOP-NET-11: NTP Clock Skew and Time-Source Failure Protocol
1. Scope & Symptoms
Applies to stratum-1/2 NTP sources drifting more than 100 ms, GPS/GNSS holdover expiry, or devices rejecting timestamps (TLS, Kerberos, log correlation).

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 2 Hours to restore a trusted time source.

Primary Cause: GNSS antenna failure, NTP anycast node isolation, or a mis-set local clock after reboot.

3. Immediate Technical Actions
Compare the sick node to two independent stratum-1 sources. Do not reboot core routers as the first step.

Move clients to the backup NTP anycast. Disable a node whose offset exceeds 100 ms.

If GNSS is down, hold over on the oven-controlled oscillator and open a facilities ticket for the antenna, not a fiber-splice ticket.

4. Mandatory Client Notification Cadence
Initial Alert: Within 20 minutes if authentication or certificates start failing.

Progress Status Updates: Every 45 minutes until offset is under 20 ms.

Tone Requirement: Time-sync specific. Do not call this a routing outage.
