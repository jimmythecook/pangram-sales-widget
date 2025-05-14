# Pangram Sales Widget

This project allows users to input a URL and a description of content to extract.
The backend uses HyperBrowser to fetch and process the webpage, an LLM to extract specific text, and Pangram to analyze the extracted text for AI likelihood.

## Project Structure

- `frontend/`: React application (Vite + React)
- `backend/`: Python application (FastAPI)

## Setup

### Backend

1.  Navigate to the `backend` directory: `cd backend`
2.  Create a virtual environment: `python -m venv venv`
3.  Activate the virtual environment:
    *   macOS/Linux: `source venv/bin/activate`
    *   Windows: `venv\Scripts\activate`
4.  Install dependencies: `pip install -r requirements.txt`
5.  Create a `.env` file from `.env.example` and fill in your API keys:
    *   `cp .env.example .env`
    *   Edit `.env` with your `HYPERBROWSER_API_KEY` and `PANGRAM_API_KEY`.
6.  Run the backend server: `uvicorn main:app --reload` (typically on `http://127.0.0.1:8000`)

### Frontend

1.  Navigate to the `frontend` directory: `cd frontend`
2.  Install dependencies: `npm install` (or `yarn install`)
3.  Run the frontend development server: `npm run dev` (or `yarn dev`) (typically on `http://localhost:5173`) 