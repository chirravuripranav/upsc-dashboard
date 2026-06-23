import json
import random

WEEKS = 18
DAYS_PER_WEEK = 7
TOTAL_DAYS = WEEKS * DAYS_PER_WEEK

# Base subjects per phase mapping
SUBJECTS = [
    {"name": "Polity", "topics": ["Historical Background", "Preamble", "Fundamental Rights", "DPSP", "Parliament", "Supreme Court", "State Govt", "Panchayati Raj", "Constitutional Bodies"]},
    {"name": "History", "topics": [
        "Prehistoric Cultures", "Indus Valley Civilisation", "Vedic Society", 
        "Pre-Maurya Period", "The Mauryan Empire", "Post-Mauryan India", 
        "The Guptas and Their Successors", "Society and Culture", 
        "Early Medieval India", "The Delhi Sultanate", "Post-Independence India"
    ]},
    {"name": "Economy", "topics": ["National Income", "Inflation", "Monetary Policy", "Fiscal Policy", "Banking", "Agriculture", "Industry", "External Sector", "Infrastructure"]},
    {"name": "Geography", "topics": ["Geomorphology", "Climatology", "Oceanography", "Indian Physiography", "Drainage System", "Climate of India", "Soils & Veg", "Economic Geo", "Human Geo"]}
]

def generate_mcq(subject, topic, index):
    return {
        "id": f"q_{index}",
        "text": f"Consider the following statements regarding {topic} in the context of {subject}:\n1. Statement one is a factual assertion often seen in UPSC PYQs.\n2. Statement two is an analytical deduction with a subtle trap.\nWhich of the statements given above is/are correct?",
        "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
        "correctIndex": random.choice([0, 1, 2, 3]),
        "explanation": f"Explanation for {topic}: Statement 1 is analyzed here. Statement 2 is analyzed here. This pattern reflects the UPSC trend of testing conceptual clarity over rote memorization.",
        "year": random.choice(["2022", "2021", "2020", "2018", "Simulated"])
    }

def generate_mains(subject, topic):
    return {
        "question": f"Discuss the significance of {topic} in shaping the modern discourse on {subject}. Critically analyze its impact on contemporary governance. (250 words, 15 marks)",
        "approach": f"**Introduction**: Define {topic} briefly.\n**Body**: Point 1. Point 2. Provide recent examples.\n**Conclusion**: Summarize its long-term relevance.",
        "model_answer": f"The evolution of {topic} within {subject} is a cornerstone of Indian administration. It began with early reforms and culminated in recent policy shifts...",
        "year": random.choice(["2019", "2020", "2021", "2023"])
    }

syllabus = []

for day in range(1, TOTAL_DAYS + 1):
    week = ((day - 1) // 7) + 1
    
    # Subjects change every few weeks
    sub1 = SUBJECTS[(week-1) % 4]
    sub2 = SUBJECTS[(week) % 4]
    
    topic1 = random.choice(sub1["topics"])
    topic2 = random.choice(sub2["topics"])
    
    is_sunday = (day % 7 == 0)
    
    title = f"Day {day} — Revision & Mock Test" if is_sunday else f"Day {day} — {sub1['name']}: {topic1} + {sub2['name']}: {topic2}"
    
    mcqs = []
    num_mcqs = 40 if is_sunday else 15
    for i in range(num_mcqs):
        s = sub1 if i % 2 == 0 else sub2
        t = topic1 if i % 2 == 0 else topic2
        mcqs.append(generate_mcq(s['name'], t, i))
        
    mains = []
    num_mains = 5 if is_sunday else 2
    for i in range(num_mains):
        s = sub1 if i % 2 == 0 else sub2
        t = topic1 if i % 2 == 0 else topic2
        mains.append(generate_mains(s['name'], t))

    syllabus.append({
        "day": day,
        "week": week,
        "title": title,
        "is_sunday": is_sunday,
        "mcqs": mcqs,
        "mains": mains
    })

with open('media/syllabus.json', 'w', encoding='utf-8') as f:
    json.dump(syllabus, f, indent=2)

print("Generated syllabus.json with 126 days of content.")
