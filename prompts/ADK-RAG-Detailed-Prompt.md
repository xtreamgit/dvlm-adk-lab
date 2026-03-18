# **Detailed Prompt**

You are a senior Google Cloud Architect, Security Architect, and AI Application Engineer. Design and implement a production-ready, cloud-native Google ADK RAG application on Google Cloud that integrates authentication and authorization using Google Identity, Google Cloud Identity Groups, and Identity-Aware Proxy (IAP) with OAuth 2.0.

You are a **Senior Google Cloud Architect, Security Architect, and AI Application Engineer**.

Design and implement a **production-ready, cloud-native Google ADK RAG application** on Google Cloud that integrates:

* Google Identity  
* Google Cloud Identity Groups  
* Identity-Aware Proxy (IAP)  
* Vertex AI  
* Google Cloud Model Armor

**Build an Agentic RAG solution that allows the users to access these agent tools:** 

* **add\_data,**  
* **browse\_documents,**   
* **create\_corpus,**   
* **delete\_corpus,**   
* **delete\_document,**   
* **get\_corpus\_info,**   
* **rag\_multi\_query,**  
* **list\_corpora,**  
* **retrieve\_document,**   
* **rag\_query, and**   
* **set\_current\_corpus.**

The application already has its core RAG functionality inside the /ref-code folder in the root directory of the project. 

The complete application and any of the Google Resources will be completely new and none of the Google services will be overwritten or deleted.

Your task is to design and implement the missing:

* authentication  
* authorization  
* access-control  
* LLM safety protections  
* runtime security enforcement

so the application can securely support **hundreds of enterprise users** interacting with **team knowledge bases via AI agents**.

## **Business Goal**

Build a secure enterprise RAG application where authenticated users can access the app, use only the corpora they are authorized to access, and invoke only the agents they are allowed to use. The security model must be based on Google identity and group membership, and must support scalable access management through groups instead of hard-coded per-user permissions.

## **Core Access Model**

Implement three distinct access-control layers:

### **1\. Application Access**

This is the first level of access.

A user must first be authorized to access the application itself through Google Identity and IAP. Only users or groups explicitly granted access to the IAP-protected web application may enter the app. IAP acts as the front door and central authorization layer for HTTPS applications. The design must use IAP-secured web app access with Google OAuth 2.0.

### **2\. Corpora Access**

This is the second level of access.

A user can only view, search, upload, modify, delete, or otherwise manage documents in corpora that are mapped to groups the user belongs to.

Corpora access must be assigned by Google IAM group membership, not by hard-coded user checks. By default, users must be assigned to one corpus group called **adk-rag-default-corpus**.

Each corpus is associated with a separate Google Cloud Storage bucket. The user will have access to at least one bucket called **adk-rag-default-corpus-bucket**. For testing purposes, the adk-rag-default-corpus-bucket will contain the documents included in the /data folder in the root of the project.

The system must support:

* users belonging to one or more groups  
* corpora mapped to one or more groups  
* users gaining corpus access through Google IAM group membership  
* document-management tools being restricted based on agent group assignment  
* read-only vs write/manage permissions where appropriate

The solution should treat the application’s authorization structure as the policy decision layer for corpus access, while Google Identity / Cloud Identity Groups remain the source of truth for membership.

### **3\. Agent Access**

This is the third level of access.

Agents are AI action code units built with Google ADK. An agent has access to a collection of tools that can manipulate or manage corpora and answer user questions. In ADK, agents are self-contained execution units that can use tools and coordinate actions. Tools are structured programming functions callable by agents.

A user can only invoke an agent if they belong to the corresponding agent-group.

Each agent-group grants access to one or more agents.

Each agent exposes one or more tools.

Each tool must enforce authorization at runtime so that even if a user can access the agent, the tool only operates on corpora that the user is allowed to use.

### Agent Groups

The user will have access to at least one agent group called **adk-rag-viewer-agent**. 

There will be 4 default agent groups:

