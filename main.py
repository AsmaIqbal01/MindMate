import os
import json
import asyncio
from datetime import datetime
from typing import Optional, List
import chainlit as cl
from openai import OpenAI
import PyPDF2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "default_key")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Global variables for session management
current_mode = None
journal_file = "journal_log.txt"

# AI Companion Character System
class AICompanion:
    def __init__(self, name="Alex", personality="supportive"):
        self.name = name
        self.personality = personality
        self.conversation_memory = []
        
    def get_persona_prompt(self):
        """Generate persona-specific system prompt"""
        persona_traits = {
            "supportive": "You are a warm, empathetic companion who provides gentle support and encouragement. You speak with kindness and patience.",
            "wise": "You are a wise, thoughtful companion who offers deep insights and philosophical perspectives. You speak with wisdom and calm reflection.",
            "cheerful": "You are an upbeat, optimistic companion who brings positivity and hope. You speak with enthusiasm and joy while remaining sensitive to emotions.",
            "calm": "You are a peaceful, serene companion who promotes tranquility and mindfulness. You speak with a soothing, meditative tone.",
            "analytical": "You are a logical, thoughtful companion who helps break down problems systematically. You speak with clarity and structured thinking."
        }
        
        base_prompt = (
            f"You are {self.name}, a personalized AI companion focused on mental health support. "
            f"{persona_traits.get(self.personality, persona_traits['supportive'])} "
            "Always maintain professional boundaries while being genuinely caring. "
            "Remember details from our conversations to provide personalized support. "
            "If someone appears to be in crisis, gently suggest professional help."
        )
        
        return base_prompt

# Default companion instance
default_companion = AICompanion()

