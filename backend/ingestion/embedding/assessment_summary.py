import os
import re
from pathlib import Path
from typing import List, Dict, Optional

class AssessmentSummaryGenerator:
    """
    Generates concise summaries from IDI and Hogan assessment .txt files.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or "backend/data/processed"

    def process_directory(self, input_dir: str) -> List[str]:
        """
        Process all IDI and Hogan .txt files in a directory and generate summaries.

        Returns:
            List of summary file paths generated.
        """
        input_path = Path(input_dir)
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        summary_files = []

        for file_path in input_path.glob("*.txt"):
            if self._is_assessment_file(file_path.name):
                summary_fp = self.generate_summary(file_path)
                if summary_fp:
                    summary_files.append(summary_fp)
        return summary_files

    def _is_assessment_file(self, filename: str) -> bool:
        return filename.startswith("IDI_") or filename.startswith("Hogan_")

    def generate_summary(self, file_path: Path) -> Optional[str]:
        """
        Generate a summary for a single assessment file and save it.

        Returns:
            Path to the summary file, or None if failed.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            summary = self._extract_summary(text, file_path.name)
            summary_filename = f"{file_path.stem}_summary.txt"
            summary_path = Path(self.output_dir) / summary_filename
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            return str(summary_path)
        except Exception as e:
            print(f"Failed to generate summary for {file_path}: {e}")
            return None

    def _extract_summary(self, text: str, filename: str) -> str:
        """
        Extracts a summary from the assessment text.
        """
        lines = text.splitlines()
        name = self._extract_name_from_filename(filename)
        scores = self._extract_scores(lines)
        summary = self._extract_section(lines, ["Summary", "Overall Impression"])
        recommendations = self._extract_section(lines, ["Recommendations", "Development Suggestions"])

        summary_text = f"Assessment: {filename}\n"
        summary_text += f"Employee: {name}\n\n"
        if scores:
            summary_text += "Scores:\n" + "\n".join(scores) + "\n\n"
        if summary:
            summary_text += f"Summary:\n{summary}\n\n"
        if recommendations:
            summary_text += f"Recommendations:\n{recommendations}\n"
        return summary_text

    def _extract_name_from_filename(self, filename: str) -> str:
        match = re.match(r"(IDI|Hogan)_([A-Za-z]+)_([A-Za-z\\-]+)\\.txt", filename)
        if match:
            return f"{match.group(2)} {match.group(3)}"
        return "Unknown"

    def _extract_scores(self, lines: List[str]) -> List[str]:
        # Look for lines that look like scores, e.g., "Cultural Openness: 85"
        score_lines = []
        for line in lines:
            if re.match(r"^[A-Za-z ]+: \\d{1,3}$", line.strip()):
                score_lines.append(line.strip())
        return score_lines

    def _extract_section(self, lines: List[str], section_headers: List[str]) -> str:
        # Find section by header and return the following lines until next header or empty line
        section = []
        in_section = False
        for line in lines:
            if any(header.lower() in line.lower() for header in section_headers):
                in_section = True
                continue
            if in_section:
                if line.strip() == "" or re.match(r"^[A-Za-z ]+:$", line.strip()):
                    break
                section.append(line.strip())
        return " ".join(section).strip() 