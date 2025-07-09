import chainlit as cl
from PyPDF2 import PdfReader
import openai
import os

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Debug print to force log output
print("✅ OPENAI_API_KEY Loaded:", bool(openai.api_key))
print("✅ Chainlit is initializing...")

# Chat completion logic
def ask_openai(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful and compassionate AI mental health assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

@cl.on_chat_start
def start():
    print("✅ Chainlit chat started.")
    cl.user_session.set("step", "menu")
    cl.user_session.set("files", [])
    cl.send_message("🧠 Welcome to MindMate!\nChoose a service:\n1. Chat with Therapist\n2. Summarize Report\n3. Write Journal Entry\nPlease type 1, 2, or 3.")

@cl.on_message
def main(message):
    step = cl.user_session.get("step")

    if step == "menu":
        if message.strip() == "1":
            cl.user_session.set("step", "therapy")
            cl.send_message("Tell me, how are you feeling today?")
        elif message.strip() == "2":
            cl.user_session.set("step", "summary")
            cl.send_message("Please upload your medical report PDF using the upload button.")
        elif message.strip() == "3":
            cl.user_session.set("step", "journal")
            cl.send_message("How do you feel today? (🙂 Happy, 😞 Sad, 😠 Angry, 😰 Anxious)")
        else:
            cl.send_message("Invalid option. Please type 1, 2, or 3.")

    elif step == "therapy":
        prompt = f"The user says: '{message}'. Respond with empathetic and thoughtful guidance."
        response = ask_openai(prompt)
        cl.send_message(response)
        cl.user_session.set("step", "menu")

    elif step == "summary":
        uploaded_files = message.elements
        if uploaded_files:
            file = uploaded_files[0]
            reader = PdfReader(file.path)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            prompt = f"Summarize this medical report in plain language: {text[:2000]}"
            response = ask_openai(prompt)
            cl.send_message(response)
            cl.user_session.set("step", "menu")
        else:
            cl.send_message("Please upload a PDF using the upload button below.")

    elif step == "journal":
        if not cl.user_session.get("mood"):
            cl.user_session.set("mood", message.strip())
            cl.send_message("Now, write your thoughts for today:")
        else:
            mood = cl.user_session.get("mood")
            entry = message.strip()
            with open("journal_log.txt", "a", encoding="utf-8") as f:
                f.write(f"Mood: {mood}\nEntry: {entry}\n---\n")
            cl.send_message("Your journal entry has been saved. Thank you!")
            cl.user_session.set("mood", None)
            cl.user_session.set("step", "menu")
