# voxmate
VoxMate is a powerful, open-source desktop voice assistant built with Python and PyQt5. It provides a hands-free way to control your computer, get information, and automate everyday tasks using simple voice commands.

This project was developed as a fun and educational summer project, combining real-time AI, natural language processing (NLP), and system control into a single, polished application.

## Features
VoxMate comes packed with a wide range of features designed to make you more productive and your desktop experience more seamless.

### Core Voice Interaction
Voice-Activated Commands: Click the microphone button and speak your command.

Text-to-Speech Feedback: The assistant responds with a clear, audible voice.

Conversation Log: Keep track of your interaction history in the main window.

Modern UI: A sleek, dark-themed interface that is easy on the eyes.

### Productivity & System Tools
#### 1. Application Launcher
Launch any configured application on your computer instantly.

How to Use: First, teach VoxMate by clicking the "Add App" button and linking a simple "nickname" (e.g., vscode) to the application's file path.

Commands:

open chrome

launch vscode

#### 2. Screenshot Tool
Capture your entire screen and save it to a location of your choice.

How to Use: Simply ask the assistant to take a screenshot. A "Save As" dialog will appear, allowing you to choose the save location and filename.

Commands:

take a screenshot

capture the screen

#### 3. Dictation Mode
A hands-free way to write notes. VoxMate will transcribe everything you say into a text file until you tell it to stop.

How to Use:

Say "start dictation" and choose a file location when prompted.

Speak freely. The assistant will append your speech to the log and eventually the file.

Say "stop dictation" to end the session and save the file.

Commands:

start dictation

stop dictation (while dictation is active)

### Information & Web Features
#### 4. Weather Forecast
Get real-time weather information for any city in the world.

How to Use: Ask for the weather and mention a city name.

Commands:

what is the weather in london?

tell me the weather for tokyo

#### 5. YouTube Player
Instantly find and play music or videos. The assistant will open a YouTube search results page in your browser.

How to Use: Say "play" followed by the song or video title.

Commands:

play bella ciao

play queen bohemian rhapsody

#### 6. Dictionary (Synonyms & Antonyms)
Look up synonyms or antonyms for any English word using NLTK's WordNet.

Commands:

what is a synonym for happy?

find an antonym for good

### Personal Assistant
#### 7. Reminders & Alarms
Set reminders using natural language. The assistant will notify you with a voice message and a desktop pop-up when the time comes.

How to Use: Say "remind me" or "set an alarm" followed by the task and the time.

Commands:

remind me to check the oven in one minute

set an alarm for tomorrow at 10am

### Prerequisites
Python 3.8+

A working microphone
