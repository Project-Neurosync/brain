# NeuroSync Technical Architecture & Data Flow Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Core Features](#core-features)
3. [Data Ingestion Pipeline](#data-ingestion-pipeline)
4. [AI Query Processing Flow](#ai-query-processing-flow)
5. [GitHub Integration Flow](#github-integration-flow)
6. [Storage Architecture](#storage-architecture)
7. [Search & Discovery Engine](#search--discovery-engine)
8. [Security & Privacy](#security--privacy)
9. [Performance & Scalability](#performance--scalability)
10. [API Reference](#api-reference)

---

## System Overview

NeuroSync is an AI-powered "Project Brain" that creates intelligent, contextual knowledge from your development workflow. It ingests data from multiple sources (GitHub, Jira, Slack, Confluence, meetings), applies ML-based importance filtering, and provides semantic search and AI assistance with deep project understanding.

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                          NeuroSync Platform                         │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js)     │  Backend (FastAPI)    │  AI Services      │
│  - Dashboard            │  - REST APIs          │  - OpenAI GPT-4    │
│  - Search Interface     │  - Authentication      │  - Embeddings      │
│  - Project Management   │  - Data Processing     │  - Intent Analysis │
├─────────────────────────────────────────────────────────────────────┤
│                        Data Processing Layer                        │
│  ML Intelligence        │  Semantic Search       │  Integration Hub  │
│  - Importance Scoring   │  - Vector Search       │  - GitHub API     │
│  - Timeline Storage     │  - Cross-Source        │  - Jira API       │
│  - Duplicate Detection  │  - Contextual Search   │  - Slack API      │
├─────────────────────────────────────────────────────────────────────┤
│                         Storage Layer                              │
│  PostgreSQL             │  ChromaDB (Vector)     │  Neo4j (Graph)    │
│  - User Data            │  - Semantic Embeddings │  - Relationships  │
│  - Projects             │  - Document Vectors    │  - Entity Links   │
│  - Metadata             │  - Search Indices      │  - Dependencies   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Features

### 1. **Multi-Source Data Ingestion**
- **GitHub Integration**: Repository scanning, commit tracking, PR analysis, issue processing
- **Jira Integration**: Issue ingestion, project management data, comment processing
- **Slack Integration**: Team communication, thread context, message processing
- **Confluence Integration**: Documentation ingestion, space management, page hierarchy
- **File Upload**: Direct file processing (PDF, DOCX, code files, batch processing)

### 2. **ML-Powered Data Intelligence**
- **Importance Scoring**: Multi-factor ML scoring (content quality, temporal relevance, author importance, project relevance, engagement, structural features)
- **Timeline-Based Storage**: Chronological organization with multi-tier storage (hot, warm, cold, frozen)
- **Duplicate Detection**: Content signature and semantic similarity-based deduplication
- **Context Relevance**: Project-specific relevance assessment with adaptive learning

### 3. **Advanced Search & Discovery**
- **Semantic Code Search**: Intent-based code search supporting 8+ categories (authentication, database, API, security, performance, error handling, testing, UI)
- **Cross-Source Search**: Unified search across code, docs, meetings, issues, comments
- **Contextual Search**: Context-aware search with proactive suggestions
- **Similar Code Detection**: Find similar patterns and implementations

### 4. **AI-Powered Project Brain**
- **Context Persistence**: Project memory across sessions
- **Multi-Source Knowledge Synthesis**: Connect code + meetings + tickets + docs
- **Code Architecture Understanding**: Dependency mapping, pattern recognition
- **Meeting Decision Tracking**: Extract and link decisions to code changes
- **Developer Onboarding**: Guided project walkthroughs

### 5. **Real-Time Collaboration**
- **WebSocket Integration**: Real-time updates and notifications
- **Live Notifications**: Data ingestion, mentions, project updates
- **Collaborative Features**: Shared project insights and team analytics

---

## Data Ingestion Pipeline

### High-Level Flow
```
Data Sources → Integration APIs → ML Processing → Storage → Search Indexing
     ↓              ↓               ↓            ↓           ↓
  GitHub         File Processing  Importance   Vector DB   Search Engine
  Jira           Content Extract  Scoring      Knowledge   AI Assistant
  Slack          Metadata Parse   Timeline     Graph       
  Confluence     Batch Process    Duplicate    PostgreSQL
  Files                          Detection
```

### Detailed Processing Steps

#### 1. **Data Collection**
```python
# Example: GitHub repository scanning
async def scan_repository(repo_url, project_id):
    # 1. Connect to GitHub API
    # 2. Scan repository structure
    # 3. Download file contents
    # 4. Extract metadata (language, size, modified date)
    # 5. Queue for processing
```

#### 2. **Content Processing**
```python
# File Processing Pipeline
async def process_file_batch(files, project_id):
    for file in files:
        # Extract content based on file type
        content = await extract_content(file)
        
        # Generate embeddings for semantic search
        embeddings = await generate_embeddings(content)
        
        # Apply ML importance scoring
        importance_score = await score_importance(content, project_context)
        
        # Detect duplicates
        is_duplicate = await detect_duplicate(content, project_id)
        
        if not is_duplicate and importance_score > threshold:
            # Store in multiple systems
            await store_in_vector_db(content, embeddings, metadata)
            await store_in_knowledge_graph(entities, relationships)
            await store_timeline_data(content, timeline_category)
```

#### 3. **ML Intelligence Processing**
```python
# ML Data Intelligence Pipeline
async def process_with_ml_intelligence(data_item, project_id):
    # Multi-factor importance scoring
    importance_analysis = {
        'content_quality': analyze_content_quality(data_item),
        'temporal_relevance': calculate_temporal_relevance(data_item),
        'author_importance': assess_author_importance(data_item),
        'project_relevance': calculate_project_relevance(data_item, project_id),
        'engagement_metrics': analyze_engagement(data_item),
        'structural_features': extract_structural_features(data_item)
    }
    
    # Calculate weighted importance score
    importance_score = calculate_weighted_score(importance_analysis)
    
    # Timeline categorization
    timeline_category = categorize_timeline(data_item.created_at)
    
    # Duplicate detection
    content_signature = generate_content_signature(data_item.content)
    semantic_similarity = calculate_semantic_similarity(data_item, existing_items)
    
    return {
        'importance_score': importance_score,
        'timeline_category': timeline_category,
        'is_duplicate': semantic_similarity > 0.85,
        'storage_tier': determine_storage_tier(importance_score, timeline_category)
    }
```

---

## AI Query Processing Flow

### When a User Asks a Question

#### 1. **Query Reception & Authentication**
```python
@router.post("/chat")
async def process_ai_query(request: ChatRequest, user: User = Depends(get_current_user)):
    # Validate user permissions for project
    # Log query for analytics
    # Initialize processing context
```

#### 2. **Intent Analysis & Query Enhancement**
```python
async def analyze_and_enhance_query(query, project_context):
    # Analyze query intent (code search, documentation, explanation, etc.)
    intent_analysis = await analyze_query_intent(query)
    
    # Extract technical terms and concepts
    technical_terms = extract_technical_terms(query)
    
    # Enhance query with synonyms and related terms
    enhanced_query = enhance_with_context(query, intent_analysis, technical_terms)
    
    return {
        'original_query': query,
        'enhanced_query': enhanced_query,
        'intent': intent_analysis,
        'search_strategy': determine_search_strategy(intent_analysis)
    }
```

#### 3. **Multi-Source Context Retrieval**
```python
async def retrieve_relevant_context(enhanced_query, project_id, search_strategy):
    # Parallel search across all data sources
    search_tasks = [
        semantic_search_code(enhanced_query, project_id),
        search_documentation(enhanced_query, project_id),
        search_meetings(enhanced_query, project_id),
        search_issues(enhanced_query, project_id),
        search_slack_messages(enhanced_query, project_id)
    ]
    
    # Execute searches in parallel
    search_results = await asyncio.gather(*search_tasks)
    
    # Merge and rank results
    merged_results = merge_and_rank_results(search_results, search_strategy)
    
    # Apply importance filtering
    filtered_results = filter_by_importance(merged_results, min_importance=0.3)
    
    return filtered_results[:20]  # Top 20 most relevant items
```

#### 4. **Knowledge Graph Context**
```python
async def get_relationship_context(entities, project_id):
    # Find related entities in knowledge graph
    related_entities = await neo4j_client.find_related_entities(entities, project_id)
    
    # Get entity relationships and dependencies
    relationships = await neo4j_client.get_entity_relationships(entities)
    
    # Build context graph
    context_graph = build_context_graph(entities, relationships)
    
    return context_graph
```

#### 5. **AI Response Generation**
```python
async def generate_ai_response(query, context_items, knowledge_graph, user_context):
    # Build comprehensive context for AI
    context_prompt = build_context_prompt(
        query=query,
        code_context=context_items['code'],
        documentation_context=context_items['docs'],
        meeting_context=context_items['meetings'],
        issue_context=context_items['issues'],
        relationship_context=knowledge_graph,
        user_role=user_context['role'],
        current_file=user_context.get('current_file'),
        recent_activity=user_context.get('recent_activity')
    )
    
    # Generate AI response with GPT-4
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": NEUROSYNC_SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt}
        ],
        temperature=0.1,
        max_tokens=2000
    )
    
    # Track token usage and costs
    await track_token_usage(user.id, response.usage)
    
    return response.choices[0].message.content
```

#### 6. **Response Enhancement & Learning**
```python
async def enhance_and_learn_from_response(query, response, context_items, user_feedback=None):
    # Store query-response pair for learning
    await store_query_response_pair(query, response, context_items)
    
    # Update search relevance based on user interaction
    if user_feedback:
        await update_relevance_scores(context_items, user_feedback)
    
    # Generate follow-up suggestions
    suggestions = await generate_followup_suggestions(query, response, context_items)
    
    return {
        'response': response,
        'suggestions': suggestions,
        'context_sources': [item['source'] for item in context_items],
        'confidence_score': calculate_confidence_score(context_items)
    }
```

---

## GitHub Integration Flow

### When You Commit New Code to GitHub

#### 1. **Webhook Reception**
```python
@router.post("/webhooks/github")
async def handle_github_webhook(request: Request):
    # Verify GitHub webhook signature
    # Parse webhook payload
    # Determine event type (push, pull_request, issues)
    
    if event_type == "push":
        await process_push_event(payload)
    elif event_type == "pull_request":
        await process_pr_event(payload)
```

#### 2. **Push Event Processing**
```python
async def process_push_event(payload):
    repository = payload['repository']
    commits = payload['commits']
    
    for commit in commits:
        # Get commit details
        commit_data = await github_client.get_commit(repository, commit['id'])
        
        # Process changed files
        for file_change in commit_data['files']:
            if file_change['status'] in ['added', 'modified']:
                # Download new/modified file content
                file_content = await github_client.get_file_content(
                    repository, file_change['filename'], commit['id']
                )
                
                # Queue for ML processing
                await queue_file_for_processing(file_content, repository, commit)
```

#### 3. **Automatic File Processing**
```python
async def process_new_commit_file(file_content, repository, commit):
    # Extract file metadata
    metadata = {
        'repository': repository['full_name'],
        'file_path': file_content['path'],
        'language': detect_language(file_content['path']),
        'commit_sha': commit['id'],
        'commit_message': commit['message'],
        'author': commit['author'],
        'timestamp': commit['timestamp']
    }
    
    # Apply ML importance scoring
    importance_analysis = await score_file_importance(
        content=file_content['content'],
        metadata=metadata,
        commit_context=commit
    )
    
    # Only process if important enough
    if importance_analysis['importance_score'] > 0.3:
        # Generate embeddings
        embeddings = await generate_embeddings(file_content['content'])
        
        # Store in vector database
        await vector_db.add_document(
            content=file_content['content'],
            embeddings=embeddings,
            metadata=metadata,
            importance_score=importance_analysis['importance_score']
        )
        
        # Update knowledge graph
        await update_knowledge_graph_with_code(file_content, metadata, commit)
        
        # Store in timeline
        await timeline_storage.store_timeline_data(
            data_item=file_content,
            timeline_category=TimelineCategory.RECENT,
            importance_level=importance_analysis['importance_level']
        )
```

#### 4. **Knowledge Graph Updates**
```python
async def update_knowledge_graph_with_code(file_content, metadata, commit):
    # Extract code entities (functions, classes, variables)
    code_entities = extract_code_entities(file_content['content'], metadata['language'])
    
    # Create/update nodes in Neo4j
    for entity in code_entities:
        await neo4j_client.create_or_update_node(
            label="CodeEntity",
            properties={
                'name': entity['name'],
                'type': entity['type'],  # function, class, variable
                'file_path': metadata['file_path'],
                'repository': metadata['repository'],
                'commit_sha': metadata['commit_sha']
            }
        )
    
    # Create relationships
    await create_code_relationships(code_entities, metadata)
    
    # Link to commit and author
    await link_commit_to_entities(commit, code_entities)
```

#### 5. **Real-Time Notifications**
```python
async def notify_project_members(repository, commit, processed_files):
    # Find project members subscribed to this repository
    project_members = await get_project_members_for_repo(repository['full_name'])
    
    # Send real-time notifications via WebSocket
    notification = {
        'type': 'code_update',
        'repository': repository['name'],
        'commit_message': commit['message'],
        'author': commit['author']['name'],
        'files_processed': len(processed_files),
        'timestamp': commit['timestamp']
    }
    
    for member in project_members:
        await websocket_manager.send_notification(member.id, notification)
```

---

## Storage Architecture

### Multi-Tier Storage System

#### 1. **PostgreSQL (Primary Database)**
```sql
-- Core data structures
Users (id, email, name, subscription_tier, token_quota, created_at)
Projects (id, name, description, owner_id, settings, created_at)
ProjectMembers (project_id, user_id, role, permissions, joined_at)
Subscriptions (id, user_id, plan, status, current_period_end)
TokenUsage (id, user_id, tokens_used, cost, timestamp, query_type)
```

#### 2. **ChromaDB (Vector Database)**
```python
# Document storage with embeddings
{
    "id": "doc_12345",
    "content": "def authenticate_user(token): ...",
    "embeddings": [0.1, 0.2, -0.3, ...],  # 384-dimensional vector
    "metadata": {
        "project_id": "proj_123",
        "source_type": "github",
        "file_path": "/auth/authentication.py",
        "language": "python",
        "importance_score": 0.85,
        "timeline_category": "recent",
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

#### 3. **Neo4j (Knowledge Graph)**
```cypher
// Entity and relationship storage
CREATE (f:Function {name: "authenticate_user", file: "/auth/auth.py"})
CREATE (c:Class {name: "AuthManager", file: "/auth/manager.py"})
CREATE (p:Project {name: "MyProject", id: "proj_123"})
CREATE (u:User {name: "John Doe", role: "developer"})

// Relationships
CREATE (f)-[:BELONGS_TO]->(c)
CREATE (f)-[:PART_OF]->(p)
CREATE (u)-[:AUTHORED]->(f)
CREATE (f)-[:CALLS]->(other_function)
```

#### 4. **Timeline Storage (Multi-Tier)**
```python
# Hot Storage (Recent - Last 7 days)
hot_storage = {
    "retention_days": 7,
    "access_frequency": "high",
    "storage_tier": "ssd",
    "importance_threshold": 0.3
}

# Warm Storage (Last Month)
warm_storage = {
    "retention_days": 30,
    "access_frequency": "medium", 
    "storage_tier": "ssd",
    "importance_threshold": 0.5
}

# Cold Storage (Last Quarter)
cold_storage = {
    "retention_days": 90,
    "access_frequency": "low",
    "storage_tier": "hdd",
    "importance_threshold": 0.7
}

# Frozen Storage (Historical)
frozen_storage = {
    "retention_days": 365,
    "access_frequency": "rare",
    "storage_tier": "archive",
    "importance_threshold": 0.8
}
```

---

## Search & Discovery Engine

### Semantic Search Pipeline

#### 1. **Query Processing**
```python
async def process_search_query(query, search_type, filters):
    # Step 1: Analyze query intent
    intent_analysis = await analyze_query_intent(query)
    
    # Step 2: Enhance query with technical terms
    enhanced_query = await enhance_query_with_context(query, intent_analysis)
    
    # Step 3: Generate query embeddings
    query_embeddings = await generate_embeddings(enhanced_query)
    
    # Step 4: Execute vector search
    vector_results = await vector_db.similarity_search(
        query_embeddings, 
        filters=filters,
        top_k=100
    )
    
    # Step 5: Apply additional filtering
    filtered_results = await apply_search_filters(vector_results, filters)
    
    # Step 6: Rank results using multi-factor scoring
    ranked_results = await rank_search_results(
        filtered_results, query, intent_analysis
    )
    
    return ranked_results[:20]  # Return top 20 results
```

#### 2. **Multi-Factor Ranking Algorithm**
```python
def calculate_result_score(result, query, intent_analysis):
    # Base vector similarity score (0.0 - 1.0)
    vector_score = result['similarity_score']
    
    # Term overlap score
    term_overlap = calculate_term_overlap(query, result['content'])
    
    # Intent matching score
    intent_match = calculate_intent_match(intent_analysis, result['metadata'])
    
    # Importance boost
    importance_boost = result['metadata']['importance_score'] * 0.2
    
    # Recency boost
    recency_boost = calculate_recency_boost(result['metadata']['created_at'])
    
    # Language/file type preference
    type_preference = calculate_type_preference(result['metadata'], user_preferences)
    
    # Weighted final score
    final_score = (
        vector_score * 0.4 +
        term_overlap * 0.2 +
        intent_match * 0.2 +
        importance_boost +
        recency_boost +
        type_preference * 0.1
    )
    
    return min(final_score, 1.0)  # Cap at 1.0
```

#### 3. **Cross-Source Search**
```python
async def cross_source_search(query, project_id, content_types):
    # Execute parallel searches across different content types
    search_tasks = []
    
    if ContentType.CODE in content_types:
        search_tasks.append(search_code_content(query, project_id))
    
    if ContentType.DOCUMENTATION in content_types:
        search_tasks.append(search_documentation(query, project_id))
    
    if ContentType.MEETING in content_types:
        search_tasks.append(search_meetings(query, project_id))
    
    if ContentType.ISSUE in content_types:
        search_tasks.append(search_issues(query, project_id))
    
    if ContentType.SLACK_MESSAGE in content_types:
        search_tasks.append(search_slack_messages(query, project_id))
    
    # Execute all searches in parallel
    search_results = await asyncio.gather(*search_tasks)
    
    # Merge results from different sources
    merged_results = merge_cross_source_results(search_results)
    
    # Apply cross-source ranking
    ranked_results = rank_cross_source_results(merged_results, query)
    
    return ranked_results
```

---

## Security & Privacy

### Data Protection Measures

#### 1. **Authentication & Authorization**
```python
# JWT-based authentication
@router.post("/login")
async def login(credentials: LoginRequest):
    user = await authenticate_user(credentials.email, credentials.password)
    if user:
        access_token = create_access_token(user.id)
        return {"access_token": access_token, "token_type": "bearer"}

# Role-based access control
async def check_project_permission(user_id: str, project_id: str, permission: str):
    member = await get_project_member(project_id, user_id)
    return member and permission in member.permissions
```

#### 2. **Data Isolation**
```python
# Project-based data isolation
async def get_user_accessible_data(user_id: str, project_id: str):
    # Verify user has access to project
    if not await check_project_access(user_id, project_id):
        raise PermissionDenied("Access denied to project")
    
    # Return only data belonging to accessible projects
    return await get_project_data(project_id)
```

#### 3. **Data Encryption**
```python
# Encrypt sensitive data at rest
class EncryptedField:
    def __init__(self, value: str):
        self.encrypted_value = encrypt_data(value, ENCRYPTION_KEY)
    
    def decrypt(self) -> str:
        return decrypt_data(self.encrypted_value, ENCRYPTION_KEY)

# API keys and tokens are encrypted
integration_config = {
    "github_token": EncryptedField(github_token),
    "jira_api_key": EncryptedField(jira_key)
}
```

#### 4. **Audit Logging**
```python
async def log_data_access(user_id: str, action: str, resource: str, project_id: str):
    audit_log = {
        "user_id": user_id,
        "action": action,  # "read", "write", "delete"
        "resource": resource,
        "project_id": project_id,
        "timestamp": datetime.utcnow(),
        "ip_address": get_client_ip(),
        "user_agent": get_user_agent()
    }
    await store_audit_log(audit_log)
```

---

## Performance & Scalability

### Performance Optimizations

#### 1. **Async Processing**
```python
# All I/O operations are async
async def process_large_dataset(items):
    # Process in batches to avoid memory issues
    batch_size = 100
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        await asyncio.gather(*[process_item(item) for item in batch])
```

#### 2. **Caching Strategy**
```python
# Redis caching for frequently accessed data
@cache(expire=3600)  # Cache for 1 hour
async def get_project_metadata(project_id: str):
    return await database.fetch_project(project_id)

# Vector search result caching
@cache(expire=1800)  # Cache for 30 minutes
async def cached_vector_search(query_hash: str, filters: dict):
    return await vector_db.similarity_search(query_hash, filters)
```

#### 3. **Database Optimization**
```sql
-- Optimized database indices
CREATE INDEX idx_documents_project_importance ON documents(project_id, importance_score DESC);
CREATE INDEX idx_documents_timeline ON documents(project_id, created_at DESC);
CREATE INDEX idx_vector_similarity ON vector_embeddings USING ivfflat (embedding vector_cosine_ops);
```

#### 4. **Background Processing**
```python
# Celery for background tasks
@celery.task
async def process_repository_scan(repo_url: str, project_id: str):
    # Long-running repository scanning happens in background
    await scan_and_process_repository(repo_url, project_id)

# Real-time updates via WebSocket
async def notify_scan_progress(project_id: str, progress: int):
    await websocket_manager.broadcast_to_project(
        project_id, 
        {"type": "scan_progress", "progress": progress}
    )
```

### Scalability Measures

#### 1. **Horizontal Scaling**
```yaml
# Docker Compose scaling
version: '3.8'
services:
  api:
    image: neurosync-api
    deploy:
      replicas: 3  # Multiple API instances
  
  worker:
    image: neurosync-worker
    deploy:
      replicas: 5  # Multiple background workers
```

#### 2. **Load Balancing**
```python
# Load balancer configuration
upstream neurosync_api {
    server api1:8000 weight=1;
    server api2:8000 weight=1;
    server api3:8000 weight=1;
}
```

---

## API Reference

### Authentication Endpoints
```python
POST /api/v1/auth/register     # User registration
POST /api/v1/auth/login        # User login
POST /api/v1/auth/refresh      # Token refresh
POST /api/v1/auth/logout       # User logout
```

### Project Management
```python
GET    /api/v1/projects                    # List user projects
POST   /api/v1/projects                    # Create new project
GET    /api/v1/projects/{project_id}       # Get project details
PUT    /api/v1/projects/{project_id}       # Update project
DELETE /api/v1/projects/{project_id}       # Delete project
POST   /api/v1/projects/{project_id}/invite # Invite user to project
```

### Data Ingestion
```python
POST /api/v1/data/upload                   # Upload files
POST /api/v1/data/sync                     # Trigger data sync
GET  /api/v1/data/sync/{sync_id}/status    # Check sync status
```

### Integration Management
```python
GET    /api/v1/integrations                # List available integrations
POST   /api/v1/integrations/connect        # Connect integration
GET    /api/v1/integrations/{integration_id}/test # Test connection
POST   /api/v1/integrations/{integration_id}/sync # Trigger sync
```

### Search & Discovery
```python
POST /api/v1/search/semantic-code          # Semantic code search
POST /api/v1/search/cross-source           # Cross-source search
POST /api/v1/search/contextual             # Contextual search
POST /api/v1/search/similar-code           # Similar code search
GET  /api/v1/search/suggestions/{project_id} # Search suggestions
GET  /api/v1/search/history/{project_id}   # Search history
```

### AI Chat
```python
POST /api/v1/chat                          # Send message to AI
GET  /api/v1/chat/history/{project_id}     # Get chat history
POST /api/v1/chat/feedback                 # Provide feedback on response
```

### ML Intelligence
```python
POST /api/v1/ml/score-importance           # Score data importance
POST /api/v1/ml/detect-duplicates          # Detect duplicate content
POST /api/v1/ml/timeline-storage           # Store timeline data
GET  /api/v1/ml/analytics/{project_id}     # Get ML analytics
POST /api/v1/ml/feedback                   # Provide learning feedback
```

### Admin Dashboard
```python
GET  /api/v1/admin/users                   # List all users
GET  /api/v1/admin/projects                # List all projects
GET  /api/v1/admin/analytics               # System analytics
POST /api/v1/admin/users/{user_id}/suspend # Suspend user
```

---

## Data Flow Summary

### Complete Data Journey

1. **Data Ingestion**: GitHub commits, Jira issues, Slack messages, uploaded files
2. **ML Processing**: Importance scoring, duplicate detection, timeline categorization
3. **Storage**: Vector embeddings, knowledge graph entities, timeline data
4. **Search Indexing**: Semantic search preparation, faceted search indices
5. **AI Context**: Multi-source context retrieval for AI responses
6. **User Interaction**: Search results, AI responses, collaborative insights
7. **Learning Loop**: User feedback improves relevance and importance scoring

### Real-Time Processing
- **GitHub Webhooks**: Instant processing of new commits and PRs
- **WebSocket Updates**: Real-time notifications and progress updates
- **Background Jobs**: Async processing of large datasets
- **Cache Invalidation**: Smart cache updates for fresh data

### Intelligence Layer
- **Context Building**: Multi-source knowledge synthesis
- **Pattern Recognition**: Code similarity and architecture understanding
- **Decision Tracking**: Meeting decisions linked to code changes
- **Predictive Insights**: Proactive suggestions based on user behavior

---

This documentation provides a comprehensive overview of NeuroSync's technical architecture, data processing flows, and feature capabilities. The system is designed for scalability, security, and intelligent knowledge management across the entire development lifecycle.
