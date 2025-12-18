from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body, Path, Request
from typing import Optional, Dict, Any
import json
import uuid
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
    from app.models.schemas import ResumeCreateRequest, ImproveResumeRequest, TailorResumeRequest, AtsScoreRequest
    SCHEMAS_AVAILABLE = True
except Exception as e:
    SCHEMAS_AVAILABLE = False
    import sys
    print(f"Warning: Failed to import schemas: {str(e)}", file=sys.stderr)
    # Create minimal BaseModels
    class ResumeCreateRequest(BaseModel):
        name: str
        email: Optional[str] = ""
    class ImproveResumeRequest(BaseModel):
        resume_id: str
    class TailorResumeRequest(BaseModel):
        resume_id: str
        job_description: str
    class AtsScoreRequest(BaseModel):
        resume_id: str
        job_description: str

router = APIRouter()

@router.post("/create")
async def create_resume_from_form(resume_data: ResumeCreateRequest = Body(...)):
    """
    Create a resume from form data (no file upload needed) - ChatGPT style.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("POST /create endpoint called")
    
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
        
        # CRITICAL: Always ensure projects, certifications, and languages are present as lists
        # Initialize them first
        generated_resume["projects"] = []
        generated_resume["certifications"] = []
        generated_resume["languages"] = []
        
        # Preserve projects, certifications, and languages from form data
        # Always use original data - AI might not include these or might format them differently
        if resume_data.projects and len(resume_data.projects) > 0:
            # Convert Pydantic models to dicts
            projects_list = []
            for proj in resume_data.projects:
                if hasattr(proj, 'model_dump'):
                    projects_list.append(proj.model_dump())
                elif hasattr(proj, 'dict'):
                    projects_list.append(proj.dict())
                elif isinstance(proj, dict):
                    projects_list.append(proj)
                else:
                    projects_list.append({"name": str(proj), "description": ""})
            generated_resume["projects"] = projects_list
        
        if resume_data.certifications and len(resume_data.certifications) > 0:
            # Preserve original certifications (they're already strings or can be converted)
            generated_resume["certifications"] = resume_data.certifications
        # If empty, keep as empty list (already initialized above)
        
        if resume_data.languages and len(resume_data.languages) > 0:
            # Preserve original languages (they're already strings or can be converted)
            generated_resume["languages"] = resume_data.languages
        # If empty, keep as empty list (already initialized above)
        
        # Final safety check - ensure they're always lists
        if not isinstance(generated_resume.get("projects"), list):
            generated_resume["projects"] = []
        if not isinstance(generated_resume.get("certifications"), list):
            generated_resume["certifications"] = []
        if not isinstance(generated_resume.get("languages"), list):
            generated_resume["languages"] = []
        
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
        
        logger.info(f"Resume created successfully with ID: {resume_id}")
        return {
            "resume_id": resume_id,
            "version": generated_resume,
            "status": "success",
            "message": "Resume created and generated with AI"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error creating resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating resume: {str(e)}")

@router.post("/upload")
async def upload_resume(
    request: Request,
    file: Optional[UploadFile] = File(None),
    pdf: Optional[UploadFile] = File(None),
    document: Optional[UploadFile] = File(None),
    resume: Optional[UploadFile] = File(None)
):
    """
    Upload a PDF resume and extract text.
    Accepts file with field name: 'file', 'pdf', 'document', or 'resume'
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Debug: Log what we received
    logger.info(f"Upload endpoint called - file: {file is not None}, pdf: {pdf is not None}, document: {document is not None}, resume: {resume is not None}")
    
    # Try to get file from any of the accepted field names
    upload_file = file or pdf or document or resume
    
    if not upload_file:
        # Additional debugging - try to get form data
        try:
            form_data = await request.form()
            received_keys = list(form_data.keys()) if hasattr(form_data, 'keys') else []
            logger.warning(f"Received form data keys: {received_keys}")
            logger.warning(f"Content-Type header: {request.headers.get('content-type', 'Not set')}")
        except Exception as e:
            logger.warning(f"Could not inspect form data: {str(e)}")
        
        logger.error("No file received in upload request")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "File is required",
                "message": "Please send a PDF file with one of these field names: 'file', 'pdf', 'document', or 'resume'",
                "accepted_field_names": ["file", "pdf", "document", "resume"],
                "example": {
                    "frontend_code": "const formData = new FormData(); formData.append('file', pdfFile);"
                }
            }
        )
    
    # Validate file type
    if upload_file.content_type not in ["application/pdf", "application/x-pdf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected PDF, got: {upload_file.content_type}. Please upload a PDF file."
        )
    
    try:
        # Extract text from PDF
        text = await pdf_parser.extract_text(upload_file)
        
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
async def improve_resume(request: ImproveResumeRequest = Body(...)):
    """
    Improve resume using AI.
    Accepts JSON body with resume_id and optional full resume data for better context.
    
    Note: This endpoint only accepts fields defined in ImproveResumeRequest schema.
    Fields like 'message', 'status', 'version' from create/upload responses should NOT be included.
    """
    import logging
    logger = logging.getLogger(__name__)
    resume_id = request.resume_id
    logger.info(f"POST /improve endpoint called with resume_id: {resume_id[:50] if resume_id else 'None'}")
    
    try:
        # Validate UUID format
        try:
            uuid.UUID(resume_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid resume ID format. Expected UUID, got: '{resume_id}'. Please use a valid resume ID."
            )
        
        # Build resume data - use provided data if available, otherwise fetch from database
        resume_data = {}
        
        # Check if frontend provided full resume data
        has_provided_data = any([
            request.name,
            request.email,
            request.summary,
            request.experiences,
            request.education,
            request.skills
        ])
        
        # Always check if resume exists in database (required for foreign key constraint)
        resume = supabase_client.get_resume(resume_id)
        if not resume:
            # If resume doesn't exist but we have full data, create it
            if has_provided_data:
                logger.info(f"Resume {resume_id} not found, creating it with provided data")
                # Build raw text from provided data
                raw_text_parts = []
                if request.name:
                    raw_text_parts.append(f"Name: {request.name}")
                if request.email:
                    raw_text_parts.append(f"Email: {request.email}")
                if request.summary:
                    raw_text_parts.append(f"\nSummary: {request.summary}")
                raw_text = "\n".join(raw_text_parts) if raw_text_parts else "Resume created from form data"
                
                # Create resume in database
                created_id = supabase_client.save_resume_raw(raw_text)
                if created_id != resume_id:
                    logger.warning(f"Created resume with different ID: {created_id} (expected: {resume_id})")
                    # Update resume_id to match what was actually created
                    resume_id = created_id
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Resume not found. Resume ID '{resume_id}' does not exist in the database. Please create the resume first using /api/v1/resumes/create or /api/v1/resumes/upload."
                )
        
        # Get existing resume data from database first (to preserve projects/certifications/languages)
        existing_resume_data = {}
        resume = supabase_client.get_resume(resume_id)
        if resume:
            version = supabase_client.get_latest_resume_version(resume_id, "latest")
            if version and version.get("content"):
                content = version.get("content")
                if isinstance(content, str):
                    content = json.loads(content)
                existing_resume_data = content
        
        if has_provided_data:
            # Use provided data from frontend (more accurate and up-to-date)
            logger.info("Using provided resume data from frontend")
            
            # Convert experiences to dicts (handle both Pydantic models and dicts)
            experiences_list = []
            for exp in (request.experiences or []):
                if isinstance(exp, dict):
                    experiences_list.append(exp)
                elif hasattr(exp, 'model_dump'):  # Pydantic v2
                    experiences_list.append(exp.model_dump())
                elif hasattr(exp, 'dict'):  # Pydantic v1
                    experiences_list.append(exp.dict())
                else:
                    experiences_list.append(exp)
            
            # Convert education to dicts (handle both Pydantic models and dicts)
            education_list = []
            for edu in (request.education or []):
                if isinstance(edu, dict):
                    education_list.append(edu)
                elif hasattr(edu, 'model_dump'):  # Pydantic v2
                    education_list.append(edu.model_dump())
                elif hasattr(edu, 'dict'):  # Pydantic v1
                    education_list.append(edu.dict())
                else:
                    education_list.append(edu)
            
            # CRITICAL FIX: Use provided data, but fallback to existing data for projects/certifications/languages
            # if they're not provided or are empty in the request
            projects = request.projects if (request.projects and len(request.projects) > 0) else (existing_resume_data.get('projects') or [])
            certifications = request.certifications if (request.certifications and len(request.certifications) > 0) else (existing_resume_data.get('certifications') or [])
            languages = request.languages if (request.languages and len(request.languages) > 0) else (existing_resume_data.get('languages') or [])
            
            resume_data = {
                "name": request.name or "",
                "email": request.email or "",
                "phone": request.phone or "",
                "linkedin": request.linkedin or "",
                "github": request.github or "",
                "website": request.website or "",
                "summary": request.summary or "",
                "experiences": experiences_list,
                "education": education_list,
                "skills": request.skills or [],
                "projects": projects,
                "certifications": certifications,
                "languages": languages
            }
            logger.info(f"Using projects from: {'request' if (request.projects and len(request.projects) > 0) else 'database'}")
            logger.info(f"Projects count: {len(projects)}")
        else:
            # Fallback: Get resume from database
            logger.info("No provided data, fetching from database")
            resume = supabase_client.get_resume(resume_id)
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            # Get latest version if available
            version = supabase_client.get_latest_resume_version(resume_id, "latest")
            if version and version.get("content"):
                content = version.get("content")
                if isinstance(content, str):
                    content = json.loads(content)
                resume_data = content
            else:
                # Use raw text as fallback
                raw_text = resume.get("raw_text", "")
                resume_data = {"raw_text": raw_text}
        
        # CRITICAL: Ensure projects, certifications, and languages are always present as lists
        if 'projects' not in resume_data or resume_data.get('projects') is None:
            resume_data['projects'] = []
        if 'certifications' not in resume_data or resume_data.get('certifications') is None:
            resume_data['certifications'] = []
        if 'languages' not in resume_data or resume_data.get('languages') is None:
            resume_data['languages'] = []
        
        # Ensure they're lists
        if not isinstance(resume_data.get('projects'), list):
            resume_data['projects'] = []
        if not isinstance(resume_data.get('certifications'), list):
            resume_data['certifications'] = []
        if not isinstance(resume_data.get('languages'), list):
            resume_data['languages'] = []
        
        logger.info(f"Resume data before AI - projects: {resume_data.get('projects')}, certifications: {resume_data.get('certifications')}, languages: {resume_data.get('languages')}")
        
        # Validate resume_data is not empty
        if not resume_data or (isinstance(resume_data, dict) and not any(resume_data.values())):
            logger.error(f"Resume data is empty for resume_id: {resume_id}")
            raise HTTPException(
                status_code=400,
                detail="Resume data is empty. Please provide resume data or ensure the resume exists in the database."
            )
        
        logger.info(f"Resume data keys: {list(resume_data.keys()) if isinstance(resume_data, dict) else 'Not a dict'}")
        
        # Build improvement context
        improvement_context = ""
        if request.improvements and len(request.improvements) > 0:
            improvement_context = f"\n\nSpecific improvements requested:\n" + "\n".join(f"- {imp}" for imp in request.improvements)
        
        tone_context = f"\n\nTone: {request.tone}" if request.tone and request.tone != "professional" else ""
        
        # Improve with AI using structured data
        logger.info("Calling improve_resume_with_data...")
        improved = await langchain_ai.improve_resume_with_data(
            resume_data, 
            improvement_context=improvement_context,
            tone=request.tone or "professional"
        )
        logger.info("AI improvement completed successfully")
        
        # CRITICAL FIX: Before saving, ALWAYS preserve projects/certifications/languages from original
        # Don't trust AI response - always use original data if it exists
        original_projects = resume_data.get('projects', [])
        original_certs = resume_data.get('certifications', [])
        original_langs = resume_data.get('languages', [])
        
        logger.info(f"Original data - projects: {len(original_projects)}, certifications: {len(original_certs)}, languages: {len(original_langs)}")
        logger.info(f"Improved data before fix - projects: {len(improved.get('projects', []))}, certifications: {len(improved.get('certifications', []))}, languages: {len(improved.get('languages', []))}")
        
        # ALWAYS use original data if it has content, regardless of what AI returned
        if original_projects and len(original_projects) > 0:
            logger.info(f"FORCING projects from original: {len(original_projects)} items")
            improved['projects'] = original_projects
        elif not improved.get('projects') or len(improved.get('projects', [])) == 0:
            improved['projects'] = []
        
        if original_certs and len(original_certs) > 0:
            logger.info(f"FORCING certifications from original: {len(original_certs)} items")
            improved['certifications'] = original_certs
        elif not improved.get('certifications') or len(improved.get('certifications', [])) == 0:
            improved['certifications'] = []
        
        if original_langs and len(original_langs) > 0:
            logger.info(f"FORCING languages from original: {len(original_langs)} items")
            improved['languages'] = original_langs
        elif not improved.get('languages') or len(improved.get('languages', [])) == 0:
            improved['languages'] = []
        
        # CRITICAL: Ensure projects, certifications, and languages are always lists before saving
        if 'projects' not in improved or not isinstance(improved.get('projects'), list):
            improved['projects'] = improved.get('projects', []) or []
        if 'certifications' not in improved or not isinstance(improved.get('certifications'), list):
            improved['certifications'] = improved.get('certifications', []) or []
        if 'languages' not in improved or not isinstance(improved.get('languages'), list):
            improved['languages'] = improved.get('languages', []) or []
        
        # Final safety check
        if not isinstance(improved.get('projects'), list):
            improved['projects'] = []
        if not isinstance(improved.get('certifications'), list):
            improved['certifications'] = []
        if not isinstance(improved.get('languages'), list):
            improved['languages'] = []
        
        logger.info(f"Final data before saving - projects: {len(improved.get('projects', []))}, certifications: {len(improved.get('certifications', []))}, languages: {len(improved.get('languages', []))}")
        
        # Save improved version
        supabase_client.save_resume_version(resume_id, improved, version_type="improved")
        
        return {
            "resume_id": resume_id,
            "version": improved,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error improving resume: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error improving resume: {str(e)}"
        )

