/**
 * PPTist AI Backend - Node.js Implementation
 * AI-powered PPT generation backend using LangChain and Express.js
 */

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { ChatOpenAI } from '@langchain/openai';
import { PromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Configuration
const config = {
  openaiApiKey: process.env.OPENAI_API_KEY,
  openaiBaseUrl: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
  defaultModel: process.env.DEFAULT_MODEL || 'gpt-4o-mini',
  defaultTemperature: parseFloat(process.env.DEFAULT_TEMPERATURE || '0.7'),
  host: process.env.HOST || '0.0.0.0',
  port: parseInt(process.env.PORT || '8000'),
  debug: process.env.DEBUG === 'true'
};

// Validate configuration
function validateConfig() {
  if (!config.openaiApiKey) {
    console.error('❌ Configuration validation failed!');
    console.error('Reason: OPENAI_API_KEY environment variable is not set');
    return false;
  }
  if (config.openaiApiKey === 'your-openai-api-key-here') {
    console.error('❌ Configuration validation failed!');
    console.error('Reason: OPENAI_API_KEY is still the default value, please set a real API Key');
    return false;
  }
  console.log(`✅ Configuration validation passed (model: ${config.defaultModel})`);
  return true;
}

// Create Express app
const app = express();

// Middleware
app.use(express.json());

// CORS configuration
const allowedOrigins = [
  'http://localhost:3000',
  'http://localhost:5173',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:5173',
  'http://localhost:8080',
  'http://127.0.0.1:8080',
  '*',
];

if (config.debug) {
  app.use(cors({ origin: '*', credentials: true }));
  console.log('🌐 CORS: Debug mode - allowing all origins');
} else {
  app.use(cors({ origin: allowedOrigins, credentials: true }));
  console.log(`🌐 CORS: Production mode - allowed origins: ${allowedOrigins.join(', ')}`);
}

// PPT outline generation template
const outlineTemplate = `You are the user's PPT outline assistant. Based on the topic below, produce a presentation outline.

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
`;

// Cover page and contents page generation template
const coverContentsTemplate = `You are an expert PPT assistant. Using the supplied outline, create JSON for a cover page and a table of contents page.

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
`;

// Section content generation template
const sectionContentTemplate = `You are an expert PPT assistant. Using the chapter details below, create JSON for a transition page and detailed content pages.

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
`;

// Build LangChain chains
function buildOutlineChain(modelName = null) {
  const model = modelName || config.defaultModel;
  const llm = new ChatOpenAI({
    temperature: config.defaultTemperature,
    modelName: model,
    openAIApiKey: config.openaiApiKey,
    configuration: {
      baseURL: config.openaiBaseUrl
    }
  });
  
  const prompt = PromptTemplate.fromTemplate(outlineTemplate);
  return prompt.pipe(llm).pipe(new StringOutputParser());
}

function buildCoverContentsChain(modelName = null) {
  const model = modelName || config.defaultModel;
  const llm = new ChatOpenAI({
    temperature: config.defaultTemperature,
    modelName: model,
    openAIApiKey: config.openaiApiKey,
    configuration: {
      baseURL: config.openaiBaseUrl
    }
  });
  
  const prompt = PromptTemplate.fromTemplate(coverContentsTemplate);
  return prompt.pipe(llm).pipe(new StringOutputParser());
}

function buildSectionContentChain(modelName = null) {
  const model = modelName || config.defaultModel;
  const llm = new ChatOpenAI({
    temperature: config.defaultTemperature,
    modelName: model,
    openAIApiKey: config.openaiApiKey,
    configuration: {
      baseURL: config.openaiBaseUrl
    }
  });
  
  const prompt = PromptTemplate.fromTemplate(sectionContentTemplate);
  return prompt.pipe(llm).pipe(new StringOutputParser());
}

// Parse outline content
function parseOutline(content) {
  const lines = content.trim().split('\n');
  const result = {
    title: '',
    chapters: []
  };
  
  let currentChapter = null;
  let currentSection = null;
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (!trimmedLine) continue;
    
    if (trimmedLine.startsWith('# ')) {
      // PPT title
      result.title = trimmedLine.substring(2).trim();
    } else if (trimmedLine.startsWith('## ')) {
      // Chapter title
      if (currentChapter) {
        result.chapters.push(currentChapter);
      }
      currentChapter = {
        title: trimmedLine.substring(3).trim(),
        sections: []
      };
      currentSection = null;
    } else if (trimmedLine.startsWith('### ')) {
      // Section title
      if (currentChapter) {
        currentSection = {
          title: trimmedLine.substring(4).trim(),
          items: []
        };
        currentChapter.sections.push(currentSection);
      }
    } else if (trimmedLine.startsWith('- ')) {
      // Content item
      if (currentSection) {
        currentSection.items.push(trimmedLine.substring(2).trim());
      }
    }
  }
  
  // Add the last chapter
  if (currentChapter) {
    result.chapters.push(currentChapter);
  }
  
  return result;
}

