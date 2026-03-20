"""
WQ LLM — FastAPI Backend
Exposes the Ontology Agent and Wellness Agent as REST APIs.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.ontology_agent import get_ontology_agent
from core import database as db

app = FastAPI(
    title="WQ LLM API",
    description="Wellness Quotient Ontology & Coaching API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup: preload the ontology agent
# ---------------------------------------------------------------------------
ontology_agent = None

@app.on_event("startup")
def startup():
    global ontology_agent
    ontology_agent = get_ontology_agent()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str

class SearchRequest(BaseModel):
    keyword: str

class ChatRequest(BaseModel):
    message: str
    user_id: str = ""
    session_id: str = ""

class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str = ""


# ---------------------------------------------------------------------------
# ONTOLOGY ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/api/ontology/summary")
def get_summary():
    """Get a high-level summary of all components (sidebar data)."""
    return ontology_agent.get_summary()


@app.get("/api/ontology/components")
def list_components():
    """List all component IDs and metadata."""
    summary = ontology_agent.get_summary()
    return {"components": summary["components"]}


@app.get("/api/ontology/components/{component_id}")
def get_component(component_id: str):
    """Get full details of a specific component."""
    component = ontology_agent.components.get(component_id)
    if not component:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")

    # Build a clean response
    entities = {}
    for name, data in component.get("entities", {}).items():
        entities[name] = {
            "description": data.get("description", ""),
            "properties": data.get("properties", {}),
            "instances": data.get("instances", []),
            "instance_count": len(data.get("instances", [])),
        }

    return {
        "id": component.get("id", component_id),
        "name": component.get("name", component_id),
        "icon": component.get("icon", "•"),
        "description": component.get("description", ""),
        "entities": entities,
        "operations": component.get("operations", []),
        "relationships": component.get("relationships", []),
        "safety": component.get("safety", None),
    }


@app.get("/api/ontology/components/{component_id}/entities/{entity_name}")
def get_entity(component_id: str, entity_name: str):
    """Get a specific entity with all its instances."""
    entity = ontology_agent.get_entity(component_id, entity_name)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found in '{component_id}'")
    return {
        "component": component_id,
        "entity": entity_name,
        "description": entity.get("description", ""),
        "properties": entity.get("properties", {}),
        "instances": entity.get("instances", []),
    }


@app.get("/api/ontology/relationships")
def get_relationships():
    """Get the full cross-component relationship graph."""
    return ontology_agent.registry.get("relationship_graph", {})


@app.get("/api/ontology/routing")
def get_routing_config():
    """Get the routing configuration (intent keywords, rules)."""
    return ontology_agent.registry.get("routing", {})


# ---------------------------------------------------------------------------
# QUERY / ROUTING ENDPOINTS
# ---------------------------------------------------------------------------

@app.post("/api/query/route")
def route_query(req: QueryRequest):
    """Route a user query to components and return structured context."""
    result = ontology_agent.process_query(req.query)
    return {
        "query": req.query,
        "primary_components": result["primary_components"],
        "routing_explanation": result["routing_explanation"],
        "operations": result["operations"],
        "red_flags": result["red_flags"],
        "context_length": len(result["context"]),
        "context_preview": result["context"][:2000],
    }


@app.post("/api/query/search")
def search_entities(req: SearchRequest):
    """Search across all components for entities matching a keyword."""
    results = ontology_agent.search_entities(req.keyword)
    return {"keyword": req.keyword, "results": results, "count": len(results)}


# ---------------------------------------------------------------------------
# CHAT ENDPOINT (uses Gemini if API key is set)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# USER REGISTRATION & AUTH
# ---------------------------------------------------------------------------

@app.post("/api/users/register")
def register_user(req: RegisterRequest):
    """Register a new user or return existing user by email."""
    if not req.name.strip() or not req.email.strip():
        raise HTTPException(status_code=400, detail="Name and email are required")
    user = db.create_user(req.name.strip(), req.email.strip().lower(), req.phone.strip())
    session = db.create_session(user["id"])
    return {"user": user, "session": session}


@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    """Get user profile."""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users/{user_id}/sessions")
def new_session(user_id: str):
    """Start a new chat session for a user."""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.create_session(user_id)


@app.get("/api/users/{user_id}/sessions")
def get_sessions(user_id: str):
    """Get all sessions for a user."""
    return db.get_user_sessions(user_id)


@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str):
    """Get all messages for a session."""
    return db.get_session_messages(session_id)


# ---------------------------------------------------------------------------
# CHAT ENDPOINT (session-aware, stores everything)
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Chat with the wellness agent.
    Requires user_id and session_id. Stores all messages for coach insights.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")

    # Route query through ontology
    result = ontology_agent.process_query(req.message)
    components = result["primary_components"]
    operations = [op["name"] for op in result["operations"]]

    # Save user message to DB
    if req.user_id and req.session_id:
        db.save_message(req.session_id, req.user_id, "user", req.message, components, operations)
        # Auto-detect insights from components
        for comp in components:
            db.save_insight(req.user_id, "topic_interest", comp, confidence=0.8)

    if not api_key:
        response_text = (
            "I'm currently running in ontology-only mode (no LLM API key set). "
            "Here's what I found in the knowledge base for your query:\n\n"
            f"**Active Components**: {', '.join(components)}\n\n"
            f"**Available Operations**: {len(operations)} operations across "
            f"{len(components)} components.\n\n"
            "Set the GEMINI_API_KEY environment variable to enable full coaching responses."
        )
        if req.user_id and req.session_id:
            db.save_message(req.session_id, req.user_id, "assistant", response_text, components, operations)
        return {"response": response_text, "components": components, "operations": operations, "mode": "ontology_only"}

    # Full LLM-powered response
    try:
        from core.wellness_agent import WellnessAgent
        agent = WellnessAgent(use_reasoning=False)

        # Replay session history from DB
        if req.session_id:
            history = db.get_session_messages(req.session_id)
            for msg in history[:-1]:  # Exclude the message we just saved
                agent.state.add_message(msg["role"], msg["content"])

        response_text = await agent.chat(req.message)

        # Save assistant response to DB
        if req.user_id and req.session_id:
            db.save_message(req.session_id, req.user_id, "assistant", response_text, components, operations)

        return {"response": response_text, "components": components, "operations": operations, "mode": "full"}
    except Exception as e:
        err_text = f"Error connecting to LLM: {str(e)}. Running in ontology-only mode."
        return {"response": err_text, "components": components, "operations": operations, "mode": "error"}


# ---------------------------------------------------------------------------
# COACH DASHBOARD ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/api/coach/dashboard")
def coach_dashboard():
    """Aggregated analytics for coaches."""
    return db.get_coach_dashboard_data()


@app.get("/api/coach/users")
def coach_list_users():
    """List all registered users with basic stats."""
    return db.list_users()


@app.get("/api/coach/users/{user_id}")
def coach_user_detail(user_id: str):
    """Full detail view of a user for coaches."""
    detail = db.get_user_detail(user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")
    return detail


@app.get("/api/coach/users/{user_id}/insights")
def coach_user_insights(user_id: str):
    """Get all insights extracted from a user's conversations."""
    return db.get_user_insights(user_id)


# ---------------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    summary = ontology_agent.get_summary()
    return {
        "status": "healthy",
        "ontology": summary["name"],
        "version": summary["version"],
        "components": len(summary["components"]),
    }
