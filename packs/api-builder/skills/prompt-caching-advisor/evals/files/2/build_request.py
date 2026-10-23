"""Builds each Claude API request for Calder Tutor, the study assistant at the Calder School of
Nursing (invented). Called once per student or instructor turn."""
import datetime

from tutor.config import MODEL
from tutor.content import FEW_SHOT, load_case_study, load_handbook
from tutor.tools import INSTRUCTOR_TOOLS, STUDENT_TOOLS


def build_request(user, session, question):
    system = [
        {
            "type": "text",
            "text": (
                f"You are Calder Tutor. Current user: {user.name} ({user.role}). "
                f"Request time: {datetime.datetime.now().isoformat()}."
            ),
        },
        # Clinical skills handbook, about 110,000 characters. Revised once per term.
        {"type": "text", "text": load_handbook()},
        # Eight worked question-and-answer examples, about 14,000 characters. Fixed.
        {"type": "text", "text": FEW_SHOT},
    ]

    # Students get 3 tools; instructors get those 3 plus 2 grading tools.
    tools = INSTRUCTOR_TOOLS if user.role == "instructor" else STUDENT_TOOLS

    # The student picks one patient case study (about 6,000 characters) at the start of a session.
    # It is sent as the first user message and stays for the whole session.
    messages = [{"role": "user", "content": load_case_study(session.case_id)}]
    messages += session.history  # all earlier turns, user and assistant, in order
    messages.append({"role": "user", "content": question})

    return {
        "model": MODEL,
        "max_tokens": 1024,
        "system": system,
        "tools": tools,
        "messages": messages,
    }
