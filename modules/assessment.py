"""
modules/assessment.py
MCQ-based skill assessment with AI gap analysis.
Questions are generated dynamically based on user profile and domain.
"""
import json, random
from flask import Blueprint, request, jsonify, session
from modules.auth import login_required
from database.models import get_db

assessment_bp = Blueprint("assessment", __name__)

# ── Question Bank ─────────────────────────────────────────────────────────────
QUESTION_BANK = {
    "Web Development": [
        {"q":"What does CSS stand for?","opts":["Cascading Style Sheets","Creative Style System","Computer Style Sheets","Colorful Style Sheets"],"ans":0,"level":"easy"},
        {"q":"Which HTML tag is used to link an external CSS file?","opts":["<style>","<css>","<link>","<script>"],"ans":2,"level":"easy"},
        {"q":"What is the correct way to select an element with id='header' in CSS?","opts":[".header","#header","*header","header"],"ans":1,"level":"easy"},
        {"q":"What does DOM stand for?","opts":["Document Object Model","Data Object Model","Document Orientation Model","Dynamic Object Module"],"ans":0,"level":"medium"},
        {"q":"Which JS method is used to fetch data from an API?","opts":["get()","fetch()","request()","load()"],"ans":1,"level":"medium"},
        {"q":"What is the purpose of React's useEffect hook?","opts":["State management","Side effects and lifecycle","Routing","Styling"],"ans":1,"level":"medium"},
        {"q":"What is a REST API?","opts":["A database","An architecture style for web services","A JavaScript library","A CSS framework"],"ans":1,"level":"medium"},
        {"q":"What does CORS stand for?","opts":["Cross-Origin Resource Sharing","Cross-Object Routing System","Client-Origin Request Service","Content-Origin Routing Standard"],"ans":0,"level":"hard"},
        {"q":"Which HTTP method is idempotent?","opts":["POST","DELETE","PUT","PATCH"],"ans":2,"level":"hard"},
        {"q":"What is the Virtual DOM in React?","opts":["A copy of the real DOM in memory","A database","A testing tool","A CSS preprocessor"],"ans":0,"level":"hard"},
    ],
    "AI/ML": [
        {"q":"What does ML stand for?","opts":["Machine Language","Machine Learning","Model Learning","Main Logic"],"ans":1,"level":"easy"},
        {"q":"Which algorithm is used for classification?","opts":["K-Means","Linear Regression","Random Forest","PCA"],"ans":2,"level":"easy"},
        {"q":"What is overfitting?","opts":["Model performs well on training but poorly on test data","Model is too simple","Model has too few parameters","Model trains too slowly"],"ans":0,"level":"easy"},
        {"q":"What does CNN stand for in deep learning?","opts":["Convolutional Neural Network","Connected Node Network","Computed Neural Net","Cyclic Neural Network"],"ans":0,"level":"medium"},
        {"q":"Which metric measures binary classification performance?","opts":["MSE","RMSE","F1-Score","R-squared"],"ans":2,"level":"medium"},
        {"q":"What is gradient descent?","opts":["An optimisation algorithm","A type of neural network","A data preprocessing step","A regularisation technique"],"ans":0,"level":"medium"},
        {"q":"What is the vanishing gradient problem?","opts":["Gradients become too large","Gradients become very small making training slow","Model converges too fast","Loss function doesn't converge"],"ans":1,"level":"hard"},
        {"q":"What is transfer learning?","opts":["Using a pretrained model on a new task","Training from scratch","Copying weights randomly","A type of unsupervised learning"],"ans":0,"level":"hard"},
        {"q":"What does LSTM stand for?","opts":["Large Short-Term Memory","Long Short-Term Memory","Linear Sequential Training Model","Layered Sequence Training Module"],"ans":1,"level":"hard"},
        {"q":"What is the purpose of dropout in neural networks?","opts":["Speed up training","Prevent overfitting","Increase model size","Add more layers"],"ans":1,"level":"hard"},
    ],
    "Data Science": [
        {"q":"What is a DataFrame in Pandas?","opts":["A chart type","A 2D labelled data structure","A machine learning model","A database table"],"ans":1,"level":"easy"},
        {"q":"Which library is used for data visualisation in Python?","opts":["NumPy","Pandas","Matplotlib","Scikit-learn"],"ans":2,"level":"easy"},
        {"q":"What does SQL stand for?","opts":["Structured Query Language","Simple Query Logic","Sequential Query Layer","Standard Query Language"],"ans":0,"level":"easy"},
        {"q":"What is the purpose of data normalisation?","opts":["Remove duplicates","Scale features to a common range","Fill missing values","Split data into train/test"],"ans":1,"level":"medium"},
        {"q":"What is a p-value in statistics?","opts":["Probability of null hypothesis being true","Probability of observing data if null hypothesis is true","Statistical power","Effect size"],"ans":1,"level":"medium"},
        {"q":"What is the difference between supervised and unsupervised learning?","opts":["Supervised uses labelled data, unsupervised doesn't","Supervised is faster","Unsupervised always clusters data","No difference"],"ans":0,"level":"medium"},
        {"q":"What is PCA used for?","opts":["Classification","Dimensionality reduction","Clustering","Regression"],"ans":1,"level":"hard"},
        {"q":"What is the Central Limit Theorem?","opts":["All distributions are normal","Sample means approach normal distribution as n increases","Mean equals median","Data must be normalised"],"ans":1,"level":"hard"},
        {"q":"What is A/B testing?","opts":["Testing two versions to compare performance","A security test","A type of regression","Database testing"],"ans":0,"level":"medium"},
        {"q":"What does ETL stand for?","opts":["Extract, Transform, Load","Extract, Test, Launch","Evaluate, Train, Learn","Export, Transfer, Log"],"ans":0,"level":"easy"},
    ],
    "Cloud Computing": [
        {"q":"What does AWS stand for?","opts":["Amazon Web Services","Advanced Web Systems","Automated Web Software","Amazon Wide Systems"],"ans":0,"level":"easy"},
        {"q":"What is a container in cloud computing?","opts":["A virtual machine","A lightweight isolated runtime environment","A database","A storage bucket"],"ans":1,"level":"easy"},
        {"q":"What is Docker used for?","opts":["Database management","Containerisation","Networking","Load balancing"],"ans":1,"level":"easy"},
        {"q":"What does Kubernetes do?","opts":["Container orchestration","Database replication","Code deployment","Monitoring"],"ans":0,"level":"medium"},
        {"q":"What is Infrastructure as Code (IaC)?","opts":["Writing infrastructure using code/config files","Cloud billing","A security tool","A CI/CD pipeline"],"ans":0,"level":"medium"},
        {"q":"What is a CDN?","opts":["Content Delivery Network","Cloud Distribution Node","Central Data Network","Container Deployment Node"],"ans":0,"level":"easy"},
        {"q":"What is serverless computing?","opts":["Computing without servers","A cloud model where you don't manage servers","Free cloud services","Offline computing"],"ans":1,"level":"medium"},
        {"q":"What is the purpose of a load balancer?","opts":["Store data","Distribute traffic across servers","Monitor CPU","Run containers"],"ans":1,"level":"medium"},
        {"q":"What is Terraform?","opts":["A cloud provider","An IaC tool","A container runtime","A monitoring tool"],"ans":1,"level":"hard"},
        {"q":"What is a VPC in AWS?","opts":["Virtual Private Cloud","Virtual Processing Core","Verified Public Container","Variable Port Configuration"],"ans":0,"level":"hard"},
    ],
    "Cybersecurity": [
        {"q":"What does SQL Injection do?","opts":["Speeds up database queries","Inserts malicious SQL to manipulate a database","Encrypts data","Backs up databases"],"ans":1,"level":"easy"},
        {"q":"What is a firewall?","opts":["An antivirus","A network security system that monitors traffic","A type of encryption","A VPN service"],"ans":1,"level":"easy"},
        {"q":"What does HTTPS stand for?","opts":["HyperText Transfer Protocol Secure","High Transfer Protocol System","Hybrid Text Protocol Security","HyperText Posting Service"],"ans":0,"level":"easy"},
        {"q":"What is phishing?","opts":["Network attack","Deceptive attempt to steal credentials via fake communication","A malware type","A password manager"],"ans":1,"level":"easy"},
        {"q":"What is XSS?","opts":["Extra Secure System","Cross-Site Scripting","Cross-Server Session","Extra Style Sheet"],"ans":1,"level":"medium"},
        {"q":"What is penetration testing?","opts":["Testing internet speed","Simulating attacks to find vulnerabilities","Testing hardware performance","A compliance check"],"ans":1,"level":"medium"},
        {"q":"What does CIA stand for in cybersecurity?","opts":["Central Intelligence Agency","Confidentiality, Integrity, Availability","Cyber Intrusion Analysis","Control, Identify, Audit"],"ans":1,"level":"medium"},
        {"q":"What is a zero-day vulnerability?","opts":["A vulnerability patched immediately","An unknown vulnerability with no available fix","A 24-hour attack window","A daily security scan"],"ans":1,"level":"hard"},
        {"q":"What is multi-factor authentication?","opts":["Using multiple passwords","Using two or more verification methods","Biometric only login","Email verification"],"ans":1,"level":"medium"},
        {"q":"What is a Man-in-the-Middle attack?","opts":["Physical hardware theft","Attacker secretly intercepts communication between two parties","DDoS attack variant","Password cracking technique"],"ans":1,"level":"hard"},
    ],
    "UI/UX Design": [
        {"q":"What does UX stand for?","opts":["User Experience","User Extension","Unified eXchange","Universal Experience"],"ans":0,"level":"easy"},
        {"q":"What is a wireframe?","opts":["A finished design","A low-fidelity layout sketch of a UI","A CSS framework","A type of font"],"ans":1,"level":"easy"},
        {"q":"What is the purpose of user personas?","opts":["Brand guidelines","Fictional representations of target users","A type of prototype","A colour palette"],"ans":1,"level":"easy"},
        {"q":"What tool is most popular for UI design?","opts":["Photoshop","Figma","Excel","JIRA"],"ans":1,"level":"easy"},
        {"q":"What is a usability test?","opts":["Testing code performance","Observing real users interacting with a product","A colour contrast check","An accessibility audit"],"ans":1,"level":"medium"},
        {"q":"What is information architecture?","opts":["Database design","Organisation and structure of content in a product","Server architecture","A design pattern"],"ans":1,"level":"medium"},
        {"q":"What is the F-pattern in UX?","opts":["A font style","A layout pattern showing how users scan content","A form design","A navigation pattern"],"ans":1,"level":"medium"},
        {"q":"What does affordance mean in UX?","opts":["Colour theory","A property that communicates how an object should be used","Typography rules","Animation speed"],"ans":1,"level":"hard"},
        {"q":"What is a design system?","opts":["A project management tool","A collection of reusable components and guidelines","A prototyping method","A colour picker"],"ans":1,"level":"hard"},
        {"q":"What is cognitive load in UX?","opts":["Processing speed","Mental effort required to use an interface","Screen resolution","Animation complexity"],"ans":1,"level":"hard"},
    ],
    "Programming Fundamentals": [
        {"q":"What is a variable?","opts":["A fixed value","A named storage location in memory","A loop","A function"],"ans":1,"level":"easy"},
        {"q":"What is the time complexity of binary search?","opts":["O(n)","O(n²)","O(log n)","O(1)"],"ans":2,"level":"medium"},
        {"q":"What does OOP stand for?","opts":["Object-Oriented Programming","Open Operating Protocol","Output Optimisation Process","Object Output Programming"],"ans":0,"level":"easy"},
        {"q":"What is recursion?","opts":["A loop","A function that calls itself","A data structure","A sorting algorithm"],"ans":1,"level":"easy"},
        {"q":"What data structure uses LIFO?","opts":["Queue","Stack","Tree","Graph"],"ans":1,"level":"easy"},
        {"q":"What is Big O notation?","opts":["A programming language","A way to describe algorithm efficiency","A type of loop","A design pattern"],"ans":1,"level":"medium"},
        {"q":"What is the difference between a list and a tuple in Python?","opts":["No difference","Lists are mutable, tuples are immutable","Tuples are faster always","Lists can only store strings"],"ans":1,"level":"medium"},
        {"q":"What is a hash table?","opts":["A sorted array","A data structure with key-value pairs using hash functions","A type of tree","A graph algorithm"],"ans":1,"level":"medium"},
        {"q":"What is dynamic programming?","opts":["Runtime programming","Breaking complex problems into simpler overlapping subproblems","Object-oriented design","A scripting technique"],"ans":1,"level":"hard"},
        {"q":"What is the difference between TCP and UDP?","opts":["No difference","TCP is reliable and ordered, UDP is faster but unreliable","UDP is encrypted","TCP is faster"],"ans":1,"level":"hard"},
    ],
}

