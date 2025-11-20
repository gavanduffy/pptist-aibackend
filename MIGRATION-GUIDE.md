# Migration Guide: Python FastAPI to Node.js Express

This document provides guidance for migrating from the Python FastAPI implementation to the new Node.js Express implementation.

## Overview

The PPTist AI Backend has been successfully ported from Python (FastAPI) to Node.js (Express.js) while maintaining full API compatibility. Both implementations can coexist, but the Node.js version offers better serverless deployment options.

## Key Differences

### Technology Stack

| Component | Python Version | Node.js Version |
|-----------|---------------|-----------------|
| Web Framework | FastAPI | Express.js |
| AI Framework | LangChain (Python) | LangChain.js |
| Runtime | Python 3.13+ | Node.js 18+ |
| Package Manager | uv | npm |
| Type Checking | Pydantic | Native JavaScript |

### File Structure

```
Python Version:
├── main.py              # Main application
├── config.py            # Configuration
├── api/index.py         # Vercel entrypoint
├── pyproject.toml       # Dependencies
└── requirements.txt     # Dependencies

Node.js Version:
├── index.js             # Main application
├── test-api.js          # Test script
├── package.json         # Dependencies
├── vercel.json          # Vercel config
├── netlify.toml         # Netlify config
└── netlify/functions/   # Netlify functions
    └── api.js
```

## API Compatibility

Both implementations expose identical endpoints with the same request/response formats:

### Endpoints

1. **GET /** - Root endpoint with API info
2. **GET /health** - Health check
3. **GET /docs** - API documentation
4. **POST /tools/aippt_outline** - Generate PPT outline
5. **POST /tools/aippt** - Generate PPT content
6. **GET /data/:filename.json** - Get template files

### Request/Response Format

No changes to request or response formats. All existing client code will work without modifications.

## Migration Steps

### 1. For Development

**Python Version:**
```bash
# Install dependencies
uv sync

# Start server
uv run main.py
```

**Node.js Version:**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Or production server
npm start
```

### 2. Environment Variables

Both versions use the same environment variables:

```bash
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_TEMPERATURE=0.7
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3. For Vercel Deployment

**Python Version:**
```json
{
  "functions": {
    "api/index.py": {
      "runtime": "python3.11",
      "maxDuration": 60
    }
  }
}
```

**Node.js Version:**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "index.js",
      "use": "@vercel/node"
    }
  ]
}
```

**To migrate:**
1. Update `vercel.json` to use Node.js configuration
2. Remove `api/index.py`
3. Deploy with `vercel`

### 4. For Netlify Deployment

The Node.js version includes Netlify support which was not available in the Python version.

**Setup:**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod
```

## Feature Parity

### Implemented Features ✅

- [x] PPT outline generation with streaming
- [x] PPT content generation with streaming
- [x] Health check endpoint
- [x] Template file serving
- [x] CORS configuration
- [x] Error handling
- [x] Environment variable configuration
- [x] Logging
- [x] API documentation endpoint

### Node.js Advantages

1. **Better Serverless Support**: Native support for both Vercel and Netlify
2. **Faster Cold Starts**: Node.js serverless functions start faster
3. **Smaller Bundle Size**: Typically smaller deployment packages
4. **Ecosystem**: Larger NPM ecosystem for additional features

### Python Advantages

1. **Type Safety**: Pydantic provides excellent runtime type checking
2. **FastAPI Features**: Built-in OpenAPI documentation generation
3. **Python AI Ecosystem**: More mature AI/ML libraries

## Testing

### Python Version
```bash
uv run test_api.py
```

### Node.js Version
```bash
npm test
# or
node test-api.js
```

## Common Issues

### Issue 1: Dependencies Not Found

**Python:** Run `uv sync`
**Node.js:** Run `npm install`

### Issue 2: Port Already in Use

Both versions default to port 8000. Change `PORT` in `.env` file.

### Issue 3: API Key Not Configured

Ensure `OPENAI_API_KEY` is set in `.env` file for both versions.

### Issue 4: Module Import Errors

**Node.js:** Ensure `"type": "module"` is in `package.json`

## Performance Considerations

### Streaming Responses

Both implementations support streaming responses. The Node.js version uses Node.js streams, while Python uses FastAPI's `StreamingResponse`.

### Memory Usage

- Python: Higher baseline memory due to Python runtime
- Node.js: Lower baseline memory, better for serverless

### Response Times

Both implementations have similar response times for AI generation, as the bottleneck is the OpenAI API call.

## Choosing Between Implementations

### Use Python Version If:
- You need strong type checking with Pydantic
- Your team is more familiar with Python
- You're using other Python-specific AI libraries
- You need FastAPI's automatic OpenAPI documentation

### Use Node.js Version If:
- You're deploying to serverless platforms (Vercel/Netlify)
- You want faster cold start times
- Your team is more familiar with JavaScript/Node.js
- You need better integration with frontend JavaScript frameworks

## Rollback Plan

If you need to rollback from Node.js to Python:

1. Keep both implementations in the repository
2. Switch Vercel configuration back to Python
3. Redeploy with Python version
4. No client-side changes needed due to API compatibility

## Support

For issues or questions:
1. Check existing documentation (README.md, README-EN.md)
2. Review RECOMMENDATIONS.md for improvement ideas
3. Submit an issue on GitHub

## Conclusion

Both implementations are production-ready and fully compatible. Choose based on your deployment platform, team expertise, and specific requirements. The Node.js version is recommended for serverless deployments.
