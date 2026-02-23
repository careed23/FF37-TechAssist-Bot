"""
FF37-TechAssist-Bot — JSON REST API blueprint.

Provides stateless API endpoints consumed by the React + Vite frontend.
"""

from flask import Blueprint, abort, current_app, jsonify, request

from .flow_engine import TroubleshootingEngine
from .logger import TroubleshootingLogger

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _engine() -> TroubleshootingEngine:
    return current_app.config["ENGINE"]


def _logger() -> TroubleshootingLogger:
    return current_app.config["LOGGER"]


def _solution_dict(solution) -> dict:
    """Serialise a Solution dataclass to a plain dict."""
    return {
        "id": solution.id,
        "title": solution.title,
        "steps": solution.steps,
        "reference_doc": solution.reference_doc,
        "video": solution.video,
        "escalate_if": solution.escalate_if,
    }


@api_bp.route("/flows")
def list_flows():
    """Return all available troubleshooting flows."""
    return jsonify(_engine().list_flows())


@api_bp.route("/flow/<flow_id>")
def get_flow(flow_id):
    """Return flow metadata and its first step ID."""
    engine = _engine()
    flow = engine.get_flow(flow_id)
    if not flow:
        abort(404)

    first = engine.get_first_step(flow_id)
    return jsonify(
        {
            "id": flow["id"],
            "name": flow["name"],
            "description": flow.get("description", ""),
            "first_step_id": first["data"]["id"] if first else None,
        }
    )


@api_bp.route("/flow/<flow_id>/step/<step_id>")
def get_step(flow_id, step_id):
    """Return a single step (question + options)."""
    result = _engine().get_step_by_id(flow_id, step_id)
    if not result:
        abort(404)

    step = result["data"]
    return jsonify(
        {
            "id": step["id"],
            "question": step.get("question", ""),
            "options": step.get("options", []),
        }
    )


@api_bp.route("/flow/<flow_id>/step/<step_id>/next", methods=["POST"])
def next_action(flow_id, step_id):
    """Given a choice value, return the next step or solution."""
    body = request.get_json(silent=True)
    if not body or "choice" not in body:
        return jsonify({"error": "Missing 'choice' in request body"}), 400

    action = _engine().get_next_action(flow_id, step_id, body["choice"])
    if not action:
        return jsonify({"error": "Invalid choice or no next action defined"}), 400

    if action["type"] == "step":
        step = action["data"]
        return jsonify(
            {
                "type": "step",
                "data": {
                    "id": step["id"],
                    "question": step.get("question", ""),
                    "options": step.get("options", []),
                },
            }
        )

    if action["type"] == "solution":
        return jsonify({"type": "solution", "data": _solution_dict(action["data"])})

    return jsonify({"error": "Unexpected action type"}), 500


@api_bp.route("/solution/<solution_id>")
def get_solution(solution_id):
    """Return a solution by ID."""
    solution = _engine().get_solution(solution_id)
    if not solution:
        abort(404)
    return jsonify(_solution_dict(solution))


@api_bp.route("/log", methods=["POST"])
def log_session():
    """Persist a completed troubleshooting session."""
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Missing request body"}), 400
    _logger().log_session(body)
    return jsonify({"ok": True})
