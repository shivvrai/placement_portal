"""
CCIP Database Seed Script
=========================
Populates the database with realistic test data for development and testing.

Run:
    cd d:\Projects\p1\backend
    python -m scripts.seed

Creates:
    - 5 departments, 60 students, 1 TPO, 1 faculty
    - 100+ skills in taxonomy
    - 12 companies with 25 jobs (each with required skills)
    - 10 placement drives (mix of statuses)
    - 40 applications + 15 placement outcomes
    - 20 subjects with curriculum skill mappings
    - 55 assessment questions (5+ per topic/difficulty)
"""

import asyncio
import os
import sys
import uuid
import random
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import engine, AsyncSessionLocal, Base
from app.core.security import hash_password


# ─── Helpers ────────────────────────────────────────────────────────

def utcnow():
    return datetime.now(timezone.utc)

def rand_cgpa():
    return Decimal(str(round(random.uniform(6.0, 9.6), 1)))

def rand_date_future(days_min=5, days_max=90):
    return date.today() + timedelta(days=random.randint(days_min, days_max))

def rand_date_past(days_min=10, days_max=180):
    return date.today() - timedelta(days=random.randint(days_min, days_max))


# ─── Data Definitions ──────────────────────────────────────────────

DEPARTMENT_DATA = [
    ("CS", "Computer Science"),
    ("IT", "Information Technology"),
    ("ECE", "Electronics & Communication"),
    ("ME", "Mechanical Engineering"),
    ("EEE", "Electrical Engineering"),
]

SKILL_DATA = [
    # (name, category)
    # Languages
    ("Python", "language"), ("JavaScript", "language"), ("Java", "language"),
    ("C++", "language"), ("SQL", "language"), ("TypeScript", "language"),
    ("Go", "language"), ("Rust", "language"), ("R", "language"),
    ("C#", "language"), ("PHP", "language"), ("Kotlin", "language"),
    # Frameworks / Libraries
    ("React", "framework"), ("Angular", "framework"), ("Vue.js", "framework"),
    ("Node.js", "framework"), ("Django", "framework"), ("Flask", "framework"),
    ("FastAPI", "framework"), ("Spring Boot", "framework"), ("Express.js", "framework"),
    ("Next.js", "framework"),
    # Tools
    ("Docker", "tool"), ("Kubernetes", "tool"), ("Git", "tool"), ("Linux", "tool"),
    ("Jenkins", "tool"), ("Nginx", "tool"), ("Webpack", "tool"), ("Vite", "tool"),
    # Platforms / Cloud
    ("AWS", "platform"), ("GCP", "platform"), ("Azure", "platform"),
    ("Terraform", "platform"), ("Firebase", "platform"),
    # Databases
    ("PostgreSQL", "database"), ("MongoDB", "database"), ("Redis", "database"),
    ("MySQL", "database"), ("Elasticsearch", "database"),
    # ML / AI
    ("Machine Learning", "concept"), ("Deep Learning", "concept"),
    ("TensorFlow", "library"), ("PyTorch", "library"), ("scikit-learn", "library"),
    ("NLP", "concept"), ("Computer Vision", "concept"), ("Statistics", "concept"),
    ("pandas", "library"), ("numpy", "library"),
    # CS Fundamentals
    ("Data Structures", "concept"), ("Algorithms", "concept"),
    ("System Design", "concept"), ("OOP", "concept"),
    ("Computer Networks", "concept"), ("Operating Systems", "concept"),
    ("Design Patterns", "concept"), ("DBMS", "concept"),
    # Data Engineering
    ("Apache Spark", "tool"), ("Apache Kafka", "tool"),
    ("Tableau", "tool"), ("Power BI", "tool"), ("Excel", "tool"),
    ("Data Analysis", "concept"), ("Data Engineering", "concept"),
    ("ETL", "concept"), ("Data Warehousing", "concept"),
    # DevOps / SRE
    ("CI/CD", "methodology"), ("Agile", "methodology"), ("Scrum", "methodology"),
    ("Microservices", "concept"), ("REST API", "concept"), ("GraphQL", "concept"),
    # Web
    ("HTML/CSS", "concept"), ("Responsive Design", "concept"),
    ("Web Security", "concept"), ("OAuth/JWT", "concept"),
    # Soft Skills
    ("Communication", "soft_skill"), ("Teamwork", "soft_skill"),
    ("Problem Solving", "soft_skill"), ("Leadership", "soft_skill"),
    ("Critical Thinking", "soft_skill"), ("Time Management", "soft_skill"),
]

