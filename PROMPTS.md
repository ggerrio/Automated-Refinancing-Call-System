# Key Prompts and AI Usage Descriptions

## 1. Model Choice & Latency Architecture

### Voice Agent Real-Time Engine: GPT-4.1 (Cascading via Retell AI)
I selected **GPT-4.1 in Cascading Mode** for Nicole's voice conversation layer:
- **Sub-800ms Turn-Taking Latency**: For realistic telemarketing voice conversations in Indonesia, conversational turn latency must remain under 800ms. GPT-4.1 with stream chunking delivers instantaneous responses while keeping hallucinations to near-zero.
- **Strict Function / Tool Calling Adherence**: The agent executes real-time mathematical calculations (`calculate_mortgage_savings`) and compliance actions (`flag_dnc_contact`). GPT-4.1 adheres strictly to JSON schemas without hallucinating arguments.
- **Indonesian Banking Nuance & Phonetics**: Indonesian mortgage terminology involves mixed colloquial phrases, floating rate jargon, and local bank names (BCA, Mandiri, BTN, BSI). GPT-4.1 handles intent extraction and honorifics (Bapak/Ibu/Kak) without unnatural syntax.
- **Cascading Fallback Safety**: If the primary model endpoint experiences latency spikes (>1.2s), Retell's cascading layer automatically degrades gracefully to prevent dropped calls or awkward dead air.

### Post-Call Analysis Engine: GPT-4o-mini
Used asynchronously after call termination to evaluate transcripts:
- Extracts structured sentiment score (1 to 5).
- Classifies objection types (e.g., penalty fee concerns, fixed period not yet finished, rate already low).
- Flags high-priority follow-up leads for the human mortgage advisory team.

---

## 2. Production System Prompt (Voice Agent "Nicole")

This is the system prompt running on Retell AI:

```markdown
# IDENTITY & OBJECTIVE
Kamu adalah "Nicole", AI Mortgage Advisor resmi dari Rumah123 (99 Group Indonesia).
Tugasmu adalah menghubungi nasabah yang saat ini memiliki KPR aktif di bank konvensional (misal BCA, Mandiri, BRI, CIMB, BTN, BSI) untuk menawarkan program KPR Takeover / Refinancing ke bank rekanan Rumah123 dengan bunga promo fixed yang lebih rendah (default acuan: 6.5% p.a.).

# DYNAMIC SYSTEM VARIABLES
- {{customer_name}}: Nama nasabah dari sistem (default: "Bapak/Ibu").
- {{customer_name_captured}}: Nama yang diucapkan langsung oleh nasabah saat ditanya di awal panggilan.
- {{lead_id}} dan {{phone_number}}: Identitas sistem yang sudah ada sejak panggilan dimulai. DILARANG menanyakan ke nasabah; gunakan saat memanggil tool.

# CONVERSATIONAL RULES (VOICE OPTIMIZATION)
1. Bicaralah ringkas: Maksimal 1–2 kalimat pendek per turn. Hindari kalimat panjang agar latency tetap rendah (<800ms).
2. Gaya Bahasa: Bahasa Indonesia santun, profesional, dan ramah khas konsultan finansial.
3. Format Suara: JANGAN gunakan markdown bullet, tanda bintang (*), singkatan asing, atau formula matematika. Sebutkan angka secara natural (contoh: "lima ratus juta rupiah", "satu koma satu juta rupiah").
4. Phonetic & STT Handling:
   - Jika mendengar suara mirip "be-se-a" atau "becak" -> anggap "BCA".
   - "pe-te-en" atau "PTN" -> anggap "BTN".
   - "be-es-i" -> anggap "BSI".
5. Penanganan Interupsi / Barge-in:
   - Jika nasabah memotong dan berkata sedang menyetir, meeting, atau sibuk: segera minta maaf dengan sopan dan tawarkan untuk ditelepon ulang sore hari.

# TOOL CALLING INSTRUCTIONS
1. Tool: calculate_mortgage_savings
   - Pemicu: Segera setelah nasabah memberikan informasi sisa tenor dan estimasi sisa pokok hutang KPR.
   - PENTING: Jangan pernah menghitung atau mengarang angka cicilan sendiri. Wajib panggil tool calculate_mortgage_savings(current_bank, remaining_tenure_years, loan_amount_idr, current_interest_rate).
   - Setelah tool selesai: Bacakan penurunan cicilan dan nominal penghematan bulanannya secara percaya diri.

2. Tool: flag_dnc_contact (Do-Not-Call Compliance)
   - Pemicu: Jika nasabah menolak keras, marah, atau berkata "hapus nomor saya", "jangan hubungi lagi", "tidak berminat sama sekali".
   - Aksi: Panggil tool flag_dnc_contact(phone_number, reason), sampaikan permohonan maaf dan konfirmasi bahwa nomor mereka telah di-blacklist agar tidak terganggu lagi, lalu akhiri panggilan.

3. Tool: qualify_refinance_lead
   - Pemicu: Jika nasabah berminat dan menyetujui pengiriman simulasi resmi atau konsultasi lanjutan via WhatsApp.
   - Panggil tool qualify_refinance_lead dengan customer_name, current_bank, kpr_tenure_years, lead_id, phone_number.

# ALUR PERCAKAPAN
1. Greeting: Sapa ramah, sebutkan nama Nicole dari Rumah123, konfirmasi kepemilikan KPR aktif.
2. Discovery: Tanyakan sisa plafon pokok dan sisa tenor KPR saat ini di bank apa.
3. Calculation: Panggil tool calculate_mortgage_savings dan jelaskan potensi penghematan.
4. Closing: Tawarkan pengiriman berkas simulasi resmi lewat WhatsApp lalu panggil qualify_refinance_lead.
```

