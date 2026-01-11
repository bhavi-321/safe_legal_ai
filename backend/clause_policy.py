from enum import Enum


class ClauseAction(str, Enum):
    REWRITE = "rewrite"
    REVIEW_ONLY = "review_only"


REWRITE_ALLOWED_RISKS = {
    "Ambiguous Termination",
    "One-Sided Termination",
    "Unclear Survival Clause",
    "Ambiguous Governing Law",
    "Asymmetric Confidentiality",
    "Ambiguous Notice Period",
    "Ambiguous Jurisdiction",
}

REVIEW_ONLY_RISKS = {
    "Uncapped Liability",
    "Unlimited Liability",
    "Unlimited Indemnity",
    "Punitive Damages Exposure",
    "Missing Liability Cap",
    "No Limitation of Liability",
    "Broad Indemnification",
    "Excessive Remedies",
}



FORBIDDEN_REWRITE_KEYWORDS = [
    "liability",
    "damages",
    "indemnify",
    "indemnification",
    "hold harmless",
    "punitive",
    "consequential",
    "incidental",
    "special damages",
    "limitation of liability",
    "liability cap",
    "cap on liability",
    "$",
]



def decide_clause_action(risk_category: str, clause_text: str) -> ClauseAction:
    """
    Decide whether a clause should be rewritten by AI
    or flagged for legal review only.

    Rules:
    1. Explicit REVIEW_ONLY risks are never rewritten
    2. Clauses touching liability, damages, or indemnity
       are never rewritten
    3. Explicit REWRITE_ALLOWED risks may be rewritten
    4. Default behavior is REVIEW_ONLY (conservative)
    """

    # Normalize inputs
    risk_category = (risk_category or "").strip()
    clause_lower = (clause_text or "").lower()

    # Explicit review-only risks
    if risk_category in REVIEW_ONLY_RISKS:
        return ClauseAction.REVIEW_ONLY

    # Keyword-based safety override
    for keyword in FORBIDDEN_REWRITE_KEYWORDS:
        if keyword in clause_lower:
            return ClauseAction.REVIEW_ONLY

    # Explicit rewrite-allowed risks
    if risk_category in REWRITE_ALLOWED_RISKS:
        return ClauseAction.REWRITE

    # Default: be conservative
    return ClauseAction.REVIEW_ONLY




UNSAFE_REWRITE_OUTPUT_TERMS = [
    "liability shall be limited",
    "in no event shall",
    "consequential damages",
    "punitive damages",
    "indirect damages",
    "$",
]


def validate_rewrite_output(rewritten_text: str) -> bool:
    """
    Validate that a rewritten clause does not introduce
    new legal concepts such as liability caps or damages exclusions.
    """
    if not rewritten_text:
        return False

    text_lower = rewritten_text.lower()
    for term in UNSAFE_REWRITE_OUTPUT_TERMS:
        if term in text_lower:
            return False

    return True

