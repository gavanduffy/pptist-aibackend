from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import os
import json
import logging
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to load prompt templates from files
def load_prompt_template(filename: str) -> str:
    """Load prompt template from external file"""
    prompt_dir = os.path.join(os.path.dirname(__file__), "prompts")
    prompt_path = os.path.join(prompt_dir, filename)
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt template file not found: {prompt_path}")
        raise HTTPException(status_code=500, detail=f"Prompt template file {filename} not found")
    except Exception as e:
        logger.error(f"Error loading prompt template {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading prompt template")

# Validate configuration
if not settings.validate():
    logger.error("❌ Configuration validation failed!")
    if not settings.openai_api_key:
        logger.error("Reason: OPENAI_API_KEY environment variable is not set")
    elif settings.openai_api_key in ["your-openai-api-key-here", "your-openrouter-api-key-here"]:
        logger.error("Reason: OPENAI_API_KEY is still the default value, please set a real API Key")
    logger.error("Please check the .env file or environment variable configuration")
else:
    logger.info(f"✅ Configuration validation passed (model: {settings.default_model})")

app = FastAPI(
    title="PPTist AI Backend",
    description="AI-powered PPT generation backend using LangChain and FastAPI",
    version="0.1.0"
)

# Configure allowed CORS origins
allowed_origins = [
    "http://localhost:3000",  # React development server
    "http://localhost:5173",  # Vite development server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8080",  # Vue development server
    "http://127.0.0.1:8080",
    
]

# If in debug mode, allow all origins (development environment)
if settings.debug:
    allowed_origins = ["*"]
    logger.info("🌐 CORS: Debug mode - allowing all origins")
