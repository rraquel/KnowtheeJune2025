import re
from pathlib import Path
from datetime import datetime, date
from backend.utils.common import slugify

def parse_assessment(file_path):
    file_path = Path(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Determine assessment type from filename
    assessment_type = None
    if file_path.stem.startswith("IDI_"):
        assessment_type = "IDI"
    elif file_path.stem.startswith("Hogan_"):
        assessment_type = "Hogan"

    lines = content.splitlines()
    
    # Always extract name from file name
    name = file_path.stem
    if name.startswith("IDI_"):
        name = name[4:]
    elif name.startswith("Hogan_"):
        name = name[6:]
    name = name.replace("_", " ")
    
    data = {
        "employee_id": slugify(name),
        "name": name,
        "assessments": []
    }

    current_assessment = None
    current_category = None
    current_scores = {}
    current_section = None
    pending_date = None

    if assessment_type == "IDI":
        # Always treat as IDI
        for line in lines:
            line = line.strip()
            if not line:
                continue
            date_match = re.search(r'Date:\s*(\w+\s+\d+,\s+\d{4})', line)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    date_obj = datetime.strptime(date_str, "%B %d, %Y")
                    pending_date = date_obj.date().isoformat()
                except ValueError:
                    pending_date = date.today().isoformat()
            # Section headers
            if line.isupper() and not line.startswith("INTERCULTURAL") and not line.startswith("CONFIDENTIAL"):
                current_category = line.strip()
                continue
            # Score patterns
            score_match = re.search(r'(\w+)\s+(\d+)', line)
            if score_match and current_category:
                dimension = score_match.group(1).strip()
                score_value = float(score_match.group(2))
                if not current_assessment:
                    current_assessment = {
                        "type": "IDI",
                        "date": pending_date or date.today().isoformat(),
                        "scores": {}
                    }
                if current_category not in current_assessment["scores"]:
                    current_assessment["scores"][current_category] = {}
                current_assessment["scores"][current_category][dimension] = score_value
        if current_assessment:
            if not current_assessment["date"]:
                current_assessment["date"] = pending_date or date.today().isoformat()
            data["assessments"].append(current_assessment)

    elif assessment_type == "Hogan":
        # Always treat as Hogan
        for line in lines:
            line = line.strip()
            if not line:
                continue
            date_match = re.search(r'Date:\s*(\w+\s+\d+,\s+\d{4})', line)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    date_obj = datetime.strptime(date_str, "%B %d, %Y")
                    pending_date = date_obj.date().isoformat()
                except ValueError:
                    pending_date = date.today().isoformat()
            # Section headers for Hogan
            if (
                "HOGAN PERSONALITY INVENTORY" in line.upper() or
                "HOGAN DEVELOPMENT SURVEY" in line.upper() or
                "MOTIVES, VALUES, PREFERENCES INVENTORY" in line.upper()
            ):
                if not current_assessment:
                    current_assessment = {
                        "type": "Hogan",
                        "date": pending_date or date.today().isoformat(),
                        "scores": {}
                    }
                continue
            # Score patterns (either 'Trait: Value' or 'Trait Value')
            score_match = re.search(r'(\w[\w ]*?):?\s*(\d+(?:\.\d+)?)', line)
            if score_match:
                trait = score_match.group(1).strip()
                score_value = float(score_match.group(2))
                if not current_assessment:
                    current_assessment = {
                        "type": "Hogan",
                        "date": pending_date or date.today().isoformat(),
                        "scores": {}
                    }
                current_assessment["scores"][trait] = score_value
        if current_assessment:
            if not current_assessment["date"]:
                current_assessment["date"] = pending_date or date.today().isoformat()
            data["assessments"].append(current_assessment)

    else:
        # Fallback: old logic, search for section headers
        for line in lines:
            line = line.strip()
            if not line:
                continue
            date_match = re.search(r'Date:\s*(\w+\s+\d+,\s+\d{4})', line)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    date_obj = datetime.strptime(date_str, "%B %d, %Y")
                    pending_date = date_obj.date().isoformat()
                except ValueError:
                    pending_date = date.today().isoformat()
            if "INTERCULTURAL DEVELOPMENT INVENTORY" in line.upper():
                if current_assessment:
                    data["assessments"].append(current_assessment)
                current_assessment = {
                    "type": "IDI",
                    "date": pending_date or date.today().isoformat(),
                    "scores": {}
                }
                pending_date = None
                current_section = "idi"
                continue
            elif (
                "HOGAN PERSONALITY INVENTORY" in line.upper() or
                "HOGAN DEVELOPMENT SURVEY" in line.upper() or
                "MOTIVES, VALUES, PREFERENCES INVENTORY" in line.upper()
            ):
                if not current_assessment or current_assessment.get("type") != "Hogan":
                    if current_assessment:
                        data["assessments"].append(current_assessment)
                    current_assessment = {
                        "type": "Hogan",
                        "date": pending_date or date.today().isoformat(),
                        "scores": {}
                    }
                    pending_date = None
                current_section = "hogan"
                continue
            if current_assessment and pending_date and not current_assessment["date"]:
                current_assessment["date"] = pending_date
                pending_date = None
            if current_section == "idi":
                if line.isupper() and not line.startswith("INTERCULTURAL") and not line.startswith("CONFIDENTIAL"):
                    current_category = line.strip()
                    continue
                score_match = re.search(r'(\w+)\s+(\d+)', line)
                if score_match and current_category:
                    dimension = score_match.group(1).strip()
                    score_value = float(score_match.group(2))
                    if current_category not in current_assessment["scores"]:
                        current_assessment["scores"][current_category] = {}
                    current_assessment["scores"][current_category][dimension] = score_value
            elif current_section == "hogan":
                score_match = re.search(r'(\w[\w ]*?):?\s*(\d+(?:\.\d+)?)', line)
                if score_match:
                    trait = score_match.group(1).strip()
                    score_value = float(score_match.group(2))
                    current_assessment["scores"][trait] = score_value
        if current_assessment:
            if not current_assessment["date"]:
                current_assessment["date"] = pending_date or date.today().isoformat()
            data["assessments"].append(current_assessment)

    return data