// Routes

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to PPTist AI Backend',
    version: '0.1.0',
    endpoints: {
      outline: '/tools/aippt_outline',
      content: '/tools/aippt',
      health: '/health',
      data: '/data/{filename}.json',
      docs: '/docs'
    }
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    message: 'PPTist AI Backend is running'
  });
});

// Generate PPT outline (streaming)
app.post('/tools/aippt_outline', async (req, res) => {
  const { model, language, content, stream = true } = req.body;
  
  console.log(`📝 Received outline generation request: model=${model}, language=${language}, requirement=${content}`);
  
  try {
    const chain = buildOutlineChain(model);
    
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    console.log('Starting PPT outline generation...');
    
    const streamResult = await chain.stream({
      content: content,
      language: language
    });
    
    for await (const chunk of streamResult) {
      res.write(chunk);
    }
    
    console.log('PPT outline generation completed');
    res.end();
    
  } catch (error) {
    console.error(`Error during outline generation: ${error.message}`);
    res.status(500).send(`Error: ${error.message}`);
  }
});

// Generate PPT content (streaming by steps)
app.post('/tools/aippt', async (req, res) => {
  const { model, language, content, stream = true } = req.body;
  
  console.log(`📄 Received content generation request: model=${model}, language=${language}`);
  console.log(`📄 Outline content length: ${content.length} characters`);
  
  try {
    // Parse outline
    const outlineData = parseOutline(content);
    console.log(`📄 Outline parsed successfully: title=${outlineData.title}, chapters=${outlineData.chapters.length}`);
    
    // Build chains
    const coverContentsChain = buildCoverContentsChain(model);
    const sectionContentChain = buildSectionContentChain(model);
    
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    let pageCount = 0;
    
    // Step 1: Generate cover page and contents page
    console.log('🏠 Starting cover and contents page generation...');
    let buffer = '';
    
    const coverStream = await coverContentsChain.stream({
      language: language,
      content: content
    });
    
    for await (const chunk of coverStream) {
      buffer += chunk;
      // Check if buffer contains complete page separator "\n\n"
      while (buffer.includes('\n\n')) {
        const idx = buffer.indexOf('\n\n');
        const pageContent = buffer.substring(0, idx);
        buffer = buffer.substring(idx + 2);
        
        if (pageContent.trim()) {
          pageCount++;
          console.log(`Generated page ${pageCount} (cover/contents)`);
          res.write(pageContent + '\n\n');
        }
      }
    }
    
    // Process remaining content
    if (buffer.trim()) {
      pageCount++;
      console.log(`Generated page ${pageCount} (cover/contents last page)`);
      res.write(buffer + '\n\n');
    }
    
    // Step 2: Generate transition and content pages for each chapter
    for (let chapterIdx = 0; chapterIdx < outlineData.chapters.length; chapterIdx++) {
      const chapter = outlineData.chapters[chapterIdx];
      console.log(`📖 Starting chapter ${chapterIdx + 1}: ${chapter.title}`);
      
      // Prepare chapter content string
      let sectionContent = `## ${chapter.title}\n`;
      for (const section of chapter.sections) {
        sectionContent += `### ${section.title}\n`;
        for (const item of section.items) {
          sectionContent += `- ${item}\n`;
        }
      }
      
      buffer = '';
      const sectionStream = await sectionContentChain.stream({
        language: language,
        section_title: chapter.title,
        section_content: sectionContent
      });
      
      for await (const chunk of sectionStream) {
        buffer += chunk;
        // Check if buffer contains complete page separator "\n\n"
        while (buffer.includes('\n\n')) {
          const idx = buffer.indexOf('\n\n');
          const pageContent = buffer.substring(0, idx);
          buffer = buffer.substring(idx + 2);
          
          if (pageContent.trim()) {
            pageCount++;
            console.log(`Generated page ${pageCount} (chapter ${chapterIdx + 1})`);
            res.write(pageContent + '\n\n');
          }
        }
      }
      
      // Process remaining content
      if (buffer.trim()) {
        pageCount++;
        console.log(`Generated page ${pageCount} (chapter ${chapterIdx + 1} last page)`);
        res.write(buffer + '\n\n');
      }
    }
    
    // Step 3: Generate end page
    console.log('🎬 Starting end page generation...');
    pageCount++;
    console.log(`Generated page ${pageCount} (end page)`);
    res.write('{"type": "end"}');
    
    console.log(`PPT content generation completed, total ${pageCount} pages generated`);
    res.end();
    
  } catch (error) {
    console.error(`Error during content generation: ${error.message}`);
    res.status(500).send(`{"error": "${error.message}"}`);
  }
});

