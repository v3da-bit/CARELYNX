import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_conflict_pdf(filename="sample_prescription_conflict.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "CARELYNX HOSPITAL - PHARMACY/CLINIC")
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.25 * inch, "123 Medical Plaza, Healthville")
    c.drawString(1 * inch, height - 1.45 * inch, "Phone: (555) 012-3456")
    
    # Line separator
    c.line(1 * inch, height - 1.6 * inch, width - 1 * inch, height - 1.6 * inch)
    
    # Patient Info
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 2 * inch, "DISCHARGE PRESCRIPTION & PLAN")
    
    c.setFont("Helvetica", 11)
    c.drawString(1 * inch, height - 2.4 * inch, "Patient Name: John Doe")
    c.drawString(1 * inch, height - 2.6 * inch, "DOB: 01/15/1975")
    c.drawString(4 * inch, height - 2.4 * inch, "MRN: 998877665")
    c.drawString(4 * inch, height - 2.6 * inch, "Date: 10/04/2026")
    
    # Clinical Information
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 3.4 * inch, "DISCHARGE MEDICATIONS:")
    c.setFont("Helvetica", 11)
    # Different dosage to trigger conflict if desired, or same dosage to just be normal.
    # Let's keep it same, but change the follow up date.
    c.drawString(1.2 * inch, height - 3.6 * inch, "- Azithromycin 500mg PO daily for 3 more days")
    c.drawString(1.2 * inch, height - 3.8 * inch, "- Lisinopril 20mg PO daily (Morning)")  # CONFLICT: 20mg vs 10mg in summary
    c.drawString(1.2 * inch, height - 4.0 * inch, "- Acetaminophen 500mg PO q6h PRN for fever or pain")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 4.8 * inch, "FOLLOW-UP APPOINTMENTS:")
    c.setFont("Helvetica", 11)
    # CONFLICT: Oct 21 instead of Oct 14
    c.drawString(1.2 * inch, height - 5.0 * inch, "- Primary Care Physician follow up on Oct 21, 2026.")
    c.drawString(1.2 * inch, height - 5.2 * inch, "- Pulmonology follow up scheduled for 10/16/2026.")
    
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(1 * inch, height - 6.5 * inch, "Electronically signed by Dr. Sarah Jenkins, MD")
    
    c.save()
    print(f"Generated {filename}")

if __name__ == "__main__":
    create_conflict_pdf()