Display name			Google Group Name 

1. admin-agent			adk-rag-admin-agent  
2. content-manager-agent	adk-rag-content-manager-agent  
3. contributor-agent		adk-rag-contributor-agent  
4. viewer-agent			adk-rag-viewer-agent (All users will be assigned to this group)

### Agent Tools

admin-group \-		

 rag\_query, list\_corpora, get\_corpus\_info, browse\_documents, add\_data, create\_corpus, delete\_document, delete\_corpus, download\_document, multi\_corpora\_query, set\_current\_corpus

Content-manager-group \- 	

rag\_query, list\_corpora, get\_corpus\_info, browse\_documents, add\_data, delete\_document, download\_document, multi\_corpora\_query, set\_current\_corpus

Contributor-group \- 	

rag\_query, list\_corpora, get\_corpus\_info, browse\_documents, add\_data,  multi\_corpora\_query, set\_current\_corpus

viewer-group \- 		

rag\_query, list\_corpora, get\_corpus\_info, browse\_documents, multi\_corpora\_query, set\_current\_corpus

## **Functional Intent**

The purpose of the IAM model is to allow authenticated users to safely use one or more agents that can perform tool-defined actions against only the corpora they are authorized to access and modify.

The system must ensure:

* a user can sign in only if allowed into the app  
* a user can see only the corpora they are allowed to use  
* a user can invoke only the agents assigned to them through agent-group membership  
* every agent tool call is validated against the user’s corpus and agent entitlements  
* authorization is enforced server-side, never only in the UI

## **Technical Requirements**

Use Google Identity and IAP with OAuth 2.0 for user authentication to the web application. IAP supports application-layer access control for HTTPS apps, and custom OAuth client configuration can be used when needed. The design should use IAP headers or verified identity tokens to identify the authenticated user on the backend.

Use Google Cloud Identity Groups or Google Groups as the identity grouping mechanism for:

* app-access groups  
* corpora-access groups  
* agent-access groups

The application must be fully cloud native and scalable to hundreds of internal users. It also uses load balancing.

The application should run on Google Cloud using a modern managed hosting platform such as Cloud Run. The architecture must prefer managed services and least operational burden unless there is a compelling reason otherwise.

Use Google ADK for agent construction, orchestration, and tool invocation. ADK supports modular agents, sessions, events, tools, and deployment patterns suitable for production AI applications.

Use Vertex AI for model access and RAG. Vertex AI RAG Engine provides corpus and file management APIs and integrates with storage/retrieval backends.

Each corpus must map to a separate GCS bucket. The design must specify:

* bucket naming convention  
* metadata model  
* lifecycle policy options  
* CMEK option  
* logging and audit requirements  
* per-corpus ingestion pipeline  
* mapping between corpus, bucket, and allowed groups

Use Google Cloud Model Armor to protect the application’s LLM interactions. Include both:

* a **simple direct API integration** for testing and learning, where the backend calls Model Armor to sanitize the **user prompt before sending it to the model** and sanitize the **model response before returning it to the user**  
* an **optional inline Vertex AI integration** using **Model Armor floor settings or templates** for Gemini `generateContent`

The design must explain when to use:

* **direct Model Armor API calls** (`sanitizeUserPrompt`, `sanitizeModelResponse`) for explicit application-managed screening and learning/testing  
* **Vertex AI integrated Model Armor** for inline screening of Gemini requests and responses

The design must include:

* the Model Armor regional API endpoint strategy  
* required IAM roles such as `roles/modelarmor.user` and any viewer/logging permissions needed for testing  
* a minimal testing workflow with one prompt sanitization call and one response sanitization call  
* how Cloud Logging will be enabled and used to review sanitization outcomes  
* example templates or floor settings for prompt injection, harmful content, and sensitive data leakage detection

Google documents that Model Armor can sanitize prompts and responses directly, and can also integrate directly with Vertex AI to screen Gemini traffic via floor settings or templates. Cloud Logging should be enabled for visibility into sanitization results.

