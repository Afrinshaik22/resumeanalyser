from flask import Flask, render_template, request, jsonify
import io
import os
from PyPDF2 import PdfReader

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_stream: io.BytesIO) -> str:
    """Extract text from a PDF file-like object using PyPDF2."""
    reader = PdfReader(file_stream)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts)


def classify_domain(text: str) -> str:
    """Rough heuristic-based domain classifier: IT / Medical / Non-tech."""
    lower = text.lower()

    it_keywords = [
        "software", "developer", "engineer", "programmer", "java", "python",
        "javascript", "node.js", "react", "angular", "git", "devops", "cloud",
        "aws", "azure", "gcp", "docker", "kubernetes", "data analyst",
        "machine learning", "sql", "database", "full stack", "frontend",
        "backend", "cybersecurity",
    ]

    medical_keywords = [
        "hospital", "clinic", "nurse", "doctor", "physician", "surgeon",
        "mbbs", "md", "patient care", "clinical", "icu", "ward", "pharmacy",
        "pharmacist", "lab technician", "radiology", "cardiology", "neurology",
        "ot technician", "mri", "ct scan", "healthcare",
    ]

    if any(k in lower for k in medical_keywords):
        return "Medical"
    if any(k in lower for k in it_keywords):
        return "IT"
    return "Non-tech"


def extract_skills(text: str) -> list[str]:
    """Simple skill extractor using a fixed catalog of common skills."""
    catalog = [
        # IT / Software
        "Python", "Java", "C", "C++", "C#", "JavaScript", "TypeScript",
        "HTML", "CSS", "React", "Angular", "Vue", "Django", "Flask",
        "Node.js", "Express", "Spring", "SQL", "NoSQL", "MongoDB",
        "PostgreSQL", "MySQL", "Git", "Docker", "Kubernetes", "AWS", "Azure",
        "GCP", "Linux", "REST API", "Machine Learning", "Data Analysis",
        # Medical
        "Patient Care", "Clinical Procedures", "Phlebotomy", "ECG",
        "BLS", "ACLS", "ICU", "Emergency Care", "Surgery Assistance",
        # Generic / Soft skills
        "Communication", "Teamwork", "Leadership", "Problem Solving",
        "Time Management", "Project Management", "Customer Service",
    ]

    found = set()
    lower = text.lower()
    for skill in catalog:
        if skill.lower() in lower:
            found.add(skill)
    return sorted(found)


def generate_feedback(text: str, domain: str, skills: list[str]):
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []

    # Length-based feedback
    if len(text) < 800:
        weaknesses.append(
            "Resume appears quite short; consider adding more detail about your experience and achievements."
        )
        suggestions.append(
            "Add 3–5 bullet points for each recent role, focusing on your responsibilities and measurable impact."
        )
    else:
        strengths.append("Good overall level of detail about your work experience.")

    # Summary presence
    first_chunk = text[:600].lower()
    if "summary" in first_chunk or "objective" in first_chunk:
        strengths.append("Professional summary/objective is present near the top of the resume.")
    else:
        weaknesses.append("No clear professional summary/objective section found at the top.")
        suggestions.append(
            "Add a 2–3 sentence professional summary that highlights your domain, years of experience, and top skills."
        )

    # Domain-specific hints
    if domain == "IT":
        strengths.append("Profile appears aligned with Information Technology.")
        core_it = ["Python", "Java", "JavaScript", "SQL", "Cloud", "DevOps"]
        if not any(s.lower() in (sk.lower() for sk in skills) for s in core_it):
            suggestions.append(
                "Highlight core technical skills (languages, frameworks, databases, cloud tools) in a dedicated Skills section."
            )
    elif domain == "Medical":
        strengths.append("Profile appears aligned with the Medical/Healthcare domain.")
        suggestions.append(
            "Include relevant licenses, registrations, and certifications with validity dates (e.g., medical council registration, BLS, ACLS)."
        )
    else:
        strengths.append("Profile seems to be from a non-technical domain.")

    # Skills section feedback
    if not skills:
        weaknesses.append("Could not clearly detect a skills section.")
        suggestions.append(
            "Create a separate Skills section listing tools, technologies, and soft skills using bullet points."
        )
    else:
        strengths.append("Key skills are visible; ensure they are grouped and easy to scan.")

    if not suggestions:
        suggestions.append(
            "Review each bullet point to emphasize outcomes and metrics (e.g., 'Improved process efficiency by 20%')."
        )

    return strengths, weaknesses, suggestions


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "No file part named 'resume' in the request."}), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are supported."}), 400

    try:
        pdf_bytes = io.BytesIO(file.read())
        text = extract_text_from_pdf(pdf_bytes)
    except Exception:
        return jsonify({"error": "Could not read the PDF file. Please upload a valid PDF resume."}), 500

    if not text.strip():
        return jsonify({"error": "No readable text found in the PDF."}), 400

    domain = classify_domain(text)
    skills = extract_skills(text)
    strengths, weaknesses, suggestions = generate_feedback(text, domain, skills)

    # NOTE: You could send the result via email here using an SMTP client or email API
    # if an email address is provided in the request form.

    return jsonify(
        {
            "domain": domain,
            "skills": skills,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
        }
    )


if __name__ == "__main__":
    # For local development use only. In production, use a proper WSGI server.
    # Bind to 0.0.0.0 so it works inside Docker containers.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