STUDENT_NAMES = [
    "Priya Agarwal", "Arjun Sharma", "Sneha Reddy", "Rahul Nair", "Divya Iyer",
    "Mohammed Ali", "Kavya Menon", "Aditya Verma", "Pooja Gupta", "Karan Joshi",
    "Shreya Das", "Vishal Kumar", "Ananya Singh", "Rohit Patil", "Neha Kapoor",
    "Siddharth Rao", "Meera Desai", "Varun Choudhury", "Ishita Bose", "Pranav Kulkarni",
    "Riya Patel", "Amit Tiwari", "Swati Mishra", "Deepak Pandey", "Komal Yadav",
    "Rajesh Khanna", "Nisha Pillai", "Sahil Mehta", "Tanya Saxena", "Manish Dubey",
    "Aisha Khan", "Vikram Rathore", "Ritika Soni", "Gaurav Thakur", "Pallavi Jain",
    "Nikhil Banerjee", "Supriya Ghosh", "Harshit Aggarwal", "Simran Kaur", "Rohan Chawla",
    "Megha Naik", "Tushar Garg", "Anjali Negi", "Rahul Deshpande", "Preeti Goyal",
    "Abhinav Srivastava", "Nandini Bhatt", "Akash Tripathi", "Shreya Murthy", "Dev Chauhan",
    "Tanvi Rajan", "Yashwant Reddy", "Aditi Hegde", "Pranesh Iyer", "Sonal Rawat",
    "Karthik Venkat", "Radhika Pandit", "Vivek Nambiar", "Isha Malhotra", "Chirag Shetty",
]

STUDENT_DEPT_WEIGHTS = ["CS"] * 22 + ["IT"] * 15 + ["ECE"] * 10 + ["ME"] * 8 + ["EEE"] * 5

COMPANY_DATA = [
    ("Google", "Technology", "Bangalore", "10000+"),
    ("Amazon", "E-Commerce / Cloud", "Hyderabad", "10000+"),
    ("Microsoft", "Technology", "Bangalore", "10000+"),
    ("Infosys", "IT Services", "Pune", "10000+"),
    ("TCS", "IT Services", "Mumbai", "10000+"),
    ("Wipro", "IT Services", "Bangalore", "10000+"),
    ("Deloitte", "Consulting", "Gurgaon", "10000+"),
    ("Goldman Sachs", "Finance", "Bangalore", "5000+"),
    ("Adobe", "Technology", "Noida", "5000+"),
    ("Flipkart", "E-Commerce", "Bangalore", "5000+"),
    ("Razorpay", "Fintech", "Bangalore", "1000+"),
    ("PhonePe", "Fintech", "Bangalore", "1000+"),
]