DOMAIN_MAP = {
    "Technology": ["Web Development","AI/ML","Programming Fundamentals","Cloud Computing"],
    "Information Technology": ["Web Development","Programming Fundamentals","Cloud Computing","Cybersecurity"],
    "Analytics": ["Data Science","AI/ML","Programming Fundamentals"],
    "Design": ["UI/UX Design","Web Development"],
    "Cybersecurity": ["Cybersecurity","Networking","Programming Fundamentals"],
    "Healthcare": ["Programming Fundamentals","Data Science"],
    "Finance & Commerce": ["Programming Fundamentals","Data Science"],
    "Business": ["Programming Fundamentals","Data Science"],
}


def _get_domains_for_user(uid: int, conn) -> list:
    """Pick assessment domains based on user's top interests and skills."""
    interests = conn.execute(
        "SELECT domain, interest_score FROM user_interest WHERE user_id=? ORDER BY interest_score DESC LIMIT 3",
        (uid,)
    ).fetchall()

    domains = []
    for row in interests:
        mapped = DOMAIN_MAP.get(row["domain"], [])
        for d in mapped:
            if d not in domains:
                domains.append(d)

    if not domains:
        domains = ["Programming Fundamentals", "Web Development", "Data Science"]

    return domains[:3]


def generate_questions(uid: int, conn, n_per_domain: int = 5) -> list:
    """Generate a mixed MCQ set for the user."""
    domains = _get_domains_for_user(uid, conn)
    questions = []
    used_ids  = set()

    for domain in domains:
        pool = QUESTION_BANK.get(domain, [])
        random.shuffle(pool)
        count = 0
        for q in pool:
            key = f"{domain}:{q['q']}"
            if key not in used_ids and count < n_per_domain:
                questions.append({
                    "domain":   domain,
                    "question": q["q"],
                    "options":  q["opts"],
                    "level":    q["level"],
                    "answer":   q["ans"],       # sent to client but hidden in JS
                })
                used_ids.add(key)
                count += 1

    random.shuffle(questions)
    return questions


