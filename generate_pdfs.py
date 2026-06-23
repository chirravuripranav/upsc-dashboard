from fpdf import FPDF
import json
import os

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('helvetica', 'B', 15)
        # Colors of frame, background and text
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 250)
        self.set_text_color(0, 50, 100)
        # Title
        self.cell(0, 10, 'UPSC Mentorship Command Centre', border=1, align='C', fill=True)
        self.ln(20)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('helvetica', 'I', 8)
        # Page number
        self.set_text_color(128)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, num, title):
        # Arial 12
        self.set_font('helvetica', 'B', 16)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 12, f'Section {num}: {title}', 0, 1, 'L', fill=True)
        self.ln(4)

    def chapter_body(self, text):
        # Times 12
        self.set_font('helvetica', '', 12)
        self.set_text_color(0, 0, 0)
        # Output justified text
        text = text.encode('ascii', 'replace').decode('ascii').replace('?', '-')
        self.multi_cell(0, 8, text)
        self.ln()

phases = [
    {
        "name": "Phase 1: Foundation (126 Days)",
        "file": "Phase_1_Guide.pdf",
        "guide": "Welcome to Phase 1! This phase is the bedrock of your UPSC preparation. The objective here is to build a rock-solid foundation in core subjects: Polity, History, Economy, and Geography. You must focus on understanding concepts rather than rote memorization.",
        "approach": "1. Textbooks: Krishna Reddy (History), M. Laxmikanth (Polity), Majid Hussain (Geography), Arihant All-in-One NCERT (Economy).\n2. Read these sources thoroughly to build your foundation.\n3. Solve 10-15 MCQs daily to test your grasp of the topic.\n4. Write at least one Mains answer daily to build articulation skills."
    },
    {
        "name": "Phase 2: Consolidation & Mains Focus (90 Days)",
        "file": "Phase_2_Guide.pdf",
        "guide": "Phase 2 shifts the focus towards Mains-specific subjects and value addition. This is where you separate yourself from the crowd by building depth in Ethics (GS4), Essay writing, and Optional subjects.",
        "approach": "1. Dedicate 40% of your time to your Optional subject.\n2. Practice full-length Essay writing every weekend.\n3. Integrate Current Affairs notes deeply into your static answers.\n4. Begin solving full-length GS papers under timed conditions."
    },
    {
        "name": "Phase 3: Prelims Exclusive Sprint (60 Days)",
        "file": "Phase_3_Guide.pdf",
        "guide": "As Prelims approaches, Phase 3 is all about maximizing your objective-solving accuracy. Halt all Mains-exclusive preparation (Optional/Ethics/Essay).",
        "approach": "1. Take comprehensive Mock Tests every alternate day.\n2. Revise the core subjects strictly through MCQs and condensed notes.\n3. Focus heavily on current affairs compilations and indices.\n4. Master elimination techniques and intelligent guessing."
    },
    {
        "name": "Phase 4: Mains Intensive & Interview Prep",
        "file": "Phase_4_Guide.pdf",
        "guide": "Congratulations on making it past Prelims! Phase 4 is a brutal cycle of answer writing, refining arguments, and finally preparing your Detailed Application Form (DAF) for the interview.",
        "approach": "1. Write one full-length Mains mock paper daily.\n2. Peer-review answers and use the AI Evaluator to fine-tune structure.\n3. Prepare a detailed questionnaire based on your DAF.\n4. Participate in mock interviews to build communication confidence."
    }
]

output_dir = r"c:\Users\prana\Downloads\project\telegram-bridge\media"
os.makedirs(output_dir, exist_ok=True)

# Try to load syllabus.json for Phase 1
syllabus = []
try:
    with open("syllabus.json", "r", encoding="utf-8") as f:
        syllabus = json.load(f)
except Exception:
    try:
        with open(os.path.join(output_dir, "syllabus.json"), "r", encoding="utf-8") as f:
            syllabus = json.load(f)
    except Exception as e:
        print("Could not load syllabus.json from any location:", e)

def clean(text):
    return str(text).encode('ascii', 'replace').decode('ascii').replace('?', '-')

for idx, phase in enumerate(phases):
    pdf = PDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('helvetica', 'B', 24)
    pdf.set_text_color(0, 50, 100)
    pdf.cell(0, 20, clean(phase["name"]), align='C')
    pdf.ln(25)
    
    # Guide
    pdf.chapter_title(1, "Mentee Guide")
    pdf.chapter_body(phase["guide"])
    
    # Approach
    pdf.chapter_title(2, "Approach & Strategy")
    pdf.chapter_body(phase["approach"])
    
    # Timetable (Only Phase 1 has the generated detailed timetable)
    if idx == 0 and syllabus:
        pdf.add_page()
        pdf.chapter_title(3, "Detailed Daily Timetable (126 Days)")
        
        pdf.set_font('helvetica', '', 10)
        for day in syllabus:
            pdf.set_font('helvetica', 'B', 11)
            pdf.cell(0, 6, clean(f"Day {day['day']}: {day['title']} (Week {day['week']})"), new_x='LMARGIN', new_y='NEXT')
            
            pdf.set_font('helvetica', '', 9)
            pdf.cell(0, 5, clean(f"MCQs to Practice: {len(day['mcqs'])} Questions"), new_x='LMARGIN', new_y='NEXT')
            pdf.cell(0, 5, clean(f"Mains Practice: {len(day['mains'])} Questions"), new_x='LMARGIN', new_y='NEXT')
            pdf.ln(3)
            
    else:
        pdf.add_page()
        pdf.chapter_title(3, "Detailed Daily Timetable")
        pdf.chapter_body("The daily timetable for this phase will be unlocked and dynamically generated as you complete the previous phase. Stay consistent and keep tracking your progress on the Command Centre dashboard!")

    output_path = os.path.join(output_dir, phase["file"])
    pdf.output(output_path)
    print(f"Generated {output_path}")

print("All PDFs generated successfully!")
