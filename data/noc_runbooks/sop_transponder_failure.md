SOP-NET-16: DWDM Transponder or Muxponder Failure Protocol
1. Scope & Symptoms
Applies to a single wavelength going down (LOS on one channel, high BER, or transponder card alarm) while the fiber plant and other channels on the same span remain up. OTDR of the cable is clean.

2. Standard Service Level Agreement (SLA)
Standard Recovery Objective: 3 Hours to swap the card or retune the spare wavelength.

Primary Cause: Transponder optics, client SFP, or line-card failure — not a physical cable cut.

3. Immediate Technical Actions
Confirm OTDR is clean and neighbor channels are up. Do not dispatch a splice team.

Fail the service onto a protection wavelength or a spare transponder in the same chassis.

If no spare, roll the client port to an alternate line system. Replace the failed card in-chassis.

4. Mandatory Client Notification Cadence
Initial Alert: Within 15 minutes of confirmed card failure.

Progress Status Updates: Every 45 minutes until the wavelength is error-free.

Tone Requirement: Hardware/wavelength specific. Explicitly not a metro fiber cut.
