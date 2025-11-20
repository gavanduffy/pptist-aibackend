# PPTist AI Backend

This project is an AI-powered PPT generation backend based on [PPTist Issue #354](https://github.com/pipipi-pikachu/PPTist/issues/354#issuecomment-2863517189), supporting custom URLs and models.

Built with LangChain and Express.js for AI-driven PPT generation service.

Designed for use with [PPTist](https://github.com/pipipi-pikachu/PPTist) AI backend PPT generation.

Compatible with PPTist branch [57e21c3b4c28ce4195fbb20815f432d596c0e5c8](https://github.com/pipipi-pikachu/PPTist/tree/b3bbb75ea467690f0c71a4b6319720959cfdc84f)

Please use the corresponding version of PPTist with this backend.

## Features

- 🤖 **AI Outline Generation**: Automatically generate PPT outline structures based on topics
- 🎨 **Smart Content Generation**: Generate complete PPT page content based on outlines
- 🔄 **Streaming Response**: Supports real-time streaming data transmission
- 🌐 **RESTful API**: Standard HTTP API interface
- 📚 **Auto Documentation**: Automatically generated API documentation
- ☁️ **Serverless Ready**: Deploy to Vercel or Netlify with zero configuration

## Tech Stack

- **Express.js**: Fast, unopinionated web framework for Node.js
- **LangChain.js**: JavaScript framework for AI application development
- **OpenAI**: GPT model support
- **Streaming APIs**: Real-time response streaming

## Quick Start

### 1. Environment Setup

Ensure your system has Node.js 18 or higher installed.

#### Install Node.js

```bash
# Using nvm (recommended)
nvm install 18
nvm use 18

# Or download from https://nodejs.org/
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Copy the environment variable template:
```bash
cp .env.example .env
```

Edit the `.env` file and set your API configuration:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# AI Model Configuration
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_TEMPERATURE=0.7

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 4. Start Service

Start the development server:
```bash
npm run dev
```

Or start production server:
```bash
npm start
```

The service will start at http://localhost:8000.

### 5. Access API Documentation

Open your browser and visit http://localhost:8000/docs to view the automatically generated API documentation.

### 6. Modify PPTist Code

```bash
# Clone source code
git clone https://github.com/pipipi-pikachu/PPTist.git

# Switch branch
git checkout 57e21c3b4c28ce4195fbb20815f432d596c0e5c8
```

Modify server address:

+ In `PPTist\src\services\index.ts`, modify the `SERVER_URL` variable to this service's address
+ In `src\views\Editor\AIPPTDialog.vue`, line 59, modify the model options in the Select tag, and line 145 change `const model = ref('GLM-4-Flash')` to your default model

### 7. Offline Mode and Custom Templates (Optional)

To use PPT generation in offline environments and add your own templates.

The project provides a tool to convert template images to base64 (original templates use URL addresses).

Template creation process reference: https://github.com/pipipi-pikachu/PPTist/blob/master/doc/AIPPT.md

Place template JSON files in the `template` folder under the project.

PPTist source code modifications:

+ In `PPTist\src\services\index.ts`, modify the `ASSET_URL` variable to this service's address
+ In `src\store\slides.ts`, line 55, add your template to the `templates` list and note to modify the image address when selecting templates (you can convert here: https://tool.chinaz.com/tools/imgtobase)

## Deployment

### Deploy to Vercel

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy:
```bash
vercel
```

3. Set environment variables in Vercel dashboard:
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`
   - `DEFAULT_MODEL`
   - `DEFAULT_TEMPERATURE`

### Deploy to Netlify

1. Install Netlify CLI:
```bash
npm install -g netlify-cli
```

2. Deploy:
```bash
netlify deploy --prod
```

3. Set environment variables in Netlify dashboard:
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`
   - `DEFAULT_MODEL`
   - `DEFAULT_TEMPERATURE`

## API Endpoints

### Health Check
```http
GET /health
```

### Generate PPT Outline
```http
POST /tools/aippt_outline
Content-Type: application/json

{
  "model": "gpt-4o-mini",
  "language": "English",
  "content": "Artificial Intelligence Applications in Education",
  "stream": true
}
```

### Generate PPT Content
```http
POST /tools/aippt
Content-Type: application/json

{
  "model": "gpt-4o-mini",
  "language": "English",
  "content": "# PPT Title\n## Chapter 1\n### Section 1\n- Content 1",
  "stream": true
}
```

## Usage Examples

### Node.js Client Example

```javascript
// Generate outline
async function generateOutline() {
  const response = await fetch('http://localhost:8000/tools/aippt_outline', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      language: 'English',
      content: 'Machine Learning Basics',
      stream: true
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    process.stdout.write(chunk);
  }
}

// Generate PPT content
async function generateContent(outline) {
  const response = await fetch('http://localhost:8000/tools/aippt', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      language: 'English',
      content: outline,
      stream: true
    })
  });
  
  // Process streaming response
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    if (chunk.trim()) {
      const pageData = JSON.parse(chunk.trim());
      console.log(JSON.stringify(pageData, null, 2));
    }
  }
}
```

### Test Script

Run the provided test script:
```bash
npm test
```

## PPT Page Types

Generated PPT content supports the following page types:

- **Cover page (cover)**: Contains title and subtitle
- **Contents page (contents)**: Contains chapter list
- **Transition page (transition)**: Transition pages between chapters
- **Content page (content)**: Specific content pages
- **End page (end)**: PPT ending page

## Output Formats

### Outline Format
```markdown
# PPT Title
## Chapter Name
### Section Name
- Content 1
- Content 2
- Content 3
```

### Page Content Format
```json
{"type": "cover", "data": {"title": "Title", "text": "Subtitle"}}
{"type": "contents", "data": {"items": ["Chapter 1", "Chapter 2"]}}
{"type": "content", "data": {"title": "Title", "items": [{"title": "Subtitle", "text": "Content"}]}}
```

## Configuration

### Supported Models

- `gpt-4o`: OpenAI GPT-4 Omni model
- `gpt-4o-mini`: OpenAI GPT-4 Omni Mini model (default)
- Other OpenAI API compatible models

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_BASE_URL` | API base URL | https://api.openai.com/v1 |
| `DEFAULT_MODEL` | Default AI model | gpt-4o-mini |
| `DEFAULT_TEMPERATURE` | Model creativity parameter | 0.7 |
| `HOST` | Server listening address | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `DEBUG` | Debug mode switch | false |

