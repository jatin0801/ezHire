# Helix Project

A web application featuring an AI-powered outreach campaign generator with a React TypeScript frontend and Flask Python backend.

## Project Overview

Helix is an intelligent platform designed to help users create, manage, and optimize outreach campaigns using AI-powered tools. The application leverages LangChain's agentic infrastructure to provide conversational assistance for crafting effective outreach sequences.

## Project Structure

- `/Frontend/helix-frontend`: React TypeScript frontend application
- `/Backend/helix-backend`: Flask Python backend application

## Getting Started

### Download Code

**Link to zip code:** https://drive.google.com/file/d/1AXD6vf5WAH1LVhwufrJgQI-rDIpiVg4I/view?usp=drive_link

### Repository Setup

```bash
cd Helix
```

### Environment Variables

Add the following keys to your environment:
- `DATABASE_URL`
- `OPENAI_API_KEY`

### Backend Setup (Flask)

```bash
cd Backend/helix-backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py
```

### Frontend Setup (React)

```bash
cd Frontend/helix-frontend

# Install dependencies 
npm install

# Run development server 
npm start
```

## Technical Details

### Tech Stack

**Frontend:**
- React with TypeScript

**Backend:**
- Python

**Frameworks:**
- LangChain (Agentic Infrastructure)
- Flask

**Database:**
- PostgreSQL

### Agentic Tools

The agent is composed of 4 tools:

1. **General_Conversation** - This tool is triggered to handle general conversations like greetings and fallback responses.

2. **Search_Best_Practices** - This tool generates best practices for creation of an outreach campaign.

3. **Generate_Outreach_Sequence** - This is used to generate the outreach sequence based on user prompt.

4. **Edit_Sequence** - This tool triggers when a user wants to edit the sequence with specific instructions.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## Contact

LinkedIn: https://www.linkedin.com/in/jatin-chhabria/