## **Identity and Authorization Design Requirements**

Design the system with the following group model:

### **App Access Groups**

Example:

* adk-rag-users  
* adk-rag-admins

These groups control whether a user may access the application at all through IAP.

### **Corpus Groups**

Example:

* adk-rag-default-corpus  
* adk-rag-name1\-corpus  
* adk-rag-name2\-corpus  
* adk-rag-name3\-corpus

These groups control what corpora the user may access and what actions they may perform.

### **Agent Groups**

Example:

* adk-rag-admin-agent  
* adk-rag-content-manager-agent  
* adk-rag-contributor-agent  
* adk-rag-viewer-agent\* 

\*(All users will be assigned to this group)

These groups control which agents the user may invoke.

The implementation must support users being in multiple groups simultaneously and receiving a union of granted permissions.

The system must also support future expansion to:

* nested groups if supported by the organization  
* role inheritance  
* approval workflows  
* temporary elevated access  
* audit and review of group-to-resource mappings

## **Authorization Engine Requirements**

Design and implement a centralized authorization layer in the application backend.

This authorization layer must:

* accept the authenticated user identity from IAP  
* resolve the user’s group memberships from a trusted source  
* map memberships to app permissions, corpus permissions, and agent permissions  
* produce an effective permission set for the current request  
* cache memberships safely for performance  
* invalidate or refresh cached entitlements on a defined TTL or event basis  
* enforce authorization before any tool action executes

The system must never trust only client-side filtering.

Every sensitive operation must perform server-side checks such as:

* can this user access the app?  
* can this user see this corpus?  
* can this user upload/download/delete/list documents in this corpus?  
* can this user invoke this agent?  
* can this specific tool operate on this corpus for this user?

## **Tool-Level Security Requirements**

For every ADK tool, implement policy enforcement.

Original Tools:

* query\_documents  
* list\_corpora  
* create\_corpus  
* add\_new\_data  
* get\_corpus\_info  
* browse\_documents  
* delete\_document  
* delete\_corpus  
* retrieve\_document  
* multi\_corpora\_query  
* set\_current\_corpus

Future Options

* upload\_document  
* reindex\_corpus  
* search\_corpus  
* summarize\_corpus  
* compare\_documents  
* export\_metadata  
* manage\_labels  
* retrieve\_thread

Each tool must:

* receive user context  
* verify the user belongs to an allowed agent-group  
* verify the user has permission for the target corpus  
* enforce action-specific authorization such as reader/editor/admin  
* log the authorization decision and action outcome  
* reject unauthorized access with structured errors

In addition to authorization checks, every tool that sends content to an LLM must support a **Model Armor screening flow**:

* sanitize the incoming user prompt before invoking Vertex AI  
* optionally sanitize retrieved corpus snippets before including them in the final model prompt  
* sanitize the model response before returning it to the user  
* record whether Model Armor inspected, allowed, modified, or blocked the content  
* enforce configurable behavior for blocked content, such as:  
  * deny the request  
  * ask the user to rephrase  
  * redact or suppress unsafe output  
  * escalate to an audit or administrator review path for sensitive operations

The implementation must distinguish between:

* **authorization failures** (user is not allowed to access a corpus/agent/tool)  
* **Model Armor screening failures** (prompt/response violates security or safety policy)

This matches Model Armor’s purpose of screening prompts and responses for risks such as harmful content, sensitive data leakage, and prompt injection. 

## **Session and User Context Requirements**

Use IAP-authenticated identity as the trusted user principal for the web session. IAP provides ways for the backend to obtain the user identity for secured applications. 

For each session, maintain:

* user email / principal  
* user id if available  
* current groups  
* effective corpus permissions  
* effective agent permissions  
* selected corpus or corpus scope  
* selected agent  
* audit metadata such as request id, timestamp, source IP if available, and decision trace

ADK sessions should carry enough context for authorized agent execution, but must not become the sole source of truth for authorization. Session data may cache entitlements, but the backend authorization service remains authoritative. ADK sessions are used to track conversation threads and context. 

