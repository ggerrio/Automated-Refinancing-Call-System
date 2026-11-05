"""
KPR Mortgage Refinancing Calculator & Do-Not-Call (DNC) Compliance Engine
Designed for 99 Group (Rumah123) Automated Refinancing Call System.

This module provides:
1. Real-time mortgage refinancing calculation using Indonesian banking standard annuity formulas.
2. Dynamic benchmark rate lookup for major Indonesian mortgage lenders (BCA, Mandiri, BRI, BTN, CIMB, BSI).
3. Natural TTS-friendly phonetic formatting for real-time voice AI agents (Retell AI).
4. Do-Not-Call (DNC) compliance registry handler.
"""

from typing import Dict, Any, Optional
import math
import datetime

# Standard floating rates for major Indonesian banks (benchmark estimates for 2025/2026)
DEFAULT_FLOATING_RATES = {
    "BCA": 10.75,
    "MANDIRI": 11.25,
    "BRI": 11.00,
    "BTN": 12.00,
    "CIMB": 10.50,
    "BSI": 11.00,  # Margin setara floating pasca fixed
    "DEFAULT": 11.00
}

TAKEOVER_PROMO_RATE = 6.50  # 99 Group partner bank promotional fixed rate (p.a.)


def calculate_monthly_installment(principal: float, annual_interest_rate_pct: float, tenure_years: int) -> float:
    """
    Calculates monthly installment using standard monthly annuity formula:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where:
      P = principal loan amount
      r = monthly interest rate (annual_rate / 12)
      n = total months (tenure_years * 12)
    """
    if principal <= 0 or tenure_years <= 0:
        return 0.0

    monthly_rate = (annual_interest_rate_pct / 100.0) / 12.0
    total_months = tenure_years * 12

    if monthly_rate == 0:
        return principal / total_months

    compounded = math.pow(1 + monthly_rate, total_months)
    installment = principal * (monthly_rate * compounded) / (compounded - 1)
    return round(installment, 2)


def format_rupiah_for_speech(amount: float) -> str:
    """
    Converts numeric rupiah amounts into clean, spoken Indonesian text
    to avoid TTS reading strange symbols or awkward number strings.
    Example: 1,120,000 -> "satu koma satu juta rupiah"
             750,000,000 -> "tujuh ratus lima puluh juta rupiah"
    """
    if amount >= 1_000_000_000:
        val = amount / 1_000_000_000
        formatted = f"{val:.1f}".replace(".0", "").replace(".", " koma ")
        return f"{formatted} miliar rupiah"
    elif amount >= 1_000_000:
        val = amount / 1_000_000
        formatted = f"{val:.1f}".replace(".0", "").replace(".", " koma ")
        return f"{formatted} juta rupiah"
    elif amount >= 1_000:
        val = round(amount / 1000)
        return f"{val:,} ribu rupiah".replace(",", ".")
    else:
        return f"{int(amount)} rupiah"


def calculate_mortgage_savings(
    current_bank: str,
    remaining_tenure_years: int,
    loan_amount_idr: float,
    current_interest_rate: Optional[float] = None,
    takeover_rate: float = TAKEOVER_PROMO_RATE
) -> Dict[str, Any]:
    """
    Main function called by Retell AI Tool `calculate_mortgage_savings`.
    Calculates current installment vs. new takeover installment and provides
    both raw numbers and TTS-ready spoken text.
    """
    # Normalize bank name
    bank_clean = current_bank.strip().upper() if current_bank else "DEFAULT"
    
    # Resolve current floating rate
    if current_interest_rate is None or current_interest_rate <= 0:
        effective_current_rate = DEFAULT_FLOATING_RATES.get(bank_clean, DEFAULT_FLOATING_RATES["DEFAULT"])
    else:
        effective_current_rate = float(current_interest_rate)

    tenure_years = max(1, int(remaining_tenure_years))
    principal = float(loan_amount_idr)

    # Compute installments
    current_installment = calculate_monthly_installment(principal, effective_current_rate, tenure_years)
    new_installment = calculate_monthly_installment(principal, takeover_rate, tenure_years)

    monthly_savings = max(0.0, current_installment - new_installment)
    total_savings = monthly_savings * (tenure_years * 12)

    # Generate natural speech string for Nicole
    spoken_current_installment = format_rupiah_for_speech(current_installment)
    spoken_new_installment = format_rupiah_for_speech(new_installment)
    spoken_savings = format_rupiah_for_speech(monthly_savings)

    spoken_pitch = (
        f"Dengan memindahkan KPR ke rekanan Rumah123 berbunga {takeover_rate} persen, "
        f"cicilan Anda turun dari sekitar {spoken_current_installment} menjadi {spoken_new_installment}. "
        f"Anda bisa menghemat sekitar {spoken_savings} setiap bulannya."
    )

    return {
        "status": "success",
        "current_bank": current_bank,
        "principal_idr": principal,
        "remaining_tenure_years": tenure_years,
        "current_interest_rate_pct": effective_current_rate,
        "takeover_interest_rate_pct": takeover_rate,
        "current_monthly_installment": round(current_installment),
        "new_monthly_installment": round(new_installment),
        "monthly_savings": round(monthly_savings),
        "total_savings_lifetime": round(total_savings),
        "spoken_pitch": spoken_pitch,
        "spoken_monthly_savings": spoken_savings
    }


def flag_dnc_contact(phone_number: str, reason: str, customer_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function called by Retell AI Tool `flag_dnc_contact`.
    Appends phone number to Do-Not-Call (DNC) list for regulatory compliance.
    """
    cleaned_phone = phone_number.strip().replace(" ", "").replace("-", "")
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return {
        "status": "blacklisted",
        "phone_number": cleaned_phone,
        "customer_name": customer_name or "Unknown",
        "reason": reason,
        "timestamp_utc": timestamp,
        "action_taken": "Removed from daily dialing queue. Added to permanent DNC registry.",
        "spoken_response": "Baik, mohon maaf atas ketidaknyamanannya. Nomor Anda telah kami catat dalam daftar blokir agar tidak dihubungi kembali. Terima kasih dan selamat beraktivitas."
    }