# ── Routes ────────────────────────────────────────────────────────────────────

@assessment_bp.route("/assessment/questions", methods=["GET"])
@login_required
def get_questions():
    uid  = session["user_id"]
    conn = get_db()
    questions = generate_questions(uid, conn)
    conn.close()
    # Strip answers before sending to client
    client_qs = [
        {"domain": q["domain"], "question": q["question"],
         "options": q["options"], "level": q["level"]}
        for q in questions
    ]
    # Store full questions (with answers) in session for server-side grading
    session["assessment_questions"] = questions
    return jsonify({"questions": client_qs, "total": len(client_qs)}), 200


@assessment_bp.route("/assessment/submit", methods=["POST"])
@login_required
def submit_assessment():
    """
    POST /api/assessment/submit
    Body: { "answers": [0, 2, 1, ...] }  (index of chosen option per question)
    """
    uid   = session["user_id"]
    data  = request.get_json(force=True)
    answers = data.get("answers", [])
    questions = session.get("assessment_questions", [])

    if not questions:
        return jsonify({"error": "No active assessment. Please start again."}), 400

    # Grade
    domain_scores = {}
    domain_totals = {}

    for i, (q, chosen) in enumerate(zip(questions, answers)):
        domain = q["domain"]
        correct = int(q["answer"]) == int(chosen)
        domain_scores[domain] = domain_scores.get(domain, 0) + (1 if correct else 0)
        domain_totals[domain] = domain_totals.get(domain, 0) + 1

    total_q       = len(questions)
    total_correct = sum(domain_scores.values())
    overall_score = round(total_correct / total_q * 100, 1) if total_q else 0

    # Classify strengths/weaknesses
    strengths  = []
    weak_areas = []
    domain_pcts = {}

    for domain in domain_totals:
        pct = round(domain_scores.get(domain, 0) / domain_totals[domain] * 100, 1)
        domain_pcts[domain] = pct
        if pct >= 70:
            strengths.append(domain)
        elif pct < 50:
            weak_areas.append(domain)

    # Save result
    conn = get_db()
    for domain in domain_totals:
        conn.execute("""
            INSERT INTO assessment_result
            (user_id, domain, score, total_questions, correct_answers, strengths, weak_areas)
            VALUES (?,?,?,?,?,?,?)
        """, (
            uid, domain, domain_pcts[domain],
            domain_totals[domain], domain_scores.get(domain, 0),
            json.dumps(strengths), json.dumps(weak_areas)
        ))
    conn.commit()

    # Build skill gap recommendations
    recommendations = {}
    for domain in weak_areas:
        recommendations[domain] = _get_recommendations(domain)

    # Career readiness (fetch top recommended career)
    rec = conn.execute(
        "SELECT c.career_name, r.compatibility_score FROM recommendation r "
        "JOIN career c ON c.career_id=r.career_id "
        "WHERE r.user_id=? ORDER BY r.rank LIMIT 1", (uid,)
    ).fetchone()
    career_readiness = {
        "career": rec["career_name"] if rec else "Your Target Career",
        "readiness": min(100, round(overall_score * 0.9 + 10, 1)) if rec else overall_score,
    }

    conn.close()
    session.pop("assessment_questions", None)

    return jsonify({
        "overall_score":    overall_score,
        "total_questions":  total_q,
        "total_correct":    total_correct,
        "domain_scores":    domain_pcts,
        "strengths":        strengths,
        "weak_areas":       weak_areas,
        "career_readiness": career_readiness,
        "recommendations":  recommendations,
    }), 200


