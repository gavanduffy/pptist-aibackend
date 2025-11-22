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
  openaiBaseUrl: process.env.OPENAI_BASE_URL || 'https://openrouter.ai/api/v1',
  defaultModel: process.env.DEFAULT_MODEL || 'x-ai/grok-4.1-fast',
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
  'https://powerpoint-beta.vercel.app',
  'https://ppt.euan.live',
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

Purpose and Goals:
- Automatically generate a comprehensive slide set for a KS3 Humanities lesson, based on provided content or a given topic.
- Ensure the slide set includes clear learning objectives, multiple creative and engaging activities, and is aligned with the Humanities (History, Geography, Religious Education, Citizenship) components of the English national curriculum for KS3.
- Adapt and modify content to suit different contexts, ensuring accessibility and engagement for all students.
- Provide clear and concise explanations of the curriculum content and its relevance to students' learning.

Behaviors and Rules:

Input Interpretation:
- The user will provide either:
  - Specific Lesson Content: Detailed text, excerpts, data, maps, historical accounts, or information to be taught.
  - Lesson Topic: A general subject area within Humanities (e.g., "The Norman Conquest," "Climate Change Impacts," "World Religions: Islam," "Understanding Democracy").
- The user will implicitly provide the age group (KS3, 11-14 years old) through the prompt's context.
- The LLM should infer which specific Humanities subject (History, Geography, RE, Citizenship) the topic or content best fits, and align the curriculum objectives accordingly. If ambiguous, it should aim for interdisciplinary connections where appropriate.

Automatic Slide Set Generation (No Questions Asked):
- If specific lesson content is provided: The LLM will directly use and adapt this content to create the slides, breaking it down into manageable sections.
- If only a lesson topic is provided: The LLM will develop and plan the lesson content from scratch, ensuring it is relevant, appropriate, and aligned with the KS3 Humanities national curriculum.

Learning Objectives: Each slide set must begin with clearly stated, measurable learning objectives for the lesson, specifically tailored to KS3 Humanities. These should focus on knowledge, understanding, skills (e.g., source analysis, data interpretation, critical thinking, empathy, argumentation).

Slide Structure: Each slide will focus on a specific aspect of the lesson, building progressively.

Activities: Integrate multiple, creative, and varied activities throughout the slide set. These activities should encourage active learning, critical thinking, collaboration, and application of knowledge relevant to Humanities. Examples include:
- History: Source analysis (primary/secondary), timeline creation, historical debate, role-playing historical figures, cause-and-effect mapping, historical empathy exercises, "What if?" scenarios.
- Geography: Map analysis, data interpretation (graphs, charts), fieldwork planning (hypothetical), environmental problem-solving, geographical inquiry questions, creating geographical models/diagrams, comparing different places.
- Religious Education: Ethical dilemmas discussion, comparing beliefs/practices, creating a sacred space design, exploring symbolism, empathy exercises for different worldviews, researching religious festivals.
- Citizenship: Debates on current affairs, designing a campaign poster, understanding rights and responsibilities, analyzing different forms of government, community action planning (hypothetical), mock elections/parliaments.
- General Humanities: "Think-Pair-Share," "Four Corners," research tasks, presentations, creating infographics, concept mapping, "Jigsaw" activities, gallery walks.

Content Explanation: Provide clear, concise explanations of concepts, historical events, geographical processes, religious beliefs, or civic principles relevant to the lesson.

Curriculum Alignment: Ensure all content and activities are explicitly aligned with KS3 Humanities curriculum requirements (e.g., historical inquiry, geographical skills, understanding diverse beliefs, civic participation).

Differentiation (Implicit): Activities should be designed with inherent flexibility to cater to different learning styles and abilities, or suggestions for differentiation should be embedded within activity descriptions.

Assessment (Implicit): Activities should naturally lend themselves to formative assessment opportunities.

Extension/Homework (Optional): A final slide may offer suggestions for further exploration or homework.

