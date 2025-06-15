import re
from pathlib import Path
from datetime import datetime
from backend.utils.common import slugify

def parse_date(date_str):
    """Parse date string into datetime object."""
    if not date_str:
        return None
    try:
        # Try common date formats
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%B %Y', '%b %Y', '%Y', '%B %d, %Y', '%b %d, %Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None
    except:
        return None

def parse_cv(file_path):
    file_path = Path(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    # Always extract name from file name
    name = file_path.stem
    if name.startswith("CV_"):
        name = name[3:]
    name = name.replace("_", " ")
    employee_id = slugify(name)
    
    data = {
        "employee_id": employee_id,
        "name": name,
        "contacts": [],
        "education": [],
        "experiences": [],
        "skills": [],
        "location": "",
        "department": "",
        "position": "",
        "email": ""
    }

    # Parse contact information
    for line in lines[:15]:
        line = line.strip()
        if not line:
            continue
            
        if "email:" in line.lower():
            data["email"] = line.split(":", 1)[1].strip()
            data["contacts"].append({
                "type": "email",
                "value": data["email"],
                "is_primary": True
            })
        elif "phone:" in line.lower():
            data["contacts"].append({
                "type": "phone",
                "value": line.split(":", 1)[1].strip(),
                "is_primary": True
            })
        elif "location:" in line.lower():
            data["location"] = line.split(":", 1)[1].strip()
        elif "linkedin:" in line.lower():
            data["contacts"].append({
                "type": "linkedin",
                "value": line.split(":", 1)[1].strip(),
                "is_primary": False
            })

    # Parse education and experience sections
    current_section = None
    current_edu = None
    current_exp = None
    edu_buffer = []
    exp_buffer = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Section headers
        if re.search(r'^(EDUCATION|EDUCATIONAL BACKGROUND|ACADEMIC QUALIFICATIONS)', line, re.IGNORECASE):
            if current_edu:
                data["education"].append(current_edu)
            current_section = "edu"
            current_edu = None
            edu_buffer = []
            continue

        if re.search(r'^(EXPERIENCE|PROFESSIONAL BACKGROUND|WORK EXPERIENCE|EMPLOYMENT|CAREER HISTORY)', line, re.IGNORECASE):
            if current_exp:
                data["experiences"].append(current_exp)
            current_section = "exp"
            current_exp = None
            exp_buffer = []
            continue

        # Education parsing
        if current_section == "edu":
            # Look for date patterns
            date_match = re.search(r'(\d{4}(?:\s*-\s*(?:Present|\d{4}))?)', line)
            if date_match:
                if current_edu:
                    data["education"].append(current_edu)
                
                # Extract dates
                dates = date_match.group(1).split('-')
                start_date = parse_date(dates[0].strip())
                end_date = parse_date(dates[1].strip()) if len(dates) > 1 else None
                
                # Previous lines should contain institution and degree
                if edu_buffer:
                    institution = edu_buffer[0].strip()
                    
                    # Parse degree and field from the second line
                    degree_line = edu_buffer[1].strip() if len(edu_buffer) > 1 else ""
                    degree = ""
                    field = ""
                    
                    # Try to extract degree and field
                    if degree_line:
                        # Look for common degree patterns
                        degree_patterns = [
                            r'(B\.?S\.?|M\.?S\.?|Ph\.?D\.?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?)\.?\s*(?:in|of)?\s*([^,]+)',
                            r'([^,]+),\s*(?:B\.?S\.?|M\.?S\.?|Ph\.?D\.?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?)',
                        ]
                        
                        for pattern in degree_patterns:
                            match = re.search(pattern, degree_line, re.IGNORECASE)
                            if match:
                                if "in" in degree_line.lower():
                                    degree = match.group(1).strip()
                                    field = match.group(2).strip()
                                else:
                                    field = match.group(1).strip()
                                    degree = match.group(2).strip()
                                break
                    
                    current_edu = {
                        "institution": institution,
                        "degree": degree,
                        "field": field,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                edu_buffer = []
            else:
                edu_buffer.append(line)

        # Experience parsing
        elif current_section == "exp":
            # Look for date patterns
            date_match = re.search(r'(\d{4}(?:\s*-\s*(?:Present|\d{4}))?)', line)
            if date_match:
                if current_exp:
                    data["experiences"].append(current_exp)
                
                # Extract dates
                dates = date_match.group(1).split('-')
                start_date = parse_date(dates[0].strip())
                end_date = parse_date(dates[1].strip()) if len(dates) > 1 else None
                
                # Previous lines should contain title and company
                if exp_buffer:
                    title_company = exp_buffer[0].strip()
                    if "|" in title_company:
                        title, company = title_company.split("|", 1)
                    else:
                        title = title_company
                        company = exp_buffer[1].strip() if len(exp_buffer) > 1 else ""
                    
                    current_exp = {
                        "title": title.strip(),
                        "company": company.strip(),
                        "start_date": start_date,
                        "end_date": end_date,
                        "description": []
                    }
                exp_buffer = []
            elif current_exp:
                if line.startswith("•"):
                    current_exp["description"].append(line[1:].strip())
            else:
                exp_buffer.append(line)

        # Skills parsing
        elif re.search(r'^(SKILLS|TECHNICAL SKILLS|COMPETENCIES)', line, re.IGNORECASE):
            current_section = "skills"
        elif current_section == "skills":
            if not line.startswith("•") and not any(kw in line.lower() for kw in ["experience", "education", "employment"]):
                skills = [s.strip() for s in line.split(",")]
                for skill in skills:
                    if skill:
                        data["skills"].append({
                            "name": skill,
                            "type": "technical"
                        })

    # Add last entries
    if current_edu:
        data["education"].append(current_edu)
    if current_exp:
        data["experiences"].append(current_exp)

    return data
