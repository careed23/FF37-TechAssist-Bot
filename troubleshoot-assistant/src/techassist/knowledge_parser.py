"""
Knowledge parser for FF37-TechAssist-Bot.

Exposes the rich workflow, glossary, procedures, escalation criteria,
best-practice, and metadata content embedded in the troubleshooting YAML
file that the interactive :class:`TroubleshootingEngine` does not consume.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class KnowledgeBase:
    """Read-only access to reference knowledge stored alongside the
    troubleshooting flows.

    The YAML data file may contain the following top-level keys beyond
    ``flows`` and ``solutions``:

    * ``workflow`` — detailed operational procedure (decision points,
      step-by-step procedures, glossary, escalation criteria, etc.)
    * ``metadata`` — changelog, approval history, and contact information.

    This class loads those sections and provides typed accessor methods.
    """

    def __init__(self, yaml_path: str | Path) -> None:
        self.yaml_path = Path(yaml_path)

        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Knowledge file not found: {yaml_path}")

        with open(self.yaml_path, "r", encoding="utf-8") as fh:
            data: Dict[str, Any] = yaml.safe_load(fh) or {}

        self._workflow: Dict[str, Any] = data.get("workflow", {})
        self._metadata: Dict[str, Any] = data.get("metadata", {})

    # ------------------------------------------------------------------
    # Workflow identity
    # ------------------------------------------------------------------

    def get_workflow(self) -> Dict[str, Any]:
        """Return the full workflow dictionary (id, name, version, etc.)."""
        return dict(self._workflow)

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Return only the identity fields of the workflow."""
        keys = ("id", "name", "version", "category", "difficulty", "estimated_time")
        return {k: self._workflow.get(k) for k in keys if k in self._workflow}

    # ------------------------------------------------------------------
    # Glossary
    # ------------------------------------------------------------------

    def get_glossary(self) -> Dict[str, str]:
        """Return telecom term definitions (e.g. ONT, CED, PP, …)."""
        return dict(self._workflow.get("glossary", {}))

    def lookup_term(self, term: str) -> Optional[str]:
        """Look up a single glossary term (case-insensitive)."""
        glossary = self._workflow.get("glossary", {})
        term_upper = term.upper()
        for key, definition in glossary.items():
            if key.upper() == term_upper:
                return definition
        return None

    # ------------------------------------------------------------------
    # Prerequisites / systems
    # ------------------------------------------------------------------

    def get_prerequisites(self) -> Dict[str, List[str]]:
        """Return access, knowledge, and materials prerequisites."""
        return dict(self._workflow.get("prerequisites", {}))

    def get_systems(self) -> List[Dict[str, Any]]:
        """Return the list of required/optional systems."""
        return list(self._workflow.get("systems", []))

    # ------------------------------------------------------------------
    # Decision points
    # ------------------------------------------------------------------

    def get_decision_points(self) -> Dict[str, Any]:
        """Return all decision-point sections from the workflow.

        Decision points are stored under keys matching the pattern
        ``decision_point_*``.
        """
        return {
            key: value
            for key, value in self._workflow.items()
            if key.startswith("decision_point")
        }

    # ------------------------------------------------------------------
    # Procedures
    # ------------------------------------------------------------------

    def get_procedures(self) -> Dict[str, Any]:
        """Return all procedure sections (``procedure_*``)."""
        return {
            key: value
            for key, value in self._workflow.items()
            if key.startswith("procedure")
        }

    def get_procedure(self, name: str) -> Optional[Dict[str, Any]]:
        """Return a single procedure by key name (e.g. ``procedure_FDT``)."""
        return self._workflow.get(name)

    # ------------------------------------------------------------------
    # Escalation criteria
    # ------------------------------------------------------------------

    def get_escalation_criteria(self) -> Dict[str, Any]:
        """Return escalation trigger definitions."""
        return dict(self._workflow.get("escalation_criteria", {}))

    # ------------------------------------------------------------------
    # Best practices & tips
    # ------------------------------------------------------------------

    def get_best_practices(self) -> Dict[str, Any]:
        """Return before/during/after best-practice tips."""
        return dict(self._workflow.get("best_practices", {}))

    def get_troubleshooting_tips(self) -> List[Dict[str, str]]:
        """Return common-issue entries (issue / cause / solution)."""
        troubleshooting = self._workflow.get("troubleshooting", {})
        return list(troubleshooting.get("common_issues", []))

    def get_time_saving_tips(self) -> List[Dict[str, str]]:
        """Return time-saving tips with rationale."""
        tips = self._workflow.get("time_saving_tips", {})
        return list(tips.get("from_5_year_veteran", []))

    def get_warnings(self) -> List[Dict[str, str]]:
        """Return critical mistakes to avoid."""
        warnings = self._workflow.get("gotchas_and_warnings", {})
        return list(warnings.get("critical_mistakes_to_avoid", []))

    # ------------------------------------------------------------------
    # Templates & output
    # ------------------------------------------------------------------

    def get_ticket_template(self) -> Optional[str]:
        """Return the ticket-notes template string."""
        output = self._workflow.get("output_format", {})
        return output.get("ticket_notes_template")

    def get_related_documents(self) -> List[Dict[str, str]]:
        """Return related-document references."""
        return list(self._workflow.get("related_documents", []))

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self) -> Dict[str, Any]:
        """Return the full metadata dictionary (changelog, approval, contact)."""
        return dict(self._metadata)

    def get_changelog(self) -> List[Dict[str, Any]]:
        """Return version-history entries."""
        return list(self._metadata.get("changelog", []))

    def get_contact_info(self) -> Dict[str, str]:
        """Return author/SME contact details."""
        return dict(self._metadata.get("contact", {}))

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Simple case-insensitive text search across all knowledge content.

        Returns a list of ``{"section": …, "key": …, "match": …}`` dicts
        for every value that contains *query*.
        """
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []
        self._search_dict(self._workflow, "workflow", query_lower, results)
        self._search_dict(self._metadata, "metadata", query_lower, results)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _search_dict(
        data: Any,
        path: str,
        query: str,
        results: List[Dict[str, Any]],
    ) -> None:
        """Recursively search *data* for string values containing *query*."""
        if isinstance(data, dict):
            for key, value in data.items():
                KnowledgeBase._search_dict(value, f"{path}.{key}", query, results)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                KnowledgeBase._search_dict(item, f"{path}[{idx}]", query, results)
        elif isinstance(data, str) and query in data.lower():
            results.append({"section": path, "match": data})


# ------------------------------------------------------------------
# Convenience loader
# ------------------------------------------------------------------

def load_knowledge_base(
    yaml_path: str | Path = "data/troubleshooting_flows.yaml",
) -> KnowledgeBase:
    """Create a :class:`KnowledgeBase` with a sensible default path."""
    return KnowledgeBase(yaml_path)


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------

if __name__ == "__main__":
    try:
        kb = load_knowledge_base()
        summary = kb.get_workflow_summary()
        print(f"✓ Knowledge base loaded: {summary.get('name', 'N/A')}")
        print(f"  Version : {summary.get('version', 'N/A')}")
        print(f"  Category: {summary.get('category', 'N/A')}")

        glossary = kb.get_glossary()
        print(f"\n✓ Glossary: {len(glossary)} terms")
        for term, definition in glossary.items():
            print(f"  {term}: {definition}")

        procedures = kb.get_procedures()
        print(f"\n✓ Procedures: {len(procedures)}")
        for name in procedures:
            print(f"  - {name}")

        tips = kb.get_troubleshooting_tips()
        print(f"\n✓ Troubleshooting tips: {len(tips)}")

        template = kb.get_ticket_template()
        print(f"✓ Ticket template: {'available' if template else 'not found'}")

        results = kb.search("ONT")
        print(f"\n✓ Search 'ONT': {len(results)} matches")

    except Exception as e:
        print(f"✗ Error: {e}")
