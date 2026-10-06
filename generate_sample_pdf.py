import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_sample_pdf(filename="sample_medical_record.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "CARELYNX HOSPITAL")
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.25 * inch, "123 Medical Plaza, Healthville")
    c.drawString(1 * inch, height - 1.45 * inch, "Phone: (555) 012-3456")
    
    # Line separator
    c.line(1 * inch, height - 1.6 * inch, width - 1 * inch, height - 1.6 * inch)
    
    # Patient Info
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 2 * inch, "DISCHARGE SUMMARY")
    
    c.setFont("Helvetica", 11)
    c.drawString(1 * inch, height - 2.4 * inch, "Patient Name: John Doe")
    c.drawString(1 * inch, height - 2.6 * inch, "DOB: 01/15/1975")
    c.drawString(4 * inch, height - 2.4 * inch, "MRN: 998877665")
    c.drawString(4 * inch, height - 2.6 * inch, "Date of Admission: 10/01/2026")
    c.drawString(4 * inch, height - 2.8 * inch, "Date of Discharge: 10/04/2026")
    
    # Clinical Information
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 3.4 * inch, "PRIMARY DIAGNOSES:")
    c.setFont("Helvetica", 11)
    c.drawString(1.2 * inch, height - 3.6 * inch, "1. Community-acquired pneumonia (resolving)")
    c.drawString(1.2 * inch, height - 3.8 * inch, "2. Essential Hypertension")
    c.drawString(1.2 * inch, height - 4.0 * inch, "3. Type 2 Diabetes Mellitus (possible, requires follow up)")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 4.5 * inch, "HOSPITAL COURSE:")
    c.setFont("Helvetica", 11)
    # Using textobject for multi-line
    textobject = c.beginText(1.2 * inch, height - 4.7 * inch)
    textobject.textLines('''The patient presented to the emergency department with shortness of breath 
and a productive cough. Chest X-ray confirmed left lower lobe infiltrate. 
He was started on IV antibiotics (Ceftriaxone and Azithromycin). Over the 
course of 3 days, his symptoms improved significantly, and he was 
transitioned to oral antibiotics.''')
    c.drawText(textobject)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 5.7 * inch, "DISCHARGE MEDICATIONS:")
    c.setFont("Helvetica", 11)
    c.drawString(1.2 * inch, height - 5.9 * inch, "- Azithromycin 500mg PO daily for 3 more days")
    c.drawString(1.2 * inch, height - 6.1 * inch, "- Lisinopril 10mg PO daily (Morning)")
    c.drawString(1.2 * inch, height - 6.3 * inch, "- Acetaminophen 500mg PO q6h PRN for fever or pain")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, height - 6.8 * inch, "FOLLOW-UP APPOINTMENTS:")
    c.setFont("Helvetica", 11)
    c.drawString(1.2 * inch, height - 7.0 * inch, "- Primary Care Physician follow up on Oct 14, 2026.")
    c.drawString(1.2 * inch, height - 7.2 * inch, "- Pulmonology follow up scheduled for 10/16/2026.")
    
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(1 * inch, height - 8 * inch, "Electronically signed by Dr. Sarah Jenkins, MD")
    
    c.save()
    print(f"Generated {filename}")

if __name__ == "__main__":
    create_sample_pdf()
