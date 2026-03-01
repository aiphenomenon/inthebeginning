"""Reactive Agent Protocol - State passing between LLM and local tool.

This module implements the reactive protocol that allows an LLM agent
and a local AST analysis tool to act as a lightweight reactive agent pair.
State is passed back and forth via structured CueSignals, enabling
iterative code intelligence without requiring the full source in context.
"""
import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

from ast_dsl.core import ASTEngine, ASTQuery, ASTResult


class CueType(Enum):
    """Types of cues the agent pair can exchange."""
    QUERY = "query"           # LLM asks tool to analyze
    RESULT = "result"         # Tool returns analysis
    REFINE = "refine"         # LLM refines a previous query
    TRANSFORM = "transform"   # LLM requests code transformation
    SYNTHESIZE = "synthesize"  # Tool synthesizes multiple results
    COMPLETE = "complete"     # Signal that the interaction is done


@dataclass
class CueSignal:
    """A signal passed between the agent pair."""
    cue_type: CueType
    payload: Any = None
    sequence_id: int = 0
    parent_id: int = 0  # For tracking refinement chains
    timestamp: float = field(default_factory=time.time)
    context_tokens_approx: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cue_type"] = self.cue_type.value
        return d

    def to_compact(self) -> str:
        """Minimal representation for context efficiency."""
        parts = [f"cue:{self.cue_type.value}#{self.sequence_id}"]
        if self.parent_id:
            parts.append(f"<-#{self.parent_id}")
        if isinstance(self.payload, dict):
            compact = json.dumps(self.payload, separators=(",", ":"))
            if len(compact) > 500:
                compact = compact[:500] + "..."
            parts.append(compact)
        elif isinstance(self.payload, str):
            parts.append(self.payload[:200])
        return " ".join(parts)

    @classmethod
    def from_dict(cls, d: dict) -> "CueSignal":
        d = dict(d)
        d["cue_type"] = CueType(d["cue_type"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AgentState:
    """Shared state between the agent pair."""
    session_id: str = ""
    turn: int = 0
    history: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    discovered_symbols: list = field(default_factory=list)
    discovered_deps: list = field(default_factory=list)
    pending_transforms: list = field(default_factory=list)
    total_tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "turn": self.turn,
            "history_len": len(self.history),
            "context_keys": list(self.context.keys()),
            "symbols_found": len(self.discovered_symbols),
            "deps_found": len(self.discovered_deps),
            "pending_transforms": len(self.pending_transforms),
            "total_tokens": self.total_tokens_used,
        }

    def to_compact(self) -> str:
        """Minimal state summary."""
        return (
            f"s:{self.session_id[:8]} t:{self.turn} "
            f"sym:{len(self.discovered_symbols)} "
            f"dep:{len(self.discovered_deps)} "
            f"tok:{self.total_tokens_used}"
        )


class ReactiveProtocol:
    """Manages the reactive interaction between LLM and AST tool.

    The protocol works as follows:
    1. LLM sends a QUERY cue with an ASTQuery payload
    2. Tool executes the query and returns a RESULT cue
    3. LLM can REFINE the query based on results
    4. LLM can request TRANSFORMations
    5. Tool can SYNTHESIZE multiple results
    6. Either side signals COMPLETE when done

    This creates an efficient iterative loop where the LLM never needs
    to hold the full source code in context - only structured AST summaries.
    """

    def __init__(self, session_id: str = ""):
        self.engine = ASTEngine()
        self.state = AgentState(
            session_id=session_id or hashlib.md5(
                str(time.time()).encode()
            ).hexdigest()[:12]
        )
        self._sequence = 0

    def _next_seq(self) -> int:
        self._sequence += 1
        return self._sequence

    def process_cue(self, cue: CueSignal) -> CueSignal:
        """Process an incoming cue and produce a response cue."""
        self.state.turn += 1
        self.state.history.append(cue.to_dict())

        handlers = {
            CueType.QUERY: self._handle_query,
            CueType.REFINE: self._handle_refine,
            CueType.TRANSFORM: self._handle_transform,
            CueType.SYNTHESIZE: self._handle_synthesize,
        }

        handler = handlers.get(cue.cue_type)
        if handler:
            response = handler(cue)
        else:
            response = CueSignal(
                cue_type=CueType.COMPLETE,
                payload={"state": self.state.to_dict()},
                sequence_id=self._next_seq(),
                parent_id=cue.sequence_id,
            )

        self.state.history.append(response.to_dict())
        self.state.total_tokens_used += (
            cue.context_tokens_approx + response.context_tokens_approx
        )
        return response

    def _handle_query(self, cue: CueSignal) -> CueSignal:
        """Handle a QUERY cue by executing the AST query."""
        if isinstance(cue.payload, dict):
            query = ASTQuery.from_dict(cue.payload)
        elif isinstance(cue.payload, ASTQuery):
            query = cue.payload
        else:
            return CueSignal(
                cue_type=CueType.RESULT,
                payload={"error": "Invalid query payload"},
                sequence_id=self._next_seq(),
                parent_id=cue.sequence_id,
            )

        result = self.engine.execute(query)

        # Update discovered state
        if query.action == "symbols" and result.success:
            self.state.discovered_symbols.extend(
                result.data if isinstance(result.data, list) else []
            )
        elif query.action == "dependencies" and result.success:
            self.state.discovered_deps.extend(
                result.data if isinstance(result.data, list) else []
            )

        response = CueSignal(
            cue_type=CueType.RESULT,
            payload=result.to_dict(),
            sequence_id=self._next_seq(),
            parent_id=cue.sequence_id,
            context_tokens_approx=result.metrics.result_tokens_approx,
        )
        return response

    def _handle_refine(self, cue: CueSignal) -> CueSignal:
        """Handle a REFINE cue by re-executing with modified parameters."""
        return self._handle_query(cue)

    def _handle_transform(self, cue: CueSignal) -> CueSignal:
        """Handle a TRANSFORM cue by applying AST transformation."""
        if isinstance(cue.payload, dict):
            query = ASTQuery.from_dict(cue.payload)
            query.action = "transform"
        else:
            return CueSignal(
                cue_type=CueType.RESULT,
                payload={"error": "Invalid transform payload"},
                sequence_id=self._next_seq(),
                parent_id=cue.sequence_id,
            )

        result = self.engine.execute(query)
        self.state.pending_transforms.append({
            "query": query.to_dict(),
            "result_hash": result.source_hash,
        })

        return CueSignal(
            cue_type=CueType.RESULT,
            payload=result.to_dict(),
            sequence_id=self._next_seq(),
            parent_id=cue.sequence_id,
            context_tokens_approx=result.metrics.result_tokens_approx,
        )

    def _handle_synthesize(self, cue: CueSignal) -> CueSignal:
        """Synthesize accumulated state into a summary."""
        summary = {
            "state": self.state.to_dict(),
            "all_symbols": self.state.discovered_symbols,
            "all_deps": self.state.discovered_deps,
            "history_summary": [
                {"type": h.get("cue_type"), "seq": h.get("sequence_id")}
                for h in self.state.history
            ],
        }
        return CueSignal(
            cue_type=CueType.RESULT,
            payload=summary,
            sequence_id=self._next_seq(),
            parent_id=cue.sequence_id,
        )

    def create_query_cue(self, action: str, target: str,
                         language: str = "python",
                         filters: dict = None) -> CueSignal:
        """Convenience: create a QUERY cue."""
        return CueSignal(
            cue_type=CueType.QUERY,
            payload=ASTQuery(
                action=action,
                target=target,
                language=language,
                filters=filters or {},
            ).to_dict(),
            sequence_id=self._next_seq(),
        )

    def run_query(self, action: str, target: str,
                  language: str = "python",
                  filters: dict = None) -> CueSignal:
        """Convenience: create and immediately process a query."""
        cue = self.create_query_cue(action, target, language, filters)
        return self.process_cue(cue)

    def get_session_log(self) -> str:
        """Get full session log as JSON."""
        return json.dumps({
            "session": self.state.to_dict(),
            "history": self.state.history,
        }, indent=2, default=str)
