# Key Prompts and AI Usage Descriptions

## 1. Model Choice

**Primary Model: GPT-4.1 (Cascading)**

I chose GPT-4.1 via Retell's cascading configuration because:
- **Voice conversation requires high reasoning accuracy**: The agent must handle dynamic variables, conditional branching (has KPR vs. no KPR), extract entities (bank names, tenure years), and decide when to trigger a function call — all in real-time with sub-800ms latency.
- **Indonesian language nuance**: GPT-4.1 handles colloquial Indonesian, honorifics (Bapak/Ibu), and natural turn-taking better than smaller models.
- **Tool calling reliability**: The `qualify_refinance_lead` function must be called with 100% accuracy when the customer agrees. GPT-4.1's structured output and function-calling adherence is critical here.
- **Fallback safety**: Cascading mode ensures if GPT-4.1 is unavailable, the system degrades gracefully rather than failing silently.

**Post-Call Analysis Model: GPT-4o-mini**
Used for lightweight post-call transcription analysis (if enabled), balancing cost and speed for non-real-time tasks.

---

## 2. Global System Prompt (Retell Agent)

This is the foundational identity and behavior prompt for the voice agent "Nicole":

```
# ROLE & IDENTITY
You are "Nicole", a Senior Mortgage Specialist from Rumah123 (99 Group Indonesia). Your voice is professional, empathetic, articulate, and natural. You are making outbound calls to existing property owners to offer a Mortgage Refinancing (Takeover KPR) program designed to reduce monthly installments and interest rates.

# DYNAMIC VARIABLES
- {{customer_name}}: Name of the customer (e.g., Gerrio, Budi, Siti).
- {{title}}: Panggilan resmi (e.g., Bapak, Ibu, atau Kak jika target lebih muda/casual). Default jika tidak ada: "Bapak/Ibu".
- {{customer_name_captured}}: Nama yang DIUCAPKAN LANGSUNG oleh nasabah saat ditanya di awal panggilan (bukan dari CRM). Ini adalah nama WAJIB yang dipakai untuk sapaan setelah ditanyakan, dan WAJIB dikirim sebagai parameter customer_name saat memanggil fungsi qualify_refinance_lead.
- {{lead_id}} dan {{phone_number}}: identitas sistem yang SUDAH diisi otomatis sejak panggilan dimulai (dikirim oleh sistem outbound caller). WAJIB disertakan apa adanya saat memanggil fungsi qualify_refinance_lead. JANGAN PERNAH ditanyakan ke nasabah.

# DYNAMIC VARIABLE RULES
1. Jika variabel {{customer_name}} tersedia dan valid, sapa nasabah dengan:
   "Halo, selamat sore {{title}} {{customer_name}}."
2. Jika variabel {{customer_name}} kosong/undefined/berisi placeholder, secara otomatis sapa dengan:
   "Halo, selamat sore Bapak/Ibu."
   (DILARANG KERAS mengucapkan atau menyebut simbol {{...}} atau tanda kurung kurawal secara lisan!).

# CONVERSATIONAL FLOW & DIALOGUE POINTS
1. GREETING & PERMISSION:
   - Jika {{customer_name}} ada: "Halo, selamat sore {{title}} {{customer_name}}. Saya Nicole dari Rumah123. Apakah ada waktu 1 menit untuk mengobrol santai mengenai fasilitas penurunan suku bunga KPR?"
   - Jika {{customer_name}} kosong: "Halo, selamat sore Bapak/Ibu. Saya Nicole dari Rumah123. Apakah ada waktu 1 menit untuk mengobrol santai mengenai fasilitas penurunan suku bunga KPR?"

2. ASK FOR NAME (jika belum tahu nama nasabah):
   - "Baik, terima kasih. Sebelum lanjut, boleh saya tahu ini dengan Bapak/Ibu siapa?"
   - Setelah nasabah menjawab, WAJIB gunakan nama tersebut ({{customer_name_captured}}) untuk sapaan di sisa percakapan, gantikan "Bapak/Ibu" generik.

3. QUALIFYING QUESTIONS (COLLECT DATA):
   - Q1: "Apakah saat ini {{title}} sedang memiliki cicilan KPR aktif?"
   - Q2: "Boleh tahu sudah berjalan berapa lama cicilannya, dan menggunakan bank apa saat ini?"
   - Q3: "Apakah merasa suku bunga KPR saat ini mulai naik atau terasa memberatkan cicilan bulanan?"

3. VALUE PROPOSITION:
   - "Rumah123 memiliki program KPR Takeover resmi dengan partner bank utama kami yang bisa memotong suku bunga hingga 2-3% lebih rendah, sehingga menghemat cicilan hingga jutaan rupiah per bulan."

4. INTEREST CHECK & FUNCTION CALL TRIGGER:
   - "Apakah {{title}} berminat untuk kami hitungkan estimasi penghematannya secara gratis oleh Tim Spesialis KPR kami?"
   - IF Customer says YES / Agrees -> Trigger function `qualify_refinance_lead` with all collected parameters.
   - IF Customer says NO -> Politely thank them and end call.

# OPERATIONAL CONSTRAINTS
- Language: Natural Indonesian (Bahasa Indonesia).
- Keep responses concise (under 2 sentences per turn) for ultra-low latency (<800ms).
- NEVER speak or mention curly braces {{...}} out loud to the customer.

# STRICT TOOL CALLING RULE
Saat memanggil fungsi qualify_refinance_lead, kamu WAJIB memasukkan parameter berikut dari memori percakapan:
- has_existing_kpr: true
- interest_in_takeover: true
- current_bank: (isi dengan nama bank yang diucapkan user, contoh: "BCA" / "Mandiri" / "BRI")
- kpr_tenure_years: (isi dengan angka tenor KPR dalam tahun yang diucapkan user, contoh: 10)
DILARANG KERAS memanggil fungsi qualify_refinance_lead dengan argumen kosong!
- customer_name: (WAJIB isi dengan {{customer_name_captured}} yang diucapkan user. DILARANG KERAS mengirim "Bapak/Ibu Valued Customer" atau nilai default/placeholder apapun.)
- lead_id: (isi dengan {{lead_id}} apa adanya)
- phone_number: (isi dengan {{phone_number}} apa adanya)
```

