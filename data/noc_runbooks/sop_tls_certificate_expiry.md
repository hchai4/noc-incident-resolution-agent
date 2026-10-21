SOP-NET-12: TLS Certificate Expiry and Chain Failure Protocol
1. Scope & Symptoms
Applies to customer-facing or interconnect TLS certificates that are expired, revoked, or missing an intermediate. Browser and API clients fail handshake; the underlay path is up.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 1 Hour to install a valid certificate or roll to the standby listener.

Primary Cause: Missed renewal, broken ACME, or an incomplete chain after a CA change.

3. Immediate Technical Actions
Confirm expiry with openssl on the listener. Do not bounce BGP or mark the circuit down.

Install the renewed cert and full chain on the standby terminator, then fail traffic over.

If the CA is unreachable, serve the last still-valid standby cert. Do not disable TLS.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes of handshake failures.

Progress Status Updates: Every 20 minutes until handshake success is restored.

Tone Requirement: Certificate and expiry specific. Path and fiber are not in scope.
