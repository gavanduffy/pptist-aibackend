from pathlib import Path
import json
import logging
from typing import Dict

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PROMPT_FILE_PATH = BASE_DIR / "prompts" / "ppt_prompts.json"
REQUIRED_PROMPT_KEYS = {"outline", "cover_contents", "section_content"}


def load_prompt_templates() -> Dict[str, str]:
    """Load prompt templates from the external JSON file."""

    try:
        with PROMPT_FILE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Prompt file not found at {PROMPT_FILE_PATH.resolve()}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Prompt file {PROMPT_FILE_PATH.resolve()} contains invalid JSON"
        ) from exc

    missing_keys = REQUIRED_PROMPT_KEYS - data.keys()
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise RuntimeError(f"Missing prompt templates: {missing}")

    return {key: str(value) for key, value in data.items()}


try:
    PROMPT_TEMPLATES = load_prompt_templates()
    logger.info("📄 Loaded prompt templates from %s", PROMPT_FILE_PATH)
except Exception as exc:  # pragma: no cover - fail fast at runtime
    logger.error("⚠️ Failed to load prompt templates: %s", exc)
    PROMPT_TEMPLATES = {}


app = FastAPI(
    title="PPTist AI Backend",
    description="AI-powered PPT generation backend using LangChain and FastAPI",
    version="0.2.0",
)

if not settings.validate():
    logger.error("❌ Configuration validation failed!")
    if not settings.openrouter_api_key:
        logger.error("Reason: OPENROUTER_API_KEY environment variable is not set")
    elif settings.openrouter_api_key == "your-openrouter-api-key-here":
        logger.error("Reason: OPENROUTER_API_KEY still uses the placeholder value")
    logger.error("Please update your .env file or environment variables")
else:
    logger.info("✅ Configuration validated (model: %s)", settings.default_model)

# Default CORS configuration for local development stacks
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

if settings.debug:
    allowed_origins = ["*"]
    logger.info("🌐 CORS: debug mode enabled - allowing all origins")
