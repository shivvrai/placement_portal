import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.models.skill import Skill
from app.models.assessment import QuestionBank
from sqlalchemy import select

async def seed_questions():
    async with AsyncSessionLocal() as db:
        # Find Python skill or create if not exists
        result = await db.execute(select(Skill).where(Skill.name == "Python"))
        skill = result.scalar_one_or_none()
        if not skill:
            skill = Skill(name="Python", normalized_name="python", category="language", domain="Software Engineering")
            db.add(skill)
            await db.flush()

        questions = [
            {
                "skill_id": skill.id,
                "concept": "Data Types",
                "difficulty": "beginner",
                "question_text": "Which of the following is a mutable data type in Python?",
                "options": [
                    {"id": "A", "text": "Tuple"},
                    {"id": "B", "text": "String"},
                    {"id": "C", "text": "List"},
                    {"id": "D", "text": "Integer"}
                ],
                "correct_option": "C",
                "explanation": "Lists are mutable, meaning they can be changed after creation. Tuples, strings, and integers are immutable."
            },
            {
                "skill_id": skill.id,
                "concept": "Functions",
                "difficulty": "beginner",
                "question_text": "What keyword is used to define a function in Python?",
                "options": [
                    {"id": "A", "text": "func"},
                    {"id": "B", "text": "def"},
                    {"id": "C", "text": "function"},
                    {"id": "D", "text": "define"}
                ],
                "correct_option": "B",
                "explanation": "The 'def' keyword is used to define a function in Python."
            },
            {
                "skill_id": skill.id,
                "concept": "Decorators",
                "difficulty": "intermediate",
                "question_text": "What does a decorator do in Python?",
                "options": [
                    {"id": "A", "text": "Modifies the behavior of a function or class"},
                    {"id": "B", "text": "Creates a visual UI element"},
                    {"id": "C", "text": "Automatically handles garbage collection"},
                    {"id": "D", "text": "Encrypts the source code"}
                ],
                "correct_option": "A",
                "explanation": "A decorator takes in a function, adds some functionality, and returns it."
            }
        ]

        for q_data in questions:
            q = QuestionBank(**q_data)
            db.add(q)

        try:
            await db.commit()
            print("Question bank seeded successfully.")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding questions: {e}")

if __name__ == "__main__":
    asyncio.run(seed_questions())