## **Data Model Requirements**

Design a normalized backend data model. Include example schemas for:

### **Users**

* user\_id  
* email  
* display\_name  
* status  
* last\_login  
* created\_at  
* updated\_at

### **Groups**

* group\_id  
* group\_email  
* group\_type enum(app\_access, corpus\_access, agent\_access)  
* display\_name  
* description  
* created\_at  
* updated\_at

### **UserGroupMemberships**

* membership\_id  
* user\_id  
* group\_id  
* source\_of\_truth  
* synced\_at

### **Corpora**

* corpus\_id  
* corpus\_name  
* description  
* gcs\_bucket  
* vertex\_rag\_corpus\_id  
* data\_classification  
* owner\_group  
* status  
* created\_at  
* updated\_at

### **CorpusGroupBindings**

* binding\_id  
* corpus\_id  
* group\_id  
* permission\_level enum(read, write, manage, admin)

### **Agents**

* agent\_id  
* agent\_name  
* description  
* status  
* deployment\_ref  
* allowed\_tools\_json  
* created\_at  
* updated\_at

### **AgentGroupBindings**

* binding\_id  
* agent\_id  
* group\_id  
* permission\_level enum(use, manage, admin)

### **AuditLogs**

* audit\_id  
* user\_id  
* user\_email  
* session\_id  
* request\_id  
* action\_type  
* target\_type  
* target\_id  
* authorization\_result  
* reason  
* timestamp

## **Group Resolution Strategy**

Design the best production approach for group resolution.

Evaluate these implementation options:

1. live group lookup from Cloud Identity / Groups API on each request  
2. cached lookup with TTL  
3. scheduled sync of groups into an internal authorization database  
4. hybrid approach with periodic sync plus on-demand refresh for misses

Recommend the best option for hundreds of users and explain tradeoffs around:

* latency  
* API quota  
* operational complexity  
* stale permissions  
* security  
* auditability

The recommended design should likely use a hybrid approach:

* Cloud Identity / Google Groups as source of truth  
* periodic sync into an internal entitlements store  
* short-lived cache for hot authorization checks  
* audit logs for changes and decisions

## **Infrastructure Requirements**

Provide a cloud-native production architecture including:

* frontend web app  
* backend API / ADK runtime   
* load balancers  
* IAP-secured entry point  
* OAuth client setup for IAP  
* Cloud Run or GKE deployment  
* Vertex AI model access  
* Vertex AI RAG Engine integration  
* Cloud Storage buckets per corpus  
* Cloud SQL, or Spanner for authorization metadata  
* Cloud Logging and Cloud Audit Logs  
* Secret Manager for secrets  
* Cloud KMS for encryption keys if CMEK is used  
* optional Pub/Sub or Cloud Tasks for ingestion workflows  
* optional Eventarc for automation

Explain and choose the best datastore for authorization metadata. Compare:

* Firestore  
* Cloud SQL PostgreSQL  
* Spanner

Recommend one based on:

* hundreds of users  
* many corpus/group/agent bindings  
* low-latency reads  
* transactional consistency  
* operational simplicity

Include Google Cloud Model Armor in the production architecture:

* Model Armor templates for prompt and response screening  
* optional Vertex AI integrated Model Armor using floor settings  
* Cloud Logging for sanitization visibility  
* Secret Manager only if needed for non-default configuration values; do not store Google-managed auth secrets unnecessarily  
* a test path in dev/test environments that uses direct Model Armor REST calls before and after Vertex AI inference  
* a production option that compares:  
  * direct API orchestration controlled by the application  
  * inline Vertex AI integration using Model Armor templates or floor settings

The architecture must clearly show where Model Armor sits in the request path:

User → IAP → Backend → \<span style="color:red"\>Model Armor sanitizeUserPrompt\</span\> → Vertex AI / ADK agent tools → \<span style="color:red"\>Model Armor sanitizeModelResponse\</span\> → User

