# Personal Assistant API Overview

## What is this application?

This project is a **Personal Assistant API** built with FastAPI, designed to help organizations automate and intelligently manage communications across email and Telegram. It provides real-time message handling, background tasks, file uploads, and intelligent responses powered by LLMs (Large Language Models).

## Key Features

- **Authentication & Organization Management**
  - Secure JWT-based authentication for organizations.
  - Endpoints for organization signup, login, update, and deletion.
  - Organization setup checks and credential management.

- **Telegram Integration**
  - Telegram login and session management using Telethon.
  - Real-time monitoring of Telegram groups/channels.
  - Automated intelligent responses to group messages.
  - Sentiment analysis and statistics for group messages.

- **Email Automation**
  - Automated email fetching and response using Google app passwords.
  - Intelligent reply generation for incoming emails.
  - Email statistics and background email task management.

- **File Uploads & Semantic Search**
  - Upload and process PDFs, images, audio, and video files.
  - Extract text, transcribe audio/video, and generate image descriptions.
  - Store file metadata and embeddings in Qdrant for semantic search.
  - Use LLMs to generate context-aware responses using uploaded files.

- **Background Tasks**
  - Start/stop background intelligence tasks for Telegram and email.
  - Monitor specific groups or all groups for real-time insights.
  - List and manage active background tasks.

- **Statistics & Analytics**
  - Get statistics for Telegram messages and email activity.
  - Analyze message volume, unique senders, replies, and date ranges.

## Technologies Used

- **FastAPI** for API endpoints.
- **MongoDB** (via Motor) for data storage.
- **Telethon** for Telegram integration.
- **Qdrant** for vector database and semantic search.
- **OpenAI** for LLM-powered responses and embeddings.
- **Deepgram** for audio/video transcription.
- **Pydantic** for data validation.
- **Docker** for containerization.

## Typical Use Cases

- Automate responses to emails and Telegram messages using AI.
- Monitor and analyze group chats for sentiment and activity.
- Upload and semantically search documents, images, and media.
- Manage organization credentials and background tasks securely.

---

For more details, see the [README.md](./README.md) or explore the API endpoints in `src/main.py`.