"""
Kaizen AI — Demo Data Generator
Generates realistic synthetic industrial documents for demo/testing.
Run this once to populate the system with demo content before recording the demo video.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors

OUT = Path("./data/sample_docs")
OUT.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()

def h1(text): return Paragraph(text, ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, spaceAfter=8))
def h2(text): return Paragraph(text, ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, spaceAfter=6))
def p(text):  return Paragraph(text, ParagraphStyle("p",  parent=styles["Normal"],   fontSize=10, spaceAfter=5, leading=15))
def sp():     return Spacer(1, 0.3*cm)


# ── 1. OEM Pump Manual ────────────────────────────────────────────────────────
def make_pump_manual():
    doc = SimpleDocTemplate(str(OUT/"Pump_P104_OEM_Manual_Rev3.pdf"), pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = [
        h1("CENTRIFUGAL PUMP P-104 — OEM OPERATION & MAINTENANCE MANUAL"),
        p("Model: CP-250 Series | Serial: SN-20210847 | Manufacturer: FlowTech Industries"),
        p("Revision: Rev 3 | Date: January 2025 | Equipment ID: P-104"),
        sp(),
        h2("1. Equipment Overview"),
        p("Pump P-104 is a horizontal centrifugal pump designed for continuous process duty in "
          "Unit-3 of the refinery. Nominal capacity: 85 m³/h at 4.2 bar discharge pressure. "
          "Design speed: 1480 RPM. Motor drive: M-104 (75 kW, 415V, 3-phase)."),
        sp(),
        h2("2. Normal Operating Parameters"),
        p("The following parameters define healthy operation for Pump P-104:"),
        Table([
            ["Parameter",         "Normal Range",    "Warning Threshold",  "Critical Threshold"],
            ["Vibration (mm/s)",  "< 2.3",           "2.3 – 4.5",          "> 7.1 (ISO Zone C)"],
            ["Bearing Temp (°C)", "55 – 70",         "70 – 85",            "> 85"],
            ["Discharge Pressure","3.8 – 4.5 bar",   "< 3.0 bar",          "< 2.0 bar"],
            ["Flow Rate (m³/h)",  "80 – 95",         "65 – 80",            "< 60"],
            ["Motor Current (A)", "120 – 135",       "135 – 145",          "> 145"],
        ], colWidths=[4.5*cm, 3.5*cm, 3.5*cm, 3.5*cm],
           style=TableStyle([
               ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a2235")),
               ("TEXTCOLOR",(0,0),(-1,0),colors.white),
               ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
               ("FONTSIZE",(0,0),(-1,-1),9),
               ("GRID",(0,0),(-1,-1),0.5,colors.grey),
               ("PADDING",(0,0),(-1,-1),5),
               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8f9fa")]),
           ])),
        sp(),
        h2("3. Maintenance Schedule"),
        p("3.1 Daily Checks: Verify vibration readings, bearing temperatures, seal leak-off flow, "
          "and discharge pressure against operating limits defined in Section 2."),
        p("3.2 Weekly: Inspect mechanical seal for leakage. Check coupling alignment. "
          "Verify motor insulation resistance > 100 MΩ."),
        p("3.3 Lubrication: Re-lubricate bearings every 500 operating hours using Mobil Grease "
          "XHP 222 (Shell Alvania EP2 equivalent). Over-lubrication causes overheating — "
          "use exactly 15g per bearing housing. Lubrication interval must not exceed 500 hours "
          "under any circumstances."),
        p("3.4 Annual Overhaul: Full disassembly, bearing replacement, wear ring inspection, "
          "impeller clearance check (max 0.4 mm), seal replacement if leakage > 5 ml/hr."),
        sp(),
        h2("3.2.1 Bearing Maintenance — Critical Procedure"),
        p("Bearing degradation is the most common failure mode for P-104. Early indicators include "
          "vibration increase above 4.5 mm/s and bearing temperature above 75°C. "
          "When vibration reaches 7.1 mm/s (ISO 10816 Zone C), immediate shutdown is required."),
        p("Historical data: Three bearing failures recorded on P-104 (2022, 2023, 2025). "
          "All three were preceded by lubrication interval exceedance of > 40 hours beyond the "
          "500-hour limit. Root cause in all cases: grease breakdown leading to metal-to-metal contact."),
        p("Replacement bearing specification: SKF 6205-2RS1/C3 (deep groove ball bearing). "
          "Do not substitute with open bearings in this application — seal contamination risk."),
        sp(),
        h2("4. Failure Modes and Corrective Actions"),
        p("4.1 High Vibration: Check bearing condition, coupling alignment, impeller balance. "
          "If vibration > 7.1 mm/s, isolate immediately. Do not operate above ISO Zone C limit."),
        p("4.2 Seal Failure: Increased leak-off flow (> 5 ml/hr) indicates seal wear. "
          "Replace mechanical seal — John Crane Type 1 or equivalent. "
          "Dry running causes immediate seal failure — never start pump without priming."),
        p("4.3 Cavitation: Erratic vibration with crackling noise, reduced flow and pressure. "
          "Check suction strainer, reduce speed, or increase suction pressure. "
          "Cavitation causes rapid impeller erosion."),
        p("4.4 Bearing Failure: Typically preceded by rising vibration over 2–4 weeks. "
          "Replace both radial and thrust bearings simultaneously. Never replace only one bearing."),
        sp(),
        h2("5. Safety Requirements"),
        p("All maintenance on P-104 must follow OISD-113 (Maintenance of Electrical Installations) "
          "and the plant Permit-to-Work system. LOTO (Lock-Out Tag-Out) is mandatory before "
          "any mechanical work. Confined space entry requires gas testing per Factory Act Section 7A."),
    ]
    doc.build(story)
    print(f"✓ Created: Pump_P104_OEM_Manual_Rev3.pdf")


# ── 2. Maintenance Log ────────────────────────────────────────────────────────
def make_maintenance_log():
    doc = SimpleDocTemplate(str(OUT/"P104_Maintenance_Log_2024_2025.pdf"), pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = [
        h1("MAINTENANCE WORK ORDER LOG — PUMP P-104"),
        p("Period: January 2024 – June 2025 | Unit: Unit-3 | Maintained by: Mechanical Team B"),
        sp(),
        Table([
            ["WO #",    "Date",       "Type",        "Action",                         "Technician",   "Parts Used",              "Hours"],
            ["WO-2401", "2024-01-15", "Preventive",  "Lubrication — Bearing Housing",  "Ravi Kumar",   "Mobil XHP 222 (15g x2)",  "1.5"],
            ["WO-2403", "2024-02-28", "Corrective",  "Mechanical Seal Replacement",    "Suresh Babu",  "John Crane Type 1 Seal",  "6.0"],
            ["WO-2407", "2024-04-10", "Preventive",  "Lubrication + Vibration Check",  "Ravi Kumar",   "Mobil XHP 222 (15g x2)",  "1.5"],
            ["WO-2415", "2024-06-05", "Inspection",  "Annual Overhaul — Partial",      "Suresh Babu",  "Wear rings (2x)",         "12.0"],
            ["WO-2422", "2024-08-12", "Preventive",  "Lubrication",                    "Ramesh G.",    "Mobil XHP 222 (15g x2)",  "1.0"],
            ["WO-2439", "2024-10-20", "Corrective",  "Bearing Replacement (both)",     "Ravi Kumar",   "SKF 6205 x2, Grease",     "8.0"],
            ["WO-2445", "2024-11-08", "Corrective",  "Seal Replacement",               "Suresh Babu",  "John Crane Type 1 Seal",  "5.5"],
            ["WO-2501", "2025-01-22", "Preventive",  "Lubrication",                    "Ravi Kumar",   "Mobil XHP 222 (15g x2)",  "1.0"],
            ["WO-2508", "2025-03-12", "Corrective",  "Bearing Replacement — CRITICAL", "Ravi Kumar",   "SKF 6205 x2, Grease 30g", "9.0"],
            ["WO-2514", "2025-05-18", "Preventive",  "Lubrication — Overdue",          "Ramesh G.",    "Mobil XHP 222 (15g x2)",  "1.5"],
        ], colWidths=[1.8*cm,2.2*cm,2.4*cm,4.8*cm,2.4*cm,3.4*cm,1.4*cm],
           style=TableStyle([
               ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a2235")),
               ("TEXTCOLOR",(0,0),(-1,0),colors.white),
               ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
               ("FONTSIZE",(0,0),(-1,-1),8),
               ("GRID",(0,0),(-1,-1),0.5,colors.grey),
               ("PADDING",(0,0),(-1,-1),4),
               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8f9fa")]),
               ("BACKGROUND",(0,9),(-1,9),colors.HexColor("#fff3cd")),  # highlight last bearing replacement
           ])),
        sp(),
        h2("Observations"),
        p("WO-2403 (Feb 2024): Seal failure attributed to dry running during pump restart after "
          "emergency shutdown on 2024-02-25. Seal face scored. Replaced with new John Crane Type 1."),
        p("WO-2439 (Oct 2024): Vibration reached 8.2 mm/s before shutdown. "
          "Lubrication interval had exceeded 600 hours (overdue by 100 hours). "
          "Both bearings showed significant wear — grease completely degraded. "
          "Root cause: lubrication schedule not followed after WO-2422."),
        p("WO-2508 (Mar 2025): Second bearing failure in 5 months. Vibration peaked at 9.1 mm/s. "
          "Investigation found lubrication interval again exceeded — last lubrication was WO-2501 "
          "(Jan 2025), gap of 51 days / estimated 612 operating hours. "
          "RECOMMENDATION: Implement automated lubrication alert at 450-hour threshold."),
        p("WO-2514 (May 2025): Lubrication completed. Vibration currently 5.4 mm/s — elevated "
          "but within operating limit. Bearing temperature 76°C — monitoring required. "
          "Next lubrication due: approximately September 2025 (500 hours from May 18)."),
    ]
    doc.build(story)
    print(f"✓ Created: P104_Maintenance_Log_2024_2025.pdf")


# ── 3. Incident Report ────────────────────────────────────────────────────────
def make_incident_report():
    doc = SimpleDocTemplate(str(OUT/"Incident_Report_INC019_P104_Bearing_Failure.pdf"), pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = [
        h1("INCIDENT REPORT — INC-019"),
        p("Equipment: Pump P-104 | Date: 08 October 2024 | Severity: HIGH"),
        p("Reported by: Shift Supervisor — Unit 3 | Investigated by: Ravi Kumar, Senior Technician"),
        sp(),
        h2("1. Incident Description"),
        p("At 03:45 hrs on 08 October 2024, continuous vibration monitoring alarmed for Pump P-104 "
          "at 7.8 mm/s. Operations attempted to reduce load but vibration climbed to 8.2 mm/s "
          "within 20 minutes. Pump was tripped at 04:05 hrs. Bearing temperature at trip was 89°C. "
          "No personnel injury. Production loss: 4 hours."),
        sp(),
        h2("2. Root Cause Analysis"),
        p("2.1 Immediate Cause: Complete bearing failure — both radial bearings seized. "
          "Grease completely carbonised. Rolling element damage visible on inspection."),
        p("2.2 Contributing Factor: Lubrication interval exceeded by approximately 100 hours. "
          "Last lubrication (WO-2422) was on 12 August 2024. Estimated operating hours at failure: "
          "approximately 600 hours since lubrication. OEM limit is 500 hours."),
        p("2.3 Root Cause: Lubrication schedule not triggered in the CMMS after WO-2422. "
          "The 500-hour lubrication reminder was not set, and no manual follow-up was performed. "
          "This is the same root cause as the 2022 and 2023 bearing failures on P-104 — "
          "a systemic CMMS scheduling failure, not an isolated incident."),
        sp(),
        h2("3. Failure Pattern — Historical"),
        p("This is the THIRD bearing failure on P-104 caused by lubrication interval exceedance. "
          "2022 failure: interval exceeded by 80 hours. 2023 failure: interval exceeded by 65 hours. "
          "2024 failure: interval exceeded by 100 hours. In all three cases, vibration exceeded "
          "7.1 mm/s approximately 2–3 weeks before catastrophic bearing failure. "
          "The pattern is consistent and predictable."),
        sp(),
        h2("4. Corrective Actions"),
        p("4.1 Immediate: Replace both bearings (SKF 6205-2RS1/C3). Re-lubricate. "
          "Verify alignment. Return to service after vibration confirmed < 2.3 mm/s."),
        p("4.2 Short-term: Set CMMS automated alert at 450-hour lubrication interval for P-104. "
          "Do not rely on manual scheduling."),
        p("4.3 Long-term: Evaluate automatic lubrication system for P-104 given recurring failures. "
          "Estimated cost: ₹1,80,000. Estimated failure prevention value: ₹4,50,000/year."),
        sp(),
        h2("5. Compliance Reference"),
        p("This incident and corrective actions are documented per OISD-113 requirements "
          "for maintenance of rotating equipment. Factory Act Section 7A notification submitted "
          "to factory inspector on 09 October 2024."),
    ]
    doc.build(story)
    print(f"✓ Created: Incident_Report_INC019_P104_Bearing_Failure.pdf")


# ── 4. Inspection Checklist ───────────────────────────────────────────────────
def make_inspection_checklist():
    doc = SimpleDocTemplate(str(OUT/"P104_Inspection_Checklist_June2025.pdf"), pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = [
        h1("MONTHLY INSPECTION CHECKLIST — PUMP P-104"),
        p("Inspection Date: 15 June 2025 | Inspector: Ramesh G. | Approved: Unit Supervisor"),
        sp(),
        Table([
            ["#", "Check Item",                          "Reading / Status",     "Limit",    "Result"],
            ["1",  "Vibration (mm/s)",                   "7.2",                  "< 7.1",    "⚠ WARN"],
            ["2",  "Bearing Temperature DE (°C)",        "81",                   "< 85",     "⚠ WARN"],
            ["3",  "Bearing Temperature NDE (°C)",       "78",                   "< 85",     "✓ OK"],
            ["4",  "Discharge Pressure (bar)",           "3.9",                  "3.8–4.5",  "✓ OK"],
            ["5",  "Flow Rate (m³/h)",                   "79",                   "80–95",    "⚠ LOW"],
            ["6",  "Motor Current (A)",                  "131",                  "120–135",  "✓ OK"],
            ["7",  "Seal Leak-off (ml/hr)",              "2.1",                  "< 5.0",    "✓ OK"],
            ["8",  "Coupling Guard Secure",              "Yes",                  "Required", "✓ OK"],
            ["9",  "Lubrication Interval (hrs since)",  "580",                   "< 500",    "✗ OVERDUE"],
            ["10", "Noise / Unusual Sound",              "Slight rumble NDE",    "None",     "⚠ WARN"],
            ["11", "Foundation Bolts Tight",             "Yes",                  "Required", "✓ OK"],
            ["12", "OISD-113 Compliance Current",        "Yes",                  "Required", "✓ OK"],
        ], colWidths=[0.8*cm,6.5*cm,3.5*cm,2.5*cm,2.2*cm],
           style=TableStyle([
               ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a2235")),
               ("TEXTCOLOR",(0,0),(-1,0),colors.white),
               ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
               ("FONTSIZE",(0,0),(-1,-1),9),
               ("GRID",(0,0),(-1,-1),0.5,colors.grey),
               ("PADDING",(0,0),(-1,-1),5),
               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8f9fa")]),
               ("BACKGROUND",(0,2),(4,2),colors.HexColor("#fff3cd")),
               ("BACKGROUND",(0,6),(4,6),colors.HexColor("#fff3cd")),
               ("BACKGROUND",(0,9),(4,9),colors.HexColor("#f8d7da")),
           ])),
        sp(),
        h2("Inspector Notes"),
        p("Vibration at 7.2 mm/s — marginally above ISO Zone C threshold of 7.1 mm/s. "
          "Recommend immediate lubrication (overdue by 80 hours) and bearing inspection. "
          "Slight rumble audible at NDE bearing suggests early-stage bearing degradation. "
          "Flow rate 1% below nominal — possibly related to increased bearing friction."),
        p("ACTION REQUIRED: Schedule lubrication within 24 hours. If vibration exceeds 7.5 mm/s "
          "before lubrication, isolate pump and inspect bearings before restart."),
        p("Next scheduled inspection: 15 July 2025."),
    ]
    doc.build(story)
    print(f"✓ Created: P104_Inspection_Checklist_June2025.pdf")


# ── 5. SOP ────────────────────────────────────────────────────────────────────
def make_sop():
    doc = SimpleDocTemplate(str(OUT/"SOP_Bearing_Replacement_Rotating_Equipment.pdf"), pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = [
        h1("STANDARD OPERATING PROCEDURE — BEARING REPLACEMENT"),
        p("SOP Number: SOP-MECH-007 | Revision: Rev 4 | Applies to: All rotating equipment"),
        p("Compliance: OISD-113, Factory Act Section 7A, ISO 10816-3"),
        sp(),
        h2("1. Prerequisites and Safety"),
        p("1.1 Obtain Permit to Work (PTW) from area supervisor before beginning work."),
        p("1.2 Apply LOTO (Lock-Out Tag-Out) on motor M-104 at MCC panel. Verify zero energy state."),
        p("1.3 Gas test required if work is in a classified hazardous area. Confirm with safety officer."),
        p("1.4 PPE: Safety boots, gloves, eye protection, hard hat. Hearing protection during operation checks."),
        sp(),
        h2("2. Bearing Replacement Procedure"),
        p("Step 1: Drain coupling housing. Remove coupling guard and coupling half from pump shaft."),
        p("Step 2: Remove bearing housing end covers. Extract bearing using puller tool. "
          "Do not use hammer on bearing — shaft damage risk."),
        p("Step 3: Clean shaft journal with lint-free cloth. Inspect for scoring or step wear. "
          "Maximum allowable shaft taper: 0.02 mm. If exceeded, replace shaft."),
        p("Step 4: Heat new bearing to 80°C in oil bath or induction heater. "
          "Never exceed 120°C. Install immediately while warm. Do not use cold press-fit."),
        p("Step 5: Apply 15g of Mobil Grease XHP 222 to each bearing housing. "
          "Do not over-lubricate — excess grease causes overheating."),
        p("Step 6: Reassemble in reverse order. Check axial float: 0.1 – 0.3 mm acceptable."),
        h2("3. Post-Replacement Verification"),
        p("3.1 Check coupling alignment: angular < 0.05 mm/100mm, parallel < 0.05 mm."),
        p("3.2 Run pump unloaded for 30 minutes. Monitor vibration and temperature continuously."),
        p("3.3 Vibration must be < 2.3 mm/s before returning to full load service."),
        p("3.4 Record work order completion in CMMS. Set lubrication reminder at +500 hours."),
    ]
    doc.build(story)
    print(f"✓ Created: SOP_Bearing_Replacement_Rotating_Equipment.pdf")


if __name__ == "__main__":
    print("\nGenerating Kaizen AI demo documents...\n")
    make_pump_manual()
    make_maintenance_log()
    make_incident_report()
    make_inspection_checklist()
    make_sop()
    print(f"\n✓ All demo documents created in: {OUT.absolute()}")
    print("  Upload these via the Kaizen AI dashboard to populate the system.\n")
