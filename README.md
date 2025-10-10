# PPTist AI Backend

This project is an AI generation backend based on [this GitHub issue response](https://github.com/pipipi-pikachu/PPTist/issues/354#issuecomment-2863517189), supporting custom URLs and models.

AI-powered PPT generation backend service based on LangChain and FastAPI.

Used as an AI backend for generating PPT with [PPTist](https://github.com/pipipi-pikachu/PPTist)

Compatible with PPTist branch [57e21c3b4c28ce4195fbb20815f432d596c0e5c8](https://github.com/pipipi-pikachu/PPTist/tree/b3bbb75ea467690f0c71a4b6319720959cfdc84f)

Please use the corresponding version of PPTist with this backend.

## Features

- 🤖 **AI Outline Generation**: Automatically generates PPT outline structure based on topics
- 🎨 **Intelligent Content Generation**: Generates complete PPT page content based on outline
- 🔄 **Streaming Response**: Supports real-time streaming data transmission
- 🌐 **RESTful API**: Standard HTTP API interface
- 📚 **Automatic Documentation**: Automatically generated API documentation
- 🔌 **OpenRouter Integration**: Configured to use OpenRouter free models by default
- 📝 **External Prompts**: Prompts stored in external files for easy customization

## Tech Stack

- **FastAPI**: Modern high-performance Web framework
- **LangChain**: AI application development framework
- **OpenRouter**: Access to multiple AI models through a unified API
- **Pydantic**: Data validation and serialization
- **uv**: Ultra-fast Python package manager

## Quick Start

### 1. Environment Setup

Ensure your system has Python 3.13 or higher installed, and install [uv](https://docs.astral.sh/uv/).

#### Install uv

```bash
# Install using pip
pip install uv

# Or using curl (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using PowerShell (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Dependencies

Install project dependencies using uv:
```bash
uv sync
```

### 3. Configure Environment Variables

Copy the environment variable template:
```bash
cp .env.example .env
```

Edit the `.env` file and set your API configuration:
```bash
# OpenRouter API Configuration
OPENAI_API_KEY=your-openrouter-api-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# AI Model Configuration (using OpenRouter free models)
# Available free models: google/gemma-2-9b-it:free, meta-llama/llama-3.2-3b-instruct:free, etc.
DEFAULT_MODEL=google/gemma-2-9b-it:free
DEFAULT_TEMPERATURE=0.7

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

**Note**: Get your free OpenRouter API key at https://openrouter.ai/

### 4. Start the Service

Start the service using uv:
```bash
uv run main.py
```

Or use uvicorn:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

The service will start at http://localhost:8000

### 5. Access API Documentation

Open your browser and visit http://localhost:8000/docs to view the automatically generated API documentation.

### 6. Modify PPTist Code

```bash
# Clone the source code
git clone https://github.com/pipipi-pikachu/PPTist.git

# Switch to the compatible branch
git checkout 57e21c3b4c28ce4195fbb20815f432d596c0e5c8
```

Modify the server address:

+ In `PPTist\src\services\index.ts`, modify the `SERVER_URL` variable to the address of this service
+ In `src\views\Editor\AIPPTDialog.vue`, line 59, modify the model options in the Select tag, and on line 145, change `const model = ref('GLM-4-Flash')` to the default model

### 7. Offline Usage and Custom Templates (Optional)

For offline PPT generation and using your own templates:

The project provides functionality to convert template images to base64 (original templates use URL addresses).

Template creation process reference: https://github.com/pipipi-pikachu/PPTist/blob/master/doc/AIPPT.md

Place created template JSON files in the `template` folder under the project.

PPTist source code modifications needed:

+ In `PPTist\src\services\index.ts`, modify the `ASSET_URL` variable to the address of this service
+ In `src\store\slides.ts`, line 55, add your template to the `templates` list, and note to modify the image address when selecting templates (you can convert here: https://tool.chinaz.com/tools/imgtobase)

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
  "model": "google/gemma-2-9b-it:free",
  "language": "English",
  "content": "Artificial Intelligence applications in education",
  "stream": true
}
```

### Generate PPT Content
```http
POST /tools/aippt
Content-Type: application/json

{
  "model": "google/gemma-2-9b-it:free",
  "language": "English",
  "content": "# PPT Title\n## Chapter 1\n### Section 1\n- Content 1",
  "stream": true
}
```

## Usage Examples

### Python Client Example

```python
import requests
import json

# Generate outline
def generate_outline():
    response = requests.post(
        "http://localhost:8000/tools/aippt_outline",
        json={
            "model": "google/gemma-2-9b-it:free",
            "language": "English",
            "content": "Machine Learning Fundamentals",
            "stream": True
        },
        stream=True
    )
    
    for chunk in response.iter_content(decode_unicode=True):
        if chunk:
            print(chunk, end='')

# Generate PPT content
def generate_content(outline):
    response = requests.post(
        "http://localhost:8000/tools/aippt",
        json={
            "model": "google/gemma-2-9b-it:free",
            "language": "English",
            "content": outline,
            "stream": True
        },
        stream=True
    )
    
    for chunk in response.iter_content(decode_unicode=True):
        if chunk.strip():
            page_data = json.loads(chunk.strip())
            print(json.dumps(page_data, ensure_ascii=False, indent=2))
```

### Test Script

Run the provided test script:
```bash
uv run test_api.py
```

## PPT Page Types

Generated PPT content supports the following page types:

- **Cover page (cover)**: Contains title and subtitle
- **Contents page (contents)**: Contains chapter list
- **Transition page (transition)**: Transition pages between chapters
- **Content page (content)**: Specific content pages
- **End page (end)**: PPT ending page

## Output Format

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

This project is configured to use **OpenRouter** which provides access to multiple AI models. Free models include:

- `google/gemma-2-9b-it:free`: Google Gemma 2 9B (default)
- `meta-llama/llama-3.2-3b-instruct:free`: Meta Llama 3.2 3B
- `meta-llama/llama-3.2-1b-instruct:free`: Meta Llama 3.2 1B
- `nousresearch/hermes-3-llama-3.1-405b:free`: Hermes 3 Llama 3.1 405B
- `microsoft/phi-3-mini-128k-instruct:free`: Microsoft Phi-3 Mini
- `microsoft/phi-3-medium-128k-instruct:free`: Microsoft Phi-3 Medium
- `google/gemma-7b-it:free`: Google Gemma 7B

You can also use any other model available on OpenRouter by setting the model name in the request or in the `DEFAULT_MODEL` environment variable.

For a full list of available models, visit: https://openrouter.ai/models

### Environment Variables

| Variable Name | Description | Default Value |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenRouter API key | Required |
| `OPENAI_BASE_URL` | API base URL | https://openrouter.ai/api/v1 |
| `DEFAULT_MODEL` | Default AI model to use | google/gemma-2-9b-it:free |
| `DEFAULT_TEMPERATURE` | Model creativity parameter | 0.7 |
| `HOST` | Server listening address | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `DEBUG` | Debug mode switch | false |

### Customizing Prompts

Prompts are stored in external text files in the `prompts/` directory and can be edited without modifying the codebase:

- `prompts/outline.txt`: Template for generating PPT outlines
- `prompts/cover_contents.txt`: Template for generating cover and contents pages
- `prompts/section_content.txt`: Template for generating section content pages

You can customize these prompts to adjust the AI's behavior and output format.

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `200`: Request successful
- `400`: Request parameter error
- `422`: Validation error
- `500`: Internal server error

Errors in streaming responses are returned in text format.

## Development Guide

### Project Structure

```
pptist-aibackend/
├── main.py              # Main application file
├── config.py            # Configuration management
├── test_api.py          # API test script
├── prompts/             # Prompt template files
│   ├── outline.txt
│   ├── cover_contents.txt
│   └── section_content.txt
├── template/            # PPT template files
├── pyproject.toml       # Project configuration and dependencies
├── .python-version      # Python version lock
├── .env.example         # Environment variable template
└── README.md            # Documentation
```

### Extending Functionality

You can customize AI behavior by:

1. Modifying prompt templates in the `prompts/` directory to adjust generation format
2. Adjusting the `temperature` parameter to control output creativity
3. Switching to different OpenRouter models based on your needs
4. Adding new prompt templates for additional content types

## License

This project is licensed under the MIT License.

## Contributing

Contributions via Issues and Pull Requests are welcome to improve this project.

## Support

If you encounter issues while using this project:

1. Check if the API Key is correctly set
2. Confirm network connection is normal
3. View server logs for detailed error information
4. Submit an Issue for help

## Reference

- Original discussion: https://github.com/pipipi-pikachu/PPTist/issues/354#issuecomment-2863517189
- PPTist project: https://github.com/pipipi-pikachu/PPTist
- OpenRouter: https://openrouter.ai/
