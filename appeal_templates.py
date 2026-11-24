"""Appeal letter template generator for common denial categories.

Each template uses Python str.format placeholders:
  claim_id, denial_id, payer, patient_ref, dos, cpt_code, icd10_code,
  billed_amount, carc_code, carc_description, provider_name
"""

TEMPLATES = {
    "Coding / modifier": """\
Re: Appeal of denied claim {claim_id} (Denial #{denial_id})
To: {payer} Claims Review Department

Date of service: {dos}
Procedure: {cpt_code}    Diagnosis: {icd10_code}
Billed amount: ${billed_amount}
Denial reason: CARC {carc_code} - {carc_description}

Dear Claims Review Team,

We are appealing the denial of the above claim. The denial states the
procedure code is inconsistent with the modifier used. After reviewing the
operative notes and CPT guidelines, the services were distinct and separately
identifiable, and the appended modifier is supported by the documentation.

Enclosed: corrected claim (if applicable), operative/procedure notes, and
supporting clinical documentation.

Please reprocess the claim for payment. Contact {provider_name} with any
questions.

Sincerely,
{provider_name} - Revenue Cycle Department
""",

    "Missing information": """\
Re: Appeal of denied claim {claim_id} (Denial #{denial_id})
To: {payer} Claims Review Department

Date of service: {dos}
Procedure: {cpt_code}    Diagnosis: {icd10_code}
Billed amount: ${billed_amount}
Denial reason: CARC {carc_code} - {carc_description}

Dear Claims Review Team,

The claim was denied for lack of information needed for adjudication. The
requested information is now enclosed: complete clinical documentation,
itemized charges, and any required attachments referenced by the remittance
remark code.

Please reprocess the claim with the attached documentation.

Sincerely,
{provider_name} - Revenue Cycle Department
""",

    "Prior authorization": """\
Re: Appeal of denied claim {claim_id} (Denial #{denial_id})
To: {payer} Claims Review Department

Date of service: {dos}
Procedure: {cpt_code}    Diagnosis: {icd10_code}
Billed amount: ${billed_amount}
Denial reason: CARC {carc_code} - {carc_description}

Dear Claims Review Team,

The claim was denied for absent precertification/authorization. We submit the
following for reconsideration: the authorization record (or, where services
were urgent/emergent, documentation of the clinical circumstances that
precluded prior authorization under the plan's own policy).

Enclosed: authorization reference (if obtained), clinical notes demonstrating
medical necessity and urgency.

Please reprocess the claim for payment.

Sincerely,
{provider_name} - Revenue Cycle Department
""",

    "Timely filing": """\
Re: Appeal of denied claim {claim_id} (Denial #{denial_id})
To: {payer} Claims Review Department

Date of service: {dos}
Procedure: {cpt_code}    Diagnosis: {icd10_code}
Billed amount: ${billed_amount}
Denial reason: CARC {carc_code} - {carc_description}

Dear Claims Review Team,

The claim was denied as past the filing limit. Our records show the claim was
originally submitted within the contractual filing window. Enclosed is the
clearinghouse acceptance report with the original submission date as proof of
timely filing.

Please reprocess the claim based on the documented original submission date.

Sincerely,
{provider_name} - Revenue Cycle Department
""",

    "Medical necessity": """\
Re: Appeal of denied claim {claim_id} (Denial #{denial_id})
To: {payer} Claims Review Department

Date of service: {dos}
Procedure: {cpt_code}    Diagnosis: {icd10_code}
Billed amount: ${billed_amount}
Denial reason: CARC {carc_code} - {carc_description}

Dear Claims Review Team,

The claim was denied as not medically necessary. The enclosed clinical
documentation demonstrates that the service meets the applicable coverage
criteria (LCD/NCD and the plan's medical policy) for the documented diagnosis.

Enclosed: progress notes, relevant test results, and the applicable coverage
policy excerpt.

Please reprocess the claim for payment.

Sincerely,
{provider_name} - Revenue Cycle Department
""",

    "Eligibility": """\
Re: Appeal of denied claim {claim_id} (Denial #{denial_id})
To: {payer} Claims Review Department

Date of service: {dos}
Procedure: {cpt_code}    Diagnosis: {icd10_code}
Billed amount: ${billed_amount}
Denial reason: CARC {carc_code} - {carc_description}

Dear Claims Review Team,

The claim was denied for coverage termination. Our eligibility verification
performed on the date of service showed active coverage. Enclosed is the
eligibility verification record (including the verification reference number
and timestamp) confirming active benefits on the date of service.

Please reprocess the claim for payment.

Sincerely,
{provider_name} - Revenue Cycle Department
""",
}

DEFAULT_TEMPLATE = TEMPLATES["Missing information"]


def generate_appeal(denial, provider_name="ABC Medical Group"):
    """Render an appeal letter for a Denial-like object.

    Expects attributes: claim_id, denial_id, payer, date_of_service,
    cpt_code, icd10_code, billed_amount, carc_code, category.
    """
    from denial_codes import describe_carc

    description, _, _ = describe_carc(denial.carc_code)
    template = TEMPLATES.get(denial.category, DEFAULT_TEMPLATE)
    return template.format(
        claim_id=denial.claim_id,
        denial_id=denial.denial_id,
        payer=denial.payer,
        patient_ref=denial.claim_id,
        dos=denial.date_of_service,
        cpt_code=denial.cpt_code,
        icd10_code=denial.icd10_code,
        billed_amount=f"{denial.billed_amount:,.2f}",
        carc_code=denial.carc_code,
        carc_description=description,
        provider_name=provider_name,
    )
