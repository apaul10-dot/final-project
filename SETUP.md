# Setup Instructions

## Prerequisites

- Python 3.7+
- Node.js 18+ and npm
- OpenAI API key OR Anthropic API key (for AI analysis)

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install LaTeX OCR (pix2tex):
```bash
pip install "pix2tex[api]"
```

5. Create a `.env` file in the backend directory:
```bash
cp .env.example .env
```

6. Edit `.env` and add your API key:
```
OPENAI_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=your_key_here
```

7. Run the backend server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Upload images of your test/quiz
4. The app will:
   - Extract equations using LaTeX OCR
   - Analyze mistakes using AI
   - Generate personalized practice questions
   - Provide feedback on your practice answers

## Notes

- Make sure both servers are running simultaneously
- The first time you use LaTeX OCR, it will download model checkpoints automatically
- For best results, use clear, well-lit images of your tests
- The AI analysis requires either OpenAI or Anthropic API keys

## Troubleshooting

### LaTeX OCR not working
- Make sure you installed pix2tex: `pip install "pix2tex[api]"`
- Check that PyTorch is installed correctly

### API errors
- Verify your API keys are set correctly in `.env`
- Check that the backend server is running on port 8000

### Frontend connection issues
- Ensure the backend is running before starting the frontend
- Check CORS settings in `backend/main.py` if accessing from a different port

