"""Prompt 5 — response schema shared by the mock and real diagnosis paths.

This is the literal JSON shape the real Gemini call must be constrained to
with response_schema when USE_MOCK=false, so the rest of the app never has
to care which path produced a DiagnosisResult.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

KNOWN_DISEASES = [
    "early_blight", "late_blight", "leaf_curl_virus", "bacterial_wilt",
    "fusarium_wilt", "blossom_end_rot", "septoria_leaf_spot",
    "spider_mite_damage", "healthy", "uncertain",
]


class DiagnosisResult(BaseModel):
    disease: str = Field(description="one of KNOWN_DISEASES")
    confidence: float = Field(ge=0.0, le=1.0)
    cited_source: Optional[str] = Field(default=None, description='e.g. "early_blight.txt Sec. 1.3"')
    treatment_recommendation: str


class DealerMatch(BaseModel):
    dealer_id: str
    name: str
    village: str
    distance_km: float
    price_per_kg: float
    treatment: str


class SellPriceMatch(BaseModel):
    market_id: str
    name: str
    distance_km: float
    price_per_quintal_today: float
    trend_direction: Literal["rising", "falling", "flat"]


class OutbreakAlert(BaseModel):
    disease: str
    nearby_report_count: int
    radius_km: float
    window_days: int
    message: str


class InsuranceClaimPacket(BaseModel):
    """Feature #1 — structured evidence packet for a crop-loss insurance claim.
    Packages data the diagnosis pipeline already produces into the shape an
    insurer's claim form actually asks for, so a farmer with crop insurance
    has something fileable instead of a diagnosis that goes no further."""
    claim_id: str
    generated_at: str
    plot_id: Optional[str] = None
    disease: str
    confidence: float
    cited_source: Optional[str] = None
    severity_estimate: Literal["moderate", "severe"]
    estimated_yield_loss_pct: int
    evidence_summary: str
    recommended_next_step: str


class GroupBuyAlert(BaseModel):
    """Feature #3 — turns an outbreak signal into a coordinated economic
    action: nearby farmers who all need the same treatment this week can
    buy together for a bulk discount, instead of each paying full price
    alone at the same dealer."""
    treatment: str
    nearby_farmer_count: int
    dealer_name: str
    dealer_distance_km: float
    standard_price_per_kg: float
    bulk_price_per_kg: float
    bulk_threshold_kg: float
    message: str


class OutbreakCluster(BaseModel):
    disease: str
    report_count: int
    center_village: str
    severity: Literal["watch", "elevated", "critical"]


class DistrictDashboard(BaseModel):
    """Feature #5 — an aggregated, anonymized view for an extension officer
    or local agricultural body: no single farmer's data, just district-wide
    signal, so the same data that serves one farmer at a time can also
    inform a policy or resourcing decision."""
    generated_at: str
    window_days: int
    total_diagnosis_reports: int
    disease_counts: dict[str, int]
    active_outbreak_clusters: List[OutbreakCluster]
    most_requested_treatment: Optional[str] = None
    plots_monitored: int


class AdvisoryResponse(BaseModel):
    diagnosis: DiagnosisResult
    weather_note: Optional[str] = None
    advisory_text_en: str
    advisory_text_local: str
    local_language: str
    audio_available: bool
    dealer: Optional[DealerMatch] = None
    sell_price: Optional[SellPriceMatch] = None
    outbreak_alert: Optional[OutbreakAlert] = None
    plot_memory_note: Optional[str] = None
    insurance_claim: Optional[InsuranceClaimPacket] = None
    group_buy_alert: Optional[GroupBuyAlert] = None