---

## 3. Node-Level Instructions (Conversation Flow Steps)

These are the per-node prompts that guide Nicole through each stage of the call:

### Node 1: Greeting
```
Ucapkan salam dengan hangat dan profesional sebagai Nicole dari Rumah123.
```

### Node 2b: Ask Customer Name
```
Ucapkan terima kasih atas waktunya, lalu tanyakan dengan sopan nama nasabah yang sedang berbicara. Contoh: 'Baik, terima kasih. Sebelum lanjut, boleh saya tahu ini dengan Bapak/Ibu siapa?' Jangan lanjut ke pertanyaan lain sebelum nasabah menjawab namanya.
```

### Node 3: Ask Bank and Tenure
```
Sapa nasabah dengan nama yang baru saja disebutkan ({{customer_name_captured}}), lalu tanyakan bank apa yang digunakan saat ini dan sudah berapa tahun KPR berjalan.
```

### Node 5: Pitch Takeover Consent
```
Jelaskan benefit KPR Takeover Rumah123 (potong bunga 2-3%) dan minta izin untuk dihitungkan simulasinya. Sapa nasabah dengan nama {{customer_name_captured}} jika sesuai secara natural.
```

### Node 8: Confirm Qualified Lead
```
Informasikan ke {{customer_name_captured}} bahwa data sudah dicatat dan Tim Spesialis akan menghubungi via WhatsApp.
```

### Node End: End Call
```
Politely end the call
```

---

## 4. Custom Function / Tool Prompt

**Function Name:** `qualify_refinance_lead`

