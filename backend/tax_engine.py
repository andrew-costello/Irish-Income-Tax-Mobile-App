# backend/tax_engine.py

from dataclasses import dataclass
from typing import Dict, Any


# Use plain string instead of Literal for Swagger compatibility
Status = str


@dataclass
class TaxInput:
    employed_income: float = 0.0
    self_employed_income: float = 0.0
    status: Status = "single"
    children_under18: int = 0
    year: int = 2025


# ===== 2025 TAX CONSTANTS (Simplified & Clean) =====

# Tax bands
BAND_SINGLE = 44_000
BAND_MARRIED = 53_000
BAND_SPCCC_EXTRA = 4_000  # extra 20% band for single parents

# Credits
CREDIT_PERSONAL_SINGLE = 2_000
CREDIT_PERSONAL_MARRIED = 4_000
CREDIT_PAYE = 2_000
CREDIT_EARNED_INCOME = 2_000
CREDIT_SPCCC = 1_900

# USC
USC_EXEMPT = 13_000
USC_B1 = 12_012
USC_B2 = 27_382
USC_B3 = 70_044
USC_R1 = 0.005
USC_R2 = 0.02
USC_R3 = 0.03
USC_R4 = 0.08

# PRSI
PRSI_A_RATE = 0.041
PRSI_A_WEEKLY_EXEMPT = 352

PRSI_S_RATE = 0.04
PRSI_S_MIN = 500
PRSI_S_THRESHOLD = 5_000


# ===== SIMPLE TAX ENGINE =====

def calculate_income_tax(ti: TaxInput) -> Dict[str, float]:
    income = ti.employed_income + ti.self_employed_income

    # Standard rate band
    if ti.status == "single":
        band = BAND_SINGLE
    elif ti.status == "single_parent":
        band = BAND_SINGLE + BAND_SPCCC_EXTRA
    else:
        band = BAND_MARRIED  # married one-income

    # 20% / 40%
    std_part = min(income, band)
    high_part = max(income - band, 0)

    gross_tax = std_part * 0.20 + high_part * 0.40

    # Credits
    credits = 0

    # Personal credit
    if ti.status == "married_one_income":
        credits += CREDIT_PERSONAL_MARRIED
    else:
        credits += CREDIT_PERSONAL_SINGLE

    # PAYE vs Earned Income credit (max 2000)
    paye = CREDIT_PAYE if ti.employed_income > 0 else 0
    earned = CREDIT_EARNED_INCOME if ti.self_employed_income > 0 else 0
    credits += min(2000, paye + earned)

    # SPCCC
    if ti.status == "single_parent" and ti.children_under18 > 0:
        credits += CREDIT_SPCCC

    net_tax = max(gross_tax - credits, 0)

    return {
        "gross_tax": round(gross_tax, 2),
        "credits": round(credits, 2),
        "net_tax": round(net_tax, 2),
        "higher_rate_income": round(high_part, 2),
        "standard_rate_band": band,
    }


def calculate_usc(ti: TaxInput) -> float:
    income = ti.employed_income + ti.self_employed_income

    if income <= USC_EXEMPT:
        return 0.0

    remaining = income
    usc = 0

    # Band 1
    part = min(remaining, USC_B1)
    usc += part * USC_R1
    remaining -= part

    # Band 2
    part = min(remaining, USC_B2 - USC_B1)
    usc += part * USC_R2
    remaining -= part

    # Band 3
    part = min(remaining, USC_B3 - USC_B2)
    usc += part * USC_R3
    remaining -= part

    usc += max(remaining, 0) * USC_R4

    return round(usc, 2)


def calculate_prsi(ti: TaxInput) -> float:
    prsi = 0

    # Class A (employed)
    if ti.employed_income > 0:
        weekly = ti.employed_income / 52
        if weekly > PRSI_A_WEEKLY_EXEMPT:
            prsi += ti.employed_income * PRSI_A_RATE

    # Class S (self-employed)
    if ti.self_employed_income > PRSI_S_THRESHOLD:
        prsi += max(ti.self_employed_income * PRSI_S_RATE, PRSI_S_MIN)

    return round(prsi, 2)


def calculate_tax(ti: TaxInput) -> Dict[str, Any]:
    income = ti.employed_income + ti.self_employed_income

    it = calculate_income_tax(ti)
    usc = calculate_usc(ti)
    prsi = calculate_prsi(ti)

    total_deductions = it["net_tax"] + usc + prsi
    net_income = income - total_deductions

    return {
        "year": ti.year,
        "status": ti.status,
        "children_under18": ti.children_under18,
        "employed_income": ti.employed_income,
        "self_employed_income": ti.self_employed_income,
        "gross_income": income,

        "income_tax": it["net_tax"],
        "usc": usc,
        "prsi": prsi,
        "total_deductions": round(total_deductions, 2),
        "net_income": round(net_income, 2),
        "net_monthly": round(net_income / 12, 2),
        "net_weekly": round(net_income / 52, 2),

        "details": it,
    }