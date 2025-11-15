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
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Normalized data keys: {list(normalized_data.keys())}")
        logger.info(f"Normalized projects: {normalized_data.get('projects', [])}")
        logger.info(f"Normalized certifications: {normalized_data.get('certifications', [])}")
        logger.info(f"Normalized languages: {normalized_data.get('languages', [])}")
        
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
        # CRITICAL: Ensure projects is a list
        if not isinstance(projects, list):
            projects = []
        logger.info(f"PDF Renderer - Projects: {projects}, Type: {type(projects)}, Length: {len(projects)}")
        if projects and len(projects) > 0:
            story.append(Paragraph('<b>Projects</b>', heading_style))
            for project in projects:
                if isinstance(project, dict):
                    name = project.get('name', '')
                    desc = project.get('description', '')
                    technologies = project.get('technologies', '')
                    url = project.get('url', '')
                    
                    if name:
                        project_text = f"<b>{escape(name)}</b>"
                        if technologies:
                            project_text += f" - {escape(str(technologies))}"
                        story.append(Paragraph(project_text, normal_style))
                    if desc:
                        story.append(Paragraph(escape(desc), normal_style))
                    if url:
                        story.append(Paragraph(f"URL: {escape(url)}", normal_style))
                else:
                    story.append(Paragraph(escape(str(project)), normal_style))
                story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.1*inch))
        else:
            logger.warning(f"Projects section skipped - projects is empty or falsy: {projects}")
        
        # Certifications
        certifications = normalized_data.get('certifications', [])
        # CRITICAL: Ensure certifications is a list
        if not isinstance(certifications, list):
            certifications = []
        logger.info(f"PDF Renderer - Certifications: {certifications}, Type: {type(certifications)}, Length: {len(certifications)}")
        if certifications and len(certifications) > 0:
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
            story.append(Spacer(1, 0.1*inch))
        else:
            logger.warning(f"Certifications section skipped - certifications is empty or falsy: {certifications}")
        
        # Languages
        languages = normalized_data.get('languages', [])
        # CRITICAL: Ensure languages is a list
        if not isinstance(languages, list):
            languages = []
        logger.info(f"PDF Renderer - Languages: {languages}, Type: {type(languages)}, Length: {len(languages)}")
        if languages and len(languages) > 0:
            story.append(Paragraph('<b>Languages</b>', heading_style))
            # Handle both string and dict formats
            lang_strings = []
            for lang in languages:
                if isinstance(lang, str):
                    lang_strings.append(lang)
                elif isinstance(lang, dict):
                    name = lang.get('name', lang.get('language', ''))
                    level = lang.get('level', lang.get('proficiency', ''))
                    if name:
                        lang_text = escape(str(name))
                        if level:
                            lang_text += f" ({escape(str(level))})"
                        lang_strings.append(lang_text)
                else:
                    lang_strings.append(escape(str(lang)))
            
            if lang_strings:
                languages_text = ', '.join(lang_strings)
                story.append(Paragraph(languages_text, normal_style))
                story.append(Spacer(1, 0.1*inch))
        else:
            logger.warning(f"Languages section skipped - languages is empty or falsy: {languages}")
        
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
    
    # CRITICAL: Ensure projects, certifications, and languages are always present as lists
    # Initialize them first to ensure they're never missing
    normalized['projects'] = []
    normalized['certifications'] = []
    normalized['languages'] = []
    
    # Copy all top-level fields
    for key, value in data.items():
        if key == 'experiences' and isinstance(value, list):
            # Normalize experience entries
            normalized[key] = [normalize_experience(exp) for exp in value]
        elif key == 'education' and isinstance(value, list):
            # Normalize education entries
            normalized[key] = [normalize_education(edu) for edu in value]
        elif key == 'skills' and isinstance(value, list):
            # Filter out empty skills and convert to strings
            normalized[key] = [str(skill) if not isinstance(skill, str) else skill 
                             for skill in value if skill and str(skill).strip()]
        elif key == 'projects':
            # CRITICAL FIX: Always process projects, even if None or empty
            if value is None:
                normalized[key] = []
            elif isinstance(value, list):
                # Normalize projects - ensure they're dicts with proper structure
                normalized[key] = [normalize_project(proj) for proj in value]
            else:
                # Convert non-list to list
                normalized[key] = [normalize_project(value)]
        elif key == 'certifications':
            # CRITICAL FIX: Always process certifications, even if None or empty
            if value is None:
                normalized[key] = []
            elif isinstance(value, list):
                # Normalize certifications - convert strings to dicts if needed
                normalized[key] = [normalize_certification(cert) for cert in value]
            else:
                # Convert non-list to list
                normalized[key] = [normalize_certification(value)]
        elif key == 'languages':
            # CRITICAL FIX: Always process languages, even if None or empty
            if value is None:
                normalized[key] = []
            elif isinstance(value, list):
                # Normalize languages - ensure they're in proper format
                normalized[key] = [lang for lang in value]
            else:
                # Convert non-list to list
                normalized[key] = [value]
        else:
            normalized[key] = value
    
    # Final safety check - ensure these fields are always lists
    if not isinstance(normalized.get('projects'), list):
        normalized['projects'] = []
    if not isinstance(normalized.get('certifications'), list):
        normalized['certifications'] = []
    if not isinstance(normalized.get('languages'), list):
        normalized['languages'] = []
    
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

def normalize_project(proj: Any) -> Dict[str, Any]:
    """Normalize a single project entry."""
    if isinstance(proj, str):
        return {"name": proj, "description": "", "technologies": "", "url": ""}
    elif isinstance(proj, dict):
        # Handle technologies as string or list
        technologies = proj.get("technologies", "")
        if isinstance(technologies, list):
            technologies = ", ".join([str(t) for t in technologies if t])
        return {
            "name": proj.get("name", "") or "",
            "description": proj.get("description", "") or "",
            "technologies": str(technologies) if technologies else "",
            "url": proj.get("url", "") or ""
        }
    else:
        return {
            "name": getattr(proj, "name", "") or "",
            "description": getattr(proj, "description", "") or "",
            "technologies": str(getattr(proj, "technologies", "")) or "",
            "url": getattr(proj, "url", "") or ""
        }

def normalize_certification(cert: Any) -> Dict[str, Any]:
    """Normalize a single certification entry."""
    if isinstance(cert, str):
        # If it's just a string, return as dict with name
        return {"name": cert, "issuer": "", "year": ""}
    elif isinstance(cert, dict):
        # If it's already a dict, ensure all fields are present
        return {
            "name": cert.get("name", cert.get("certification", str(cert.get("name", "")))) or "",
            "issuer": cert.get("issuer", cert.get("issuing_organization", cert.get("issuer", ""))) or "",
            "year": cert.get("year", "") or ""
        }
    else:
        # Convert anything else to string and use as name
        return {
            "name": str(cert) if cert else "",
            "issuer": "",
            "year": ""
        }
