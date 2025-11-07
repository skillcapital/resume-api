from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from typing import Optional, Dict, Any
import json
from pydantic import BaseModel

# Import services safely - handle import errors gracefully
try:
    from app.services import pdf_parser, pdf_exporter, langchain_ai, supabase_client
    SERVICES_AVAILABLE = True
except Exception as e:
    SERVICES_AVAILABLE = False
    import sys
    print(f"Warning: Failed to import services: {str(e)}", file=sys.stderr)
    # Create dummy modules to prevent NameError
    class DummyModule:
        pass
    pdf_parser = DummyModule()
    pdf_exporter = DummyModule()
    langchain_ai = DummyModule()
    supabase_client = DummyModule()

# Import schemas safely
try:
    from app.models.schemas import ResumeCreateRequest
    SCHEMAS_AVAILABLE = True
except Exception as e:
    SCHEMAS_AVAILABLE = False
    import sys
    print(f"Warning: Failed to import schemas: {str(e)}", file=sys.stderr)
    # Create a minimal BaseModel for ResumeCreateRequest
    class ResumeCreateRequest(BaseModel):
        name: str
        email: Optional[str] = ""

router = APIRouter()

@router.post("/create")
async def create_resume_from_form(resume_data: ResumeCreateRequest = Body(...)):
    """
    Create a resume from form data (no file upload needed) - ChatGPT style.
    """
    try:
        # Convert to dict for AI processing
        personal_info = {
            "name": resume_data.name,
            "email": resume_data.email,
            "phone": resume_data.phone,
            "linkedin": resume_data.linkedin,
            "github": resume_data.github,
            "website": resume_data.website,
            "summary": resume_data.summary,
            "experiences": [exp.dict() for exp in resume_data.experiences],
            "education": [edu.dict() for edu in resume_data.education],
            "skills": resume_data.skills,
            "projects": resume_data.projects or [],
            "certifications": resume_data.certifications or [],
            "languages": resume_data.languages or []
        }
        
        # Generate resume with AI
        if resume_data.job_description:
            # Generate tailored resume directly
            generated_resume = await langchain_ai.generate_resume_from_info(
                personal_info, 
                resume_data.job_description
            )
        else:
            # Generate improved resume
            generated_resume = await langchain_ai.generate_resume_from_info(personal_info)
        
        # Ensure contact info is present in the generated payload (do not rely on the model)
        generated_resume["email"] = resume_data.email or ""
        generated_resume["phone"] = resume_data.phone or ""
        generated_resume["linkedin"] = resume_data.linkedin or ""
        generated_resume["github"] = resume_data.github or ""
        generated_resume["website"] = resume_data.website or ""
        
        # Build raw text for storage
        raw_text_parts = [f"Name: {resume_data.name}"]
        if resume_data.email:
            raw_text_parts.append(f"Email: {resume_data.email}")
        raw_text_parts.append(f"\nSummary: {generated_resume.get('summary', '')}")
        raw_text = "\n".join(raw_text_parts)
        
        # Save to database
        resume_id = supabase_client.save_resume_raw(raw_text)
        
        # Save AI-generated version
        version_type = "tailored" if resume_data.job_description else "improved"
        supabase_client.save_resume_version(resume_id, generated_resume, version_type=version_type)
        
        return {
            "resume_id": resume_id,
            "version": generated_resume,
            "status": "success",
            "message": "Resume created and generated with AI"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating resume: {str(e)}")

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF resume and extract text.
    """
    try:
        # Extract text from PDF
        text = await pdf_parser.extract_text(file)
        
        # Save to Supabase
        resume_id = supabase_client.save_resume_raw(text)
        
        return {
            "resume_id": resume_id,
            "parsed_text": text[:500] + "..." if len(text) > 500 else text,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@router.post("/improve")
async def improve_resume(resume_id: str = Form(...)):
    """
    Improve resume using AI.
    """
    try:
        # Get resume from database
        resume = supabase_client.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Improve with AI
        improved = await langchain_ai.improve_resume(resume)
        
        # Save improved version
        supabase_client.save_resume_version(resume_id, improved)
        
        return {
            "resume_id": resume_id,
            "version": improved,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error improving resume: {str(e)}")

@router.post("/tailor")
async def tailor_resume(
    resume_id: str = Form(...),
    job_description: str = Form(...)
):
    """
    Tailor resume for a specific job description.
    """
    try:
        # Get resume from database
        resume = supabase_client.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Tailor with AI
        tailored = await langchain_ai.tailor_resume(resume, job_description)
        
        # Save tailored version
        supabase_client.save_resume_version(resume_id, tailored, version_type="tailored")
        
        return {
            "resume_id": resume_id,
            "tailored": tailored,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tailoring resume: {str(e)}")

@router.get("/templates")
async def get_available_templates():
    """
    Get list of available resume templates.
    """
    try:
        templates = pdf_exporter.get_available_templates()
        # Return templates with preview info
        template_info = [
            {
                "name": template,
                "preview_url": f"/api/v1/resumes/preview/{template}",
                "description": _get_template_description(template)
            }
            for template in templates
        ]
        return {
            "templates": templates,
            "template_info": template_info,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

def _get_template_description(template_name: str) -> str:
    """Get description for a template."""
    descriptions = {
        "default": "Standard professional resume with clean layout",
        "modern": "Contemporary design with gradient header and modern styling",
        "classic": "Traditional Times New Roman format, perfect for conservative industries",
        "minimal": "Clean, minimalist design with focus on content",
        "professional": "Corporate blue design, perfect for business and corporate roles",
        "executive": "Elegant serif font design for senior and executive positions",
        "tech": "Developer-focused design with monospace fonts and tech aesthetics",
        "roshani": "Professional two-column layout - Clean and ATS-friendly format",
    }
    return descriptions.get(template_name, "Professional resume template")

@router.get("/preview/{template_name}")
async def get_template_preview(template_name: str):
    """
    Generate a preview HTML for a template using sample data.
    """
    try:
        # Sample resume data for preview
        sample_data = {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "+1 (555) 123-4567",
            "linkedin": "linkedin.com/in/johndoe",
            "summary": "Experienced software engineer with expertise in full-stack development. Passionate about building scalable applications and leading technical teams.",
            "experiences": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Company Inc.",
                    "period": "2020 - Present",
                    "bullets": [
                        "Led development of microservices architecture",
                        "Improved system performance by 40%",
                        "Mentored team of 5 junior developers"
                    ]
                },
                {
                    "title": "Software Engineer",
                    "company": "Startup Solutions",
                    "period": "2018 - 2020",
                    "bullets": [
                        "Developed RESTful APIs",
                        "Implemented CI/CD pipelines",
                        "Collaborated with cross-functional teams"
                    ]
                }
            ],
            "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of Technology",
                    "year": "2018"
                }
            ],
            "projects": [
                {
                    "name": "E-Commerce Platform",
                    "description": "Built scalable e-commerce platform handling 10K+ daily transactions",
                    "technologies": "React, Node.js, MongoDB"
                }
            ]
        }
        
        # Normalize data
        normalized_data = pdf_exporter.normalize_resume_data(sample_data)
        
        # Get template - use absolute path for Vercel compatibility
        from jinja2 import Environment, FileSystemLoader
        import os
        
        # Get absolute path to templates directory
        current_file = os.path.abspath(__file__)
        # routes_resume.py is in app/api/, so go up two levels to app/, then into templates
        app_dir = os.path.dirname(os.path.dirname(current_file))
        template_dir = os.path.join(app_dir, "templates")
        
        # Ensure template directory exists
        if not os.path.exists(template_dir):
            # Fallback: try relative path
            template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
            template_dir = os.path.abspath(template_dir)
        
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Validate template
        if template_name not in pdf_exporter.AVAILABLE_TEMPLATES:
            template_name = "default"
        
        template_file = pdf_exporter.AVAILABLE_TEMPLATES[template_name]
        template = env.get_template(template_file)
        
        # Render HTML
        html_str = template.render(data=normalized_data)
        
        # Return HTML preview
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_str)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

@router.get("/export/{resume_id}")
async def export_resume(
    resume_id: str, 
    version_type: Optional[str] = "latest",
    template: Optional[str] = "default"
):
    """
    Export resume as PDF with selected template.
    
    Args:
        resume_id: Resume ID
        version_type: Version type (latest, improved, tailored)
        template: Template name (default, modern, classic, minimal)
    """
    try:
        # Get latest resume version
        version = supabase_client.get_latest_resume_version(resume_id, version_type)
        if not version:
            raise HTTPException(status_code=404, detail="Resume version not found")
        
        # Extract content - handle both dict and JSON string
        raw_content = version.get("content")
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Raw content type: {type(raw_content).__name__}")
        
        # Handle content parsing
        if raw_content is None:
            raise HTTPException(status_code=500, detail="Resume content is None")
        
        if isinstance(raw_content, str):
            # If content is a JSON string, parse it
            try:
                content = json.loads(raw_content)
                logger.info("Successfully parsed JSON string to dict")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Invalid JSON in resume content: {str(e)}"
                )
        elif isinstance(raw_content, dict):
            content = raw_content
            logger.info("Content is already a dict")
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Expected dict or str, got {type(raw_content).__name__}: {str(raw_content)[:100]}"
            )
        
        # Validate content structure
        if not content:
            raise HTTPException(
                status_code=500,
                detail="Resume content is empty"
            )
        
        logger.info(f"Content keys: {list(content.keys())}")
        logger.info(f"Using template: {template}")
        
        # Generate PDF with selected template
        try:
            pdf_bytes = pdf_exporter.render_pdf(content, template_name=template)
            logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"PDF generation failed: {str(e)}"
            )
        
        # Upload to Supabase storage
        try:
            url = supabase_client.upload_pdf(resume_id, pdf_bytes, template=template)
            logger.info(f"PDF uploaded to Supabase: {url}")
        except Exception as e:
            logger.error(f"Supabase upload failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload PDF to storage: {str(e)}"
            )
        
        return {
            "resume_id": resume_id,
            "pdf_url": url,
            "template": template,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in export: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting resume: {str(e)}")

@router.post("/ats-score")
async def calculate_ats_score_endpoint(
    resume_id: str = Form(...),
    job_description: str = Form(...)
):
    """
    Calculate ATS score for a resume against a job description.
    """
    try:
        # Get latest resume version
        version = supabase_client.get_latest_resume_version(resume_id, "latest")
        if not version:
            raise HTTPException(status_code=404, detail="Resume version not found")
        
        # Extract content - handle both dict and JSON string
        raw_content = version.get("content")
        
        if raw_content is None:
            raise HTTPException(status_code=500, detail="Resume content is None")
        
        if isinstance(raw_content, str):
            # If content is a JSON string, parse it
            try:
                resume_data = json.loads(raw_content)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Invalid JSON in resume content: {str(e)}"
                )
        elif isinstance(raw_content, dict):
            resume_data = raw_content
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Expected dict or str, got {type(raw_content).__name__}"
            )
        
        # Calculate ATS score
        ats_score = await langchain_ai.calculate_ats_score(resume_data, job_description)
        
        return {
            "resume_id": resume_id,
            "ats_score": ats_score,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating ATS score: {str(e)}")

@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    """
    Get resume by ID.
    """
    try:
        resume = supabase_client.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return resume
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching resume: {str(e)}")

