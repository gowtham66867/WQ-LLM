# WQ LLM — Wellness Quotient AI Assistant

An LLM-powered wellness assistant for the [Wellness Quotient](https://www.wellnessquotient.community/) community. Helps people engage with their lifestyle transformation journey through intelligent, ontology-grounded conversations.

## Architecture (Session 19 Aligned)

- **Ontology-First**: All wellness knowledge is structured in a formal ontology (`ontology/`)
- **Role-Based Model Governance**: Different LLM roles (Planner, Verifier, Optimizer) via `config/models.yaml`
- **System 2 Reasoning**: Draft-Verify-Refine loop ensures advice quality and safety
- **Episodic Memory**: Skeletonized session history for long-term user journeys
- **Markdown Skills**: Natural language skill files for wellness interventions

## Project Structure

```
WQ LLM/
├── config/
│   └── models.yaml              # Model registry & role-based governance
├── ontology/
│   ├── wellness_ontology.yaml   # Core ontology (domains, concepts, relationships)
│   ├── conditions.yaml          # Lifestyle conditions & symptoms
│   ├── interventions.yaml       # Evidence-based interventions
│   └── assessments.yaml         # Intake & progress assessments
├── core/
│   ├── model_manager.py         # Role-based LLM access
│   ├── reasoning.py             # System 2 Draft-Verify-Refine engine
│   ├── episodic_memory.py       # Session skeletonization
│   ├── query_optimizer.py       # JitRL query enhancement
│   ├── ontology_engine.py       # Ontology loader & query interface
│   └── utils.py                 # Logging & helpers
├── skills/
│   ├── nutrition_coach/SKILL.md
│   ├── sleep_optimizer/SKILL.md
│   ├── stress_management/SKILL.md
│   └── fitness_guide/SKILL.md
├── memory/
│   └── episodes/                # Skeletonized session history
├── requirements.txt
└── main.py                      # Entry point
```

## Quick Start

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
python main.py
```

## Ontology Design

The wellness ontology is the knowledge backbone. It defines:
- **Domains**: High-level wellness pillars (Nutrition, Sleep, Fitness, etc.)
- **Concepts**: Specific topics within each domain
- **Conditions**: Lifestyle issues people face (obesity, insomnia, stress, etc.)
- **Interventions**: Evidence-based actions mapped to conditions
- **Assessments**: Structured intake questionnaires
- **Relationships**: How concepts connect (causes, alleviates, requires, etc.)
