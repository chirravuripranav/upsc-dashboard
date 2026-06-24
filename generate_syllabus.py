import json
import os

def create_syllabus():
    syllabus = [
        {
            "id": "polity",
            "title": "Indian Polity (M. Laxmikanth)",
            "topics": [
                { "id": "historical_background", "title": "Historical Background" },
                { "id": "making_of_constitution", "title": "Making of the Constitution" },
                { "id": "salient_features", "title": "Salient Features of the Constitution" },
                { "id": "preamble", "title": "Preamble of the Constitution" },
                { "id": "union_and_territory", "title": "Union and its Territory" },
                { "id": "citizenship", "title": "Citizenship" },
                { "id": "fundamental_rights", "title": "Fundamental Rights" },
                { "id": "dpsp", "title": "Directive Principles of State Policy" },
                { "id": "fundamental_duties", "title": "Fundamental Duties" },
                { "id": "amendment", "title": "Amendment of the Constitution" }
            ]
        },
        {
            "id": "history",
            "title": "Modern History (Spectrum)",
            "topics": [
                { "id": "advent_europeans", "title": "Advent of Europeans in India" },
                { "id": "british_expansion", "title": "Expansion and Consolidation of British Power" },
                { "id": "revolt_1857", "title": "The Revolt of 1857" },
                { "id": "socio_religious", "title": "Socio-Religious Reform Movements" },
                { "id": "early_nationalism", "title": "Beginnings of Modern Nationalism" },
                { "id": "inc_foundation", "title": "Indian National Congress: Foundation and Moderate Phase" },
                { "id": "extremist_phase", "title": "Era of Militant Nationalism (1905-1909)" },
                { "id": "gandhian_era_early", "title": "Emergence of Gandhi" },
                { "id": "non_cooperation", "title": "Non-Cooperation Movement and Khilafat Aandolan" },
                { "id": "civil_disobedience", "title": "Civil Disobedience Movement and Round Table Conferences" }
            ]
        }
    ]

    with open('media/syllabus.json', 'w', encoding='utf-8') as f:
        json.dump(syllabus, f, indent=2, ensure_ascii=False)
    print("Created media/syllabus.json")

def create_pyq_db():
    pyq_db = {
        "polity": {
            "historical_background": {
                "mcqs": [
                    {
                        "type": "pyq",
                        "year": "2019",
                        "q": "Which of the following Acts created the Supreme Court at Calcutta?",
                        "opts": ["Regulating Act, 1773", "Pitt's India Act, 1784", "Charter Act, 1813", "Government of India Act, 1858"],
                        "ans": 0,
                        "exp": "The Regulating Act of 1773 established the Supreme Court at Calcutta as the first court of judicature in India. Sir Elijah Impey was its first Chief Justice."
                    },
                    {
                        "type": "pyq",
                        "year": "2015",
                        "q": "Under which of the following Acts was the Board of Control established?",
                        "opts": ["Regulating Act, 1773", "Pitt's India Act, 1784", "Charter Act, 1853", "Indian Councils Act, 1861"],
                        "ans": 1,
                        "exp": "Pitt's India Act 1784 created two bodies: (1) Board of Control for political affairs, and (2) Court of Directors for commercial affairs. This established a system of double government."
                    }
                ],
                "mains": [
                    {
                        "type": "pyq",
                        "year": "2019",
                        "q": "Trace the evolution of the East India Company from a trading body to a political power in India. What were the key milestones in this transformation?",
                        "approach": ["Start with establishment of EIC in 1600 as a trading company", "Discuss the pivotal Battle of Plassey (1757) and Battle of Buxar (1764)", "Cover the Regulating Act 1773 and Pitt's India Act 1784"],
                        "model": "The East India Company (EIC), established by Royal Charter in 1600, underwent a remarkable transformation...\nPhase 1 — Trading Company (1600-1757)...\nPhase 2 — Military-Political Power (1757-1784)..."
                    }
                ]
            }
        }
    }

    with open('pyq_database.json', 'w', encoding='utf-8') as f:
        json.dump(pyq_db, f, indent=2, ensure_ascii=False)
    print("Created pyq_database.json")

if __name__ == '__main__':
    create_syllabus()
    create_pyq_db()