// Get JSON file from template directory
app.get('/data/:filename.json', async (req, res) => {
  const { filename } = req.params;
  
  try {
    const filePath = join(__dirname, 'template', `${filename}.json`);
    const data = await readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(data);
    
    console.log(`📄 Successfully read file: ${filename}.json`);
    res.json(jsonData);
    
  } catch (error) {
    if (error.code === 'ENOENT') {
      console.log(`📁 File not found: ${filename}.json`);
      res.status(404).json({ detail: `File ${filename}.json not found` });
    } else if (error instanceof SyntaxError) {
      console.error(`🚫 JSON format error: ${filename}.json - ${error.message}`);
      res.status(400).json({ detail: `File ${filename}.json has invalid JSON format` });
    } else {
      console.error(`🚫 Failed to read file: ${filename}.json - ${error.message}`);
      res.status(500).json({ detail: 'Internal server error' });
    }
  }
});

// API documentation endpoint (basic info)
app.get('/docs', (req, res) => {
  res.json({
    title: 'PPTist AI Backend API',
    version: '0.1.0',
    description: 'AI-powered PPT generation backend using LangChain and Express.js',
    endpoints: [
      {
        path: '/health',
        method: 'GET',
        description: 'Health check endpoint'
      },
      {
        path: '/tools/aippt_outline',
        method: 'POST',
        description: 'Generate PPT outline',
        body: {
          model: 'string (optional, default: gpt-4o-mini)',
          language: 'string (required)',
          content: 'string (required, max 50 chars)',
          stream: 'boolean (optional, default: true)'
        }
      },
      {
        path: '/tools/aippt',
        method: 'POST',
        description: 'Generate PPT content',
        body: {
          model: 'string (optional, default: gpt-4o-mini)',
          language: 'string (required)',
          content: 'string (required, outline content)',
          stream: 'boolean (optional, default: true)'
        }
      },
      {
        path: '/data/:filename.json',
        method: 'GET',
        description: 'Get JSON template file'
      }
    ]
  });
});

// Start server
if (validateConfig()) {
  app.listen(config.port, config.host, () => {
    console.log(`🚀 Starting PPTist AI Backend...`);
    console.log(`📡 Server address: http://${config.host}:${config.port}`);
    console.log(`📚 API docs: http://${config.host}:${config.port}/docs`);
  });
} else {
  console.error('❌ Startup failed: OpenAI API Key is not configured or invalid');
  console.error('Please set OPENAI_API_KEY environment variable or create .env file');
  console.error('You can copy .env.example to .env and modify the API Key');
  process.exit(1);
}

export default app;
