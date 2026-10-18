"""Feature #1 — crop-loss insurance claim assistant.

Most smallholder farmers who DO have crop insurance never file a claim
because the paperwork and evidence requirements are a barrier they can't
clear alone. This packages data the diagnosis pipeline already produces
(timestamped diagnosis, citation, confidence) into the structured evidence
shape an insurer's claim form actually asks for.

Real logic, no mocking needed -- this is pure packaging of data already
generated elsewhere in the pipeline.
"""
import uuid
from datetime import datetime

from schemas import DiagnosisResult, InsuranceClaimPacket

# Diseases severe/fast-moving enough that a confirmed diagnosis plausibly
# justifies starting a claim, with a rough yield-loss estimate per severity
# band. These are illustrative demo figures, not actuarial numbers -- a real
# deployment would source this from an agricultural insurer's own loss tables.
_CLAIMABLE_DISEASES = {
    "early_blight": {"severity": "moderate", "yield_loss_pct": 15},
    "late_blight": {"severity": "severe", "yield_loss_pct": 35},
    "bacterial_wilt": {"severity": "severe", "yield_loss_pct": 40},
    "fusarium_wilt": {"severity": "severe", "yield_loss_pct": 30},
    "leaf_curl_virus": {"severity": "moderate", "yield_loss_pct": 20},
}

_MIN_CONFIDENCE_TO_CLAIM = 0.6


def build_insurance_claim_packet(diagnosis: DiagnosisResult, plot_id: str | None = None) -> InsuranceClaimPacket | None:
    """Returns a claim packet only when the diagnosis is both severe enough
    and confident enough to be worth a farmer's time filing -- a low-
    confidence or minor-disorder diagnosis correctly returns None rather
    than nudging someone toward a claim that likely won't be approved."""
    profile = _CLAIMABLE_DISEASES.get(diagnosis.disease)
    if not profile or diagnosis.confidence < _MIN_CONFIDENCE_TO_CLAIM:
        return None

    now = datetime.now()
    claim_id = f"CLM-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    evidence_summary = (
        f"Diagnosis: {diagnosis.disease.replace('_', ' ')} "
        f"({int(diagnosis.confidence * 100)}% confidence), grounded in "
        f"{diagnosis.cited_source or 'the regional disease guide'}. "
        f"Estimated yield loss: {profile['yield_loss_pct']}% if untreated."
    )

    return InsuranceClaimPacket(
        claim_id=claim_id,
        generated_at=now.isoformat(timespec="seconds"),
        plot_id=plot_id,
        disease=diagnosis.disease,
        confidence=diagnosis.confidence,
        cited_source=diagnosis.cited_source,
        severity_estimate=profile["severity"],
        estimated_yield_loss_pct=profile["yield_loss_pct"],
        evidence_summary=evidence_summary,
        recommended_next_step=(
            "This evidence packet is ready to attach to a crop-loss insurance claim. "
            "Take 2-3 more photos today dated clearly, then contact your insurer's "
            "local agent or helpline to file within the standard reporting window."
        ),
    )


if __name__ == "__main__":
    from gemini_client import diagnose_crop_photo

    diagnosis = diagnose_crop_photo("the whole plant wilted suddenly but leaves are still green")
    packet = build_insurance_claim_packet(diagnosis, plot_id="P001")
    print(packet.model_dump_json(indent=2) if packet else "No claim packet generated (not severe/confident enough).")

    diagnosis_healthy = diagnose_crop_photo("everything looks fine, plant is green and growing well")
    packet_healthy = build_insurance_claim_packet(diagnosis_healthy, plot_id="P002")
    print("\nHealthy case:", packet_healthy)
