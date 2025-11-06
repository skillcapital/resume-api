from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from io import BytesIO
import os
from typing import Dict, Any

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
env = Environment(loader=FileSystemLoader(template_dir))

# Available templates
AVAILABLE_TEMPLATES = {
    "default": "resume_default.html",
    "modern": "resume_modern.html",
    "classic": "resume_classic.html",
    "minimal": "resume_minimal.html",
    "professional": "resume_professional.html",
    "executive": "resume_executive.html",
    "tech": "resume_tech.html",
    "roshani": "resume_roshani.html",
}

def render_pdf(data: Dict[str, Any], template_name: str = "default") -> bytes:
    """
    Render resume data to PDF using HTML template.
    
    Args:
        data: Resume data dictionary
        template_name: Name of the template to use (default, modern, classic, minimal)
    """
    try:
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")
        
        # Validate template name
        if template_name not in AVAILABLE_TEMPLATES:
            template_name = "default"
        
        # Normalize data - ensure all nested dicts are properly formatted
        # Convert any string keys or values to proper structure
        normalized_data = normalize_resume_data(data)
        
        # Load template
        template_file = AVAILABLE_TEMPLATES[template_name]
        template = env.get_template(template_file)
        
        # Render HTML - template expects 'data' variable
        html_str = template.render(data=normalized_data)
        
        # Convert HTML to PDF using xhtml2pdf
        result = BytesIO()
        pdf = pisa.CreatePDF(
            BytesIO(html_str.encode("UTF-8")),
            dest=result,
            encoding='UTF-8'
        )
        
        if not pdf.err:
            return result.getvalue()
        else:
            raise Exception(f"Error generating PDF: {pdf.err}")
            
    except Exception as e:
        raise Exception(f"Error generating PDF: {str(e)}")

def get_available_templates() -> list:
    """
    Get list of available template names.
    """
    return list(AVAILABLE_TEMPLATES.keys())

def normalize_resume_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize resume data to ensure consistent structure for template rendering.
    """
    normalized = {}
    
    # Copy all top-level fields
    for key, value in data.items():
        if key == 'experiences' and isinstance(value, list):
            # Normalize experience entries
            normalized[key] = [normalize_experience(exp) for exp in value]
        elif key == 'education' and isinstance(value, list):
            # Normalize education entries
            normalized[key] = [normalize_education(edu) for edu in value]
        elif key == 'skills' and isinstance(value, list):
            # Filter out empty skills
            normalized[key] = [skill for skill in value if skill and str(skill).strip()]
        else:
            normalized[key] = value
    
    return normalized

def normalize_experience(exp: Any) -> Dict[str, Any]:
    """Normalize a single experience entry."""
    if isinstance(exp, str):
        return {"title": exp, "company": "", "bullets": []}
    elif isinstance(exp, dict):
        return {
            "title": exp.get("title", "") or "",
            "company": exp.get("company", "") or "",
            "period": exp.get("period", "") or "",
            "bullets": exp.get("bullets", []) if isinstance(exp.get("bullets"), list) else []
        }
    else:
        # Try attribute access
        return {
            "title": getattr(exp, "title", "") or "",
            "company": getattr(exp, "company", "") or "",
            "period": getattr(exp, "period", "") or "",
            "bullets": getattr(exp, "bullets", []) if isinstance(getattr(exp, "bullets", []), list) else []
        }

def normalize_education(edu: Any) -> Dict[str, Any]:
    """Normalize a single education entry."""
    if isinstance(edu, str):
        return {"degree": edu, "institution": "", "year": ""}
    elif isinstance(edu, dict):
        return {
            "degree": edu.get("degree", "") or "",
            "institution": edu.get("institution", "") or "",
            "year": edu.get("year", "") or ""
        }
    else:
        # Try attribute access
        return {
            "degree": getattr(edu, "degree", "") or "",
            "institution": getattr(edu, "institution", "") or "",
            "year": getattr(edu, "year", "") or ""
        }
