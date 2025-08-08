
# 🛠️ Backend Implementation Plan for KTFlow MVP

## 📌 Tech Stack
- Language: TypeScript / Node.js
- Framework: Express.js / NestJS (recommended)
- Database: PostgreSQL (via Prisma ORM)
- Auth: Clerk (via JWT)
- Deployment: Vercel Functions / Railway / Render
- APIs: GitHub, Jira, Google Meet / Readai

---

## 🧩 Feature Modules (Modular by Domain)

### 1. Auth Module
- Integrate Clerk
- Middleware to extract JWT & user roles
- Guard routes for org/project roles (Admin, Editor, Viewer)

### 2. Organization & Project Management
- Create org → auto-create default workspace
- Create project under org
- Add/invite members with roles
- CRUD: org/project/member tables

### 3. GitHub/Jira Integration
- Setup OAuth/token storage for GitHub/Jira
- Webhook endpoints:
  - GitHub: PR, Issue, Comment, Commit push
  - Jira: Ticket updated/created
- Store updates in updates table

### 4. Documentation & AI Assistant
- Doc table: section-based project knowledge
- LLM endpoint:
  - Query + context retrieval (RAG)
  - Embedding generation
  - Chat message storage
- Update docs via:
  - Chat-generated answer
  - Manual edit interface

### 5. Meeting Transcripts
- Upload transcript / fetch via Readai or Google Meet
- Extract:
  - Project name
  - Tasks / decisions / repo mentions
- Save meeting summary row

### 6. Chat Module
- Project chat room endpoint
- Messages: prompt + response
- Store chat history with vector reference

### 7. Timeline / Updates
- Endpoint to retrieve updates per project
- Merge: GitHub + Jira + transcript items
- Categorized by source & timestamp

### 8. Payments & Subscription
- Stripe integration
- Plans: Free / Org+ / Enterprise
- Add plan & usage table
- Webhooks: stripe.subscription.created, updated, deleted
- Restrict org/project features based on plan

---

## 📁 Folder Structure Suggestion (NestJS)
```
/src
  /auth
  /org
  /project
  /docs
  /chat
  /webhook
  /meeting
  /subscription
  /common (guards, middlewares, dtos)
```

---

## 📅 Timeline Suggestion (15 Days Backend MVP)
| Day | Task |
|-----|------|
| 1-2 | Setup project, DB schema, Clerk Auth |
| 3-4 | Org/project/member routes |
| 5-6 | GitHub/Jira webhook + storage |
| 7-8 | Chat API + vector store prep |
| 9-10| Meeting transcript parser, doc write API |
| 11  | Timeline API (merged events) |
| 12-13| Stripe integration |
| 14-15| Internal test + bug fixes + Postman export |
