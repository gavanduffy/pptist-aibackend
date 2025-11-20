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

# Validate configuration
if not settings.validate():
    logger.error("❌ Configuration validation failed!")
    if not settings.openai_api_key:
        logger.error("Reason: OPENAI_API_KEY environment variable is not set")
    elif settings.openai_api_key == "your-openai-api-key-here":
        logger.error("Reason: OPENAI_API_KEY is still the default value, please set a real API Key")
    logger.error("Please check .env file or environment variable configuration")
else:
    logger.info(f"✅ Configuration validation passed (model: {settings.default_model})")

app = FastAPI(
    title="PPTist AI Backend",
    description="AI-powered PPT generation backend using LangChain and FastAPI",
    version="0.1.0"
)

# Configure CORS allowed origins
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
    """Handle request validation errors, provide detailed error information"""
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

# PPT outline generation template
outline_template = """You are the user's PPT outline assistant. Based on the topic below, produce a presentation outline.

Guidelines:
- Create between 2 and 6 chapters, with a hard maximum of 10.
- Each chapter should contain 1 to 10 sections and vary the number of sections when possible.
- Section bullet points must stay between 1 and 6 items.
- Do not include commentary or explanations outside the outline.

Output format:
# PPT Title
## Chapter name
### Section name
- Bullet point
- Bullet point
### Section name
- ...

Topic requirements: {content}
Language of the outline: {language}
"""

outline_prompt = PromptTemplate.from_template(outline_template)

# PPT cover page and contents page generation template
cover_contents_template = """
You are an expert PPT assistant. Using the supplied outline, create JSON for a cover page and a table of contents page.

Output requirements:
- Each page must be a standalone JSON object on a single line.
- Separate pages with two newline characters.
- Do not add commentary or explanations.

Important notes:
- Only generate a cover page ("cover") and a contents page ("contents").
- Keep each text field under 100 words while staying descriptive.

Example (each JSON object on one line):

{{"type": "cover", "data": {{ "title": "API Overview", "text": "Discover the key elements of interface design" }}}}

{{"type": "contents", "data": {{ "items": ["Definition", "Classification", "Design Principles"] }}}}

Language: {language}
Outline content: {content}
"""

cover_contents_prompt = PromptTemplate.from_template(cover_contents_template)

# PPT section content generation template
section_content_template = """
You are an expert PPT assistant. Using the chapter details below, create JSON for a transition page and detailed content pages.

Output requirements:
- Each page must be a standalone JSON object on a single line.
- Separate pages with two newline characters.
- Do not add commentary or explanations.

Important notes:
- Generate one transition page ("transition") per chapter.
- Generate one content page ("content") for every section within the chapter.
- Keep each text field under 100 words while remaining informative.

Example (each JSON object on one line):

{{"type": "transition", "data": {{ "title": "Interface Definition", "text": "Introducing the core meaning of interfaces" }}}}

{{"type": "content", "data": {{ "title": "Interface Definition", "items": [ {{ "title": "Concept", "text": "Interfaces describe behaviours without implementations." }}, {{ "title": "Role", "text": "They enable polymorphism and loose coupling." }} ] }}}}

Language: {language}
Chapter title: {section_title}
Chapter details: {section_content}
"""

section_content_prompt = PromptTemplate.from_template(section_content_template)



def build_outline_chain(model_name: str = None):
    """Build PPT outline generation chain"""
    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenAI API Key is not configured")
    
    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"]
    )
    return outline_prompt | llm | StrOutputParser()


def build_cover_contents_chain(model_name: str = None):
    """Build cover page and contents page generation chain"""
    if not settings.validate():
        raise HTTPException(status_code=500, detail="OpenAI API Key is not configured")
    
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
        raise HTTPException(status_code=500, detail="OpenAI API Key is not configured")
    
    model_config = settings.get_model_config(model_name)
    llm = ChatOpenAI(
        temperature=model_config["temperature"],
        model=model_config["model"],
        openai_api_key=model_config["openai_api_key"],
        openai_api_base=model_config["openai_api_base"]
    )
    return section_content_prompt | llm | StrOutputParser()




def parse_outline(content: str) -> dict:
    """Parse outline content, extract title and chapter information"""
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
        elif line.startswith('## '):  # Chapter title
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
    
    # Add the last chapter
    if current_chapter:
        result['chapters'].append(current_chapter)
    
    return result


# 请求模型定义
class PPTOutlineRequest(BaseModel):
    model: str = Field('gpt-4o-mini', description="使用的模型名称，例如 gpt-4o 或 gpt-4o-mini")
    language: str = Field(..., description="生成内容的语言，例如 中文、English")
    content: str = Field(..., max_length=50, description="生成的要求，不超过50字")
    stream: bool = True


class PPTContentRequest(BaseModel):
    model: str = Field('gpt-4o-mini', description="使用的模型名称，例如 gpt-4o 或 gpt-4o-mini")
    language: str = Field(..., description="生成内容的语言，例如 中文、English")
    content: str = Field(..., description="PPT大纲内容")
    stream: bool = True