Also show the alternative inline pattern:

User → IAP → Backend → Vertex AI Gemini with \<span style="color:red"\>ModelArmorConfig / Vertex AI integration\</span\> → User

Google’s docs describe both the direct API pattern and the integrated Vertex AI pattern.

## **Security Requirements**

Implement least privilege everywhere.

The app’s runtime service account must have only the minimal permissions needed to:

* read authorization metadata  
* access allowed storage resources indirectly through the app logic  
* call Vertex AI APIs  
* write logs and metrics

Do not rely on end-user direct Google Cloud IAM permissions to GCS buckets for app behavior. The app should act as the policy enforcement point. Bucket access should generally be mediated by the application service account and backend authorization layer.

Include security controls for:

* input validation  
* prompt injection resistance  
* document-level authorization validation  
* tool abuse prevention  
* rate limiting  
* audit logging  
* tamper-resistant logs  
* CSRF/session protection where applicable  
* secure header handling from IAP  
* verification of signed identity assertions where needed  
* separation of duties between app admins, corpus admins, and agent admins

Include recommendations for VPC-SC and CMEK where relevant. Vertex AI RAG Engine documentation states support for VPC-SC and CMEK.

Include Model Armor-specific protections for:

* prompt injection screening  
* harmful content detection  
* sensitive data leakage detection  
* suspicious or policy-violating model output  
* logging and review of sanitization decisions

The solution must define a policy for:

* when content is only inspected  
* when content is blocked  
* when content is redacted or replaced  
* how blocked content is surfaced to the user and captured in audit records

Include recommendations for:

* starting with **inspect-only** in development  
* validating false positives/false negatives  
* then moving selected flows to **inspect-and-block** in production

Google documents inspect-only as the default when enabling Vertex AI integration via floor settings, and supports changing enforcement to inspect-and-block.

# Google Cloud Model Armor Integration

## The architecture must integrate Google Cloud Model Armor.

## Two integration approaches must be implemented.

### 1\. Direct Model Armor API Integration

## Use Model Armor REST APIs to:

* ## sanitize user prompts

* ## sanitize model responses

## This enables testing and learning the Model Armor API behavior.

### 2\. Vertex AI Integrated Model Armor

## Support optional inline protection using:

* ## Model Armor templates

* ## Vertex AI floor settings

## ---

# Model Armor Security Flow

## User → IAP → Backend API → Model Armor `sanitizeUserPrompt` → Vertex AI / ADK Agent → Model Armor `sanitizeModelResponse` → User

## ---

# Tool-Level Security Requirements

## Each ADK tool must enforce:

* ## agent authorization

* ## corpus authorization

* ## Model Armor prompt screening

* ## Model Armor response screening

## If Model Armor blocks content:

* ## deny the request

* ## ask user to rephrase

* ## redact unsafe output

* ## log the event

## **Scalability Requirements**

Design for hundreds of concurrent enterprise users.

Address:

* stateless horizontal scaling  
* caching strategy for entitlements  
* connection pooling  
* async document ingestion  
* background reindexing  
* quotas and backoff  
* retries and idempotency  
* monitoring and SLOs  
* cold start mitigation if using Cloud Run  
* autoscaling settings  
* multi-environment deployment for dev, test, prod

## **Required Deliverables**

Produce all of the following in detail:

### **1\. Reference Architecture**

A complete end-to-end architecture description with all major Google Cloud services, trust boundaries, data flows, and access-control flows.

### **2\. IAM and Group Model**

A detailed model for:

* app access  
* corpus access  
* agent access  
* example groups  
* example users  
* example permission resolution logic

### **3\. Authorization Decision Flow**

Describe the exact runtime flow from:

* user reaches app URL  
* IAP authenticates user  
* backend receives identity  
* backend resolves groups  
* backend computes entitlements  
* UI displays only allowed agents/corpora  
* user invokes an agent  
* agent calls a tool  
* tool authorization is enforced  
* result is returned and audited

