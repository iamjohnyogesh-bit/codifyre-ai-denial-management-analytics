"""Reference data for CARC/RARC denial codes used in US healthcare RCM.

CARC = Claim Adjustment Reason Code (why the payer adjusted/denied)
RARC = Remittance Advice Remark Code (additional context)
"""

# CARC code -> (short description, denial category, appealable)
CARC_MAP = {
    "1":   ("Deductible amount", "Patient responsibility", False),
    "2":   ("Coinsurance amount", "Patient responsibility", False),
    "3":   ("Co-payment amount", "Patient responsibility", False),
    "4":   ("Procedure code inconsistent with the modifier used", "Coding / modifier", True),
    "16":  ("Claim/service lacks information needed for adjudication", "Missing information", True),
    "18":  ("Exact duplicate claim/service", "Duplicate", True),
    "22":  ("Care may be covered by another payer (COB)", "Coordination of benefits", True),
    "27":  ("Expenses incurred after coverage terminated", "Eligibility", True),
    "29":  ("The time limit for filing has expired", "Timely filing", True),
    "45":  ("Charge exceeds fee schedule / maximum allowable", "Contractual", False),
    "50":  ("Non-covered service, not deemed medical necessity", "Medical necessity", True),
    "96":  ("Non-covered charge(s)", "Non-covered service", False),
    "97":  ("Payment included in allowance for another service (bundled)", "Bundling", True),
    "109": ("Claim not covered by this payer / contractor", "Wrong payer", True),
    "197": ("Precertification/authorization absent", "Prior authorization", True),
    "204": ("Service not covered under patient's current benefit plan", "Benefit coverage", False),
    "222": ("Exceeds the contracted maximum number of hours/days/units", "Unit limit", True),
}

# RARC code -> description (common ones used with denials)
RARC_MAP = {
    "N30":  "Patient ineligible for this service",
    "N362": "Claim lacks an operative report",
    "N386": "This decision was based on a Local Coverage Determination (LCD)",
    "N425": "This is a duplicate of a previously processed claim",
    "N479": "Missing explanation of benefits (COB)",
    "N522": "Duplicate of a claim processed or to be processed",
    "M51":  "Missing/incomplete/invalid procedure code(s)",
    "M62":  "Missing/incomplete/invalid other diagnosis",
    "M76":  "Missing/incomplete/invalid diagnosis or condition",
    "M80":  "Not covered when performed during the same session/date as a previously processed service",
    "MA04": "Secondary payment cannot be considered without the primary payer's identity",
    "MA130":"Your claim contains incomplete and/or invalid information",
    "N657": "This should be billed with the appropriate code for these services",
}


def describe_carc(code):
    """Return (description, category, appealable) for a CARC code, or generic unknowns."""
    return CARC_MAP.get(str(code), ("Unknown adjustment reason", "Other", True))


def describe_rarc(code):
    """Return the description for a RARC code, or a generic placeholder."""
    return RARC_MAP.get(str(code), "See remittance advice for details")
