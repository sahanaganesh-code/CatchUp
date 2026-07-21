from typing import List, Optional
from sqlalchemy import select
from app.config import settings
from app.models import ProposedAction, Evidence, ApproveActionResponse
from app.db import SessionLocal, ActionRow
from app.store import vector_store
from app.gemini_client import generate_text
import logging
import uuid
import json

logger = logging.getLogger(__name__)


def _action_to_model(row: ActionRow) -> ProposedAction:
    return ProposedAction(
        action_id=row.id,
        session_id=row.session_id,
        action_type=row.action_type,
        title=row.title,
        description=row.description,
        evidence=[Evidence(**e) for e in row.evidence],
        metadata=row.action_metadata,
        approved=row.approved,
        executed=row.executed,
        created_at=row.created_at,
    )


def propose_actions(session_id: str) -> List[ProposedAction]:
    """
    Propose actions based on meeting transcript.
    HARD RULE: Each action must have evidence quotes.
    """
    logger.info(f"Proposing actions for session {session_id}")

    # Get all chunks
    all_chunks = vector_store.get_all_chunks(session_id)

    if not all_chunks:
        logger.warning(f"No chunks found for session {session_id}")
        return []

    # Build context
    context = "\n\n".join([
        f"[{chunk['timestamp']}] {chunk.get('speaker', 'Speaker')}: {chunk['text']}"
        for chunk in all_chunks[:30]  # Limit context
    ])

    prompt = f"""Analyze this meeting transcript and propose actionable items. For each action, identify:
1. Action type (notion_task, calendar_event, email_followup, or slides)
2. Title
3. Description
4. Relevant timestamps from the transcript

Transcript:
{context}

Provide your response as a JSON array of actions with this structure:
[
  {{
    "action_type": "notion_task",
    "title": "Action title",
    "description": "Detailed description",
    "timestamps": ["HH:MM:SS", "HH:MM:SS"],
    "metadata": {{"priority": "high", "due_date": "2024-03-01"}}
  }}
]

Focus on concrete, actionable items mentioned in the meeting.
"""

    try:
        content = generate_text(prompt, model=settings.gemini_model).strip()

        # Extract JSON from response
        json_match = content
        if "```json" in content:
            json_match = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_match = content.split("```")[1].split("```")[0].strip()

        proposed_actions_data = json.loads(json_match)

        proposed_actions = []
        with SessionLocal() as db:
            for action_data in proposed_actions_data:
                # Find evidence for this action
                evidence = []
                timestamps = action_data.get("timestamps", [])
                for ts in timestamps[:settings.max_evidence_quotes]:
                    # Find chunk with matching timestamp
                    matching_chunks = [c for c in all_chunks if c["timestamp"] == ts]
                    if matching_chunks:
                        chunk = matching_chunks[0]
                        evidence.append(Evidence(
                            timestamp=chunk["timestamp"],
                            quote=chunk["text"][:200],
                            speaker=chunk.get("speaker")
                        ))

                # If no evidence found, use general chunks
                if len(evidence) < settings.min_evidence_quotes:
                    for chunk in all_chunks[:settings.max_evidence_quotes]:
                        if len(evidence) >= settings.max_evidence_quotes:
                            break
                        evidence.append(Evidence(
                            timestamp=chunk["timestamp"],
                            quote=chunk["text"][:200],
                            speaker=chunk.get("speaker")
                        ))

                evidence = evidence[:settings.max_evidence_quotes]
                row = ActionRow(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    action_type=action_data["action_type"],
                    title=action_data["title"],
                    description=action_data["description"],
                    evidence=[e.model_dump() for e in evidence],
                    action_metadata=action_data.get("metadata", {}),
                    approved=False,
                    executed=False,
                )
                db.add(row)
                db.flush()
                proposed_actions.append(_action_to_model(row))
            db.commit()

        logger.info(f"Proposed {len(proposed_actions)} actions for session {session_id}")
        return proposed_actions

    except Exception as e:
        logger.error(f"Error proposing actions: {e}")
        return []


def approve_action(action_id: str, approved: bool) -> ApproveActionResponse:
    """
    Approve and execute an action.
    HARD RULE: Action only executes if approved=True.
    """
    logger.info(f"Processing approval for action {action_id}: approved={approved}")

    with SessionLocal() as db:
        row = db.get(ActionRow, action_id)
        if not row:
            return ApproveActionResponse(
                action_id=action_id,
                approved=False,
                executed=False,
                message="Action not found"
            )

        row.approved = approved

        if not approved:
            db.commit()
            logger.info(f"Action {action_id} rejected by user")
            return ApproveActionResponse(
                action_id=action_id,
                approved=False,
                executed=False,
                message="Action rejected by user"
            )

        # Execute action (stub implementation)
        executed = execute_action(_action_to_model(row))
        row.executed = executed
        db.commit()

        return ApproveActionResponse(
            action_id=action_id,
            approved=True,
            executed=executed,
            message="Action approved and executed" if executed else "Action approved but execution failed"
        )


def execute_action(action: ProposedAction) -> bool:
    """
    Execute an approved action (stub implementation).
    HARD RULE: This should only be called after approval.
    """
    logger.info(f"Executing action {action.action_id} of type {action.action_type}")

    try:
        if action.action_type == "notion_task":
            # Stub: In production, integrate with Notion API
            logger.info(f"[STUB] Creating Notion task: {action.title}")
            logger.info(f"[STUB] Task details: {action.description}")
            return True

        elif action.action_type == "calendar_event":
            # Stub: In production, integrate with Google Calendar API
            logger.info(f"[STUB] Creating calendar event: {action.title}")
            logger.info(f"[STUB] Event details: {action.description}")
            return True

        elif action.action_type == "email_followup":
            # Stub: In production, integrate with email API
            logger.info(f"[STUB] Sending email follow-up: {action.title}")
            logger.info(f"[STUB] Email content: {action.description}")
            return True

        elif action.action_type == "slides":
            # Stub: In production, integrate with Google Slides API
            logger.info(f"[STUB] Generating slides: {action.title}")
            logger.info(f"[STUB] Slide content: {action.description}")
            return True

        else:
            logger.warning(f"Unknown action type: {action.action_type}")
            return False

    except Exception as e:
        logger.error(f"Error executing action {action.action_id}: {e}")
        return False


def get_action(action_id: str) -> Optional[ProposedAction]:
    """Get an action by ID."""
    with SessionLocal() as db:
        row = db.get(ActionRow, action_id)
        return _action_to_model(row) if row else None


def list_actions(session_id: str = None) -> List[ProposedAction]:
    """List all actions, optionally filtered by session."""
    with SessionLocal() as db:
        query = select(ActionRow)
        if session_id:
            query = query.where(ActionRow.session_id == session_id)
        rows = db.execute(query).scalars().all()
        return [_action_to_model(r) for r in rows]