## Error Handling

API returns appropriate HTTP status codes and error messages:

- `200`: Request successful
- `400`: Request parameter error
- `404`: Resource not found
- `500`: Internal server error

Errors in streaming responses are returned as text format.

## Development Guide

### Project Structure

```
pptist-aibackend/
├── index.js             # Main application file
├── test-api.js          # API test script
├── package.json         # Project configuration and dependencies
├── netlify.toml         # Netlify deployment configuration
├── vercel.json          # Vercel deployment configuration
├── .env.example         # Environment variable template
├── README.md            # Chinese documentation
├── README-EN.md         # English documentation
├── netlify/
│   └── functions/
│       └── api.js       # Netlify serverless function
└── template/            # Template files
```

### Extending Features

You can customize AI behavior by modifying templates in `index.js`:

1. Modify `outlineTemplate` to adjust outline generation format
2. Modify `coverContentsTemplate` to adjust cover and contents page generation format
3. Modify `sectionContentTemplate` to adjust section content generation format
4. Adjust `temperature` parameter to control output creativity

## License

This project uses the MIT license.

## Contributing

Issues and Pull Requests are welcome to improve this project.

## Support

If you encounter issues during use, please:

1. Check if API Key is set correctly
2. Confirm network connection is normal
3. View server logs for detailed error information
4. Submit an Issue for help

## Reference

https://github.com/pipipi-pikachu/PPTist/issues/354#issuecomment-2863517189

https://github.com/pipipi-pikachu/PPTist/issues/354
