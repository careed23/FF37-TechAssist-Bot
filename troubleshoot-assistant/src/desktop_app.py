import argparse
from datetime import datetime
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.parse import urlparse
import webbrowser

from flow_engine import TroubleshootingEngine
from logger import TroubleshootingLogger


def _resolve_app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


APP_ROOT = _resolve_app_root()
DATA_PATH = APP_ROOT / "data" / "troubleshooting_flows.yaml"
LOG_PATH = APP_ROOT / "logs" / "troubleshooting_log.csv"


class TechAssistDesktopApp:
    def __init__(self, root: tk.Tk, flows_path: Path, log_path: Path):
        self.root = root
        self.engine = TroubleshootingEngine(str(flows_path))
        self.logger = TroubleshootingLogger(str(log_path))
        self.current_flow = None
        self.current_step = None
        self.current_solution = None
        self.session_data = {}
        self.choice_var = tk.StringVar()
        self.resolution_var = tk.StringVar()

        self._configure_window()
        self._build_layout()
        self.show_flow_list()

    def _configure_window(self) -> None:
        self.root.title("FF37 TechAssist Bot")
        self.root.geometry("980x680")
        self.root.minsize(860, 600)
        self.root.configure(background="#f5f7fb")
        self.root.option_add("*Font", ("Segoe UI", 10))

        style = ttk.Style(self.root)
        theme_names = {name.lower() for name in style.theme_names()}
        if sys.platform.startswith("win") and "vista" in theme_names:
            style.theme_use("vista")
        elif "clam" in theme_names:
            style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("TLabel", background="#f5f7fb", foreground="#1f2937")
        style.configure("TButton", font=("Segoe UI", 10), padding=(14, 6))
        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=30,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.map(
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", "#1d4ed8")],
        )
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#1d4ed8")
        style.configure("Subheader.TLabel", font=("Segoe UI", 10), foreground="#4b5563")
        style.configure("Section.TLabel", font=("Segoe UI", 14, "bold"), foreground="#111827")
        style.configure("Question.TLabel", font=("Segoe UI", 12, "bold"), foreground="#111827")
        style.configure(
            "Option.TRadiobutton",
            font=("Segoe UI", 11),
            background="#f5f7fb",
            foreground="#111827",
        )

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(24, 18))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="FF37 TechAssist Bot", style="Header.TLabel")
        title.grid(row=0, column=0, sticky="w")
        subtitle = ttk.Label(
            header,
            text="Interactive Troubleshooting Assistant",
            style="Subheader.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.home_button = ttk.Button(header, text="All Issues", command=self.show_flow_list)
        self.home_button.grid(row=0, column=1, rowspan=2, sticky="e")

        self.content = ttk.Frame(self.root, padding=(28, 18))
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)

    def _clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def _reset_session(self) -> None:
        self.session_data = {
            "flow_id": None,
            "flow_name": None,
            "steps_taken": [],
            "solution_id": None,
            "resolved": None,
            "start_time": None,
            "end_time": None,
        }

    def show_flow_list(self) -> None:
        self._clear_content()
        self._reset_session()
        self.current_flow = None
        self.current_step = None
        self.current_solution = None
        self.home_button.state(["disabled"])

        heading = ttk.Label(
            self.content,
            text="Select a troubleshooting scenario",
            style="Section.TLabel",
        )
        heading.grid(row=0, column=0, sticky="w")

        flows = self.engine.list_flows()
        if not flows:
            ttk.Label(self.content, text="No troubleshooting flows are available.").grid(
                row=1, column=0, sticky="w", pady=(12, 0)
            )
            return

        tree_frame = ttk.Frame(self.content)
        tree_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        tree_frame.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)

        columns = ("Issue", "Description")
        self.flow_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        self.flow_tree.heading("Issue", text="Issue")
        self.flow_tree.heading("Description", text="Description")
        self.flow_tree.column("Issue", width=240, anchor="w")
        self.flow_tree.column("Description", width=600, anchor="w")
        self.flow_tree.tag_configure("even", background="#f9fafb")
        self.flow_tree.tag_configure("odd", background="#ffffff")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.flow_tree.yview)
        self.flow_tree.configure(yscrollcommand=scrollbar.set)

        self.flow_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._flow_lookup = {}
        for idx, flow in enumerate(flows):
            tag = "even" if idx % 2 == 0 else "odd"
            item = self.flow_tree.insert(
                "", "end", values=(flow["name"], flow["description"]), tags=(tag,)
            )
            self._flow_lookup[item] = flow["id"]

        self.flow_tree.bind("<Double-1>", lambda event: self._start_selected_flow())

        actions = ttk.Frame(self.content)
        actions.grid(row=2, column=0, sticky="e", pady=(16, 0))
        ttk.Button(actions, text="Start Selected Issue", command=self._start_selected_flow).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(actions, text="Exit", command=self.root.destroy).grid(row=0, column=1)

    def _start_selected_flow(self) -> None:
        selected = self.flow_tree.selection()
        if not selected:
            messagebox.showwarning("Select an Issue", "Please select an issue to continue.")
            return
        flow_id = self._flow_lookup.get(selected[0])
        if not flow_id:
            messagebox.showerror("Error", "Unable to load the selected troubleshooting flow.")
            return
        self.start_flow(flow_id)

    def start_flow(self, flow_id: str) -> None:
        flow = self.engine.get_flow(flow_id)
        if not flow:
            messagebox.showerror("Error", "Unable to load the selected troubleshooting flow.")
            return

        first_step = self.engine.get_first_step(flow_id)
        if not first_step or first_step.get("type") != "step":
            messagebox.showerror("Error", "The selected flow does not contain any steps.")
            return

        self.session_data.update(
            {
                "flow_id": flow["id"],
                "flow_name": flow["name"],
                "steps_taken": [],
                "solution_id": None,
                "resolved": None,
                "start_time": datetime.now(),
                "end_time": None,
            }
        )

        self.current_flow = flow
        self.show_step(first_step["data"])

    def show_step(self, step: dict) -> None:
        self._clear_content()
        self.home_button.state(["!disabled"])
        self.current_step = step
        self.choice_var.set("")

        ttk.Label(self.content, text=self.current_flow["name"], style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self.content, text=self.current_flow.get("description", "")).grid(
            row=1, column=0, sticky="w", pady=(4, 12)
        )

        ttk.Label(self.content, text=step["question"], style="Question.TLabel").grid(
            row=2, column=0, sticky="w"
        )

        options_frame = ttk.Frame(self.content)
        options_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        options_frame.columnconfigure(0, weight=1)

        for idx, option in enumerate(step.get("options", [])):
            option_frame = ttk.Frame(options_frame)
            option_frame.grid(row=idx, column=0, sticky="ew", pady=(0, 8))
            option_frame.columnconfigure(0, weight=1)

            radio = ttk.Radiobutton(
                option_frame,
                text=option["value"],
                variable=self.choice_var,
                value=option["value"],
                style="Option.TRadiobutton",
            )
            radio.grid(row=0, column=0, sticky="w")
            description = option.get("description")
            if description:
                ttk.Label(option_frame, text=description).grid(
                    row=1, column=0, sticky="w", padx=(24, 0)
                )

        actions = ttk.Frame(self.content)
        actions.grid(row=4, column=0, sticky="e", pady=(20, 0))
        ttk.Button(actions, text="Continue", command=self._advance_step).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(actions, text="Cancel", command=self.show_flow_list).grid(row=0, column=1)

    def _advance_step(self) -> None:
        choice = self.choice_var.get()
        if not choice:
            messagebox.showwarning("Selection Required", "Select an option to continue.")
            return

        selected_option = next(
            (
                option
                for option in self.current_step.get("options", [])
                if option["value"] == choice
            ),
            None,
        )
        if not selected_option:
            messagebox.showerror(
                "Selection Error",
                "The selected option could not be found. Please try again.",
            )
            return
        self.session_data["steps_taken"].append(
            {
                "step_id": self.current_step.get("id", "unknown"),
                "question": self.current_step.get("question"),
                "answer": selected_option["value"],
                "answer_description": selected_option.get("description", ""),
            }
        )

        next_action = self.engine.get_next_action(
            self.current_flow["id"], self.current_step.get("id"), selected_option["value"]
        )
        if not next_action:
            messagebox.showerror(
                "Configuration Error",
                "No next action found for this option. Please contact support.",
            )
            return

        if next_action["type"] == "solution":
            self.show_solution(next_action["data"])
        elif next_action["type"] == "step":
            self.show_step(next_action["data"])
        else:
            messagebox.showerror(
                "Configuration Error",
                "Unexpected flow action type. Please contact support.",
            )

    def show_solution(self, solution) -> None:
        self._clear_content()
        self.home_button.state(["!disabled"])
        self.resolution_var.set("")
        self.current_solution = solution

        title = self._get_solution_value(solution, "title", "")
        steps = self._get_solution_value(solution, "steps", [])
        reference_doc = self._get_solution_value(solution, "reference_doc")
        video = self._get_solution_value(solution, "video")
        escalate_if = self._get_solution_value(solution, "escalate_if")

        ttk.Label(
            self.content,
            text=f"Resolution: {title}",
            style="Section.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(self.content, text=self.current_flow["name"]).grid(
            row=1, column=0, sticky="w", pady=(4, 12)
        )

        steps_frame = ttk.Frame(self.content)
        steps_frame.grid(row=2, column=0, sticky="ew")
        steps_frame.columnconfigure(0, weight=1)

        for idx, step in enumerate(steps, 1):
            ttk.Label(
                steps_frame,
                text=f"{idx}. {step}",
                wraplength=820,
                justify="left",
            ).grid(row=idx - 1, column=0, sticky="w", pady=(0, 6))

        metadata = ttk.Frame(self.content)
        metadata.grid(row=3, column=0, sticky="w", pady=(12, 0))

        if reference_doc:
            ttk.Label(metadata, text=f"Reference: {reference_doc}").grid(
                row=0, column=0, sticky="w"
            )
            ttk.Button(
                metadata,
                text="Open Reference",
                command=lambda: self._open_resource("Reference", reference_doc),
            ).grid(row=0, column=1, padx=(8, 0))

        if video:
            ttk.Label(metadata, text=f"Video: {video}").grid(row=1, column=0, sticky="w")
            ttk.Button(
                metadata,
                text="Open Video",
                command=lambda: self._open_resource("Video", video),
            ).grid(row=1, column=1, padx=(8, 0))

        if escalate_if:
            ttk.Label(
                self.content,
                text=f"Escalate if: {escalate_if}",
                wraplength=820,
            ).grid(row=4, column=0, sticky="w", pady=(12, 0))

        resolution_frame = ttk.Frame(self.content)
        resolution_frame.grid(row=5, column=0, sticky="w", pady=(18, 0))
        ttk.Radiobutton(
            resolution_frame,
            text="Issue resolved",
            variable=self.resolution_var,
            value="yes",
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            resolution_frame,
            text="Needs escalation",
            variable=self.resolution_var,
            value="no",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        actions = ttk.Frame(self.content)
        actions.grid(row=6, column=0, sticky="e", pady=(18, 0))
        ttk.Button(actions, text="Complete Session", command=self._complete_session).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(actions, text="Start Over", command=self.show_flow_list).grid(row=0, column=1)

    def _extract_solution_id(self, solution) -> str:
        return self._get_solution_value(solution, "id", "")

    def _open_resource(self, label: str, resource: str) -> None:
        resource_path = Path(resource).expanduser()
        if not resource_path.is_absolute():
            resource_path = APP_ROOT / resource_path
        if resource_path.exists():
            webbrowser.open_new_tab(resource_path.resolve().as_uri())
            return
        parsed = urlparse(resource)
        if parsed.scheme in {"http", "https"}:
            webbrowser.open_new_tab(resource)
            return
        messagebox.showinfo(
            f"{label} unavailable",
            f"{label} '{resource}' was not found as a local file or URL.",
        )

    def _get_solution_value(self, solution, key: str, default=None):
        if hasattr(solution, key):
            return getattr(solution, key)
        if isinstance(solution, dict):
            return solution.get(key, default)
        return default

    def _complete_session(self) -> None:
        resolved_value = self.resolution_var.get()
        if resolved_value not in {"yes", "no"}:
            messagebox.showwarning(
                "Outcome Required", "Please confirm the outcome to complete this session."
            )
            return

        resolved = resolved_value == "yes"
        end_time = datetime.now()
        start_time = self.session_data.get("start_time")
        duration = 0
        if start_time:
            duration = (end_time - start_time).total_seconds()

        self.session_data.update(
            {
                "solution_id": self._extract_solution_id(self.current_solution),
                "resolved": resolved,
                "end_time": end_time,
                "duration": duration,
            }
        )
        self.logger.log_session(self.session_data)
        self.show_completion(resolved)

    def show_completion(self, resolved: bool) -> None:
        self._clear_content()
        self.home_button.state(["!disabled"])

        message = (
            f"✅ Great news! The {self.session_data.get('flow_name')} issue was resolved and logged."
            if resolved
            else (
                f"⚠️ The session has been logged. Please follow escalation procedures for "
                f"{self.session_data.get('flow_name')}."
            )
        )

        ttk.Label(self.content, text="Session logged", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self.content, text=message, wraplength=820).grid(
            row=1, column=0, sticky="w", pady=(8, 16)
        )

        actions = ttk.Frame(self.content)
        actions.grid(row=2, column=0, sticky="e")
        ttk.Button(
            actions, text="Troubleshoot another issue", command=self.show_flow_list
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Exit", command=self.root.destroy).grid(row=0, column=1)

    def capture_screenshot(self, path: Path) -> None:
        try:
            from PIL import ImageGrab
        except ImportError as exc:
            raise RuntimeError("Pillow is required for --screenshot output.") from exc

        self.root.update_idletasks()
        self.root.update()
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        ImageGrab.grab(bbox=(x, y, x + width, y + height)).save(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FF37 TechAssist Bot Desktop GUI")
    parser.add_argument("--flows", type=Path, default=DATA_PATH, help="Path to YAML flows file")
    parser.add_argument("--log", type=Path, default=LOG_PATH, help="Path to CSV log file")
    parser.add_argument(
        "--screenshot",
        type=Path,
        help="Optional path to save a screenshot of the main window",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = tk.Tk()
    app = TechAssistDesktopApp(root, args.flows, args.log)

    if args.screenshot:
        def _take_screenshot():
            try:
                app.capture_screenshot(args.screenshot)
            finally:
                root.after(200, root.destroy)

        root.after(800, _take_screenshot)

    root.mainloop()


if __name__ == "__main__":
    main()