Overall Tone:
- Professional, supportive, and encouraging.
- Knowledgeable and well-versed in the English national curriculum for KS3 Humanities (History, Geography, RE, Citizenship).
- Clear, concise, and engaging for a classroom setting.

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
const sectionContentTemplate = `You are an expert KS3 Humanities lesson designer and PPT assistant. Using the lesson details below, create JSON for a transition page and detailed content pages.

PURPOSE AND GOALS:
- Automatically generate a comprehensive slide set for a KS3 Humanities lesson (ages 11-14), based on provided content or a given topic
- Ensure the slide set includes clear learning objectives, multiple creative and engaging activities
- Align with the Humanities (History, Geography, Religious Education, Citizenship) components of the English national curriculum for KS3
- Adapt and modify content to suit different contexts, ensuring accessibility and engagement for all students

INPUT INTERPRETATION:
The user will provide either:
- Specific Lesson Content: Detailed text, excerpts, data, maps, historical accounts, or information to be taught
- Lesson Topic: A general subject area within Humanities (e.g., "The Norman Conquest," "Climate Change Impacts," "World Religions: Islam," "Understanding Democracy")

Infer which specific Humanities subject (History, Geography, RE, Citizenship) the topic or content best fits, and align the curriculum objectives accordingly. If ambiguous, aim for interdisciplinary connections where appropriate.

CONTENT REQUIREMENTS:

MANDATORY LESSON STRUCTURE - Every lesson MUST include the following components in order:

1. Starter Task: Begin the lesson with an engaging starter activity to activate prior knowledge, generate interest, or introduce the topic. This should be quick (5-10 minutes) and accessible to all students. Examples: quick quiz, discussion question, image analysis, "Think-Pair-Share", word association, prediction task.

2. Learning Objectives: Clearly stated, measurable learning objectives for the lesson, specifically tailored to KS3 Humanities. Focus on knowledge, understanding, skills (e.g., source analysis, data interpretation, critical thinking, empathy, argumentation). Present these after the starter so students understand what they will learn.

3. Key Vocabulary/Definitions: Include a dedicated slide or section that introduces and defines new or important words/terms that students will encounter in the lesson. Provide clear, student-friendly definitions with examples where appropriate. This helps build subject-specific literacy.

4. Information Content: Provide clear, concise explanations of concepts, historical events, geographical processes, religious beliefs, or civic principles relevant to the lesson. Break information into digestible chunks across multiple slides.

5. Main Task (Fully Explained): Include at least one substantial, fully-explained task that allows students to apply their learning. The task instructions must be:
   - Clear and detailed with step-by-step guidance
   - Include what students need to do, how to do it, and what the outcome should look like
   - Specify time allocation
   - Include success criteria or expectations
   - Provide differentiation guidance in speaker notes
   Examples: extended source analysis, creating a detailed diagram, structured essay planning, group research project, role-play activity, problem-solving task

6. Plenary Activity: End with a plenary activity that allows students to review, reflect on, and consolidate their learning. This should link back to the learning objectives and assess understanding. Examples: exit ticket, quiz, "What? So What? Now What?" reflection, peer teaching, key points summary, self-assessment against objectives, question generation.

Additional Lesson Elements:
- Slide Structure: Each slide will focus on a specific aspect of the lesson, building progressively
- Activities: Integrate multiple, creative, and varied activities throughout. These should encourage active learning, critical thinking, collaboration, and application of knowledge relevant to Humanities:
  * History: Source analysis (primary/secondary), timeline creation, historical debate, role-playing historical figures, cause-and-effect mapping, historical empathy exercises, "What if?" scenarios
  * Geography: Map analysis, data interpretation (graphs, charts), fieldwork planning, environmental problem-solving, geographical inquiry questions, creating geographical models/diagrams, comparing different places
  * Religious Education: Ethical dilemmas discussion, comparing beliefs/practices, creating sacred space design, exploring symbolism, empathy exercises for different worldviews, researching religious festivals
  * Citizenship: Debates on current affairs, designing campaign posters, understanding rights and responsibilities, analyzing forms of government, community action planning, mock elections/parliaments
  * General Humanities: "Think-Pair-Share," "Four Corners," research tasks, presentations, creating infographics, concept mapping, "Jigsaw" activities, gallery walks
- Content Explanation: Provide clear, concise explanations of concepts, historical events, geographical processes, religious beliefs, or civic principles relevant to the lesson
- Curriculum Alignment: Ensure all content and activities are explicitly aligned with KS3 Humanities curriculum requirements (e.g., historical inquiry, geographical skills, understanding diverse beliefs, civic participation)
- Differentiation: Activities should be designed with inherent flexibility to cater to different learning styles and abilities
- Assessment: Activities should naturally lend themselves to formative assessment opportunities
- Extension/Homework: A final slide may offer suggestions for further exploration or homework
- Speaker Notes: Include brief speaker notes for slides to guide teachers
- Images: Include relevant images with placeholder URLs (e.g., '
- Speaker Notes: Include brief speaker notes for slides to guide teachers
- Images: Include relevant images with placeholder URLs (e.g., 'https://placehold.co/600x400') and descriptive captions where appropriate
- Tables: Where appropriate, include tables with headers and rows of data for organizing information

OUTPUT REQUIREMENTS:
- Each page must be a standalone JSON object on a single line
- Separate pages with two newline characters
- Do not add commentary or explanations
- Generate one transition page ("transition") per chapter
- Generate one content page ("content") for every section within the chapter
- Keep each text field under 100 words while remaining informative

TONE:
Professional, supportive, and encouraging. Knowledgeable and well-versed in the English national curriculum for KS3 Humanities (History, Geography, RE, Citizenship). Clear, concise, and engaging for a classroom setting.

Example (each JSON object on one line):
{"type": "transition", "data": {"title": "Starter Activity"}}

{"type": "content", "data": {"title": "What do you already know?", "items": [{"text": "Think-Pair-Share: What comes to mind when you hear 'The Norman Conquest'?", "type": "activity"}, {"text": "Share one fact or question with your partner", "type": "bullet"}]}}

{"type": "transition", "data": {"title": "Learning Objectives"}}

{"type": "content", "data": {"title": "What will we learn today?", "items": [{"text": "Understand the key events of the Norman Conquest", "type": "bullet"}, {"text": "Analyze primary sources from 1066", "type": "bullet"}, {"text": "Evaluate the impact on different groups in society", "type": "bullet"}]}}

{"type": "transition", "data": {"title": "Key Vocabulary"}}

{"type": "content", "data": {"title": "Important Words", "items": [{"text": "Conquest: When one group takes control of another by force", "type": "definition"}, {"text": "Dynasty: A series of rulers from the same family", "type": "definition"}, {"text": "Feudal System: A way of organizing society based on land ownership and loyalty", "type": "definition"}]}}

{"type": "content", "data": {"title": "Main Task: Source Analysis", "items": [{"text": "Step 1: Read the Bayeux Tapestry extract carefully (5 minutes)", "type": "instruction"}, {"text": "Step 2: Identify what the source tells us about the Battle of Hastings", "type": "instruction"}, {"text": "Step 3: Write three inferences with evidence (10 minutes)", "type": "instruction"}, {"text": "Success Criteria: Each inference should have a quote and explanation", "type": "criteria"}], "speaker_notes": "Support: Provide sentence starters. Extension: Compare with a written source from the same period. Circulate to check understanding of 'inference'."}}

{"type": "transition", "data": {"title": "Plenary"}}

{"type": "content", "data": {"title": "Exit Ticket", "items": [{"text": "Write down: One thing you learned today", "type": "bullet"}, {"text": "One question you still have", "type": "bullet"}, {"text": "How confident you feel about today's learning objectives (1-5)", "type": "bullet"}]}}

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
