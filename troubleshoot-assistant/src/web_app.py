from datetime import datetime
from pathlib import Path
import os

from flask import Flask, abort, redirect, render_template, request, session, url_for
from jinja2 import DictLoader

from flow_engine import TroubleshootingEngine
from logger import TroubleshootingLogger

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "troubleshooting_flows.yaml"
LOG_PATH = BASE_DIR.parent / "logs" / "troubleshooting_log.csv"
SECRET_KEY_PATH = BASE_DIR.parent / "logs" / ".secret_key"

BASE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ title }}</title>
  <style>
    body {
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background: #f5f7fb;
      margin: 0;
      color: #1f2a44;
    }
    .container {
      max-width: 960px;
      margin: 40px auto;
      background: #fff;
      padding: 32px;
      border-radius: 16px;
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 16px;
      margin-bottom: 24px;
    }
    h1 {
      font-size: 1.6rem;
      margin: 0;
    }
    h2 {
      margin-top: 0;
      color: #1f2937;
    }
    .subheading {
      color: #64748b;
      font-size: 0.95rem;
    }
    a {
      color: #2563eb;
      text-decoration: none;
    }
    a.button, button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 10px 18px;
      border-radius: 10px;
      border: none;
      background: #2563eb;
      color: #fff;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
    }
    a.button.secondary, button.secondary {
      background: #0f172a;
    }
    .flow-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 16px;
    }
    .flow-card {
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }
    .flow-title {
      font-weight: 700;
      margin-bottom: 6px;
    }
    .flow-description {
      color: #64748b;
      margin: 0;
    }
    form {
      display: grid;
      gap: 16px;
    }
    .option {
      display: grid;
      gap: 6px;
      padding: 14px;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
      cursor: pointer;
    }
    .option:hover {
      border-color: #94a3b8;
      background: #f8fafc;
    }
    .option input {
      margin-right: 8px;
    }
    .option-label {
      font-weight: 600;
    }
    .option-description {
      color: #64748b;
      font-size: 0.92rem;
    }
    .metadata {
      background: #f1f5f9;
      padding: 14px;
      border-radius: 10px;
      color: #475569;
      display: grid;
      gap: 8px;
    }
    .callout {
      border-left: 4px solid #f59e0b;
      background: #fffbeb;
      padding: 12px 16px;
      border-radius: 8px;
      color: #92400e;
    }
    .error {
      color: #b91c1c;
      background: #fee2e2;
      padding: 10px 14px;
      border-radius: 10px;
    }
    ol {
      padding-left: 20px;
    }
    .footer-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>FF37 TechAssist Bot</h1>
        <div class="subheading">Interactive Troubleshooting Assistant</div>
      </div>
      <a class="button secondary" href="{{ url_for('index') }}">All Issues</a>
    </header>
    {% block content %}{% endblock %}
  </div>
</body>
</html>
"""

INDEX_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>Select a troubleshooting scenario</h2>
{% if flows %}
<ul class="flow-list">
  {% for flow in flows %}
  <li class="flow-card">
    <div>
      <div class="flow-title">{{ flow.name }}</div>
      <p class="flow-description">{{ flow.description }}</p>
    </div>
    <a class="button" href="{{ url_for('start_flow', flow_id=flow.id) }}">Start</a>
  </li>
  {% endfor %}
</ul>
{% else %}
<p>No troubleshooting flows are available.</p>
{% endif %}
{% endblock %}
"""

STEP_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>{{ flow.name }}</h2>
<p class="subheading">{{ flow.description }}</p>
<h3>{{ step.question }}</h3>
{% if error %}
<div class="error">{{ error }}</div>
{% endif %}
<form method="post">
  {% for option in step.options %}
  <label class="option">
    <div>
      <input type="radio" name="choice" value="{{ option.value }}" required />
      <span class="option-label">{{ option.value }}</span>
    </div>
    {% if option.description %}
    <div class="option-description">{{ option.description }}</div>
    {% endif %}
  </label>
  {% endfor %}
  <div class="footer-actions">
    <button type="submit">Continue</button>
    <a class="button secondary" href="{{ url_for('index') }}">Cancel</a>
  </div>
</form>
{% endblock %}
"""

SOLUTION_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>Resolution: {{ solution.title }}</h2>
<p class="subheading">{{ flow.name }}</p>
<ol>
  {% for step in solution.steps %}
  <li>{{ step }}</li>
  {% endfor %}
</ol>
<div class="metadata">
  {% if solution.reference_doc %}
  <div><strong>Reference:</strong> <a href="{{ solution.reference_doc }}" target="_blank" rel="noopener">{{ solution.reference_doc }}</a></div>
  {% endif %}
  {% if solution.video %}
  <div><strong>Video:</strong> <a href="{{ solution.video }}" target="_blank" rel="noopener">{{ solution.video }}</a></div>
  {% endif %}
</div>
{% if solution.escalate_if %}
<div class="callout"><strong>Escalate if:</strong> {{ solution.escalate_if }}</div>
{% endif %}
{% if error %}
<div class="error">{{ error }}</div>
{% endif %}
<form method="post">
  <div>
    <label><input type="radio" name="resolved" value="yes" required /> Issue resolved</label>
  </div>
  <div>
    <label><input type="radio" name="resolved" value="no" required /> Needs escalation</label>
  </div>
  <div class="footer-actions">
    <button type="submit">Complete Session</button>
    <a class="button secondary" href="{{ url_for('index') }}">Start Over</a>
  </div>
</form>
{% endblock %}
"""

COMPLETE_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>Session logged</h2>
<p>
  {% if resolved %}
  ✅ Great news! The {{ flow_name }} issue was resolved and logged for analytics.
  {% else %}
  ⚠️ The session has been logged. Please follow escalation procedures for {{ flow_name }}.
  {% endif %}
