#!/usr/bin/env node
/**
 * PPTist AI Backend API Test Script
 */

const BASE_URL = 'http://localhost:8000';

async function testHealth() {
  console.log('🔍 Testing health check...');
  try {
    const response = await fetch(`${BASE_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Health check passed');
      console.log(`Response: ${JSON.stringify(data)}`);
      return true;
    } else {
      console.log(`❌ Health check failed: ${response.status}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Connection failed: ${error.message}`);
    return false;
  }
}

async function testPPTOutline() {
  console.log('\n📝 Testing PPT outline generation...');
  
  const data = {
    model: 'gpt-4o-mini',
    language: 'English',
    content: 'Artificial Intelligence Applications in Education',
    stream: true
  };
  
  try {
    const response = await fetch(`${BASE_URL}/tools/aippt_outline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      console.log('✅ Outline generation request successful');
      console.log('📄 Generated outline content:');
      console.log('-'.repeat(50));
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        process.stdout.write(chunk);
      }
      
      console.log('\n' + '-'.repeat(50));
    } else {
      console.log(`❌ Outline generation failed: ${response.status}`);
      const errorText = await response.text();
      console.log(`Error message: ${errorText}`);
    }
  } catch (error) {
    console.log(`❌ Request failed: ${error.message}`);
  }
}

async function testPPTContent() {
  console.log('\n🎨 Testing PPT content generation...');
  
  // Sample outline
  const sampleOutline = `# Artificial Intelligence Applications in Education
## AI Education Overview
### Definition and Significance of AI in Education
- Application of AI technology in education
- Enhancing teaching effectiveness and learning experience
- Promoting educational modernization
### Development History of AI in Education
- Early exploration phase
- Technology breakthrough period
- Large-scale application period
## Specific Application Scenarios
### Personalized Learning
- Intelligent content recommendation
- Adaptive learning paths
- Learning effectiveness assessment`;
  
  const data = {
    model: 'gpt-4o-mini',
    language: 'English',
    content: sampleOutline,
    stream: true
  };
  
  try {
    const response = await fetch(`${BASE_URL}/tools/aippt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      console.log('✅ Content generation request successful');
      console.log('🎯 Generated PPT pages:');
      console.log('-'.repeat(50));
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let pageCount = 0;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          if (buffer.trim()) {
            pageCount++;
            console.log(`Page ${pageCount}:`);
            try {
              const pageData = JSON.parse(buffer.trim());
              console.log(JSON.stringify(pageData, null, 2));
            } catch {
              console.log(buffer.trim());
            }
            console.log('-'.repeat(30));
          }
          break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        // Split by double newlines
        const parts = buffer.split('\n\n');
        
        // Process all complete pages (all but the last part)
        for (let i = 0; i < parts.length - 1; i++) {
          if (parts[i].trim()) {
            pageCount++;
            console.log(`Page ${pageCount}:`);
            try {
              const pageData = JSON.parse(parts[i].trim());
              console.log(JSON.stringify(pageData, null, 2));
            } catch {
              console.log(parts[i].trim());
            }
            console.log('-'.repeat(30));
          }
        }
        
        // Keep the last incomplete part in the buffer
        buffer = parts[parts.length - 1];
      }
      
      console.log(`Total ${pageCount} pages generated`);
    } else {
      console.log(`❌ Content generation failed: ${response.status}`);
      const errorText = await response.text();
      console.log(`Error message: ${errorText}`);
    }
  } catch (error) {
    console.log(`❌ Request failed: ${error.message}`);
  }
}

async function main() {
  console.log('🧪 PPTist AI Backend API Test');
  console.log('='.repeat(50));
  
  // Test server connection
  const isHealthy = await testHealth();
  if (!isHealthy) {
    console.log('❌ Server is not running or cannot connect');
    console.log('Please start the server first: npm start');
    return;
  }
  
  // Test outline generation
  await testPPTOutline();
  
  // Wait before testing content generation
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test content generation
  await testPPTContent();
  
  console.log('\n🎉 Testing completed!');
}

main().catch(console.error);