else:
    logger.info(f"🌐 CORS: Production mode - allowed origins: {allowed_origins}")

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add request validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors and provide detailed error messages"""
    logger.error(f"🚫 Request validation failed: {request.method} {request.url}")
    logger.error(f"🚫 Error details: {exc.errors()}")
    
    # Extract request body information
    try:
        body = await request.body()
        if body:
            logger.error(f"🚫 Request body: {body.decode('utf-8')}")
    except Exception:
        pass
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Request parameter validation failed",
            "help": {
                "/tools/aippt_outline": "Required parameters: model, language, content",
                "/tools/aippt": "Required parameters: model, language, content"
            }
        }
    )

router = APIRouter()

# Load prompt templates from external files
outline_template = load_prompt_template("outline.txt")
outline_prompt = PromptTemplate.from_template(outline_template)

cover_contents_template = load_prompt_template("cover_contents.txt")
cover_contents_prompt = PromptTemplate.from_template(cover_contents_template)

section_content_template = load_prompt_template("section_content.txt")
section_content_prompt = PromptTemplate.from_template(section_content_template)




def build_outline_chain(model_name: str = None):
    """Build PPT outline generation chain"""
    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured")
    
    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"]
    )
    return outline_prompt | llm | StrOutputParser()


def build_cover_contents_chain(model_name: str = None):
    """Build cover and contents page generation chain"""
    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured")
    
    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"]
    )
    return cover_contents_prompt | llm | StrOutputParser()


def build_section_content_chain(model_name: str = None):
    """Build section content generation chain"""
    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured")
    
    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"]
    )
    return section_content_prompt | llm | StrOutputParser()




def parse_outline(content: str) -> dict:
    """Parse outline content and extract title and chapter information"""
    lines = content.strip().split('\n')
    result = {
        'title': '',
        'chapters': []
    }
    
    current_chapter = None
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):  # PPT标题
            result['title'] = line[2:].strip()
        elif line.startswith('## '):  # 章节标题
            if current_chapter:
                result['chapters'].append(current_chapter)
            current_chapter = {
                'title': line[3:].strip(),
                'sections': []
            }
            current_section = None
        elif line.startswith('### '):  # 节标题
            if current_chapter:
                current_section = {
                    'title': line[4:].strip(),
                    'items': []
                }
                current_chapter['sections'].append(current_section)
        elif line.startswith('- '):  # 内容项
            if current_section:
                current_section['items'].append(line[2:].strip())
    
    # 添加最后一个章节
    if current_chapter:
        result['chapters'].append(current_chapter)
    
    return result


# 请求模型定义
class PPTOutlineRequest(BaseModel):
    model: str = Field('gpt-4o-mini', description="Model name to use, e.g. gpt-4o or gpt-4o-mini")
    language: str = Field(..., description="Language for generated content, e.g. Chinese, English")
    content: str = Field(..., max_length=50, description="Generation requirements, no more than 50 characters")
    stream: bool = True


class PPTContentRequest(BaseModel):
    model: str = Field('gpt-4o-mini', description="Model name to use, e.g. gpt-4o or gpt-4o-mini")
    language: str = Field(..., description="Language for generated content, e.g. Chinese, English")
    content: str = Field(..., description="PPT outline content")
    stream: bool = True


# 路由实现
@router.post("/tools/aippt_outline")
async def generate_ppt_outline_stream(request: PPTOutlineRequest):
    """Generate PPT outline (streaming response)"""
    logger.info(f"📝 Received outline generation request: model={request.model}, language={request.language}, requirement={request.content}")
    
    try:
        chain = build_outline_chain(request.model)
    except HTTPException as e:
        logger.error(f"Failed to build outline generation chain: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Exception building outline generation chain: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    async def token_stream():
        try:
            logger.info("Starting PPT outline generation...")
            async for chunk in chain.astream({
                "content": request.content,
                "language": request.language
            }):
                yield chunk
            logger.info("PPT outline generation completed")
        except Exception as e:
            error_msg = f"生成过程中出错: {str(e)}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"

    return StreamingResponse(token_stream(), media_type="text/event-stream")


@router.post("/tools/aippt")
async def generate_ppt_content_stream(request: PPTContentRequest):
    """Generate PPT content (step-by-step streaming response)"""
    logger.info(f"📄 Received content generation request: model={request.model}, language={request.language}")
    logger.info(f"📄 Outline content length: {len(request.content)} characters")
    
    # 解析大纲
    try:
        outline_data = parse_outline(request.content)
        logger.info(f"📄 Successfully parsed outline: title={outline_data[\'title\']}, chapters={len(outline_data[\'chapters\'])}")
    except Exception as e:
        logger.error(f"Failed to parse outline: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to parse outline format")
    
    # 构建生成链
    try:
        cover_contents_chain = build_cover_contents_chain(request.model)
        section_content_chain = build_section_content_chain(request.model)
    except HTTPException as e:
        logger.error(f"Failed to build generation chain: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Exception building generation chain: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    async def structured_page_stream():
        page_count = 0
        
        try:
            # 第一步：生成封面页和目录页
            logger.info("🏠 Starting cover and contents page generation...")
            buffer = ""
            async for chunk in cover_contents_chain.astream({
                "language": request.language,
                "content": request.content
            }):
                buffer += chunk
                # 检查缓冲区中是否包含完整的页面分隔符 "\n\n"
                while "\n\n" in buffer:
                    page_content, separator, rest_of_buffer = buffer.partition("\n\n")
                    if page_content.strip():
                        page_count += 1
                        logger.debug(f"Generated page {page_count} content (cover/contents)")
                        yield page_content + separator
                    buffer = rest_of_buffer
            
            # 处理剩余内容
            if buffer.strip():
                page_count += 1
                logger.debug(f"Generated page {page_count} content (last cover/contents page)")
                yield buffer + "\n\n"
            
            # 第二步：为每个章节生成过渡页和内容页
            for chapter_idx, chapter in enumerate(outline_data['chapters']):
                logger.info(f"📖 Starting chapter {chapter_idx + 1} generation: {chapter[\'title\']}")
                
                # 准备章节内容字符串
                section_content = f"## {chapter['title']}\n"
                for section in chapter['sections']:
                    section_content += f"### {section['title']}\n"
                    for item in section['items']:
                        section_content += f"- {item}\n"
                
                buffer = ""
                async for chunk in section_content_chain.astream({
                    "language": request.language,
                    "section_title": chapter['title'],
                    "section_content": section_content
                }):
                    buffer += chunk
                    # 检查缓冲区中是否包含完整的页面分隔符 "\n\n"
                    while "\n\n" in buffer:
                        page_content, separator, rest_of_buffer = buffer.partition("\n\n")
                        if page_content.strip():
                            page_count += 1
                            logger.debug(f"Generated page {page_count} content (chapter {chapter_idx + 1})")
                            yield page_content + separator
                        buffer = rest_of_buffer
                
                # 处理剩余内容
                if buffer.strip():
                    page_count += 1
                    logger.debug(f"Generated page {page_count} content (last page of chapter {chapter_idx + 1})")
                    yield buffer + "\n\n"
            
            # 第三步：生成结束页
            logger.info("🎬 Starting end page generation...")
            page_count += 1
            logger.debug(f"Generated page {page_count} content (end page)")
            yield '{"type": "end"}'
            
            logger.info(f"PPT content generation completed, total {page_count} pages generated")
            
        except Exception as e:
            error_msg = f"生成过程中出错: {str(e)}"
            logger.error(error_msg)
            yield f'{{"error": "{error_msg}"}}'

    return StreamingResponse(structured_page_stream(), media_type="text/event-stream")


# 添加健康检查端点
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "PPTist AI Backend is running"}


# 添加JSON文件读取端点
@router.get("/data/{filename}.json")
async def get_json_file(filename: str):
    """Read JSON files from template directory"""
    try:
        # 构建文件路径
        file_path = os.path.join("template", f"{filename}.json")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"📁 File not found: {file_path}")
            raise HTTPException(status_code=404, detail=f"File {filename}.json not found")
        
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"📄 Successfully read file: {filename}.json")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"🚫 JSON format error: {filename}.json - {str(e)}")
        raise HTTPException(status_code=400, detail=f"File {filename}.json format error")
    except Exception as e:
        logger.error(f"🚫 Failed to read file: {filename}.json - {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# 注册路由
app.include_router(router)


# 根路径
@app.get("/")
async def root():
    return {
        "message": "Welcome to PPTist AI Backend",
        "version": "0.1.0",
        "endpoints": {
            "outline": "/tools/aippt_outline",
            "content": "/tools/aippt",
            "health": "/health",
            "data": "/data/{filename}.json",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    if not settings.validate():
        logger.error("❌ Startup failed: OpenAI API Key not configured or invalid")
        logger.error("Please set OPENAI_API_KEY environment variable or create .env file")
        logger.error("You can copy .env.example to .env and modify the API Key in it")
        exit(1)
    
    logger.info(f"🚀 Starting PPTist AI Backend...")
    logger.info(f"📡 Server address: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API documentation: http://{settings.host}:{settings.port}/docs")
    
    try:
        uvicorn.run(
            "main:app",  # 使用字符串导入路径以支持 reload 功能
            host=settings.host,
            port=settings.port,
            reload=settings.debug
        )
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        logger.error("Please check if port is in use or other startup issues")
        raise