</p>
<div class="footer-actions">
  <a class="button" href="{{ url_for('index') }}">Troubleshoot another issue</a>
</div>
{% endblock %}
"""


def load_secret_key() -> str:
    env_key = os.environ.get("TECHASSIST_SECRET_KEY")
    if env_key:
        if len(env_key) < 32:
            raise ValueError(
                "TECHASSIST_SECRET_KEY must be at least 32 characters long for secure session encryption."
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


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = load_secret_key()

    engine = TroubleshootingEngine(str(DATA_PATH))
    logger = TroubleshootingLogger(str(LOG_PATH))

    app.jinja_loader = DictLoader(
        {
            "base.html": BASE_TEMPLATE,
            "index.html": INDEX_TEMPLATE,
            "step.html": STEP_TEMPLATE,
            "solution.html": SOLUTION_TEMPLATE,
            "complete.html": COMPLETE_TEMPLATE,
        }
    )

    def render_page(template_name: str, **context):
        return render_template(template_name, **context)

    def set_initial_session_data(flow: dict):
        session["session_data"] = {
            "flow_id": flow["id"],
            "flow_name": flow["name"],
            "steps_taken": [],
            "solution_id": None,
            "resolved": None,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
        }

    def get_validated_session_data(flow_id: str):
        session_data = session.get("session_data")
        if not session_data or session_data.get("flow_id") != flow_id:
            return None
        return session_data


    def extract_solution_id(solution_data):
        if hasattr(solution_data, "id"):
            return solution_data.id
        if isinstance(solution_data, dict):
            return solution_data.get("id")
        return None

    @app.route("/")
    def index():
        flows = engine.list_flows()
        return render_page("index.html", title="FF37 TechAssist Bot", flows=flows)

    @app.route("/flow/<flow_id>/start")
    def start_flow(flow_id):
        flow = engine.get_flow(flow_id)
        if not flow:
            abort(404)

        set_initial_session_data(flow)
        first_step = engine.get_first_step(flow_id)
        if not first_step or first_step.get("type") != "step":
            abort(404)

        return redirect(
            url_for("flow_step", flow_id=flow_id, step_id=first_step["data"]["id"])
        )

    @app.route("/flow/<flow_id>/step/<step_id>", methods=["GET", "POST"])
    def flow_step(flow_id, step_id):
        flow = engine.get_flow(flow_id)
        if not flow:
            abort(404)

        session_data = get_validated_session_data(flow_id)
        if not session_data:
            return redirect(url_for("start_flow", flow_id=flow_id))

        step_result = engine.get_step_by_id(flow_id, step_id)
        if not step_result or step_result.get("type") != "step":
            abort(404)

        step = step_result["data"]
        error = None

        if request.method == "POST":
            choice = request.form.get("choice", "").strip()
            options_by_value = {option["value"]: option for option in step.get("options", [])}
            selected_option = options_by_value.get(choice)
            if not selected_option:
                error = "Please select an option to continue. If this persists, refresh the page."
            else:
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
                    error = (
                        "Configuration error: No next action defined for the selected option. "
                        "Please contact support."
                    )
                elif next_action["type"] == "solution":
                    solution_id = extract_solution_id(next_action["data"])
                    if not solution_id:
                        error = (
                            "Configuration error: Solution is missing an identifier. "
                            "Please contact support."
                        )
                    else:
                        return redirect(
                            url_for(
                                "solution_view",
                                flow_id=flow_id,
                                solution_id=solution_id,
                            )
                        )
                elif next_action["type"] == "step":
                    return redirect(
                        url_for(
                            "flow_step",
                            flow_id=flow_id,
                            step_id=next_action["data"]["id"],
                        )
                    )
                else:
                    error = "Configuration error: Unexpected flow action type. Please contact support."

        return render_page(
            "step.html",
            title=f"{flow['name']} | FF37 TechAssist Bot",
            flow=flow,
            step=step,
            error=error,
        )

    @app.route("/flow/<flow_id>/solution/<solution_id>", methods=["GET", "POST"])
    def solution_view(flow_id, solution_id):
        flow = engine.get_flow(flow_id)
        if not flow:
            abort(404)

        session_data = get_validated_session_data(flow_id)
        if not session_data:
            return redirect(url_for("start_flow", flow_id=flow_id))

        solution = engine.get_solution(solution_id)
        if not solution:
            abort(404)

        error = None

        if request.method == "POST":
            resolved_value = request.form.get("resolved")
            if resolved_value not in {"yes", "no"}:
                error = "Please confirm the outcome to complete this session."
            else:
                resolved = resolved_value == "yes"
                end_time = datetime.now()
                solution_id = extract_solution_id(solution)

                session_data["solution_id"] = solution_id or ""
                session_data["resolved"] = resolved
                session_data["end_time"] = end_time.isoformat()

                duration = 0
                start_time = session_data.get("start_time")
                if start_time:
                    try:
                        duration = (end_time - datetime.fromisoformat(start_time)).total_seconds()
                    except ValueError as exc:
                        app.logger.warning("Could not parse session start time: %s", exc)

                session_data["duration"] = duration
                logger.log_session(session_data)
                session.pop("session_data", None)

                return render_page(
                    "complete.html",
                    title="Session Complete | FF37 TechAssist Bot",
                    resolved=resolved,
                    flow_name=flow.get("name", "this"),
                )

        return render_page(
            "solution.html",
            title=f"Resolution | {flow['name']}",
            solution=solution,
            flow=flow,
            error=error,
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.logger.warning(
        "Development server active on 127.0.0.1. Use a production WSGI server for deployments."
    )
    app.run(host="127.0.0.1", port=5000, debug=False)