class MentalHealthAssistant:
    def __init__(self):
        self.client = openai_client
        
    async def therapy_chat(self, message: str, chat_history: List = None, companion: AICompanion = None) -> str:
        """
        Generate supportive therapy responses using OpenAI with companion personality
        """
        try:
            # Use companion or default
            if companion is None:
                companion = default_companion
            
            # Build conversation context with companion persona
            messages = [
                {
                    "role": "system",
                    "content": companion.get_persona_prompt()
                }
            ]
            
            # Add chat history if available
            if chat_history:
                messages.extend(chat_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I'm sorry, I'm having trouble connecting right now. Please try again later. Error: {str(e)}"
    
    async def summarize_medical_report(self, pdf_content: str) -> str:
        """
        Summarize medical PDF content using OpenAI
        """
        try:
            prompt = (
                "Please provide a clear and concise summary of this medical report. "
                "Focus on key findings, diagnoses, recommendations, and important "
                "medical information. Present the information in an organized, "
                "easy-to-understand format while maintaining medical accuracy. "
                "If the document doesn't appear to be a medical report, please "
                "indicate that.\n\nDocument content:\n\n"
            ) + pdf_content
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a medical document summarization assistant. "
                            "Provide clear, accurate summaries of medical reports "
                            "while maintaining professional medical terminology "
                            "and ensuring no critical information is lost."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I'm sorry, I couldn't process the medical report. Please try again later. Error: {str(e)}"
    
    def extract_pdf_content(self, pdf_file) -> str:
        """
        Extract text content from PDF file
        """
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text()
            
            return text_content
            
        except Exception as e:
            raise Exception(f"Failed to extract PDF content: {str(e)}")
    
    def save_journal_entry(self, mood: str, entry: str) -> bool:
        """
        Save journal entry with mood and timestamp
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            journal_data = {
                "timestamp": timestamp,
                "mood": mood,
                "entry": entry
            }
            
            # Append to journal file
            with open(journal_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(journal_data) + "\n")
            
            return True
            
        except Exception as e:
            print(f"Error saving journal entry: {str(e)}")
            return False

# Initialize the assistant
assistant = MentalHealthAssistant()

@cl.on_chat_start
async def start():
    """
    Initialize the chat session with tabs
    """
    global current_mode
    current_mode = "therapy"  # Default to therapy tab
    
    # Set up tabs and companion customization
    await cl.ChatSettings(
        [
            cl.input_widget.Switch(
                id="therapy_tab",
                label="Therapy Chat",
                initial=True,
                tooltip="Have a supportive conversation with a compassionate AI assistant"
            ),
            cl.input_widget.Switch(
                id="pdf_tab", 
                label="Medical Report Summarizer",
                initial=False,
                tooltip="Upload a PDF medical report for a clear summary"
            ),
            cl.input_widget.Switch(
                id="journal_tab",
                label="Mood Journaling", 
                initial=False,
                tooltip="Record your thoughts and feelings with mood tracking"
            ),
            cl.input_widget.TextInput(
                id="companion_name",
                label="Companion Name",
                initial="Alex",
                placeholder="Enter your AI companion's name",
                tooltip="Customize your AI companion's name"
            ),
            cl.input_widget.Select(
                id="companion_personality",
                label="Companion Personality",
                values=["supportive", "wise", "cheerful", "calm", "analytical"],
                initial_index=0,
                tooltip="Choose your companion's personality style"
            )
        ]
    ).send()
    
    # Initialize default companion in session
    cl.user_session.set("companion", default_companion)
    
    await cl.Message(
        content="**Welcome to your Mental Health Assistant!**\n\n"
                f"Meet {default_companion.name}, your personalized AI companion! You can customize your companion's name and personality in the settings.\n\n"
                "## How to Use the Tabs\n"
                "**Location**: Look for the settings/tabs section in the chat interface - it should appear as toggle switches or settings options.\n\n"
                "Use the tabs above to switch between different features:\n\n"
                "**Therapy Chat** (currently active) - Have a supportive conversation with your personalized AI companion\n\n"
                "**Medical Report Summarizer** - Upload a PDF medical report for a clear summary\n\n"
                "**Mood Journaling** - Record your thoughts and feelings with mood tracking\n\n"
                "## Companion Customization\n"
                "**Companion Name**: Give your AI companion a personal name\n"
                "**Personality**: Choose from supportive, wise, cheerful, calm, or analytical\n\n"
                "You can start by sharing what's on your mind, or customize your companion in the settings first!"
    ).send()

@cl.on_settings_update
async def setup_agent(settings):
    """
    Handle tab switching and companion customization
    """
    global current_mode
    
    # Update companion based on settings
    companion_name = settings.get("companion_name", "Alex")
    companion_personality = settings.get("companion_personality", "supportive")
    
    # Create/update companion instance
    companion = AICompanion(
        name=companion_name,
        personality=companion_personality
    )
    
    # Store companion in session
    cl.user_session.set("companion", companion)
    
    # Determine which tab is active
    if settings.get("therapy_tab", False):
        current_mode = "therapy"
        await cl.Message(
            content=f"**Therapy Chat Mode with {companion_name}**\n\n"
                    f"Hi! I'm {companion_name}, your {companion_personality} companion. "
                    "You're now in a safe space to share your thoughts and feelings. "
                    "I'm here to listen and provide supportive responses. "
                    "Feel free to share what's on your mind."
        ).send()
    elif settings.get("pdf_tab", False):
        current_mode = "pdf_summary"
        await cl.Message(
            content=f"**Medical Report Summarizer Mode with {companion_name}**\n\n"
                    f"Hi! I'm {companion_name}. Please upload a PDF medical report that you'd like me to summarize. "
                    "I'll provide a clear and concise summary of the key findings.\n\n"
                    "Use the attachment button or drag and drop your PDF file."
        ).send()
    elif settings.get("journal_tab", False):
        current_mode = "journal_mood"
        await cl.Message(
            content=f"**Mood Journaling Mode with {companion_name}**\n\n"
                    f"Hi! I'm {companion_name}. Let's start with your current mood. "
                    "Please describe how you're feeling today using one or a few words "
                    "(e.g., 'happy', 'anxious', 'peaceful', 'stressed', etc.)"
        ).send()