@router.post("/tailor")
async def tailor_resume(request: TailorResumeRequest = Body(...)):
    """
    Tailor resume for a specific job description.
    Accepts JSON body: {"resume_id": "uuid-string", "job_description": "string"}
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        resume_id = request.resume_id
        job_description = request.job_description
        
        # Validate UUID format
        try:
            uuid.UUID(resume_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid resume ID format. Expected UUID, got: '{resume_id}'. Please use a valid resume ID."
            )
        
        # Get resume from database
        resume = supabase_client.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # CRITICAL FIX: Get latest version with structured data (to preserve projects/certifications/languages)
        resume_data = {}
        version = supabase_client.get_latest_resume_version(resume_id, "latest")
        if version and version.get("content"):
            content = version.get("content")
            if isinstance(content, str):
                content = json.loads(content)
            resume_data = content
            logger.info("Using structured data from latest version for tailoring")
            logger.info(f"Retrieved data keys: {list(resume_data.keys())}")
            logger.info(f"Retrieved projects: {resume_data.get('projects', [])}")
            logger.info(f"Retrieved certifications: {resume_data.get('certifications', [])}")
            logger.info(f"Retrieved languages: {resume_data.get('languages', [])}")
        else:
            # Fallback to raw text
            raw_text = resume.get("raw_text", "")
            resume_data = {"raw_text": raw_text}
            logger.info("Using raw text for tailoring (no structured version found)")
        
        # CRITICAL: Ensure projects, certifications, and languages are always present as lists
        if 'projects' not in resume_data or resume_data.get('projects') is None:
            resume_data['projects'] = []
        if 'certifications' not in resume_data or resume_data.get('certifications') is None:
            resume_data['certifications'] = []
        if 'languages' not in resume_data or resume_data.get('languages') is None:
            resume_data['languages'] = []
        
        # Ensure they're lists
        if not isinstance(resume_data.get('projects'), list):
            resume_data['projects'] = []
        if not isinstance(resume_data.get('certifications'), list):
            resume_data['certifications'] = []
        if not isinstance(resume_data.get('languages'), list):
            resume_data['languages'] = []
        
        logger.info(f"Resume data before tailoring - projects: {len(resume_data.get('projects', []))}, certifications: {len(resume_data.get('certifications', []))}, languages: {len(resume_data.get('languages', []))}")
        
        # Tailor with AI using structured data
        tailored = await langchain_ai.tailor_resume_with_data(resume_data, job_description)
        
        # CRITICAL FIX: Before saving, ALWAYS preserve projects/certifications/languages from original
        # Don't trust AI response - always use original data if it exists
        original_projects = resume_data.get('projects', [])
        original_certs = resume_data.get('certifications', [])
        original_langs = resume_data.get('languages', [])
        
        logger.info(f"Original data - projects: {len(original_projects)}, certifications: {len(original_certs)}, languages: {len(original_langs)}")
        logger.info(f"Tailored data before fix - projects: {len(tailored.get('projects', []))}, certifications: {len(tailored.get('certifications', []))}, languages: {len(tailored.get('languages', []))}")
        
        # ALWAYS use original data if it has content, regardless of what AI returned
        if original_projects and len(original_projects) > 0:
            logger.info(f"FORCING projects from original: {len(original_projects)} items")
            tailored['projects'] = original_projects
        elif not tailored.get('projects') or len(tailored.get('projects', [])) == 0:
            tailored['projects'] = []
        
        if original_certs and len(original_certs) > 0:
            logger.info(f"FORCING certifications from original: {len(original_certs)} items")
            tailored['certifications'] = original_certs
        elif not tailored.get('certifications') or len(tailored.get('certifications', [])) == 0:
            tailored['certifications'] = []
        
        if original_langs and len(original_langs) > 0:
            logger.info(f"FORCING languages from original: {len(original_langs)} items")
            tailored['languages'] = original_langs
        elif not tailored.get('languages') or len(tailored.get('languages', [])) == 0:
            tailored['languages'] = []
        
        # CRITICAL: Ensure projects, certifications, and languages are always lists before saving
        if 'projects' not in tailored or not isinstance(tailored.get('projects'), list):
            tailored['projects'] = tailored.get('projects', []) or []
        if 'certifications' not in tailored or not isinstance(tailored.get('certifications'), list):
            tailored['certifications'] = tailored.get('certifications', []) or []
        if 'languages' not in tailored or not isinstance(tailored.get('languages'), list):
            tailored['languages'] = tailored.get('languages', []) or []
        
        # Final safety check
        if not isinstance(tailored.get('projects'), list):
            tailored['projects'] = []
        if not isinstance(tailored.get('certifications'), list):
            tailored['certifications'] = []
        if not isinstance(tailored.get('languages'), list):
            tailored['languages'] = []
        
        logger.info(f"Final data before saving - projects: {len(tailored.get('projects', []))}, certifications: {len(tailored.get('certifications', []))}, languages: {len(tailored.get('languages', []))}")
        
        # Save tailored version
        supabase_client.save_resume_version(resume_id, tailored, version_type="tailored")
        
        return {
            "resume_id": resume_id,
            "tailored": tailored,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error tailoring resume: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
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
    resume_id: str = Path(..., description="Resume UUID"),
    version_type: Optional[str] = "latest",
    template: Optional[str] = "default"
):
    """
    Export resume as PDF with selected template.
    
    Args:
        resume_id: Resume ID (UUID)
        version_type: Version type (latest, improved, tailored)
        template: Template name (default, modern, classic, minimal)
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(resume_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid resume ID format. Expected UUID, got: '{resume_id}'. Please use a valid resume ID."
            )
        
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
        
        # CRITICAL FIX: Ensure projects, certifications, and languages are always lists
        # Even if they're None or missing, set them to empty lists to avoid issues
        if 'projects' not in content or content.get('projects') is None:
            content['projects'] = []
        if 'certifications' not in content or content.get('certifications') is None:
            content['certifications'] = []
        if 'languages' not in content or content.get('languages') is None:
            content['languages'] = []
        
        # Ensure they're actually lists (not strings or other types)
        if not isinstance(content.get('projects'), list):
            content['projects'] = []
        if not isinstance(content.get('certifications'), list):
            content['certifications'] = []
        if not isinstance(content.get('languages'), list):
            content['languages'] = []
        
        logger.info(f"Content keys: {list(content.keys())}")
        logger.info(f"Content has projects: {bool(content.get('projects'))}")
        logger.info(f"Content has certifications: {bool(content.get('certifications'))}")
        logger.info(f"Content has languages: {bool(content.get('languages'))}")
        logger.info(f"Projects: {content.get('projects')}")
        logger.info(f"Certifications: {content.get('certifications')}")
        logger.info(f"Languages: {content.get('languages')}")
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
        
        # Upload to Supabase storage (optional - for future use)
        try:
            url = supabase_client.upload_pdf(resume_id, pdf_bytes, template=template)
            logger.info(f"PDF uploaded to Supabase: {url}")
        except Exception as e:
            logger.warning(f"Supabase upload failed (continuing with direct download): {str(e)}")
            # Continue even if upload fails - we'll return PDF directly
        
        # Return PDF directly with correct headers
        from fastapi.responses import Response
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="resume_{resume_id}_{template}.pdf"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in export: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting resume: {str(e)}")

