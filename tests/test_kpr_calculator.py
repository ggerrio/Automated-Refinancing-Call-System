import unittest
from src.kpr_calculator import (
    calculate_monthly_installment,
    format_rupiah_for_speech,
    calculate_mortgage_savings,
    flag_dnc_contact
)

class TestKprCalculator(unittest.TestCase):
    def test_monthly_installment_calculation(self):
        # Rp 500,000,000 at 12% for 10 years (120 months)
        # Formula: r = 0.01, n = 120 -> Monthly ~ Rp 7,173,546.54
        installment = calculate_monthly_installment(500_000_000, 12.0, 10)
        self.assertAlmostEqual(installment, 7173546.54, delta=100)

    def test_mortgage_savings(self):
        res = calculate_mortgage_savings(
            current_bank="BCA",
            remaining_tenure_years=10,
            loan_amount_idr=600_000_000,
            current_interest_rate=10.75,
            takeover_rate=6.50
        )
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["monthly_savings"], 0)
        self.assertIn("juta rupiah", res["spoken_pitch"])
        self.assertIn("BCA", res["current_bank"])

    def test_format_rupiah_for_speech(self):
        self.assertEqual(format_rupiah_for_speech(1_500_000), "1 koma 5 juta rupiah")
        self.assertEqual(format_rupiah_for_speech(1_000_000_000), "1 miliar rupiah")

    def test_flag_dnc_contact(self):
        res = flag_dnc_contact("+628123456789", "Tidak berminat dan minta hapus nomor")
        self.assertEqual(res["status"], "blacklisted")
        self.assertEqual(res["phone_number"], "+628123456789")
        self.assertIn("daftar blokir", res["spoken_response"])

if __name__ == "__main__":
    unittest.main()