def _get_recommendations(domain: str) -> dict:
    recs = {
        "Web Development": {
            "certs": ["freeCodeCamp Web Dev","The Odin Project","Meta Front-End Certificate"],
            "resources": ["MDN Web Docs","javascript.info","React Docs"],
            "skills": ["JavaScript","React","HTML/CSS","Node.js"],
        },
        "AI/ML": {
            "certs": ["Andrew Ng ML Specialisation","Fast.ai","Google ML Crash Course"],
            "resources": ["Kaggle Learn","Papers With Code","Towards Data Science"],
            "skills": ["Python","Scikit-learn","TensorFlow","Statistics"],
        },
        "Data Science": {
            "certs": ["IBM Data Science Certificate","Google Data Analytics","DataCamp"],
            "resources": ["Kaggle","Mode Analytics","SQL Zoo"],
            "skills": ["Python","SQL","Statistics","Data Visualisation"],
        },
        "Cloud Computing": {
            "certs": ["AWS Cloud Practitioner","Azure Fundamentals","GCP Associate"],
            "resources": ["AWS Free Tier","Microsoft Learn","Google Cloud Skills Boost"],
            "skills": ["AWS","Docker","Kubernetes","Terraform"],
        },
        "Cybersecurity": {
            "certs": ["CompTIA Security+","CEH","CISSP","TryHackMe"],
            "resources": ["TryHackMe","HackTheBox","OWASP Top 10"],
            "skills": ["Network Security","Ethical Hacking","Python","Linux"],
        },
        "UI/UX Design": {
            "certs": ["Google UX Design Certificate","Interaction Design Foundation"],
            "resources": ["Nielsen Norman Group","UX Collective","Figma Community"],
            "skills": ["Figma","User Research","Prototyping","Design Systems"],
        },
        "Programming Fundamentals": {
            "certs": ["CS50 Harvard","PCEP Python Certification","freeCodeCamp"],
            "resources": ["LeetCode","HackerRank","GeeksForGeeks"],
            "skills": ["Python","DSA","Problem Solving","OOP"],
        },
    }
    return recs.get(domain, {"certs": [], "resources": [], "skills": []})


@assessment_bp.route("/assessment/history", methods=["GET"])
@login_required
def assessment_history():
    uid  = session["user_id"]
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM assessment_result WHERE user_id=? ORDER BY taken_at DESC LIMIT 20", (uid,)
    ).fetchall()
    conn.close()
    return jsonify({"history": [dict(r) for r in rows]}), 200