@router.post("/ats-score")
async def calculate_ats_score_endpoint(request: AtsScoreRequest = Body(...)):
    """
    Calculate ATS score for a resume against a job description.
    Accepts JSON body: {"resume_id": "uuid-string", "job_description": "string"}
    """
    try:
        resume_id = request.resume_id
        job_description = request.job_description
        
        # Validate UUID format
        try:
            uuid.UUID(resume_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid resume ID format. Expected UUID, got: '{resume_id}'. Please use a valid resume ID."
            )
        
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

# Explicit GET handlers for action endpoints to prevent catch-all route from matching
# These are hidden from Swagger UI since they're just error handlers
@router.get("/improve", include_in_schema=False)
async def get_improve_not_allowed():
    """Prevent GET requests to improve endpoint."""
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. 'improve' is an action endpoint. Use POST /api/v1/resumes/improve instead of GET."
    )

@router.get("/tailor", include_in_schema=False)
async def get_tailor_not_allowed():
    """Prevent GET requests to tailor endpoint."""
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. 'tailor' is an action endpoint. Use POST /api/v1/resumes/tailor instead of GET."
    )

@router.get("/upload", include_in_schema=False)
async def get_upload_not_allowed():
    """Prevent GET requests to upload endpoint."""
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. 'upload' is an action endpoint. Use POST /api/v1/resumes/upload instead of GET."
    )