# 路由实现
@router.post("/tools/aippt_outline")
async def generate_ppt_outline_stream(request: PPTOutlineRequest):
    """生成PPT大纲（流式返回）"""
    logger.info(f"📝 收到大纲生成请求: 模型={request.model}, 语言={request.language}, 要求={request.content}")
    
    try:
        chain = build_outline_chain(request.model)
    except HTTPException as e:
        logger.error(f"构建大纲生成链失败: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"构建大纲生成链异常: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

    async def token_stream():
        try:
            logger.info("开始生成PPT大纲...")
            async for chunk in chain.astream({
                "content": request.content,
                "language": request.language
            }):
                yield chunk
            logger.info("PPT大纲生成完成")
        except Exception as e:
            error_msg = f"生成过程中出错: {str(e)}"
            logger.error(error_msg)
            yield f"错误: {error_msg}"

    return StreamingResponse(token_stream(), media_type="text/event-stream")


@router.post("/tools/aippt")
async def generate_ppt_content_stream(request: PPTContentRequest):
    """生成PPT内容（分步骤流式返回）"""
    logger.info(f"📄 收到内容生成请求: 模型={request.model}, 语言={request.language}")
    logger.info(f"📄 大纲内容长度: {len(request.content)} 字符")
    
    # 解析大纲
    try:
        outline_data = parse_outline(request.content)
        logger.info(f"📄 解析大纲成功: 标题={outline_data['title']}, 章节数={len(outline_data['chapters'])}")
    except Exception as e:
        logger.error(f"解析大纲失败: {str(e)}")
        raise HTTPException(status_code=400, detail="大纲格式解析失败")
    
    # 构建生成链
    try:
        cover_contents_chain = build_cover_contents_chain(request.model)
        section_content_chain = build_section_content_chain(request.model)
    except HTTPException as e:
        logger.error(f"构建生成链失败: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"构建生成链异常: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
    
    async def structured_page_stream():
        page_count = 0
        
        try:
            # 第一步：生成封面页和目录页
            logger.info("🏠 开始生成封面页和目录页...")
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
                        logger.debug(f"生成第 {page_count} 页内容（封面/目录）")
                        yield page_content + separator
                    buffer = rest_of_buffer
            
            # 处理剩余内容
            if buffer.strip():
                page_count += 1
                logger.debug(f"生成第 {page_count} 页内容（封面/目录最后一页）")
                yield buffer + "\n\n"
            
            # 第二步：为每个章节生成过渡页和内容页
            for chapter_idx, chapter in enumerate(outline_data['chapters']):
                logger.info(f"📖 开始生成第 {chapter_idx + 1} 章: {chapter['title']}")
                
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
                            logger.debug(f"生成第 {page_count} 页内容（第{chapter_idx + 1}章）")
                            yield page_content + separator
                        buffer = rest_of_buffer
                
                # 处理剩余内容
                if buffer.strip():
                    page_count += 1
                    logger.debug(f"生成第 {page_count} 页内容（第{chapter_idx + 1}章最后一页）")
                    yield buffer + "\n\n"
            
            # 第三步：生成结束页
            logger.info("🎬 开始生成结束页...")
            page_count += 1
            logger.debug(f"生成第 {page_count} 页内容（结束页）")
            yield '{"type": "end"}'
            
            logger.info(f"PPT内容生成完成，总共生成 {page_count} 页")
            
        except Exception as e:
            error_msg = f"生成过程中出错: {str(e)}"
            logger.error(error_msg)
            yield f'{{"error": "{error_msg}"}}'

    return StreamingResponse(structured_page_stream(), media_type="text/event-stream")


# 添加健康检查端点
@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "PPTist AI Backend is running"}


# 添加JSON文件读取端点
@router.get("/data/{filename}.json")
async def get_json_file(filename: str):
    """读取template目录下的JSON文件"""
    try:
        # 构建文件路径
        file_path = os.path.join("template", f"{filename}.json")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"📁 文件不存在: {file_path}")
            raise HTTPException(status_code=404, detail=f"文件 {filename}.json 不存在")
        
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"📄 成功读取文件: {filename}.json")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"🚫 JSON格式错误: {filename}.json - {str(e)}")
        raise HTTPException(status_code=400, detail=f"文件 {filename}.json 格式错误")
    except Exception as e:
        logger.error(f"🚫 读取文件失败: {filename}.json - {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


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
        logger.error("❌ 启动失败: OpenAI API Key is not configured或无效")
        logger.error("请设置 OPENAI_API_KEY 环境变量或创建 .env 文件")
        logger.error("可以复制 .env.example 为 .env 并修改其中的 API Key")
        exit(1)
    
    logger.info(f"🚀 启动 PPTist AI Backend...")
    logger.info(f"📡 服务器地址: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API 文档: http://{settings.host}:{settings.port}/docs")
    
    try:
        uvicorn.run(
            "main:app",  # 使用字符串导入路径以支持 reload 功能
            host=settings.host,
            port=settings.port,
            reload=settings.debug
        )
    except Exception as e:
        logger.error(f"❌ 启动失败: {str(e)}")
        logger.error("请检查端口是否被占用或其他启动问题")
        raise