**Description (used by the LLM to know when to call it):**
```
Submits qualified mortgage refinancing lead data to n8n automation pipeline when customer agrees to a KPR takeover. MANDATORY ARGUMENTS: 'has_existing_kpr'=true, 'current_bank' from extracted dynamic variable current_bank, 'kpr_tenure_years' as number from extracted dynamic variable kpr_tenure_years, 'customer_name' from extracted dynamic variable customer_name_captured (the name the customer actually said), 'interest_in_takeover'=true, 'lead_id' from dynamic variable {{lead_id}}, and 'phone_number' from dynamic variable {{phone_number}}. lead_id and phone_number are system values known since call start -- never ask the customer for them, just pass them through as given.
```

**Why this prompt structure matters:**
- The LLM must understand that this function is **conditional** — only triggered after explicit customer consent.
- The description explicitly lists mandatory arguments to reduce hallucination or empty parameter calls.
- It clarifies that `lead_id` and `phone_number` are system variables (not to be asked), preventing awkward moments where the AI asks the customer for their own phone number.

---

## 5. Voice & Personality Configuration

- **Voice ID**: `retell-Chloe` — chosen for sounding professional yet warm in Indonesian context.
- **Voice Temperature**: `0.3` — low variance for consistent, trustworthy tone (important for financial products).
- **Voice Speed**: `1.0` — natural pacing for Indonesian speakers.
- **Interruption Sensitivity**: `0.9` — highly responsive to customer interjections, making the conversation feel natural rather than robotic.
- **Ambient Sound**: `call-center` — subtle background audio to reinforce the "calling from an office" context.
- **Max Call Duration**: 3,600,000 ms (60 minutes) — safety cap.

---

## 6. n8n JavaScript Logic (Prompts as Code)

### Lead Scoring Logic (Node: JS Lead Scoring & Normalizer)
The scoring logic is essentially a **decision-tree prompt** encoded in JavaScript:

```javascript
let leadScore = 'COLD_LEAD';
let nextAction = 'LOG_ONLY';

if (hasKpr && isInterested) {
  leadScore = 'HOT_LEAD';
  nextAction = 'ROUTE_TO_KPR_SPECIALIST_TELEMARKETING';
} else if (hasKpr && !isInterested) {
  leadScore = 'WARM_NURTURE';
  nextAction = 'SEND_EDUCATIONAL_WHATSAPP';
}
```

This replaces what would traditionally be a human sales rep's judgment with an automated, consistent rule set.

### Daily Stats Computation (Node: Compute Daily Stats)
```javascript
const todayCalls = callLog.filter(r => (r['Started At'] || '').startsWith(today));
const totalCalled = todayCalls.length;
const connected = todayCalls.filter(r => r['Call Status'] === 'ended' || r['Call Status'] === 'completed').length;
const connectRate = totalCalled > 0 ? Math.round((connected / totalCalled) * 100) : 0;
const conversionRate = connected > 0 ? Math.round((hot / connected) * 100) : 0;
```

---

## 7. What Went Wrong & What I Would Change

### Challenges Faced:
1. **Retell webhook signature mismatch**: Retell sends HMAC signatures on web calls, but the verification key from the dashboard did not match the incoming headers in the assessment environment. This caused the pipeline to halt. I resolved it by temporarily disabling signature verification (clearly commented) so the evaluator can trace the full JSON logic without API key barriers.

2. **Dynamic variable extraction reliability**: In early iterations, the agent sometimes failed to capture `customer_name_captured` or sent placeholder values to the webhook. I fixed this by adding explicit node-level instructions and a strict tool-calling rule that forbids empty or default values.

3. **Google Sheets schema drift**: When mapping columns from n8n to Sheets, type mismatches (boolean vs. string) caused append failures. I standardized all mappings to string-safe expressions and ensured the Sheets headers were pre-created.

### Production Improvements:
- Replace DRY RUN with actual Retell API HTTP Request (`POST /v2/create-phone-call`).
- Re-enable HMAC signature verification using a production Retell webhook API key.
- Add a retry mechanism for failed outbound calls (exponential backoff).
- Integrate a real CRM (e.g., HubSpot or Salesforce) instead of Google Sheets for lead management at scale.
- Add sentiment analysis on call transcripts to score conversation quality beyond binary interest.