else:
    logger.info("🌐 CORS: production mode - allowed origins: %s", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def prompt_template(key: str) -> PromptTemplate:
    """Return the requested prompt template or raise an HTTP error."""

    template_text = PROMPT_TEMPLATES.get(key)
    if not template_text:
        logger.error("Prompt template '%s' is not available", key)
        raise HTTPException(status_code=500, detail=f"Prompt template '{key}' is not available")
    return PromptTemplate.from_template(template_text)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a helpful validation error response."""

    logger.error("🚫 Validation failed: %s %s", request.method, request.url)
    logger.error("🚫 Details: %s", exc.errors())

    try:
        body = await request.body()
        if body:
            logger.error("🚫 Request body: %s", body.decode("utf-8"))
    except Exception:  # pragma: no cover - best effort logging
        pass

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed",
            "help": {
                "/tools/aippt_outline": "Required body: model, language, content",
                "/tools/aippt": "Required body: model, language, content",
            },
        },
    )


router = APIRouter()


def build_outline_chain(model_name: str | None = None):
    """Create the chain that generates the PPT outline."""

    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenRouter API key is missing")

    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"],
        default_headers=model_config["default_headers"],
    )
    return prompt_template("outline") | llm | StrOutputParser()


def build_cover_contents_chain(model_name: str | None = None):
    """Create the chain that generates the cover and table of contents."""

    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenRouter API key is missing")

    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"],
        default_headers=model_config["default_headers"],
    )
    return prompt_template("cover_contents") | llm | StrOutputParser()


def build_section_content_chain(model_name: str | None = None):
    """Create the chain that generates detailed section content."""

    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenRouter API key is missing")

    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"],
        default_headers=model_config["default_headers"],
    )
    return prompt_template("section_content") | llm | StrOutputParser()


def parse_outline(content: str) -> Dict[str, object]:
    """Parse the outline text into a structured dictionary."""

    lines = content.strip().split("\n")
    result: Dict[str, object] = {
        "title": "",
        "chapters": [],
    }

    current_chapter = None
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("# "):
            result["title"] = line[2:].strip()
        elif line.startswith("## "):
            if current_chapter:
                result["chapters"].append(current_chapter)
            current_chapter = {
                "title": line[3:].strip(),
                "sections": [],
            }
            current_section = None
        elif line.startswith("### "):
            if current_chapter is not None:
                current_section = {
                    "title": line[4:].strip(),
                    "items": [],
                }
                current_chapter["sections"].append(current_section)
        elif line.startswith("- ") and current_section is not None:
            current_section["items"].append(line[2:].strip())

    if current_chapter:
        result["chapters"].append(current_chapter)

    return result


class PPTOutlineRequest(BaseModel):
    model: str = Field(
        default_factory=lambda: settings.default_model,
        description="Model name to use, for example openrouter/auto",
    )
    language: str = Field(..., description="Target language for the generated outline")
    content: str = Field(..., description="Prompt describing the presentation goals")
    stream: bool = Field(True, description="Whether to stream tokens back to the client")


class PPTContentRequest(BaseModel):
    model: str = Field(
        default_factory=lambda: settings.default_model,
        description="Model name to use, for example openrouter/auto",
    )
    language: str = Field(..., description="Target language for the generated content")
    content: str = Field(..., description="PPT outline content to expand")
    stream: bool = Field(True, description="Whether to stream tokens back to the client")


@router.post("/tools/aippt_outline")
async def generate_ppt_outline_stream(request: PPTOutlineRequest):
    """Generate a PPT outline and stream the response."""

    logger.info(
        "📝 Outline request received: model=%s, language=%s", request.model, request.language
    )

    try:
        chain = build_outline_chain(request.model)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to build outline generation chain: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    async def token_stream():
        try:
            logger.info("Starting PPT outline generation…")
            async for chunk in chain.astream(
                {
                    "content": request.content,
                    "language": request.language,
                }
            ):
                yield chunk
            logger.info("PPT outline generation completed")
        except Exception as exc:  # pragma: no cover - streaming safety net
            error_msg = f"Error during generation: {exc}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"

    return StreamingResponse(token_stream(), media_type="text/event-stream")


@router.post("/tools/aippt")
async def generate_ppt_content_stream(request: PPTContentRequest):
    """Generate PPT content (cover, chapters, ending) as a streamed response."""

    logger.info("📄 Content request received: model=%s, language=%s", request.model, request.language)
    logger.info("📄 Outline length: %s characters", len(request.content))

    try:
        outline_data = parse_outline(request.content)
        logger.info(
            "📄 Outline parsed successfully: title=%s, chapters=%s",
            outline_data.get("title"),
            len(outline_data.get("chapters", [])),
        )
    except Exception as exc:
        logger.exception("Failed to parse outline: %s", exc)
        raise HTTPException(status_code=400, detail="Unable to parse outline format") from exc

    try:
        cover_contents_chain = build_cover_contents_chain(request.model)
        section_content_chain = build_section_content_chain(request.model)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to build content chains: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    async def structured_page_stream():
        page_count = 0

        try:
            logger.info("🏠 Generating cover and table of contents…")
            buffer = ""
            async for chunk in cover_contents_chain.astream(
                {
                    "language": request.language,
                    "content": request.content,
                }
            ):
                buffer += chunk
                while "\n\n" in buffer:
                    page_content, separator, rest_of_buffer = buffer.partition("\n\n")
                    if page_content.strip():
                        page_count += 1
                        logger.debug("Yielding page %s (cover/contents)", page_count)
                        yield page_content + separator
                    buffer = rest_of_buffer

            if buffer.strip():
                page_count += 1
                logger.debug("Yielding page %s (final cover/contents chunk)", page_count)
                yield buffer + "\n\n"

            for chapter_index, chapter in enumerate(outline_data["chapters"], start=1):
                logger.info("📖 Generating chapter %s: %s", chapter_index, chapter["title"])

                section_content = f"## {chapter['title']}\n"
                for section in chapter["sections"]:
                    section_content += f"### {section['title']}\n"
                    for item in section["items"]:
                        section_content += f"- {item}\n"

                buffer = ""
                async for chunk in section_content_chain.astream(
                    {
                        "language": request.language,
                        "section_title": chapter["title"],
                        "section_content": section_content,
                    }
                ):
                    buffer += chunk
                    while "\n\n" in buffer:
                        page_content, separator, rest_of_buffer = buffer.partition("\n\n")
                        if page_content.strip():
                            page_count += 1
                            logger.debug(
                                "Yielding page %s (chapter %s)", page_count, chapter_index
                            )
                            yield page_content + separator
                        buffer = rest_of_buffer

                if buffer.strip():
                    page_count += 1
                    logger.debug(
                        "Yielding page %s (final chunk for chapter %s)", page_count, chapter_index
                    )
                    yield buffer + "\n\n"

            logger.info("🎬 Generating ending page…")
            page_count += 1
            logger.debug("Yielding page %s (ending)", page_count)
            yield '{"type": "end"}'

            logger.info("PPT content generation finished. Total pages: %s", page_count)
        except Exception as exc:  # pragma: no cover - streaming safety net
            error_msg = f"Error during generation: {exc}"
            logger.error(error_msg)
            yield json.dumps({"error": error_msg})

    return StreamingResponse(structured_page_stream(), media_type="text/event-stream")


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""

    return {"status": "healthy", "message": "PPTist AI Backend is running"}


@router.get("/data/{filename}.json")
async def get_json_file(filename: str):
    """Read JSON templates from the template directory."""

    try:
        file_path = BASE_DIR / "template" / f"{filename}.json"

        if not file_path.exists():
            logger.warning("📁 File not found: %s", file_path)
            raise HTTPException(status_code=404, detail=f"File {filename}.json not found")

        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        logger.info("📄 Successfully read file: %s.json", filename)
        return data

    except json.JSONDecodeError as exc:
        logger.error("🚫 Invalid JSON in %s.json: %s", filename, exc)
        raise HTTPException(status_code=400, detail=f"File {filename}.json is not valid JSON") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("🚫 Failed to read file %s.json: %s", filename, exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to PPTist AI Backend",
        "version": app.version,
        "endpoints": {
            "outline": "/tools/aippt_outline",
            "content": "/tools/aippt",
            "health": "/health",
            "data": "/data/{filename}.json",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    if not settings.validate():
        logger.error("❌ Startup aborted: OpenRouter API key is missing or invalid")
        logger.error("Please set OPENROUTER_API_KEY in your environment or .env file")
        exit(1)

    logger.info("🚀 Starting PPTist AI Backend…")
    logger.info("📡 Server address: http://%s:%s", settings.host, settings.port)
    logger.info("📚 API docs: http://%s:%s/docs", settings.host, settings.port)

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