@router.get("/create", include_in_schema=False)
async def get_create_not_allowed():
    """Prevent GET requests to create endpoint."""
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("GET request received on /create endpoint - method not allowed")
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. 'create' is an action endpoint. Use POST /api/v1/resumes/create instead of GET."
    )

@router.get("/ats-score", include_in_schema=False)
async def get_ats_score_not_allowed():
    """Prevent GET requests to ats-score endpoint."""
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. 'ats-score' is an action endpoint. Use POST /api/v1/resumes/ats-score instead of GET."
    )

@router.get("/{resume_id}")
async def get_resume(resume_id: str = Path(..., description="Resume UUID")):
    """
    Get resume by ID.
    """
    try:
        # Prevent action endpoints from being matched as resume IDs
        action_endpoints = ["create", "upload", "improve", "tailor", "ats-score", "templates", "export", "preview"]
        if resume_id.lower() in action_endpoints:
            raise HTTPException(
                status_code=404,
                detail=f"Resume not found. '{resume_id}' is an action endpoint, not a resume ID. Use GET /api/v1/resumes/{{resume_id}} with a valid UUID."
            )
        
        # Validate UUID format
        try:
            uuid.UUID(resume_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid resume ID format. Expected UUID, got: '{resume_id}'. Please use a valid resume ID."
            )
        
        resume = supabase_client.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return resume
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching resume: {str(e)}")

