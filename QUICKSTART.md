# Quick Start Guide

Get up and running with the PPTist AI Backend Node.js implementation in minutes.

## Prerequisites

- Node.js 18 or higher
- npm (comes with Node.js)
- OpenAI API key

## Installation

1. **Clone the repository** (if not already done)
   ```bash
   git clone https://github.com/gavanduffy/pptist-aibackend.git
   cd pptist-aibackend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-actual-api-key-here
   OPENAI_BASE_URL=https://api.openai.com/v1
   DEFAULT_MODEL=gpt-4o-mini
   DEFAULT_TEMPERATURE=0.7
   HOST=0.0.0.0
   PORT=8000
   DEBUG=false
   ```

4. **Start the server**
   ```bash
   npm start
   ```

5. **Verify it's working**
   ```bash
   curl http://localhost:8000/health
   ```
   
   You should see:
   ```json
   {
     "status": "healthy",
     "message": "PPTist AI Backend is running"
   }
   ```

## Testing the API

### 1. Generate an Outline

```bash
curl -X POST http://localhost:8000/tools/aippt_outline \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "language": "English",
    "content": "Artificial Intelligence in Education",
    "stream": true
  }'
```

### 2. Generate PPT Content

First, save an outline to a file, then use it to generate content:

```bash
# Generate outline and save to file
curl -X POST http://localhost:8000/tools/aippt_outline \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "language": "English",
    "content": "Machine Learning Basics",
    "stream": true
  }' > outline.txt

# Use outline to generate content
curl -X POST http://localhost:8000/tools/aippt \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gpt-4o-mini\",
    \"language\": \"English\",
    \"content\": \"$(cat outline.txt)\",
    \"stream\": true
  }"
```

### 3. Run Test Script

Use the included test script:
```bash
npm test
```

## Deployment

### Deploy to Vercel

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   vercel
   ```

4. **Set environment variables**
   
   In your Vercel dashboard:
   - Go to Project Settings → Environment Variables
   - Add `OPENAI_API_KEY` with your API key
   - Add other variables from `.env.example`

5. **Deploy to production**
   ```bash
   vercel --prod
   ```

### Deploy to Netlify

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**
   ```bash
   netlify login
   ```

3. **Deploy**
   ```bash
   netlify deploy --prod
   ```

4. **Set environment variables**
   
   In your Netlify dashboard:
   - Go to Site Settings → Environment Variables
   - Add `OPENAI_API_KEY` with your API key
   - Add other variables from `.env.example`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with API information |
| `/health` | GET | Health check |
| `/docs` | GET | API documentation |
| `/tools/aippt_outline` | POST | Generate PPT outline |
| `/tools/aippt` | POST | Generate PPT content |
| `/data/:filename.json` | GET | Get template file |

## Common Issues

### Port Already in Use

If port 8000 is already in use, change it in `.env`:
```bash
PORT=3000
```

### API Key Invalid

Make sure your API key is correct and has sufficient credits:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Module Not Found

If you see "Cannot find module" errors:
```bash
npm install
```

### EACCES Permission Error

If you get permission errors on Linux/Mac:
```bash
sudo npm install -g vercel
# or
sudo npm install -g netlify-cli
```

## Next Steps

1. **Read the documentation**
   - [README-EN.md](README-EN.md) - Complete documentation
   - [RECOMMENDATIONS.md](RECOMMENDATIONS.md) - Improvement suggestions
   - [SECURITY.md](SECURITY.md) - Security analysis

2. **Integrate with PPTist**
   - Follow instructions in README-EN.md section 6

3. **Customize**
   - Modify prompts in `index.js`
   - Add your own templates in `template/` directory
   - Adjust configuration in `.env`

4. **Improve**
   - Implement recommendations from RECOMMENDATIONS.md
   - Add rate limiting
   - Set up monitoring

## Getting Help

- **Documentation**: Check README-EN.md for detailed information
- **Issues**: Check existing GitHub issues
- **API Errors**: Check server logs for detailed error messages
- **Deployment**: Check Vercel/Netlify deployment logs

## Quick Reference

**Start server:**
```bash
npm start
```

**Start with auto-reload (development):**
```bash
npm run dev
```

**Run tests:**
```bash
npm test
```

**Deploy to Vercel:**
```bash
vercel --prod
```

**Deploy to Netlify:**
```bash
netlify deploy --prod
```

## Architecture

```
┌─────────────┐
│   Client    │
│  (PPTist)   │
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────────────────┐
│   Express.js Server     │
│   - CORS middleware     │
│   - Route handlers      │
│   - Error handling      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   LangChain.js          │
│   - Prompt templates    │
│   - Streaming           │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   OpenAI API            │
│   - GPT-4o-mini         │
│   - Text generation     │
└─────────────────────────┘
```

## Development Workflow

1. **Make changes** to `index.js` or other files
2. **Test locally** with `npm run dev`
3. **Run tests** with `npm test`
4. **Commit changes** to git
5. **Deploy** to Vercel or Netlify
6. **Verify** deployment is working

## Support

For additional help, see:
- [README-EN.md](README-EN.md) - Full documentation
- [MIGRATION-GUIDE.md](MIGRATION-GUIDE.md) - Migration from Python
- [SECURITY.md](SECURITY.md) - Security information

---

**That's it! You're ready to use the PPTist AI Backend.** 🚀
