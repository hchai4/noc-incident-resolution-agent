from pydantic import BaseModel, Field, field_validator
from typing import Optional


class AlarmPayload(BaseModel):
    """
    Input schema representing an incoming automated network monitor alert.
    """
    incident_id: str = Field(description="Unique NOC incident ticket ID (e.g., 'INC-88912')")
    circuit_id: str = Field(description="Impacted circuit identifier (e.g., 'IEPL-9021-LAX-TYO')")
    alarm_type: str = Field(description="Standardized alarm event (e.g., 'FIBER_CUT', 'BGP_LEAK', 'POWER_FAIL', 'DDOS')")
    raw_symptom: str = Field(description="Raw telemetry alert message from monitoring sensors")
    detected_at: str = Field(description="ISO timestamp when the alarm triggered")


class IncidentNotificationDraft(BaseModel):
    """
    Output schema for the AI Incident Resolution Agent.
    Guarantees structured, audit-compliant client communications.
    """
    incident_id: str = Field(description="Incident reference identifier")
    client_name: str = Field(description="Enterprise client company name")
    circuit_id: str = Field(description="Impacted circuit identifier")
    severity: str = Field(description="Incident severity level (P1_CRITICAL, P2_MAJOR, P3_MODERATE)")
    root_cause_category: str = Field(description="Identified cause based on SOP (e.g., 'Physical Fiber Cut', 'BGP Route Leak')")
    mitigation_action_taken: str = Field(description="Immediate technical action taken by NOC engineering based on runbook")
    estimated_restoration_time: str = Field(description="Confirmed restoration ETA, or explicit statement regarding update window")
    next_update_window_minutes: int = Field(gt=0, description="Mandatory scheduled update window in minutes based on client SLA tier")
    notification_email_body: str = Field(description="Full, executive-ready formatted email communication addressed to customer contact")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid_levels = ["P1_CRITICAL", "P2_MAJOR", "P3_MODERATE", "P4_LOW"]
        v_clean = v.strip().upper()
        if v_clean not in valid_levels:
            return "P1_CRITICAL"  # Conservative default for safety
        return v_clean
        