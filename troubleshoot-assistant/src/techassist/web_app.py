"""
FF37-TechAssist-Bot — Flask web application.

Uses file-based Jinja2 templates (``templates/``) and a static CSS file
(``static/style.css``) instead of inline strings, keeping the module
focused on route logic.
"""

from datetime import datetime
from pathlib import Path
import os

from flask import (
    Blueprint,
    Flask,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from .flow_engine import TroubleshootingEngine
from .logger import TroubleshootingLogger

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DATA_PATH = PROJECT_ROOT / "data"
LOG_PATH = PROJECT_ROOT / "logs" / "troubleshooting_log.csv"
SECRET_KEY_PATH = PROJECT_ROOT / "logs" / ".secret_key"
REACT_DIST = PROJECT_ROOT.parent / "web-frontend" / "dist"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def load_secret_key() -> str:
    """Load or generate a secret key for Flask session encryption."""
    env_key = os.environ.get("TECHASSIST_SECRET_KEY")
    if env_key:
        if len(env_key) < 32:
            raise ValueError(
                "TECHASSIST_SECRET_KEY must be at least 32 characters long "
                "for secure session encryption."
            )
        return env_key

    def read_stored_key():
        try:
            stored = SECRET_KEY_PATH.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None
        if stored and len(stored) >= 32:
            return stored
        return None

    SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_key = os.urandom(32).hex()
    try:
        fd = os.open(SECRET_KEY_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        stored_key = read_stored_key()
        if stored_key:
            return stored_key
        fd = os.open(SECRET_KEY_PATH, os.O_WRONLY | os.O_TRUNC, 0o600)

    with os.fdopen(fd, "w", encoding="utf-8") as secret_file:
        try:
            os.fchmod(secret_file.fileno(), 0o600)
        except OSError:
            pass
        secret_file.write(generated_key)
    return generated_key


def _set_initial_session_data(flow: dict) -> None:
    """Populate the Flask session with fresh troubleshooting data."""
    session["session_data"] = {
        "flow_id": flow["id"],
        "flow_name": flow["name"],
        "steps_taken": [],
        "solution_id": None,
        "resolved": None,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
    }


def _get_validated_session_data(flow_id: str):
    """Return session data if it matches *flow_id*, else ``None``."""
    session_data = session.get("session_data")
    if not session_data or session_data.get("flow_id") != flow_id:
        return None
    return session_data


def _extract_solution_id(solution_data):
    """Get the id from a Solution object or dict."""
    if hasattr(solution_data, "id"):
        return solution_data.id
    if isinstance(solution_data, dict):
        return solution_data.get("id")
    return None


# ------------------------------------------------------------------
# Step POST logic
# ------------------------------------------------------------------

def _handle_step_post(engine, flow_id, step, session_data):
    """Process a POST on the step page.

    Returns ``(redirect_url, None)`` on success or ``(None, error_string)``
    on validation failure.
    """
    choice = request.form.get("choice", "").strip()
    options_by_value = {
        option["value"]: option for option in step.get("options", [])
    }
    selected_option = options_by_value.get(choice)

    if not selected_option:
        return None, "Please select an option to continue. If this persists, refresh the page."

    session_data["steps_taken"].append(
        {
            "step_id": step.get("id", "unknown"),
            "question": step.get("question"),
            "answer": selected_option["value"],
            "answer_description": selected_option.get("description", ""),
        }
    )
    session["session_data"] = session_data

    next_action = engine.get_next_action(
        flow_id, step.get("id"), selected_option["value"]
    )
    if not next_action:
        return None, (
            "Configuration error: No next action defined for the selected option. "
            "Please contact support."
        )

    if next_action["type"] == "solution":
        sol_id = _extract_solution_id(next_action["data"])
        if not sol_id:
            return None, (
                "Configuration error: Solution is missing an identifier. "
                "Please contact support."
            )
        return url_for("main.solution_view", flow_id=flow_id, solution_id=sol_id), None

    if next_action["type"] == "step":
        return url_for(
            "main.flow_step", flow_id=flow_id, step_id=next_action["data"]["id"]
        ), None

    return None, (
        "Configuration error: Unexpected flow action type. Please contact support."
    )


# ------------------------------------------------------------------
# Solution POST logic
# ------------------------------------------------------------------

def _handle_solution_post(logger, flow, solution, session_data):
    """Process a POST on the solution page.

    Returns ``(response, None)`` on success or ``(None, error_string)``
    on validation failure.
    """
    resolved_value = request.form.get("resolved")
    if resolved_value not in {"yes", "no"}:
        return None, "Please confirm the outcome to complete this session."

    resolved = resolved_value == "yes"
    end_time = datetime.now()
    sol_id = _extract_solution_id(solution)

    session_data["solution_id"] = sol_id or ""
    session_data["resolved"] = resolved
    session_data["end_time"] = end_time.isoformat()

    duration = 0
    start_time = session_data.get("start_time")
    if start_time:
        try:
            duration = (
                end_time - datetime.fromisoformat(start_time)
            ).total_seconds()
        except ValueError:
            pass

    session_data["duration"] = duration
    logger.log_session(session_data)
    session.pop("session_data", None)

    response = render_template(
        "complete.html",
        title="Session Complete | FF37 TechAssist Bot",
        resolved=resolved,
        flow_name=flow.get("name", "this"),
    )
    return response, None


# ------------------------------------------------------------------
# Blueprint with top-level route handlers
# ------------------------------------------------------------------

bp = Blueprint("main", __name__)


def _get_engine() -> TroubleshootingEngine:
    return current_app.config["ENGINE"]


def _get_logger() -> TroubleshootingLogger:
    return current_app.config["LOGGER"]


@bp.route("/")
def index():
    flows = _get_engine().list_flows()
    return render_template(
        "index.html", title="FF37 TechAssist Bot", flows=flows
    )


@bp.route("/flow/<flow_id>/start")
def start_flow(flow_id):
    engine = _get_engine()
    flow = engine.get_flow(flow_id)
    if not flow:
        abort(404)

    _set_initial_session_data(flow)
    first_step = engine.get_first_step(flow_id)
    if not first_step or first_step.get("type") != "step":
        abort(404)

    return redirect(
        url_for("main.flow_step", flow_id=flow_id, step_id=first_step["data"]["id"])
    )


@bp.route("/flow/<flow_id>/step/<step_id>", methods=["GET", "POST"])
def flow_step(flow_id, step_id):
    engine = _get_engine()
    flow = engine.get_flow(flow_id)
    if not flow:
        abort(404)

    session_data = _get_validated_session_data(flow_id)
    if not session_data:
        return redirect(url_for("main.start_flow", flow_id=flow_id))

    step_result = engine.get_step_by_id(flow_id, step_id)
    if not step_result or step_result.get("type") != "step":
        abort(404)

    step = step_result["data"]
    error = None

    if request.method == "POST":
        redirect_url, error = _handle_step_post(
            engine, flow_id, step, session_data
        )
        if redirect_url:
            return redirect(redirect_url)

    return render_template(
        "step.html",
        title=f"{flow['name']} | FF37 TechAssist Bot",
        flow=flow,
        step=step,
        error=error,
    )


@bp.route("/flow/<flow_id>/solution/<solution_id>", methods=["GET", "POST"])
def solution_view(flow_id, solution_id):
    engine = _get_engine()
    logger = _get_logger()
    flow = engine.get_flow(flow_id)
    if not flow:
        abort(404)

    session_data = _get_validated_session_data(flow_id)
    if not session_data:
        return redirect(url_for("main.start_flow", flow_id=flow_id))

    solution = engine.get_solution(solution_id)
    if not solution:
        abort(404)

    error = None

    if request.method == "POST":
        response, error = _handle_solution_post(
            logger, flow, solution, session_data
        )
        if response is not None:
            return response

    return render_template(
        "solution.html",
        title=f"Resolution | {flow['name']}",
        solution=solution,
        flow=flow,
        error=error,
    )


# ------------------------------------------------------------------
# Application factory
# ------------------------------------------------------------------

def create_app() -> Flask:
    """Build and return the configured Flask application."""
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.secret_key = load_secret_key()

    # Temporarily load only generated_flows.yaml for debugging
    #app.config["ENGINE"] = TroubleshootingEngine(str(DATA_PATH))
    #app.config["LOGGER"] = TroubleshootingLogger(str(LOG_PATH))

    # JSON API blueprint (always registered)
    from .api import api_bp  # noqa: PLC0415
    app.register_blueprint(api_bp)

    if REACT_DIST.exists():
        # Serve the React SPA: static assets by path, index.html for all other routes.
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_react(path: str = ""):  # pragma: no cover
            if path.startswith("api/") or path.startswith("static/"):
                abort(404)
            full = REACT_DIST / path
            if path and full.is_file():
                return send_from_directory(str(REACT_DIST), path)
            return send_from_directory(str(REACT_DIST), "index.html")
    else:
        # Fall back to the original Jinja2 UI when no React build is present.
        app.register_blueprint(bp)

    app.logger.info(f"App config: {app.config}")
    return app


app = create_app()


def main() -> None:
    """Entry point for the web application."""
    app.logger.warning(
        "Development server active on 127.0.0.1. "
        "Use a production WSGI server for deployments."
    )
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
