Let's create example configurations for different use cases to help users understand how to adapt the system to their specific needs.

# Example Configurations for Different Use Cases

This document provides practical example configurations for various use cases of the Thought Processing System. Each example includes the necessary YAML configurations and explanations of how to adapt the system for specific scenarios.

## Table of Contents

1. [Basic Note-Taking System](#basic-note-taking-system)
2. [Academic Research Assistant](#academic-research-assistant)
3. [Content Creation Workflow](#content-creation-workflow)
4. [Project Management Assistant](#project-management-assistant)
5. [Personal Knowledge Management](#personal-knowledge-management)

## Basic Note-Taking System

This configuration sets up a simple system for capturing and processing personal notes with minimal agents and local LLM support.

### Configuration Files

wow this ai is a mess. 

**config.yaml**
```yaml
app:
  name: "Simple Note Processor"
  log_level: "INFO"
  log_dir: "./logs"
  data_dir: "./notes"
  output_format: "markdown"

processing:
  auto_process: true
  notification: true
  backup: true
  backup_dir: "./backups"
```

**agents.yaml**
```yaml
crew:
  name: "Note Taking Crew"
  description: "A minimal crew for processing personal notes"
  
agents:
  capture:
    name: "Capture Agent"
    description: "Captures and processes initial notes"
    llm_config: "ollama_llama3"
    prompts:
      default: |
        You are a helpful assistant that processes raw notes.
        Please organize the following note, correct any spelling errors, and format it nicely:
        
        {input}
  
  clarify:
    name: "Clarify Agent"
    description: "Clarifies and expands notes when needed"
    llm_config: "ollama_llama3"
    prompts:
      default: |
        Review this note and identify any unclear or ambiguous parts.
        Then, expand on those parts to make the note more comprehensive:
        
        {input}
```

**llms.yaml**
```yaml
llms:
  default: "ollama_llama3"
  
  ollama_llama3:
    provider: "ollama"
    model: "llama3"
    temperature: 0.3
    max_tokens: 2000
```

## Academic Research Assistant

This configuration creates a comprehensive research assistant with advanced models for deep analysis and specialized academic tasks.

### Configuration Files

**config.yaml**
```yaml
app:
  name: "Academic Research Assistant"
  log_level: "INFO"
  log_dir: "./logs"
  data_dir: "./research_data"
  output_format: "markdown"
  citation_style: "APA"

processing:
  auto_process: true
  notification: true
  backup: true
  backup_dir: "./research_backups"
  
integrations:
  zotero:
    enabled: true
    api_key: "${ZOTERO_API_KEY}"
    library_id: "${ZOTERO_LIBRARY_ID}"
```

**agents.yaml**
```yaml
crew:
  name: "Research Crew"
  description: "Advanced crew for academic research assistance"
  
agents:
  literature_review:
    name: "Literature Review Agent"
    description: "Analyzes academic papers and creates summaries"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        You are an expert academic researcher.
        Please analyze the following paper extract and provide:
        1. A concise summary of key findings
        2. The methodology used
        3. Limitations acknowledged
        4. How this connects to the broader literature
        
        PAPER:
        {input}
  
  hypothesis_generator:
    name: "Hypothesis Generator"
    description: "Generates research hypotheses based on literature gaps"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Based on the following literature review, identify 3-5 potential research
        hypotheses that address gaps in the current understanding:
        
        LITERATURE REVIEW:
        {input}
  
  methodology_designer:
    name: "Methodology Designer"
    description: "Designs research methodologies to test hypotheses"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        For the following research hypothesis, design an appropriate research methodology:
        1. Outline the approach (qualitative, quantitative, mixed)
        2. Suggest data collection methods
        3. Recommend analysis techniques
        4. Address potential limitations
        
        HYPOTHESIS:
        {input}
  
  citation_formatter:
    name: "Citation Formatter"
    description: "Formats citations according to academic styles"
    llm_config: "ollama_llama3"
    prompts:
      default: |
        Format the following reference information into proper {citation_style} style:
        
        {input}
```

**llms.yaml**
```yaml
llms:
  default: "openai_gpt4"
  
  openai_gpt4:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.1
    max_tokens: 8000
    api_key: "${OPENAI_API_KEY}"
  
  anthropic_claude:
    provider: "anthropic"
    model: "claude-3-opus-20240229"
    temperature: 0.2
    max_tokens: 10000
    api_key: "${ANTHROPIC_API_KEY}"
    
  ollama_llama3:
    provider: "ollama"
    model: "llama3"
    temperature: 0.3
    max_tokens: 4000
```

## Content Creation Workflow

This configuration sets up a system optimized for content creators who need help with ideation, drafting, and publication preparation.

### Configuration Files

**config.yaml**
```yaml
app:
  name: "Content Creation System"
  log_level: "INFO"
  log_dir: "./logs"
  data_dir: "./content"
  output_format: "markdown"

processing:
  auto_process: true
  notification: true
  backup: true
  backup_dir: "./content_backups"
  
integrations:
  wordpress:
    enabled: true
    api_url: "${WP_API_URL}"
    username: "${WP_USERNAME}"
    app_password: "${WP_APP_PASSWORD}"
```

**agents.yaml**
```yaml
crew:
  name: "Content Creation Crew"
  description: "Specialized crew for content creation and publication"
  
agents:
  idea_generator:
    name: "Idea Generator"
    description: "Generates content ideas based on topics and trends"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Based on the following topic area and target audience, generate 5 compelling content ideas:
        
        TOPIC: {topic}
        AUDIENCE: {audience}
        
        For each idea, provide:
        1. A catchy title
        2. A brief description (1-2 sentences)
        3. Key points to cover
  
  outliner:
    name: "Content Outliner"
    description: "Creates detailed outlines for content"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        Create a detailed outline for the following content idea:
        
        TITLE: {title}
        DESCRIPTION: {description}
        
        The outline should include:
        1. Introduction with hook
        2. Main sections with subpoints
        3. Conclusion with call to action
  
  drafter:
    name: "Content Drafter"
    description: "Writes first drafts based on outlines"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Based on the following outline, write a first draft of the content.
        Maintain a {tone} tone and aim for approximately {word_count} words:
        
        OUTLINE:
        {input}
  
  editor:
    name: "Content Editor"
    description: "Edits and refines draft content"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Edit and improve the following content draft:
        1. Check for clarity and flow
        2. Enhance language and style
        3. Ensure consistency
        4. Correct any grammatical or spelling errors
        
        DRAFT:
        {input}
  
  seo_optimizer:
    name: "SEO Optimizer"
    description: "Optimizes content for search engines"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        Optimize the following content for SEO:
        1. Suggest a SEO-friendly title
        2. Provide meta description
        3. Recommend keyword density adjustments
        4. Suggest internal and external linking opportunities
        
        TARGET KEYWORDS: {keywords}
        
        CONTENT:
        {input}
```

**llms.yaml**
```yaml
llms:
  default: "anthropic_claude"
  
  anthropic_claude:
    provider: "anthropic"
    model: "claude-3-opus-20240229"
    temperature: 0.7
    max_tokens: 12000
    api_key: "${ANTHROPIC_API_KEY}"
  
  openai_gpt4:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.6
    max_tokens: 8000
    api_key: "${OPENAI_API_KEY}"
```

## Project Management Assistant

This configuration creates a system for managing projects, tracking tasks, and facilitating team collaboration.

### Configuration Files

**config.yaml**
```yaml
app:
  name: "Project Management Assistant"
  log_level: "INFO"
  log_dir: "./logs"
  data_dir: "./projects"
  output_format: "markdown"

processing:
  auto_process: true
  notification: true
  backup: true
  backup_dir: "./project_backups"
  
integrations:
  github:
    enabled: true
    api_key: "${GITHUB_API_KEY}"
    repository: "${GITHUB_REPOSITORY}"
  
  jira:
    enabled: true
    url: "${JIRA_URL}"
    username: "${JIRA_USERNAME}"
    api_token: "${JIRA_API_TOKEN}"
```

**agents.yaml**
```yaml
crew:
  name: "Project Management Crew"
  description: "Specialized crew for project management tasks"
  
agents:
  requirements_analyzer:
    name: "Requirements Analyzer"
    description: "Analyzes and structures project requirements"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        Analyze the following project requirements:
        1. Identify clear requirements vs. ambiguous ones
        2. Categorize requirements (functional, non-functional)
        3. Highlight potential dependencies
        4. Flag any potential risks or contradictions
        
        REQUIREMENTS:
        {input}
  
  task_breaker:
    name: "Task Breakdown Agent"
    description: "Breaks down requirements into actionable tasks"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Break down the following requirement into specific, actionable tasks:
        1. Create individual task descriptions
        2. Estimate effort (Low/Medium/High)
        3. Identify dependencies between tasks
        4. Suggest task assignee roles
        
        REQUIREMENT:
        {input}
  
  meeting_summarizer:
    name: "Meeting Summarizer"
    description: "Creates concise summaries of project meetings"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        Summarize the following meeting transcript:
        1. Key decisions made
        2. Action items (with owners if mentioned)
        3. Important discussions
        4. Open questions or issues
        
        TRANSCRIPT:
        {input}
  
  status_reporter:
    name: "Status Report Generator"
    description: "Generates project status reports"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Generate a project status report based on the following updates:
        1. Overall status (On track/At risk/Off track)
        2. Key accomplishments
        3. Current challenges
        4. Next steps
        5. Resource needs
        
        UPDATES:
        {input}
```

**llms.yaml**
```yaml
llms:
  default: "openai_gpt4"
  
  openai_gpt4:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.2
    max_tokens: 8000
    api_key: "${OPENAI_API_KEY}"
  
  anthropic_claude:
    provider: "anthropic"
    model: "claude-3-sonnet-20240229"
    temperature: 0.3
    max_tokens: 8000
    api_key: "${ANTHROPIC_API_KEY}"
  
  ollama_llama3:
    provider: "ollama"
    model: "llama3"
    temperature: 0.4
    max_tokens: 4000
```

## Personal Knowledge Management

This configuration creates a system for managing personal knowledge, integrating with note-taking apps, and building a knowledge graph.

### Configuration Files

**config.yaml**
```yaml
app:
  name: "Personal Knowledge Manager"
  log_level: "INFO"
  log_dir: "./logs"
  data_dir: "./knowledge_base"
  output_format: "markdown"

processing:
  auto_process: true
  notification: true
  backup: true
  backup_dir: "./kb_backups"
  
integrations:
  obsidian:
    enabled: true
    vault_path: "${OBSIDIAN_VAULT_PATH}"
  
  readwise:
    enabled: true
    api_key: "${READWISE_API_KEY}"
```

**agents.yaml**
```yaml
crew:
  name: "Knowledge Management Crew"
  description: "Specialized crew for personal knowledge management"
  
agents:
  capture:
    name: "Capture Agent"
    description: "Processes raw notes and highlights"
    llm_config: "ollama_llama3"
    prompts:
      default: |
        Process the following raw note/highlight:
        1. Clean up formatting
        2. Fix any obvious errors
        3. Preserve all important information
        
        INPUT:
        {input}
  
  summarizer:
    name: "Summary Agent"
    description: "Creates concise summaries of longer content"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Create a concise summary of the following content:
        1. Main ideas (3-5 bullet points)
        2. Key insights
        3. Potential applications
        
        CONTENT:
        {input}
  
  connector:
    name: "Connection Agent"
    description: "Identifies connections between knowledge items"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        Analyze this note and identify potential connections:
        1. Related concepts already in the knowledge base
        2. Suggested tags/categories
        3. Recommended backlinks
        
        KNOWLEDGE BASE CONTEXT:
        {context}
        
        NOTE TO ANALYZE:
        {input}
  
  question_answerer:
    name: "Question Answering Agent"
    description: "Answers questions based on knowledge base"
    llm_config: "anthropic_claude"
    prompts:
      default: |
        Answer the following question based ONLY on the provided knowledge base extracts:
        
        QUESTION: {question}
        
        KNOWLEDGE BASE EXTRACTS:
        {context}
        
        If the answer cannot be determined from the provided information, clearly state that.
  
  knowledge_graph:
    name: "Knowledge Graph Agent"
    description: "Updates and maintains the knowledge graph"
    llm_config: "openai_gpt4"
    prompts:
      default: |
        Based on this new piece of information, update the knowledge graph:
        1. Identify new entities
        2. Establish relationships between entities
        3. Update properties of existing entities
        
        CURRENT KNOWLEDGE GRAPH EXCERPT:
        {context}
        
        NEW INFORMATION:
        {input}
```

**llms.yaml**
```yaml
llms:
  default: "anthropic_claude"
  
  anthropic_claude:
    provider: "anthropic"
    model: "claude-3-opus-20240229"
    temperature: 0.3
    max_tokens: 10000
    api_key: "${ANTHROPIC_API_KEY}"
  
  openai_gpt4:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.2
    max_tokens: 8000
    api_key: "${OPENAI_API_KEY}"
  
  ollama_llama3:
    provider: "ollama"
    model: "llama3"
    temperature: 0.2
    max_tokens: 4000
```

## Implementation Notes

### How to Use These Configurations

1. **Copy and Adapt**: Copy the relevant configurations to your setup and adapt them to your specific needs
2. **Environment Variables**: Replace values in `${...}` with actual values or set up environment variables
3. **LLM Selection**: Choose LLMs based on your specific needs and budget
4. **Prompt Customization**: Modify the prompts to better match your specific use case

### Configuration Tips

- **Start Simple**: Begin with a minimal configuration and add complexity as needed
- **Test Prompts**: Test each agent's prompts individually before integrating them
- **Balance Local and Remote**: Use local models for less complex tasks and remote models for advanced reasoning
- **Consider Resource Constraints**: Be mindful of token limits and API costs when configuring LLMs

### Integration Guidance

For integrations with external systems, you'll need to:

1. Configure API keys in your `.env` file
2. Set up appropriate permissions for the APIs
3. Create integration handlers in the `integrations` directory
4. Test connections before production use