JOB_DATA = [
    # (company_idx, title, role_category, min_cgpa, sal_min, sal_max, eligible_depts, required_skills)
    (0, "SDE-1", "Software Engineering", 7.5, 28, 45, ["CS", "IT"], ["Python", "Data Structures", "Algorithms", "System Design", "SQL", "Git"]),
    (0, "Data Analyst", "Data Science", 7.0, 20, 32, ["CS", "IT", "ECE"], ["Python", "SQL", "Statistics", "pandas", "Tableau"]),
    (1, "SDE-1", "Software Engineering", 7.0, 22, 38, ["CS", "IT"], ["Java", "Data Structures", "Algorithms", "AWS", "SQL", "Docker"]),
    (1, "Data Engineer", "Data Engineering", 7.0, 18, 30, ["CS", "IT", "ECE"], ["Python", "SQL", "Apache Spark", "AWS", "ETL"]),
    (2, "SDE Intern", "Software Engineering", 7.5, 35, 50, ["CS"], ["C++", "Data Structures", "Algorithms", "OOP", "System Design"]),
    (2, "ML Engineer", "Machine Learning", 8.0, 30, 48, ["CS", "IT"], ["Python", "Machine Learning", "Deep Learning", "PyTorch", "Statistics"]),
    (3, "Systems Engineer", "Software Engineering", 6.0, 3.5, 4.5, ["CS", "IT", "ECE", "ME", "EEE"], ["Java", "SQL", "DBMS", "OOP"]),
    (3, "Senior Systems Engineer", "Software Engineering", 7.0, 5, 7, ["CS", "IT", "ECE"], ["Python", "React", "Node.js", "SQL", "Agile"]),
    (4, "Assistant Systems Engineer", "Software Engineering", 5.5, 3.0, 3.6, ["CS", "IT", "ECE", "ME", "EEE"], ["Java", "SQL", "Communication"]),
    (4, "Digital Engineer", "Software Engineering", 7.0, 5, 7, ["CS", "IT"], ["Python", "React", "Docker", "CI/CD", "Agile"]),
    (5, "Project Engineer", "Software Engineering", 6.0, 3.5, 5, ["CS", "IT", "ECE", "ME"], ["Java", "SQL", "OOP", "Teamwork"]),
    (6, "Analyst", "Consulting", 7.5, 8, 12, ["CS", "IT", "ECE"], ["SQL", "Excel", "Python", "Data Analysis", "Communication"]),
    (6, "Technology Consultant", "Consulting", 7.0, 10, 15, ["CS", "IT"], ["Python", "AWS", "Docker", "Microservices", "Agile"]),
    (7, "Technology Analyst", "Finance Technology", 8.0, 18, 28, ["CS", "IT"], ["Java", "Python", "SQL", "Data Structures", "System Design"]),
    (8, "Member of Technical Staff", "Software Engineering", 7.5, 18, 28, ["CS", "IT"], ["JavaScript", "React", "Node.js", "TypeScript", "Git"]),
    (9, "SDE-1", "Software Engineering", 7.0, 18, 30, ["CS", "IT"], ["Java", "Data Structures", "Algorithms", "MySQL", "Docker"]),
    (9, "Data Scientist", "Data Science", 7.5, 15, 25, ["CS", "IT"], ["Python", "Machine Learning", "Statistics", "SQL", "pandas"]),
    (10, "Backend Engineer", "Software Engineering", 7.0, 15, 25, ["CS", "IT"], ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"]),
    (10, "Frontend Engineer", "Software Engineering", 7.0, 14, 22, ["CS", "IT"], ["JavaScript", "React", "TypeScript", "HTML/CSS", "Git"]),
    (11, "Full Stack Developer", "Software Engineering", 7.0, 14, 22, ["CS", "IT"], ["Python", "React", "PostgreSQL", "Docker", "REST API"]),
    (1, "Cloud Support Engineer", "Cloud", 6.5, 10, 16, ["CS", "IT", "ECE"], ["AWS", "Linux", "Python", "Computer Networks", "Docker"]),
    (2, "Program Manager", "Management", 8.0, 25, 40, ["CS", "IT"], ["Communication", "Agile", "System Design", "Leadership"]),
    (7, "Quantitative Analyst", "Finance Technology", 8.5, 30, 80, ["CS"], ["Python", "Statistics", "Machine Learning", "C++", "Algorithms"]),
    (8, "Research Scientist", "Machine Learning", 8.0, 22, 35, ["CS"], ["Python", "Deep Learning", "PyTorch", "NLP", "Statistics"]),
    (0, "DevOps Engineer", "DevOps", 7.0, 22, 35, ["CS", "IT"], ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Terraform"]),
]

SUBJECT_DATA = {
    "CS": [
        ("CS301", "Data Structures & Algorithms", 5, 4),
        ("CS302", "Database Management Systems", 5, 4),
        ("CS303", "Operating Systems", 5, 3),
        ("CS304", "Software Engineering", 5, 3),
        ("CS401", "Computer Networks", 6, 4),
        ("CS402", "Machine Learning", 6, 4),
        ("CS403", "Big Data Analytics", 6, 3),
        ("CS404", "Web Technologies", 6, 3),
        ("CS501", "Cloud Computing", 7, 3),
        ("CS502", "Deep Learning", 7, 4),
        ("CS503", "Natural Language Processing", 7, 3),
        ("CS601", "Distributed Systems", 8, 3),
        ("CS602", "Information Security", 8, 3),
        ("CS603", "Project Work", 8, 6),
    ],
    "IT": [
        ("IT301", "Data Structures", 5, 4),
        ("IT302", "DBMS", 5, 4),
        ("IT401", "Web Development", 6, 4),
        ("IT402", "Cloud Computing", 6, 3),
    ],
    "ECE": [
        ("ECE301", "Digital Signal Processing", 5, 4),
        ("ECE302", "Embedded Systems", 5, 4),
    ],
}

# Mapping: subject_code → list of skill names for curriculum skills
SUBJECT_SKILL_MAP = {
    "CS301": ["Data Structures", "Algorithms", "Python", "C++"],
    "CS302": ["SQL", "DBMS", "PostgreSQL"],
    "CS303": ["Operating Systems", "Linux"],
    "CS304": ["Agile", "Git", "OOP"],
    "CS401": ["Computer Networks", "REST API", "Web Security"],
    "CS402": ["Machine Learning", "Python", "Statistics", "scikit-learn"],
    "CS403": ["Apache Spark", "Data Analysis", "Python"],
    "CS404": ["HTML/CSS", "JavaScript", "React", "Node.js"],
    "CS501": ["AWS", "Docker", "Kubernetes", "Terraform"],
    "CS502": ["Deep Learning", "PyTorch", "Python"],
    "CS503": ["NLP", "Python", "Machine Learning"],
    "CS601": ["System Design", "Microservices", "Apache Kafka"],
    "CS602": ["Web Security", "OAuth/JWT", "Computer Networks"],
    "CS603": ["Git", "Docker", "Communication", "System Design"],
    "IT301": ["Data Structures", "Algorithms", "Java"],
    "IT302": ["SQL", "DBMS", "MySQL"],
    "IT401": ["HTML/CSS", "JavaScript", "React"],
    "IT402": ["AWS", "Docker"],
    "ECE301": ["Python", "Statistics"],
    "ECE302": ["C++", "Linux"],
}

ASSESSMENT_QUESTIONS = [
    # ─── Python ───────────────────────────────────────────
    ("Python", "beginner", "What is the output of `print(type([]))`?",
     ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"],
     "<class 'list'>", "[] creates an empty list."),
    ("Python", "beginner", "Which keyword defines a function in Python?",
     ["func", "define", "def", "function"],
     "def", "The 'def' keyword is used to define functions."),
    ("Python", "beginner", "What does `len('hello')` return?",
     ["4", "5", "6", "Error"],
     "5", "'hello' has 5 characters."),
    ("Python", "beginner", "Which data type is immutable in Python?",
     ["list", "dict", "set", "tuple"],
     "tuple", "Tuples are immutable — they cannot be changed after creation."),
    ("Python", "beginner", "What is the correct syntax to output 'Hello World'?",
     ["echo('Hello World')", "print('Hello World')", "p('Hello World')", "console.log('Hello World')"],
     "print('Hello World')", "Python uses print() for output."),
    ("Python", "intermediate", "What does `list(range(0, 10, 3))` return?",
     ["[0, 3, 6, 9]", "[0, 3, 6]", "[3, 6, 9]", "[0, 1, 2, 3]"],
     "[0, 3, 6, 9]", "range(0, 10, 3) generates 0, 3, 6, 9."),
    ("Python", "intermediate", "What is the difference between a list and a tuple?",
     ["Lists are mutable, tuples are immutable", "Tuples are faster", "No difference", "Lists use {} syntax"],
     "Lists are mutable, tuples are immutable", "Lists can be modified; tuples cannot."),
    ("Python", "intermediate", "What does the `@staticmethod` decorator do?",
     ["Defines a static method with no access to instance", "Makes the method private", "Caches the result", "Makes it async"],
     "Defines a static method with no access to instance", "Static methods don't receive self or cls."),
    ("Python", "intermediate", "What is the output of `{1, 2, 3} & {2, 3, 4}`?",
     ["{2, 3}", "{1, 2, 3, 4}", "{1, 4}", "Error"],
     "{2, 3}", "& is the intersection operator for sets."),
    ("Python", "intermediate", "What is a list comprehension?",
     ["A compact syntax to create lists", "A way to compress lists", "A sorting algorithm", "A type of loop"],
     "A compact syntax to create lists", "e.g., [x**2 for x in range(5)]"),
    ("Python", "advanced", "What is the output of `print([x**2 for x in range(5) if x % 2 != 0])`?",
     ["[1, 9]", "[0, 4, 16]", "[1, 4, 9]", "[1, 9, 25]"],
     "[1, 9]", "Odd numbers in range(5) are 1, 3. Their squares are 1, 9."),
    ("Python", "advanced", "What does `__slots__` do in a class?",
     ["Restricts attributes and saves memory", "Defines class methods", "Creates getters/setters", "Enables multithreading"],
     "Restricts attributes and saves memory", "__slots__ prevents __dict__ creation per instance."),
    ("Python", "advanced", "What is the GIL in Python?",
     ["Global Interpreter Lock — limits true parallelism", "A garbage collector", "A graphics library", "A file lock"],
     "Global Interpreter Lock — limits true parallelism", "The GIL prevents true multi-threading in CPython."),
    ("Python", "advanced", "How does `asyncio.gather()` differ from `asyncio.wait()`?",
     ["gather returns results in order; wait returns as completed", "No difference", "gather is synchronous", "wait is deprecated"],
     "gather returns results in order; wait returns as completed", "gather preserves order of results."),
    ("Python", "advanced", "What is a metaclass in Python?",
     ["A class of a class — controls class creation", "A superclass", "An abstract class", "A private class"],
     "A class of a class — controls class creation", "Metaclasses define how classes behave."),
    # ─── SQL ──────────────────────────────────────────────
    ("SQL", "beginner", "Which SQL clause filters rows?",
     ["WHERE", "HAVING", "GROUP BY", "ORDER BY"],
     "WHERE", "WHERE filters rows before grouping."),
    ("SQL", "beginner", "Which command adds a new row to a table?",
     ["INSERT INTO", "ADD ROW", "CREATE ROW", "APPEND"],
     "INSERT INTO", "INSERT INTO table VALUES (...) adds a row."),
    ("SQL", "beginner", "What does SELECT DISTINCT do?",
     ["Returns unique values only", "Selects all columns", "Filters NULL values", "Joins two tables"],
     "Returns unique values only", "DISTINCT removes duplicate rows."),
    ("SQL", "beginner", "Which clause sorts the result set?",
     ["ORDER BY", "SORT BY", "GROUP BY", "ARRANGE BY"],
     "ORDER BY", "ORDER BY sorts results in ASC or DESC order."),
    ("SQL", "beginner", "What does COUNT(*) return?",
     ["Number of rows", "Sum of all values", "Average value", "Maximum value"],
     "Number of rows", "COUNT(*) counts all rows including NULLs."),
    ("SQL", "intermediate", "What does a LEFT JOIN return?",
     ["All rows from left + matching from right", "Only matching rows", "All rows from right", "All rows from both"],
     "All rows from left + matching from right", "LEFT JOIN keeps all left-table rows."),
    ("SQL", "intermediate", "What is a CTE (Common Table Expression)?",
     ["A temporary named result set using WITH", "A type of index", "A stored procedure", "A trigger"],
     "A temporary named result set using WITH", "WITH cte AS (SELECT ...) enables readable subqueries."),
    ("SQL", "intermediate", "What is normalization?",
     ["Organizing data to reduce redundancy", "Adding indexes", "Encrypting data", "Compressing tables"],
     "Organizing data to reduce redundancy", "Normal forms (1NF, 2NF, 3NF) reduce data duplication."),
    ("SQL", "intermediate", "What is the difference between WHERE and HAVING?",
     ["WHERE filters rows; HAVING filters groups", "No difference", "HAVING is faster", "WHERE works with aggregates"],
     "WHERE filters rows; HAVING filters groups", "HAVING is used after GROUP BY with aggregate functions."),
    ("SQL", "intermediate", "What does an INDEX do?",
     ["Speeds up data retrieval", "Encrypts data", "Compresses data", "Backs up data"],
     "Speeds up data retrieval", "Indexes create a data structure for faster lookups."),
    ("SQL", "advanced", "Which window function gives rank with gaps?",
     ["RANK()", "DENSE_RANK()", "ROW_NUMBER()", "NTILE()"],
     "RANK()", "RANK() skips ranks after ties, creating gaps."),
    ("SQL", "advanced", "What is a deadlock in databases?",
     ["Two transactions waiting for each other indefinitely", "A corrupted table", "A slow query", "A network error"],
     "Two transactions waiting for each other indefinitely", "Deadlocks require intervention to resolve."),
    ("SQL", "advanced", "What is the difference between OLTP and OLAP?",
     ["OLTP for transactions, OLAP for analytics", "No difference", "OLTP is slower", "OLAP is for inserts only"],
     "OLTP for transactions, OLAP for analytics", "OLTP handles daily operations; OLAP supports analysis."),
    ("SQL", "advanced", "What is a materialized view?",
     ["A stored query result that can be refreshed", "A temporary table", "A virtual table", "An index type"],
     "A stored query result that can be refreshed", "Unlike regular views, materialized views store data physically."),
    ("SQL", "advanced", "Explain ACID properties in databases.",
     ["Atomicity, Consistency, Isolation, Durability", "Add, Create, Insert, Delete", "Access, Control, Identity, Data", "Aggregate, Count, Index, Distinct"],
     "Atomicity, Consistency, Isolation, Durability", "ACID ensures reliable transaction processing."),
    # ─── React ────────────────────────────────────────────
    ("React", "beginner", "What hook manages state in a functional component?",
     ["useState", "useEffect", "useContext", "useReducer"],
     "useState", "useState returns [value, setter] for local state."),
    ("React", "beginner", "What is JSX?",
     ["JavaScript syntax extension for writing HTML-like code", "A JSON variant", "A CSS framework", "A testing library"],
     "JavaScript syntax extension for writing HTML-like code", "JSX is compiled to React.createElement() calls."),
    ("React", "beginner", "How do you pass data from parent to child component?",
     ["Props", "State", "Context", "Refs"],
     "Props", "Props are read-only data passed from parent to child."),
    ("React", "beginner", "What does `useEffect` with an empty dependency array do?",
     ["Runs only on mount", "Runs on every render", "Runs on unmount", "Never runs"],
     "Runs only on mount", "useEffect(() => {}, []) runs once after initial render."),
    ("React", "beginner", "What is the virtual DOM?",
     ["A lightweight copy of the real DOM for efficient updates", "A database", "A CSS engine", "A server-side feature"],
     "A lightweight copy of the real DOM for efficient updates", "React compares virtual DOM snapshots to minimize real DOM changes."),
    ("React", "intermediate", "What is the purpose of `useCallback`?",
     ["Memoize a function to prevent unnecessary re-creations", "Create a callback URL", "Handle errors", "Manage state"],
     "Memoize a function to prevent unnecessary re-creations", "useCallback prevents child re-renders when parent re-renders."),
    ("React", "intermediate", "What is React Context used for?",
     ["Sharing state globally without prop drilling", "Making API calls", "Routing between pages", "Styling components"],
     "Sharing state globally without prop drilling", "Context provides a way to pass data through the component tree."),
    ("React", "intermediate", "What is the difference between controlled and uncontrolled components?",
     ["Controlled: React manages value; Uncontrolled: DOM manages value", "No difference", "Controlled is faster", "Uncontrolled uses hooks"],
     "Controlled: React manages value; Uncontrolled: DOM manages value", "Controlled components use state to drive form values."),
    ("React", "intermediate", "What does `React.memo()` do?",
     ["Prevents re-rendering if props haven't changed", "Stores data in memory", "Creates a memo component", "Adds comments"],
     "Prevents re-rendering if props haven't changed", "React.memo is a higher-order component for performance optimization."),
    ("React", "intermediate", "How do you handle side effects in React?",
     ["useEffect hook", "useState hook", "render method", "constructor"],
     "useEffect hook", "useEffect handles side effects like API calls, subscriptions, and DOM manipulation."),
    # ─── Data Structures ──────────────────────────────────
    ("Data Structures", "beginner", "What is the time complexity of accessing an array element by index?",
     ["O(1)", "O(n)", "O(log n)", "O(n²)"],
     "O(1)", "Arrays provide constant-time access by index."),
    ("Data Structures", "beginner", "Which data structure follows LIFO?",
     ["Stack", "Queue", "Array", "Linked List"],
     "Stack", "Stack = Last In, First Out."),
    ("Data Structures", "beginner", "What is a linked list?",
     ["A sequence of nodes where each points to the next", "An array with links", "A tree structure", "A hash table"],
     "A sequence of nodes where each points to the next", "Each node contains data and a pointer to the next node."),
    ("Data Structures", "beginner", "Which data structure follows FIFO?",
     ["Queue", "Stack", "Tree", "Graph"],
     "Queue", "Queue = First In, First Out."),
    ("Data Structures", "beginner", "What is the time complexity of binary search?",
     ["O(log n)", "O(n)", "O(1)", "O(n log n)"],
     "O(log n)", "Binary search halves the search space each step."),
    ("Data Structures", "intermediate", "What is the average time complexity of hash table lookup?",
     ["O(1)", "O(n)", "O(log n)", "O(n²)"],
     "O(1)", "Hash tables provide constant-time average lookup."),
    ("Data Structures", "intermediate", "What is a balanced BST?",
     ["A BST where height difference of subtrees is at most 1", "A BST with equal values", "A complete binary tree", "A BST with no leaves"],
     "A BST where height difference of subtrees is at most 1", "AVL trees and Red-Black trees are balanced BSTs."),
    ("Data Structures", "intermediate", "What is the worst-case time of quicksort?",
     ["O(n²)", "O(n log n)", "O(n)", "O(log n)"],
     "O(n²)", "Worst case occurs when pivot is always the smallest/largest element."),
    ("Data Structures", "intermediate", "What is a heap data structure?",
     ["A complete binary tree with heap property", "A sorted array", "A hash table", "A graph"],
     "A complete binary tree with heap property", "In a max-heap, parent is always >= children."),
    ("Data Structures", "intermediate", "What is BFS?",
     ["Breadth-First Search — explores level by level", "Best-First Search", "Binary File Search", "Backward Forward Search"],
     "Breadth-First Search — explores level by level", "BFS uses a queue and visits all neighbors before going deeper."),
]


# ─── Main Seed Function ────────────────────────────────────────────

async def seed():
    # Import models inside function to avoid import issues
    from app.models.user import User, Student, Department, Faculty
    from app.models.skill import Skill, StudentSkill, CurriculumSkill
    from app.models.industry import Company, Job, JobSkill
    from app.models.placement import PlacementDrive, Application, PlacementOutcome, InterviewStage
    from app.models.academic import Subject, Semester, AcademicRecord
    from app.models.assessment import AssessmentQuestionBank

    print("🔧 Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("🌱 Seeding data...")
    async with AsyncSessionLocal() as db:
        # ── 1. Departments ────────────────────────────────
        print("  📁 Departments...")
        departments = {}
        for code, name in DEPARTMENT_DATA:
            dept = Department(code=code, name=name)
            db.add(dept)
            departments[code] = dept
        await db.flush()

        # ── 2. Skills Taxonomy ────────────────────────────
        print("  🧠 Skills taxonomy...")
        skills = {}
        for name, category in SKILL_DATA:
            skill = Skill(
                name=name,
                normalized_name=name.lower(),
                category=category,
            )
            db.add(skill)
            skills[name] = skill
        await db.flush()

        # ── 3. TPO User ──────────────────────────────────
        print("  👤 TPO + Faculty users...")
        tpo_user = User(
            email="tpo@ccip.edu",
            password_hash=hash_password("tpo123"),
            role="tpo",
            first_name="Admin",
            last_name="TPO",
            phone="9876543210",
            is_active=True,
        )
        db.add(tpo_user)

        faculty_user = User(
            email="faculty@ccip.edu",
            password_hash=hash_password("faculty123"),
            role="faculty",
            first_name="Dr. Sharma",
            last_name="HOD",
            phone="9876543211",
            is_active=True,
        )
        db.add(faculty_user)
        await db.flush()

        faculty_prof = Faculty(
            id=faculty_user.id,
            department_id=departments["CS"].id,
            designation="Professor & HOD",
            is_hod=True,
        )
        db.add(faculty_prof)

        # ── 4. Students ──────────────────────────────────
        print("  🎓 Students...")
        students = []
        for i, name in enumerate(STUDENT_NAMES):
            parts = name.split()
            dept_code = STUDENT_DEPT_WEIGHTS[i % len(STUDENT_DEPT_WEIGHTS)]
            roll = f"{dept_code}21B{str(i + 1).zfill(3)}"

            user = User(
                email=f"{parts[0].lower()}.{parts[1].lower()}{i}@ccip.edu",
                password_hash=hash_password("student123"),
                role="student",
                first_name=parts[0],
                last_name=parts[1],
                phone=f"98765{str(10000 + i)}",
                is_active=True,
            )
            db.add(user)
            await db.flush()

            student = Student(
                id=user.id,
                roll_number=roll,
                department_id=departments[dept_code].id,
                current_semester=random.choice([7, 8]),
                admission_year=2021,
                cgpa=rand_cgpa(),
                bio=f"Passionate {dept_code} student interested in technology and innovation.",
                consent_profile_visible=random.random() > 0.3,
                consent_resume_analysis=random.random() > 0.4,
            )
            db.add(student)
            students.append((student, dept_code))
        await db.flush()

        # ── 5. Student Skills ─────────────────────────────
        print("  💡 Student skills...")
        skill_list = list(skills.values())
        for student, dept_code in students:
            num = random.randint(5, 12)
            chosen = random.sample(skill_list, min(num, len(skill_list)))
            for sk in chosen:
                ss = StudentSkill(
                    student_id=student.id,
                    skill_id=sk.id,
                    confidence=Decimal(str(round(random.uniform(0.3, 0.95), 2))),
                    source=random.choice(["resume", "academic", "manual", "assessment"]),
                )
                db.add(ss)
        await db.flush()

        # ── 6. Companies ──────────────────────────────────
        print("  🏢 Companies...")
        companies = []
        for name, industry, location, size in COMPANY_DATA:
            company = Company(
                name=name,
                industry=industry,
                location=location,
                company_size=size,
                data_source="curated",
            )
            db.add(company)
            companies.append(company)
        await db.flush()

        # ── 7. Jobs + Job Skills ──────────────────────────
        print("  💼 Jobs...")
        jobs = []
        for comp_idx, title, role_cat, min_cgpa, sal_min, sal_max, eligible, req_skills in JOB_DATA:
            job = Job(
                company_id=companies[comp_idx].id,
                title=title,
                description=f"{title} role at {COMPANY_DATA[comp_idx][0]}. Looking for talented candidates.",
                role_category=role_cat,
                min_cgpa=Decimal(str(min_cgpa)),
                location=COMPANY_DATA[comp_idx][2],
                job_type="full_time",
                salary_min=Decimal(str(sal_min)),
                salary_max=Decimal(str(sal_max)),
                eligible_departments=eligible,
                is_active=True,
                data_source="curated",
            )
            db.add(job)
            await db.flush()
            jobs.append(job)

            # Attach required skills
            for sk_name in req_skills:
                if sk_name in skills:
                    js = JobSkill(
                        job_id=job.id,
                        skill_id=skills[sk_name].id,
                        importance=random.choice(["required", "required", "preferred"]),
                        confidence=Decimal(str(round(random.uniform(0.7, 1.0), 2))),
                    )
                    db.add(js)
        await db.flush()

        # ── 8. Placement Drives ───────────────────────────
        print("  📋 Placement drives...")
        drives = []
        drive_configs = [
            (0, "Google Campus Hiring 2025", "upcoming", rand_date_future(30, 60), 7.5, ["CS", "IT"], 38.5),
            (1, "Amazon SDE Hiring", "upcoming", rand_date_future(15, 45), 7.0, ["CS", "IT"], 30.0),
            (2, "Microsoft Internship Drive", "open", rand_date_future(5, 20), 7.5, ["CS"], 45.0),
            (3, "Infosys Recruitment 2025", "open", rand_date_future(3, 15), 6.0, ["CS", "IT", "ECE", "ME", "EEE"], 4.0),
            (4, "TCS Digital Drive", "open", rand_date_future(7, 25), 7.0, ["CS", "IT", "ECE"], 7.0),
            (5, "Wipro Elite Hiring", "in_progress", rand_date_past(5, 15), 6.0, ["CS", "IT", "ECE", "ME"], 4.5),
            (6, "Deloitte Analyst Program", "in_progress", rand_date_past(10, 30), 7.5, ["CS", "IT", "ECE"], 12.0),
            (7, "Goldman Sachs Technology", "completed", rand_date_past(30, 90), 8.0, ["CS", "IT"], 25.0),
            (8, "Adobe MTS Hiring", "completed", rand_date_past(45, 120), 7.5, ["CS", "IT"], 24.0),
            (9, "Flipkart SDE Drive", "completed", rand_date_past(60, 150), 7.0, ["CS", "IT"], 22.0),
        ]
        for comp_idx, title, status, drive_date, min_cgpa, depts, ctc in drive_configs:
            deadline = drive_date - timedelta(days=random.randint(3, 10)) if isinstance(drive_date, date) else None
            drive = PlacementDrive(
                company_id=companies[comp_idx].id,
                title=title,
                description=f"Campus recruitment drive by {COMPANY_DATA[comp_idx][0]}.",
                drive_date=drive_date,
                registration_deadline=datetime.combine(deadline, datetime.min.time(), tzinfo=timezone.utc) if deadline else None,
                min_cgpa=Decimal(str(min_cgpa)),
                eligible_departments=depts,
                max_backlogs=0 if min_cgpa >= 7.0 else 1,
                roles_offered=[JOB_DATA[comp_idx][1]],
                salary_ctc=Decimal(str(ctc)),
                status=status,
                academic_year="2025-26",
                created_by=tpo_user.id,
            )
            db.add(drive)
            drives.append(drive)
        await db.flush()

        # ── 9. Applications ──────────────────────────────
        print("  📝 Applications...")
        applications = []
        for drive_idx, drive in enumerate(drives):
            # Pick eligible students
            eligible = [
                (s, dc) for s, dc in students
                if dc in (drive.eligible_departments or [])
                and (s.cgpa or 0) >= float(drive.min_cgpa or 0)
            ]
            num_applicants = min(len(eligible), random.randint(4, 12))
            applicants = random.sample(eligible, num_applicants) if eligible else []

            for s, dc in applicants:
                statuses = {
                    "upcoming": ["applied"],
                    "open": ["applied", "applied", "shortlisted"],
                    "in_progress": ["applied", "shortlisted", "shortlisted", "in_progress"],
                    "completed": ["applied", "shortlisted", "selected", "selected", "rejected"],
                }
                app_status = random.choice(statuses.get(drive.status, ["applied"]))
                app = Application(
                    student_id=s.id,
                    drive_id=drive.id,
                    status=app_status,
                    current_stage="Resume Screening" if app_status == "applied" else (
                        "Technical Interview" if app_status in ("shortlisted", "in_progress") else "HR Round"
                    ),
                )
                db.add(app)
                applications.append((app, s, drive))
        await db.flush()

        # Add interview stages for some applications
        for app, student, drive in applications:
            if app.status in ("shortlisted", "in_progress", "selected"):
                stages = [
                    ("Resume Screening", 1, "passed"),
                    ("Online Assessment", 2, "passed" if app.status != "shortlisted" else "scheduled"),
                ]
                if app.status in ("in_progress", "selected"):
                    stages.append(("Technical Interview", 3, "passed" if app.status == "selected" else "scheduled"))
                if app.status == "selected":
                    stages.append(("HR Round", 4, "passed"))

                for stage_name, order, stage_status in stages:
                    stage = InterviewStage(
                        application_id=app.id,
                        stage_name=stage_name,
                        stage_order=order,
                        status=stage_status,
                    )
                    db.add(stage)
        await db.flush()

        # ── 10. Placement Outcomes ────────────────────────
        print("  🏆 Placement outcomes...")
        selected_apps = [(a, s, d) for a, s, d in applications if a.status == "selected"]
        for app, student, drive in selected_apps:
            outcome = PlacementOutcome(
                student_id=student.id,
                company_name=COMPANY_DATA[[c.id for c in companies].index(drive.company_id)][0] if drive.company_id in [c.id for c in companies] else "Unknown",
                role=JOB_DATA[drives.index(drive) % len(JOB_DATA)][1],
                salary_ctc=drive.salary_ctc,
                placement_type="on_campus",
                academic_year="2025-26",
                data_type="real",
            )
            db.add(outcome)
        await db.flush()

        # ── 11. Semesters ─────────────────────────────────
        print("  📅 Semesters...")
        semesters = {}
        for num in range(5, 9):
            sem = Semester(
                name=f"Semester {num}",
                number=num,
                academic_year="2024-25" if num <= 6 else "2025-26",
                is_current=(num == 8),
            )
            db.add(sem)
            semesters[num] = sem
        await db.flush()

        # ── 12. Subjects ──────────────────────────────────
        print("  📚 Subjects...")
        subjects = {}
        for dept_code, subj_list in SUBJECT_DATA.items():
            for code, name, sem_num, credits in subj_list:
                subj = Subject(
                    code=code,
                    name=name,
                    department_id=departments[dept_code].id,
                    semester_number=sem_num,
                    credits=credits,
                    subject_type="core",
                )
                db.add(subj)
                subjects[code] = subj
        await db.flush()

        # ── 13. Curriculum Skills ─────────────────────────
        print("  🔗 Curriculum skill mappings...")
        for subj_code, skill_names in SUBJECT_SKILL_MAP.items():
            if subj_code in subjects:
                for sk_name in skill_names:
                    if sk_name in skills:
                        cs = CurriculumSkill(
                            subject_id=subjects[subj_code].id,
                            skill_id=skills[sk_name].id,
                            coverage_level=random.choice(["introduced", "practiced", "mastered"]),
                            mapping_source="manual",
                        )
                        db.add(cs)
        await db.flush()

        # ── 14. Academic Records ──────────────────────────
        print("  📊 Academic records...")
        grades = ["A+", "A", "A", "B+", "B+", "B", "B", "C+", "C"]
        grade_points_map = {"A+": 10, "A": 9, "B+": 8, "B": 7, "C+": 6, "C": 5}
        for student, dept_code in students[:30]:  # First 30 students get records
            dept_subjects = [
                (code, subj) for code, subj in subjects.items()
                if code.startswith(dept_code)
            ]
            for subj_code, subj in dept_subjects:
                sem_num = subj.semester_number
                if sem_num in semesters:
                    grade = random.choice(grades)
                    rec = AcademicRecord(
                        student_id=student.id,
                        subject_id=subj.id,
                        semester_id=semesters[sem_num].id,
                        grade=grade,
                        grade_points=Decimal(str(grade_points_map.get(grade, 7))),
                        marks=Decimal(str(random.randint(55, 98))),
                        max_marks=Decimal("100"),
                        status="completed",
                    )
                    db.add(rec)
        await db.flush()

        # ── 15. Assessment Questions ──────────────────────
        print("  ❓ Assessment questions...")
        for topic, difficulty, qtext, options, correct, explanation in ASSESSMENT_QUESTIONS:
            # Link to skill if topic matches
            skill_id = None
            if topic in skills:
                skill_id = skills[topic].id
            elif topic == "Data Structures" and "Data Structures" in skills:
                skill_id = skills["Data Structures"].id

            q = AssessmentQuestionBank(
                topic=topic,
                difficulty=difficulty,
                question_text=qtext,
                options=options,
                correct_answer=correct,
                explanation=explanation,
                skill_id=skill_id,
                is_active=True,
                quality_status="reviewed",
            )
            db.add(q)
        await db.flush()

        # ── Commit ────────────────────────────────────────
        await db.commit()

    print()
    print("=" * 60)
    print("✅ Database seeded successfully!")
    print("=" * 60)
    print()
    print(f"  📁 Departments:     {len(DEPARTMENT_DATA)}")
    print(f"  🧠 Skills:          {len(SKILL_DATA)}")
    print(f"  🎓 Students:        {len(STUDENT_NAMES)}")
    print(f"  👤 TPO User:        tpo@ccip.edu / tpo123")
    print(f"  👤 Faculty User:    faculty@ccip.edu / faculty123")
    print(f"  👤 Student Login:   priya.agarwal0@ccip.edu / student123")
    print(f"  🏢 Companies:       {len(COMPANY_DATA)}")
    print(f"  💼 Jobs:            {len(JOB_DATA)}")
    print(f"  📋 Drives:          {len(drive_configs)}")
    print(f"  📝 Applications:    {len(applications)}")
    print(f"  🏆 Placements:      {len(selected_apps)}")
    print(f"  📚 Subjects:        {sum(len(v) for v in SUBJECT_DATA.values())}")
    print(f"  ❓ Questions:       {len(ASSESSMENT_QUESTIONS)}")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