### **4\. Database Schema**

Provide concrete SQL or schema definitions for the metadata store.

### **5\. API Design**

Define backend APIs such as:

* GET /me  
* GET /me/permissions  
* GET /corpora  
* GET /agents  
* POST /agent-sessions  
* POST /agent-invoke  
* POST /corpora/{id}/documents  
* DELETE /corpora/{id}/documents/{docId}

For each API, specify:

* request  
* response  
* auth requirements  
* authorization checks  
* audit fields

Add Model Armor testing APIs such as:

* `POST /security/model-armor/sanitize-prompt`  
* `POST /security/model-armor/sanitize-response`  
* `POST /agent-invoke-secure`

For each API, specify:

* request payload  
* Model Armor template or configuration used  
* response fields including sanitization result  
* whether the content was allowed, modified, or blocked  
* audit fields and logging behavior

`POST /agent-invoke-secure` must demonstrate this flow:

1. authenticate user via IAP  
2. authorize app/corpus/agent access  
3. sanitize user prompt with Model Armor  
4. call Vertex AI / ADK agent only if allowed  
5. sanitize model response with Model Armor  
6. return safe response with audit metadata

The sanitized endpoints correspond directly to Model Armor REST methods for user prompts and model responses. 

### **6\. ADK Agent Design**

Define:

* agent classes  
* tool registration  
* user-context injection  
* authorization middleware / decorator  
* safe tool wrappers  
* sample pseudo-code or real code

Provide production-style Python example code for:

* calling Model Armor `sanitizeUserPrompt`  
* calling Model Armor `sanitizeModelResponse`  
* interpreting sanitization results  
* rejecting or redacting blocked content  
* integrating Model Armor before and after a Vertex AI call  
* optional example of Vertex AI Gemini request using Model Armor integrated configuration

Include one minimal direct API example for learning/testing and one application middleware example for production use.

Google exposes dedicated REST methods for both sanitization calls, and Vertex AI also supports Model Armor configuration.

* 

### **7\. Google Cloud Implementation Plan**

Provide a step-by-step implementation plan for:

* IAP configuration  
* OAuth client configuration  
* backend identity extraction  
* Cloud Identity Groups integration  
* group sync job  
* authorization service  
* corpus mapping service  
* agent-group mapping  
* deployment to Cloud Run

Provide Terraform or deployment guidance for:

* enabling required APIs for Model Armor  
* IAM bindings for `roles/modelarmor.user`  
* Cloud Logging configuration needed to review sanitization activity  
* optional environment variables for Model Armor template names and regional endpoints

Google documents the need to grant the Vertex AI service account `roles/modelarmor.user` for Vertex AI integration, and recommends Cloud Logging for visibility.

### **8\. Example Code**

Provide production-style Python example code for:

* extracting IAP identity  
* resolving groups  
* computing effective permissions  
* enforcing tool authorization  
* registering ADK agents and tools  
* calling Vertex AI RAG components  
* writing audit logs

### **9\. Terraform**

Provide Terraform for:

* IAP-related components where supported  
* Cloud Run or GKE  
* service accounts  
* IAM bindings  
* Secret Manager  
* Cloud SQL / Firestore / Spanner resources  
* GCS buckets per corpus  
* logging/monitoring basics

### **10\. Threat Model**

Provide a threat model specific to this app, including:

* unauthorized app access  
* unauthorized corpus access  
* unauthorized agent access  
* tool misuse  
* confused deputy risk  
* stale group memberships  
* privilege escalation  
* prompt injection leading to unauthorized tool invocation  
* logging gaps  
* excessive service account privilege  
* prompt injection attempts against agent tools  
* jailbreak attempts  
* sensitive data exfiltration through prompts  
* sensitive data leakage through model responses  
* unsafe generated content returned to users  
* failure modes when Model Armor is unavailable or misconfigured  
* bypass risks if some tools call Vertex AI without the sanitization wrapper  
* 

For each threat include:

