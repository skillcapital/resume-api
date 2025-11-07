from io import BytesIO
from typing import Dict, Any
from html import escape

# Lazy imports to prevent crashes on module load
def _get_reportlab_imports():
    """Lazy import reportlab modules only when needed."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    return {
        'letter': letter,
        'getSampleStyleSheet': getSampleStyleSheet,
        'ParagraphStyle': ParagraphStyle,
        'inch': inch,
        'SimpleDocTemplate': SimpleDocTemplate,
        'Paragraph': Paragraph,
        'Spacer': Spacer,
        'colors': colors,
        'TA_CENTER': TA_CENTER
    }

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
    Render resume data to PDF using ReportLab (Vercel-compatible).
    
    Args:
        data: Resume data dictionary
        template_name: Name of the template to use (default, modern, classic, minimal)
    """
    try:
        # Lazy import reportlab modules
        rl = _get_reportlab_imports()
        letter = rl['letter']
        getSampleStyleSheet = rl['getSampleStyleSheet']
        ParagraphStyle = rl['ParagraphStyle']
        inch = rl['inch']
        SimpleDocTemplate = rl['SimpleDocTemplate']
        Paragraph = rl['Paragraph']
        Spacer = rl['Spacer']
        colors = rl['colors']
        TA_CENTER = rl['TA_CENTER']
        
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")
        
        # Validate template name
        if template_name not in AVAILABLE_TEMPLATES:
            template_name = "default"
        
        # Normalize data
        normalized_data = normalize_resume_data(data)
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for the 'Flowable' objects
        story = []
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        # Heading style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            spaceBefore=12
        )
        
        # Normal style
        normal_style = styles['Normal']
        
        # Name
        name = normalized_data.get('name', '')
        if name:
            story.append(Paragraph(escape(name), title_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Contact info
        contact_info = []
        if normalized_data.get('email'):
            contact_info.append(escape(normalized_data['email']))
        if normalized_data.get('phone'):
            contact_info.append(escape(normalized_data['phone']))
        if normalized_data.get('linkedin'):
            contact_info.append(f"LinkedIn: {escape(normalized_data['linkedin'])}")
        if normalized_data.get('github'):
            contact_info.append(f"GitHub: {escape(normalized_data['github'])}")
        
        if contact_info:
            story.append(Paragraph(' | '.join(contact_info), normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary = normalized_data.get('summary', '')
        if summary:
            story.append(Paragraph('<b>Professional Summary</b>', heading_style))
            story.append(Paragraph(escape(summary), normal_style))
            story.append(Spacer(1, 0.15*inch))
        
        # Experience
        experiences = normalized_data.get('experiences', [])
        if experiences:
            story.append(Paragraph('<b>Professional Experience</b>', heading_style))
            for exp in experiences:
                title = exp.get('title', '')
                company = exp.get('company', '')
                period = exp.get('period', '')
                
                if title or company:
                    exp_header = f"<b>{escape(title)}</b>"
                    if company:
                        exp_header += f" - {escape(company)}"
                    if period:
                        exp_header += f" ({escape(period)})"
                    story.append(Paragraph(exp_header, normal_style))
                
                bullets = exp.get('bullets', [])
                for bullet in bullets:
                    story.append(Paragraph(f"• {escape(str(bullet))}", normal_style))
                
                story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.1*inch))
        
        # Education
        education = normalized_data.get('education', [])
        if education:
            story.append(Paragraph('<b>Education</b>', heading_style))
            for edu in education:
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                year = edu.get('year', '')
                
                edu_text = f"<b>{escape(degree)}</b>"
                if institution:
                    edu_text += f" - {escape(institution)}"
                if year:
                    edu_text += f" ({escape(year)})"
                story.append(Paragraph(edu_text, normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Skills
        skills = normalized_data.get('skills', [])
        if skills:
            story.append(Paragraph('<b>Skills</b>', heading_style))
            skills_text = ', '.join([escape(str(skill)) for skill in skills])
            story.append(Paragraph(skills_text, normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Projects
        projects = normalized_data.get('projects', [])
        if projects:
            story.append(Paragraph('<b>Projects</b>', heading_style))
            for project in projects:
                if isinstance(project, dict):
                    name = project.get('name', '')
                    desc = project.get('description', '')
                    if name:
                        story.append(Paragraph(f"<b>{escape(name)}</b>", normal_style))
                    if desc:
                        story.append(Paragraph(escape(desc), normal_style))
                else:
                    story.append(Paragraph(escape(str(project)), normal_style))
                story.append(Spacer(1, 0.1*inch))
        
        # Certifications
        certifications = normalized_data.get('certifications', [])
        if certifications:
            story.append(Paragraph('<b>Certifications</b>', heading_style))
            for cert in certifications:
                if isinstance(cert, dict):
                    name = cert.get('name', '')
                    issuer = cert.get('issuer', '')
                    year = cert.get('year', '')
                    cert_text = f"<b>{escape(name)}</b>"
                    if issuer:
                        cert_text += f" - {escape(issuer)}"
                    if year:
                        cert_text += f" ({escape(year)})"
                    story.append(Paragraph(cert_text, normal_style))
                else:
                    story.append(Paragraph(escape(str(cert)), normal_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
            
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
