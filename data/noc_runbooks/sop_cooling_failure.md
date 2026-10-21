SOP-NET-14: Datacenter Cooling Failure Protocol
1. Scope & Symptoms
Applies to CRAC/CRAH failure, raised-floor hot spots above 32 C, or chilled-water plant trip. Power and optics may still be up. This is thermal, not a utility blackout.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 90 Minutes to restore cooling or begin a controlled load shed.

Primary Cause: CRAC compressor fail, chilled-water leak, or blocked hot-aisle containment.

3. Immediate Technical Actions
Read inlet temperatures on the affected row. Do not start the diesel plant unless power is also failing.

Open emergency ventilation and drop non-critical compute first. Keep core routing on the coolest row.

If temperature is still rising after 20 minutes, start a planned migration off that hall. This is not a generator-fail playbook.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes if inlet temperature exceeds 32 C.

Progress Status Updates: Every 30 minutes until the hall is under 27 C.

Tone Requirement: Facilities-thermal. Do not describe this as a municipal power collapse.
