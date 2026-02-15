import argparse
from datetime import datetime
import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.parse import urlparse
import webbrowser

from flow_engine import TroubleshootingEngine
from logger import TroubleshootingLogger

APP_NAME = "FF37-TechAssist-Bot"


def _resolve_app_root() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", project_root))
    return project_root


def _resolve_log_root(app_root: Path) -> Path:
    if getattr(sys, "frozen", False):
        app_data = os.environ.get("APPDATA")
        base_dir = Path(app_data) if app_data else Path.home()
        return base_dir / APP_NAME / "logs"
    return app_root / "logs"


APP_ROOT = _resolve_app_root()
DATA_PATH = APP_ROOT / "data" / "troubleshooting_flows.yaml"
LOG_ROOT = _resolve_log_root(APP_ROOT)
LOG_PATH = LOG_ROOT / "troubleshooting_log.csv"


class TechAssistDesktopApp:
    HEADER_ROWS_WITH_LOGO = 4
    HEADER_ROWS_WITHOUT_LOGO = 3
    TARGET_LOGO_WIDTH = 260

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
        self._hovered_item = None
        self._row_tags = {}

        self._configure_window()
        self._build_layout()
        self.show_flow_list()

    def _configure_window(self) -> None:
        self.root.title("FF37 TechAssist Bot")
        self.root.geometry("980x680")
        self.root.minsize(860, 600)
        mica_background = "#eef2f8"
        card_background = "#ffffff"
        text_primary = "#0f172a"
        text_secondary = "#5b6b82"
        accent_color = "#00bfa5"

        self.root.configure(background=mica_background)
        self.root.option_add("*Font", ("Segoe UI Variable", 10))

        style = ttk.Style(self.root)
        theme_names = {name.lower() for name in style.theme_names()}
        if sys.platform.startswith("win") and "vista" in theme_names:
            style.theme_use("vista")
        elif "clam" in theme_names:
            style.theme_use("clam")
        style.configure("TFrame", background=mica_background)
        style.configure("Content.TFrame", background=mica_background)
        style.configure("Card.TFrame", background=card_background, borderwidth=1, relief="solid")
        style.configure("TLabel", background=mica_background, foreground=text_primary)
        style.configure("TButton", font=("Segoe UI Variable", 10), padding=(16, 8))
        style.configure(
            "Primary.TButton",
            font=("Segoe UI Variable", 10, "semibold"),
            foreground="#ffffff",
            background="#0ea5e9",
            borderwidth=0,
            padding=(20, 8),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#22d3ee"), ("pressed", "#0284c7")],
        )
        style.configure(
            "Glass.TButton",
            font=("Segoe UI Variable", 10),
            foreground=text_primary,
            background="#f8fafc",
            borderwidth=1,
            relief="solid",
            padding=(16, 8),
        )
        style.map(
            "Glass.TButton",
            background=[("active", "#ffffff"), ("pressed", "#e2e8f0")],
        )
        style.configure(
            "DataGrid.Treeview",
            font=("Segoe UI Variable", 10),
            rowheight=36,
            background=card_background,
            fieldbackground=card_background,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "DataGrid.Treeview.Heading",
            font=("Segoe UI Variable", 10, "semibold"),
            background="#e2e8f0",
            foreground=text_primary,
        )
        style.map(
            "DataGrid.Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", text_primary)],
        )
        style.configure("Header.TLabel", font=("Segoe UI Variable", 20, "semibold"), foreground=text_primary)
        style.configure("Subheader.TLabel", font=("Segoe UI Variable", 10), foreground=text_secondary)
        style.configure("Section.TLabel", font=("Segoe UI Variable", 14, "semibold"), foreground=text_primary)
        style.configure("Question.TLabel", font=("Segoe UI Variable", 12, "semibold"), foreground=text_primary)
        style.configure(
            "Option.TRadiobutton",
            font=("Segoe UI Variable", 11),
            background=mica_background,
            foreground=text_primary,
        )
        style.configure(
            "Logo.TLabel",
            font=("Segoe UI Variable", 11, "semibold"),
            foreground=accent_color,
            background=mica_background,
        )
        style.configure(
            "LogoAccent.TLabel",
            font=("Segoe UI Variable", 11, "bold"),
            foreground=accent_color,
            background=mica_background,
        )

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(32, 22), style="Content.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        brand = ttk.Frame(header, style="Content.TFrame")
        brand.grid(row=0, column=0, sticky="w")

        logo_image = self._load_logo_image()
        header_rows = (
            self.HEADER_ROWS_WITH_LOGO if logo_image else self.HEADER_ROWS_WITHOUT_LOGO
        )
        if logo_image:
            self.logo_label = ttk.Label(brand, image=logo_image)
            self.logo_label.image = logo_image
            self.logo_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        branding = ttk.Frame(brand, style="Content.TFrame")
        branding.grid(row=1, column=0, sticky="w")
        ttk.Label(branding, text="FORGED FIBER", style="Logo.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(branding, text="37", style="LogoAccent.TLabel").grid(
            row=0, column=1, sticky="w", padx=(6, 0)
        )

        title = ttk.Label(brand, text="FF37 TechAssist Bot", style="Header.TLabel")
        title.grid(row=2, column=0, sticky="w", pady=(6, 0))
        subtitle = ttk.Label(
            brand,
            text="Interactive Troubleshooting Assistant",
            style="Subheader.TLabel",
        )
        subtitle.grid(row=3, column=0, sticky="w", pady=(4, 0))

        self.home_button = ttk.Button(
            header, text="All Issues", command=self.show_flow_list, style="Glass.TButton"
        )
        self.home_button.grid(row=0, column=1, rowspan=header_rows, sticky="e")

        self.content = ttk.Frame(self.root, padding=(32, 24), style="Content.TFrame")
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

        tree_frame = ttk.Frame(self.content, style="Card.TFrame", padding=2)
        tree_frame.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        tree_frame.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)

        columns = ("Issue", "Description")
        self.flow_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=12, style="DataGrid.Treeview"
        )
        self.flow_tree.heading("Issue", text="Issue")
        self.flow_tree.heading("Description", text="Description")
        self.flow_tree.column("Issue", width=240, anchor="w")
        self.flow_tree.column("Description", width=600, anchor="w")
        self.flow_tree.tag_configure("even", background="#f8fafc")
        self.flow_tree.tag_configure("odd", background="#ffffff")
        self.flow_tree.tag_configure("hover", background="#e0f2fe")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.flow_tree.yview)
        self.flow_tree.configure(yscrollcommand=scrollbar.set)

        self.flow_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._flow_lookup = {}
        self._row_tags = {}
        for idx, flow in enumerate(flows):
            tag = "even" if idx % 2 == 0 else "odd"
            item = self.flow_tree.insert(
                "", "end", values=(flow["name"], flow["description"]), tags=(tag,)
            )
            self._flow_lookup[item] = flow["id"]
            self._row_tags[item] = tag

        self.flow_tree.bind("<Double-1>", lambda event: self._start_selected_flow())
        self.flow_tree.bind("<Motion>", self._on_tree_motion)
        self.flow_tree.bind("<Leave>", self._on_tree_leave)

        actions = ttk.Frame(self.content)
        actions.grid(row=2, column=0, sticky="e", pady=(20, 0))
        ttk.Button(
            actions,
            text="Start Selected Issue",
            command=self._start_selected_flow,
            style="Primary.TButton",
        ).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(actions, text="Exit", command=self.root.destroy, style="Glass.TButton").grid(
            row=0, column=1
        )

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

    def _on_tree_motion(self, event: tk.Event) -> None:
        row_id = self.flow_tree.identify_row(event.y)
        if row_id == self._hovered_item:
            return
        if self._hovered_item:
            base_tag = self._row_tags.get(self._hovered_item)
            if base_tag:
                self.flow_tree.item(self._hovered_item, tags=(base_tag,))
        self._hovered_item = row_id
        if row_id:
            base_tag = self._row_tags.get(row_id)
            tags = (base_tag, "hover") if base_tag else ("hover",)
            self.flow_tree.item(row_id, tags=tags)

    def _on_tree_leave(self, _event: tk.Event) -> None:
        if not self._hovered_item:
            return
        base_tag = self._row_tags.get(self._hovered_item)
        if base_tag:
            self.flow_tree.item(self._hovered_item, tags=(base_tag,))
        self._hovered_item = None

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
        options_frame.grid(row=3, column=0, sticky="ew", pady=(16, 0))
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
        actions.grid(row=4, column=0, sticky="e", pady=(22, 0))
        ttk.Button(actions, text="Continue", command=self._advance_step, style="Primary.TButton").grid(
            row=0, column=0, padx=(0, 10)
        )
        ttk.Button(actions, text="Cancel", command=self.show_flow_list, style="Glass.TButton").grid(
            row=0, column=1
        )

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
                style="Glass.TButton",
            ).grid(row=0, column=1, padx=(8, 0))

        if video:
            ttk.Label(metadata, text=f"Video: {video}").grid(row=1, column=0, sticky="w")
            ttk.Button(
                metadata,
                text="Open Video",
                command=lambda: self._open_resource("Video", video),
                style="Glass.TButton",
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
        actions.grid(row=6, column=0, sticky="e", pady=(20, 0))
        ttk.Button(
            actions, text="Complete Session", command=self._complete_session, style="Primary.TButton"
        ).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(
            actions, text="Start Over", command=self.show_flow_list, style="Glass.TButton"
        ).grid(row=0, column=1)

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

    def _load_logo_image(self):
        logo_path = APP_ROOT / "logo.png"
        if not logo_path.exists():
            return None
        try:
            image = tk.PhotoImage(file=str(logo_path))
        except tk.TclError:
            return None
        target_width = self.TARGET_LOGO_WIDTH
        if target_width <= 0:
            return image
        scale = max(1, round(image.width() / target_width))
        if scale > 1:
            image = image.subsample(scale, scale)
        return image

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
            actions,
            text="Troubleshoot another issue",
            command=self.show_flow_list,
            style="Primary.TButton",
        ).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(actions, text="Exit", command=self.root.destroy, style="Glass.TButton").grid(
            row=0, column=1
        )

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