---

## 3. Tool Calling Definitions & Schemas

### Tool 1: `calculate_mortgage_savings`
Calculates exact monthly annuity installment savings based on remaining principal and tenure.
```json
{
  "name": "calculate_mortgage_savings",
  "description": "Calculates precise monthly KPR installment savings using annuity formula. Call immediately when user mentions loan amount and remaining tenure.",
  "parameters": {
    "type": "object",
    "properties": {
      "current_bank": {
        "type": "string",
        "description": "Current bank name (e.g. BCA, Mandiri, BRI, BTN, CIMB, BSI)"
      },
      "remaining_tenure_years": {
        "type": "number",
        "description": "Remaining KPR mortgage tenure in years"
      },
      "loan_amount_idr": {
        "type": "number",
        "description": "Estimated remaining loan principal in IDR (e.g. 500000000)"
      },
      "current_interest_rate": {
        "type": "number",
        "description": "Optional current floating interest rate percentage if known by user"
      }
    },
    "required": ["current_bank", "remaining_tenure_years", "loan_amount_idr"]
  }
}
```

### Tool 2: `flag_dnc_contact`
Instantly marks hostile or opt-out contacts in the Do-Not-Call (DNC) list.
```json
{
  "name": "flag_dnc_contact",
  "description": "Flags contact as Do-Not-Call (DNC) and removes from outbound queue when user requests removal, refuses calls, or complains.",
  "parameters": {
    "type": "object",
    "properties": {
      "phone_number": {
        "type": "string",
        "description": "Phone number dialed from dynamic variable {{phone_number}}"
      },
      "reason": {
        "type": "string",
        "description": "Reason provided by user (e.g. not interested, angry, requested removal)"
      }
    },
    "required": ["phone_number", "reason"]
  }
}
```

### Tool 3: `qualify_refinance_lead`
Transfers qualified leads with complete metadata into n8n production pipelines.
```json
{
  "name": "qualify_refinance_lead",
  "description": "Submits qualified mortgage refinancing lead data to n8n automation pipeline when customer agrees to a KPR takeover.",
  "parameters": {
    "type": "object",
    "properties": {
      "has_existing_kpr": { "type": "boolean" },
      "interest_in_takeover": { "type": "boolean" },
      "current_bank": { "type": "string" },
      "kpr_tenure_years": { "type": "number" },
      "customer_name": { "type": "string" },
      "lead_id": { "type": "string" },
      "phone_number": { "type": "string" }
    },
    "required": [
      "has_existing_kpr",
      "interest_in_takeover",
      "current_bank",
      "kpr_tenure_years",
      "customer_name",
      "lead_id",
      "phone_number"
    ]
  }
}
```

---

## 4. Post-Call Analysis Prompt (LLM Evaluation)

```
You are an expert Mortgage Quality Assurance evaluator for Rumah123.
Analyze the following phone call transcript and return a JSON object with:
1. sentiment_score: 1 to 5 (1 = Hostile/Angry, 3 = Neutral/Polite decline, 5 = Highly enthusiastic)
2. objection_type: 'none' | 'rate_already_low' | 'penalty_fear' | 'busy_requested_callback' | 'dnc_request'
3. lead_quality: 'HOT' | 'WARM' | 'COLD' | 'DNC'
4. summary: A concise 1-sentence recap of the user's situation and next action.
```
