# Test Analysis & Practice App

An intelligent web application that analyzes your test mistakes and generates personalized practice questions to strengthen weak areas.

> **"Most tools ask 'what do you want to study?' This asks 'what do you NOT understand and why?'"**

## Features

- 📸 **Upload Test Images**: Take photos of your tests/quizzes/evaluations
- 🔍 **Automatic Mistake Recognition**: AI-powered analysis of your mistakes
- 📝 **Detailed Feedback**: Understand what went wrong and why
- 🎯 **Personalized Practice**: Generate practice questions based on your weak areas
- ✅ **Answer Verification**: Submit practice answers and get instant feedback
- 📊 **Progress Tracking**: Track your improvement over time

## How It Works

1. **Upload**: Submit photos of your completed tests
2. **Analyze**: The app recognizes equations using LaTeX OCR and analyzes mistakes using AI
3. **Learn**: Get detailed explanations of what you did wrong and how to fix it
4. **Practice**: Receive personalized practice questions targeting your weak areas
5. **Improve**: Submit your practice answers and get feedback to reinforce learning

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), SQLAlchemy
- **OCR**: LaTeX-OCR (pix2tex) for equation recognition
- **AI**: OpenAI GPT-4 / Anthropic Claude for mistake analysis and question generation
- **Database**: SQLite (development) / PostgreSQL (production)
- **Math Rendering**: KaTeX for LaTeX equation display

## Quick Start

See [SETUP.md](./SETUP.md) for detailed setup instructions.

### Prerequisites

- Python 3.7+
- Node.js 18+
- OpenAI API key OR Anthropic API key

### Backend

```bash
cd backend
pip install -r requirements.txt
pip install "pix2tex[api]"
cp env.example .env
# Edit .env and add your API key
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to use the app!

## Project Structure

```
final-project/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── services/            # Business logic services
│   │   ├── latex_ocr.py     # LaTeX OCR integration
│   │   ├── ai_analyzer.py   # Mistake analysis
│   │   └── question_generator.py  # Practice question generation
│   ├── database/            # Database models and schemas
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   ├── components/      # React components
│   │   └── types.ts         # TypeScript types
│   └── package.json
├── README.md
└── SETUP.md
```

## API Endpoints

- `POST /api/upload-test` - Upload test images
- `POST /api/analyze-mistakes` - Analyze mistakes in answers
- `POST /api/generate-practice` - Generate practice questions
- `POST /api/submit-practice-answer` - Submit and verify practice answers

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

