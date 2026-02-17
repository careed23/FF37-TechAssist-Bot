import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class TroubleshootingLogger:
    """
    Logs troubleshooting sessions for analytics and reporting
    """
    
    def __init__(self, log_file: str = 'logs/troubleshooting_log.csv'):
        """
        Initialize logger
        
        Args:
            log_file: Path to CSV log file
        """
        self.log_file = Path(log_file)
        
        # Create logs directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create log file with headers if it doesn't exist
        if not self.log_file.exists():
            self._create_log_file()
    
    def _create_log_file(self):
        """Create log file with CSV headers"""
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'flow_id',
                'flow_name',
                'solution_id',
                'steps_taken',
                'num_steps',
                'resolved',
                'duration_seconds',
                'session_date'
            ])
    
    def log_session(self, session_data: Dict):
        """
        Log a completed troubleshooting session
        
        Args:
            session_data: Dictionary containing session information
        """
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                timestamp = datetime.now().isoformat()
                session_date = datetime.now().strftime('%Y-%m-%d')
                
                # Serialize steps as JSON
                steps_json = json.dumps(session_data.get('steps_taken', []))
                
                writer.writerow([
                    timestamp,
                    session_data.get('flow_id', ''),
                    session_data.get('flow_name', ''),
                    session_data.get('solution_id', ''),
                    steps_json,
                    len(session_data.get('steps_taken', [])),
                    session_data.get('resolved', False),
                    session_data.get('duration', 0),
                    session_date
                ])
                
        except Exception as e:
            print(f"Warning: Could not log session: {e}")
    
    def get_session_count(self) -> int:
        """
        Get total number of logged sessions
        
        Returns:
            Total session count
        """
        if not self.log_file.exists():
            return 0
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # Subtract 1 for header row
                return sum(1 for _ in f) - 1
        except Exception:
            return 0
    
    def get_resolution_rate(self) -> float:
        """
        Calculate percentage of issues successfully resolved
        
        Returns:
            Resolution rate as percentage (0-100)
        """
        if not self.log_file.exists():
            return 0.0
        
        try:
            total = 0
            resolved = 0
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total += 1
                    if row['resolved'].lower() == 'true':
                        resolved += 1
            
            return (resolved / total * 100) if total > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def get_most_common_flows(self, limit: int = 5) -> List[tuple]:
        """
        Get most frequently used troubleshooting flows
        
        Args:
            limit: Maximum number of flows to return
            
        Returns:
            List of tuples (flow_name, count) sorted by frequency
        """
        if not self.log_file.exists():
            return []
        
        try:
            flow_counts = {}
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    flow_name = row['flow_name']
                    flow_counts[flow_name] = flow_counts.get(flow_name, 0) + 1
            
            # Sort by count (descending) and return top N
            sorted_flows = sorted(
                flow_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return sorted_flows[:limit]
            
        except Exception:
            return []
    
    def get_most_common_solutions(self, limit: int = 5) -> List[tuple]:
        """
        Get most frequently used solutions
        
        Args:
            limit: Maximum number of solutions to return
            
        Returns:
            List of tuples (solution_id, count) sorted by frequency
        """
        if not self.log_file.exists():
            return []
        
        try:
            solution_counts = {}
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    solution_id = row['solution_id']
                    if solution_id:
                        solution_counts[solution_id] = solution_counts.get(solution_id, 0) + 1
            
            # Sort by count (descending) and return top N
            sorted_solutions = sorted(
                solution_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return sorted_solutions[:limit]
            
        except Exception:
            return []
    
    def get_average_duration(self) -> float:
        """
        Calculate average troubleshooting session duration
        
        Returns:
            Average duration in seconds
        """
        if not self.log_file.exists():
            return 0.0
        
        try:
            total_duration = 0
            count = 0
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        duration = float(row['duration_seconds'])
                        total_duration += duration
                        count += 1
                    except (ValueError, KeyError):
                        continue
            
            return (total_duration / count) if count > 0 else 0.0
            
        except Exception:
            return 0.0


# For testing
if __name__ == "__main__":
    logger = TroubleshootingLogger()
    
    print(f"Total sessions: {logger.get_session_count()}")
    print(f"Resolution rate: {logger.get_resolution_rate():.1f}%")
    print(f"Average duration: {logger.get_average_duration():.1f} seconds")
    
    print("\nMost common flows:")
    for flow, count in logger.get_most_common_flows():
        print(f"  {flow}: {count}")
    
    print("\nMost common solutions:")
    for solution, count in logger.get_most_common_solutions():
        print(f"  {solution}: {count}")
