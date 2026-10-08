"""
Zero-dependency PDF generator for CARELYNX sample medical records.
Generates standard PDF 1.4 files containing realistic hospital discharge summaries.
"""

def create_pdf(filename: str, text_lines: list[tuple[str, int, float, float]]):
    """
    text_lines is a list of (text, font_size, x_pt, y_pt) where (0,0) is bottom-left.
    Standard Letter page is 612 x 792 pt.
    """
    stream_content = []
    # Begin text object
    stream_content.append("BT")
    for text, font_size, x, y in text_lines:
        safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content.append(f"/F1 {font_size} Tf")
        stream_content.append(f"1 0 0 1 {x} {y} Tm")
        stream_content.append(f"({safe_text}) Tj")
    stream_content.append("ET")
    
    stream_data = "\n".join(stream_content).encode("latin-1")
    stream_len = len(stream_data)
    
    body = (
        f"%PDF-1.4\n"
        f"1 0 obj\n"
        f"<< /Type /Catalog /Pages 2 0 R >>\n"
        f"endobj\n"
        f"2 0 obj\n"
        f"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        f"endobj\n"
        f"3 0 obj\n"
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
        f"endobj\n"
        f"4 0 obj\n"
        f"<< /Length {stream_len} >>\n"
        f"stream\n"
    ).encode("latin-1") + stream_data + (
        b"\nendstream\n"
        b"endobj\n"
        b"5 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        b"endobj\n"
    )
    
    # Write xref and trailer
    # Calculate object offsets
    lines = body.split(b"\n")
    offsets = [0]
    pos = 0
    # Find obj positions
    import re
    for obj_num in range(1, 6):
        m = re.search(f"{obj_num} 0 obj".encode("latin-1"), body)
        offsets.append(m.start() if m else 0)
    
    xref_pos = len(body)
    xref = (
        f"xref\n"
        f"0 6\n"
        f"0000000000 65535 f \n"
        f"{offsets[1]:010d} 00000 n \n"
        f"{offsets[2]:010d} 00000 n \n"
        f"{offsets[3]:010d} 00000 n \n"
        f"{offsets[4]:010d} 00000 n \n"
        f"{offsets[5]:010d} 00000 n \n"
        f"trailer\n"
        f"<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n"
        f"{xref_pos}\n"
        f"%%EOF\n"
    ).encode("latin-1")
    
    with open(filename, "wb") as f:
        f.write(body + xref)
    print(f"Successfully generated {filename}")

def generate_sample_discharge_summary():
    lines = [
        ("CARELYNX MEMORIAL HOSPITAL", 16, 72, 730),
        ("Department of Internal Medicine -- 123 Health Plaza, Metro City", 10, 72, 712),
        ("Direct Line: (555) 019-2834 -- 24hr Nurse Triage: (555) 019-9999", 9, 72, 698),
        ("-------------------------------------------------------------------------------------------------------", 10, 72, 686),
        ("PATIENT DISCHARGE SUMMARY & CARE PLAN", 14, 72, 665),
        ("Patient Name: Eleanor Vance            DOB: 04/12/1968 (Age: 58)       MRN: 99482-CV", 10, 72, 642),
        ("Attending: Dr. Sarah Jenkins, MD      Date of Admission: 10/01/2026   Date of Discharge: 10/04/2026", 10, 72, 626),
        ("-------------------------------------------------------------------------------------------------------", 10, 72, 612),
        ("PRIMARY DIAGNOSES:", 12, 72, 590),
        ("1. Community-acquired pneumonia (resolving)", 10, 90, 574),
        ("2. Essential Hypertension", 10, 90, 558),
        ("3. Type 2 Diabetes Mellitus (possible, requires follow up)", 10, 90, 542),
        ("DISCHARGE MEDICATIONS:", 12, 72, 516),
        ("- Azithromycin 500mg PO daily for 3 more days", 10, 90, 500),
        ("- Lisinopril 10mg PO daily (Morning)", 10, 90, 484),
        ("- Acetaminophen 500mg PO q6h PRN for fever or pain", 10, 90, 468),
        ("FOLLOW-UP APPOINTMENTS:", 12, 72, 442),
        ("- Primary Care Physician follow up on Oct 14, 2026.", 10, 90, 426),
        ("- Pulmonology follow up scheduled for 10/16/2026.", 10, 90, 410),
        ("WARNING SIGNS (WHEN TO CALL OR SEEK IMMEDIATE CARE):", 12, 72, 384),
        ("- Call doctor if fever exceeds 101F", 10, 90, 368),
        ("- Go to the emergency department if shortness of breath worsens", 10, 90, 352),
        ("DISCHARGE INSTRUCTIONS & ACTIVITY:", 12, 72, 326),
        ("- Low sodium diet", 10, 90, 310),
        ("- Avoid heavy lifting", 10, 90, 294),
        ("- Drink plenty of fluids", 10, 90, 278),
        ("Electronically signed by Dr. Sarah Jenkins, MD -- License #MD-882194", 9, 72, 220),
    ]
    create_pdf("sample_medical_record.pdf", lines)

def generate_conflicting_prescription():
    lines = [
        ("CARELYNX PHARMACY DISCHARGE ORDERS", 16, 72, 730),
        ("Prescription & Medication Verification Slip", 11, 72, 712),
        ("Patient: Eleanor Vance -- MRN: 99482-CV -- Date: 10/04/2026", 10, 72, 690),
        ("-------------------------------------------------------------------------------------------------------", 10, 72, 676),
        ("CURRENT MEDICATIONS:", 12, 72, 650),
        ("- Lisinopril 20mg PO daily (Morning)", 10, 90, 630),
        ("- Azithromycin 500mg PO daily for 3 more days", 10, 90, 610),
        ("FOLLOW-UP APPOINTMENTS:", 12, 72, 570),
        ("- Primary Care Physician follow up on Oct 18, 2026.", 10, 90, 550),
        ("Dispensed by Metro Pharmacy #402 -- Phone: (555) 019-3344", 9, 72, 480),
    ]
    create_pdf("sample_conflicting_prescription.pdf", lines)

if __name__ == "__main__":
    generate_sample_discharge_summary()
    generate_conflicting_prescription()


