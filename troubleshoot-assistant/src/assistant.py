from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box
from flow_engine import TroubleshootingEngine
from logger import TroubleshootingLogger
import sys
from datetime import datetime


console = Console()


class TroubleshootAssistant:
    """
    Main interactive troubleshooting assistant
    """
    
    def __init__(self, flows_file='data/troubleshooting_flows.yaml'):
        """Initialize the assistant"""
        try:
            self.engine = TroubleshootingEngine(flows_file)
            self.logger = TroubleshootingLogger()
        except Exception as e:
            console.print(f"[bold red]Error initializing assistant: {e}[/bold red]")
            sys.exit(1)
        
        self.session_data = {
            'flow_id': None,
            'flow_name': None,
            'steps_taken': [],
            'solution_id': None,
            'resolved': None,
            'start_time': None,
            'end_time': None
        }
    
    def start(self):
        """Main entry point for the assistant"""
        console.clear()
        
        # Display header
        console.print(Panel.fit(
            "[bold cyan]🔧 FF37 TechAssist Bot[/bold cyan]\n"
            "[white]Interactive Troubleshooting Assistant[/white]\n"
            "[dim]Version 1.0 - Forged Fiber 37 Remote Tech Assist[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        
        self.session_data['start_time'] = datetime.now()
        
        # Show main menu
        self.show_main_menu()
    
    def show_main_menu(self):
        """Display available troubleshooting scenarios"""
        console.print("\n[bold white]What issue are you troubleshooting?[/bold white]\n")
        
        flows = self.engine.list_flows()
        
        if not flows:
            console.print("[red]No troubleshooting flows available.[/red]")
            return
        
        # Create table of available flows
        table = Table(
            show_header=True, 
            header_style="bold magenta",
            border_style="dim",
            box=box.ROUNDED
        )
        table.add_column("#", style="cyan", width=4, justify="center")
        table.add_column("Issue", style="white", width=40)
        table.add_column("Description", style="dim", width=60)
        
        for idx, flow in enumerate(flows, 1):
            table.add_row(
                str(idx) + "\n",
                flow['name'] + "\n",
                flow['description'] + "\n"
            )
        
        console.print(table)
        
        # Get user selection
        console.print()
        choice = Prompt.ask(
            "[bold cyan]Select issue number[/bold cyan] [dim](or 'q' to quit)[/dim]",
            choices=[str(i) for i in range(1, len(flows) + 1)] + ['q', 'Q']
        )
        
        if choice.lower() == 'q':
            console.print("\n[cyan]Goodbye![/cyan]\n")
            sys.exit(0)
        
        # Load selected flow
        selected_flow_info = flows[int(choice) - 1]
        selected_flow = self.engine.get_flow(selected_flow_info['id'])
        
        if not selected_flow:
            console.print("[red]Error: Could not load flow[/red]")
            return
        
        self.session_data['flow_id'] = selected_flow['id']
        self.session_data['flow_name'] = selected_flow['name']
        
        # Start troubleshooting
        self.run_flow(selected_flow)
    
    def run_flow(self, flow: dict):
        """Execute a troubleshooting flow"""
        console.print(f"\n[bold green]▶ Starting: {flow['name']}[/bold green]\n")
        
        # Get first step
        current_step_data = self.engine.get_first_step(flow['id'])
        
        if not current_step_data or current_step_data['type'] != 'step':
            console.print("[red]Error: Invalid flow structure[/red]")
            return
        
        current_step = current_step_data['data']
        
        # Main troubleshooting loop
        while True:
            # Display current question
            console.print(f"[bold cyan]❓ {current_step['question']}[/bold cyan]\n")
            
            # Display options
            options_table = Table(
                show_header=False,
                border_style="dim",
                box=None,
                padding=(0, 2)
            )
            options_table.add_column("Num", style="yellow", width=4)
            options_table.add_column("Option", style="white")
            
            for idx, option in enumerate(current_step['options'], 1):
                options_table.add_row(
                    f"{idx}.",
                    f"[yellow]{option['value']}[/yellow] - {option['description']}"
                )
            
            console.print(options_table)
            
            # Get user choice
            console.print()
            choice_num = Prompt.ask(
                "[bold]Select option[/bold]",
                choices=[str(i) for i in range(1, len(current_step['options']) + 1)]
            )
            
            selected_option = current_step['options'][int(choice_num) - 1]
            
            # Log the step taken
            self.session_data['steps_taken'].append({
                'step_id': current_step.get('id', 'unknown'),
                'question': current_step['question'],
                'answer': selected_option['value'],
                'answer_description': selected_option['description']
            })
            
            console.print()  # Spacing
            
            # Get next action
            next_action = self.engine.get_next_action(
                self.session_data['flow_id'],
                current_step.get('id'),
                selected_option['value']
            )
            
            if not next_action:
                console.print("[red]Error: Invalid flow configuration - no next action found[/red]")
                break
            
            # Handle next action
            if next_action['type'] == 'solution':
                # Display solution and end flow
                self.show_solution(next_action['data'])
                break
            
            elif next_action['type'] == 'step':
                # Continue to next step
                current_step = next_action['data']
            
            else:
                console.print(f"[red]Error: Unknown action type: {next_action['type']}[/red]")
                break
    
    def show_solution(self, solution):
        """Display resolution steps and complete session"""
        console.print(Panel.fit(
            f"[bold green]✓ Resolution: {solution.title}[/bold green]",
            border_style="green",
            box=box.DOUBLE
        ))
        
        console.print()
        
        # Display resolution steps
        console.print("[bold white]Follow these steps:[/bold white]\n")
        
        for idx, step in enumerate(solution.steps, 1):
            # Indent sub-steps (lines starting with spaces or bullets)
            if step.strip().startswith('•') or step.startswith('  '):
                console.print(f"    [dim]{step}[/dim]")
            else:
                console.print(f"  [white]{idx}.[/white] {step}")
        
        console.print()
        
        # Show reference documentation
        if solution.reference_doc:
            console.print(f"[dim]📄 Reference Doc: {solution.reference_doc}[/dim]")
        
        if solution.video:
            console.print(f"[dim]🎥 Video Tutorial: {solution.video}[/dim]")
        
        # Show escalation criteria
        if solution.escalate_if:
            console.print()
            console.print(Panel(
                f"[yellow]⚠️  Escalate if:[/yellow] {solution.escalate_if}",
                border_style="yellow",
                box=box.ROUNDED
            ))
        
        console.print()
        
        # Ask if issue was resolved
        resolved = Confirm.ask(
            "[bold]Was the issue resolved?[/bold]",
            default=True
        )
        
        # Complete session
        self.session_data['solution_id'] = solution.id
        self.session_data['resolved'] = resolved
        self.session_data['end_time'] = datetime.now()
        
        # Calculate duration
        if self.session_data['start_time']:
            duration = (self.session_data['end_time'] - self.session_data['start_time']).total_seconds()
            self.session_data['duration'] = duration
        
        # Log the session
        self.logger.log_session(self.session_data)
        
        # Provide feedback
        if resolved:
            console.print("\n[green]✓ Great! Session logged successfully.[/green]")
        else:
            console.print("\n[yellow]Session logged. Consider escalating this issue.[/yellow]")
            console.print("[dim]Check escalation procedures in the reference documentation.[/dim]")
        
        # Ask if user wants to troubleshoot another issue
        console.print()
        another = Confirm.ask(
            "[bold]Troubleshoot another issue?[/bold]",
            default=False
        )
        
        if another:
            # Reset session data
            self.session_data = {
                'flow_id': None,
                'flow_name': None,
                'steps_taken': [],
                'solution_id': None,
                'resolved': None,
                'start_time': datetime.now(),
                'end_time': None
            }
            self.start()
        else:
            console.print("\n[cyan]Thanks for using FF37 TechAssist Bot![/cyan]")
            console.print("[dim]All sessions are logged for analytics and continuous improvement.[/dim]\n")
            sys.exit(0)


def main():
    """Entry point for the CLI application"""
    try:
        assistant = TroubleshootAssistant()
        assistant.start()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Session interrupted by user.[/yellow]")
        console.print("[cyan]Goodbye![/cyan]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        console.print("[dim]Please report this issue to the development team.[/dim]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