* attack path  
* risk  
* mitigations  
* detection signals  
* where Model Armor helps  
* where authorization still remains necessary  
* detection and logging signals  
* fallback behavior if sanitization cannot be completed

## **Important Design Rules**

1. Authentication and authorization must be separate concerns.  
2. IAP grants access to the application, not automatically to every corpus or every agent.  
3. Group membership must drive corpus and agent entitlements.  
4. Every tool call must re-check authorization server-side.  
5. UI visibility is convenience only; backend enforcement is mandatory.  
6. The design must be scalable, maintainable, and auditable.  
7. Prefer group-driven administration over manual user-by-user grants.  
8. Prefer managed Google Cloud services and least privilege.  
9. All authorization decisions must be explainable and logged.  
10. The solution must support future expansion to more agents, more corpora, and more granular roles.

## **Preferred Architecture Direction**

Unless you identify a clearly better design, use the following opinionated baseline:

* Frontend: web UI behind HTTPS Load Balancer \+ IAP, or IAP-secured Cloud Run frontend  
* Backend: Python FastAPI service using Google ADK  
* Hosting: Cloud Run for simplicity, unless GKE is justified  
* Identity: Google Identity with IAP OAuth 2.0  
* Entitlements source: Cloud Identity Groups / Google Groups  
* Entitlements store: Cloud SQL PostgreSQL or Firestore, with a clear recommendation  
* Corpora storage: one GCS bucket per corpus  
* RAG layer: Vertex AI RAG Engine  
* Agent framework: Google ADK  
* Sync engine: scheduled job to sync group memberships and resource bindings  
* Audit: Cloud Logging \+ structured application audit tables  
* Secrets: Secret Manager  
* Encryption: Google-managed keys by default, CMEK option for regulated environments

## **Output Format**

Return the answer in this exact structure:

1. Executive Summary  
2. Architecture Overview  
3. Identity and Access Model  
4. Group Taxonomy and Examples  
5. Runtime Authorization Flow  
6. Data Model / Schema  
7. ADK Agent and Tool Design  
8. Google Cloud Services Mapping  
9. Deployment Architecture  
10. Security Controls  
11. Scalability Design  
12. API Specification  
13. Example Python Code  
14. Terraform Examples  
15. Threat Model  
16. Operational Runbook  
17. Future Enhancements  
18. Final Recommendation  
19. Model Armor Integration Design  
    1. must include:  
* direct API testing workflow  
* template/floor-setting strategy  
* prompt and response sanitization sequence  
* example REST calls  
* example Python integration  
* recommended rollout path from inspect-only to enforce/block  
* logging, monitoring, and audit design

Be explicit, opinionated, and implementation-ready. Do not stay at a conceptual level only. Provide concrete schemas, sample code, decision logic, and deployment guidance.


"Build a production-ready Python FastAPI + Google ADK RAG application on Google Cloud that uses IAP with Google OAuth 2.0 for application authentication, Cloud Identity Groups / Google Groups for authorization, Vertex AI RAG Engine for corpus retrieval, Cloud Storage with one bucket per corpus, and Google Cloud Model Armor for prompt and response protection. Implement three layers of authorization: app access, corpus access, and agent access. Users gain app access through app groups, corpus access through corpus groups, and agent access through agent groups. Every ADK tool must enforce authorization server-side using the authenticated IAP user identity and the effective entitlements derived from group membership. In addition, implement a simple direct Model Armor API integration that sanitizes the user prompt before model invocation and sanitizes the model response before returning it to the user. Also show an optional Vertex AI inline Model Armor integration using templates or floor settings. Generate the reference architecture, SQL schema, Python code, FastAPI routes, authorization middleware, ADK agent definitions, tool wrappers, group sync service, Model Armor integration code, Terraform, threat model, and deployment steps for Cloud Run. Include structured audit logging, Cloud Logging visibility for sanitization results, least-privilege service accounts, and a scalable entitlement caching strategy suitable for hundreds of users."