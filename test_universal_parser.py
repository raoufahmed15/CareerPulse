"""Universal parser sanity test - uses three very different CV styles.

This test intentionally uses CVs with completely different people,
countries, industries, and layouts to prove the parser is NOT bound
to any specific CV.
"""
import sys

sys.path.insert(0, "backend")

from app.services.resume_parser import parse_resume  # noqa: E402

# ------------------------------------------------------------------
# CV 1: German software engineer (date-first layout, "|" separators)
# ------------------------------------------------------------------
CV1 = """Lukas Weber
Full Stack Developer
Berlin, Germany
lukas.weber@example.de | +49 30 1234 5678

Professional Summary
Passionate full stack developer with 8 years building scalable
web applications for the DACH region.

Technical Skills
Languages: TypeScript, Go, Rust | Frontend: React, Vue.js | Backend: Node.js, PostgreSQL
DevOps: Docker, Kubernetes, AWS

Work Experience
Senior Full Stack Developer  |  HelloFresh  |  03/2021 - Present
  - Led migration of monolith to microservices (30+ services)
  - Reduced CI build time by 40%
Backend Developer  July 2019 - Feb 2021
  Zalando SE
  - Built REST APIs handling 2M requests/day
  - Mentored 4 junior developers

Education
B.Sc. Software Engineering  2015 - 2019
  Technical University of Munich

Projects
ShopAnalytica  |  React, Node.js, MongoDB
  Real-time e-commerce analytics dashboard processing 50k events/min

Certifications
AWS Certified Developer - Associate

Languages
German (Native) | English (Professional)
"""

# ------------------------------------------------------------------
# CV 2: Finance analyst, date-last layout, "•" bullets
# ------------------------------------------------------------------
CV2 = """Sofia Marchetti
Financial Analyst • Chicago, IL
sofia.marchetti@gmail.com • +1 312 555 0198
linkedin.com/in/sofiamarchetti

PROFESSIONAL SUMMARY
Analyst with 5 years of experience in financial modeling and
risk assessment for Fortune 500 companies.

EMPLOYMENT HISTORY
Goldman Sachs | Associate 2019 - 2022
  • Built DCF and LBO models for M&A deals worth $2B
  • Automated monthly reporting using Python and Excel VBA

JP Morgan | Analyst
2017 - 2019
  • Prepared quarterly earnings presentations for leadership
  • Detected anomalies in trading data leading to $500k savings

EDUCATION
Bachelor of Science in Finance, 2017
University of Chicago

SKILLS
Excel, Power BI, Python, SQL, Financial Modeling, Risk Management
"""

# ------------------------------------------------------------------
# CV 3: medical academic, labeled lines, multi-page style
# ------------------------------------------------------------------
CV3 = """Dr. Amara Okafor
Cardiologist & Researcher
University College Hospital Ibadan, Nigeria
+234 801 234 5678
a.okafor@hospital.ng

Objective
To combine clinical cardiology with translational research on
hypertension in West Africa.

Education
Doctor of Medicine (M.D.)
University of Ibadan, Nigeria
2008 - 2014

Work Experience
Senior Registrar, Cardiology
UCH Ibadan
2018 - Present
- Supervised 15 cardiology residents
- Published 12 peer-reviewed papers on hypertension

Research Fellow
Harvard Medical School
2016 - 2018
- Ran clinical trials on beta-blocker efficacy

Publications
Okafor, A. et al. (2021). Hypertension in West Africa. Lancet.

Skills
Echocardiography, Clinical Trials Design, SPSS, R Statistics

Languages
English, Igbo, Yoruba

Volunteer
Eko Health Campaign | 8/2017 - 12/2018 as Volunteer Cardiologist
"""

# ------------------------------------------------------------------
# CV 4: generic but realistic headings that should still parse without
# relying on a specific CV template.
# ------------------------------------------------------------------
CV4 = """Aisha Rahman
Software Engineer
London, UK
aisha.r@gmail.com | +44 7700 900123

Career Summary
Backend engineer with 7 years building APIs and distributed systems.

Core Competencies
Python, FastAPI, Django, Postgres, Docker, Kubernetes, AWS

Research Experience
Senior Backend Engineer | Finora Ltd | 2022 - Present
- Built event-driven services
- Reduced latency 32%

Academic Background
MSc Computer Science 2017 - 2019
King's College London
"""


def main() -> None:
    tests = [
        ("CV1 - German Full Stack", CV1),
        ("CV2 - US Financial Analyst", CV2),
        ("CV3 - Nigerian Academic", CV3),
        ("CV4 - Common Section Names", CV4),
    ]

    for name, cv in tests:
        try:
            r = parse_resume(cv)
            assert isinstance(r, dict), "must return dict"
            assert "name" in r and "skills" in r and "education" in r
            print(f"OK  {name}")
            print(f"    name     = {r['name']!r}")
            print(f"    title    = {r['title']!r}")
            print(f"    email    = {r['email']!r}")
            print(f"    phone    = {r['phone']!r}")
            print(f"    location = {r['location']!r}")
            print(f"    skills   = {r['skills'][:8]} ... ({len(r['skills'])} total)")
            if name == "CV4 - Common Section Names":
                assert r["summary"] and "backend" in r["summary"].lower()
                assert any("python" in s.lower() for s in r["skills"])
                assert len(r["experience"]) >= 1
                assert len(r["education"]) >= 1
            print(f"    education= {len(r['education'])} record(s)")
            for edu in r["education"]:
                print(f"        {edu.get('institution')!r} | "
                      f"{edu.get('degree')!r} | "
                      f"{edu.get('start_date')} - {edu.get('end_date')}")
            print(f"    experience={len(r['experience'])} record(s)")
            for exp in r["experience"]:
                print(f"        {exp.get('job_title')!r} @ {exp.get('company')!r} | "
                      f"{exp.get('start_date')} - {exp.get('end_date')} | "
                      f"descs={len(exp.get('description') or [])}")
            print(f"    projects = {len(r['projects'])}")
            print(f"    languages= {r['languages']}")
            print(f"    certs    = {r['certifications']}")
            print(f"    awards   = {r['awards']}")
            print(f"    additional_sections = {list(r['additional_sections'].keys())}")
            print()
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name}: {exc}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    print("All universal parser checks passed.")


if __name__ == "__main__":
    main()