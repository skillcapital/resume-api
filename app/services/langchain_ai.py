import json
from typing import Dict, Any, Optional

# Lazy imports to prevent crashes on module load
def _get_chat_openai():
    """Lazy import ChatOpenAI only when needed."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI

def _get_chat_prompt_template():
    """Lazy import ChatPromptTemplate only when needed."""
    from langchain_core.prompts import ChatPromptTemplate
    return ChatPromptTemplate

# Initialize LLM lazily to avoid errors if API key is missing
llm = None

def get_llm():
    """Get or create LLM instance."""
    global llm
    if llm is None:
        from app.core.config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Please set it in environment variables.")
        ChatOpenAI = _get_chat_openai()
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=OPENAI_API_KEY
        )
    return llm

async def improve_resume(resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Improve resume using AI - make it concise, measurable, and action-driven.
    """
    try:
        raw_text = resume.get("raw_text", "")
        
        ChatPromptTemplate = _get_chat_prompt_template()
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a professional resume writer. Rewrite resumes to be concise, measurable, and action-driven. Always return valid JSON."),
            ("human", """
Rewrite this resume text to be professional, concise, measurable, and action-driven.

Return valid JSON with the following structure:
{{
    "name": "Full Name",
    "summary": "2-3 sentence professional summary highlighting key achievements",
    "experiences": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "period": "Start Date - End Date",
            "bullets": ["Achievement 1 with metrics", "Achievement 2 with metrics", "Achievement 3 with impact"]
        }}
    ],
    "skills": ["Technical Skill 1", "Technical Skill 2", "Technical Skill 3", "Technical Skill 4", "Technical Skill 5", "Technical Skill 6", "Technical Skill 7"],
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "Institution Name",
            "year": "Year"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Project description",
            "technologies": "Tech stack used"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification Name",
            "issuer": "Issuing Organization",
            "year": "Year"
        }}
    ]
}}

IMPORTANT: Extract ALL skills from the resume. List ALL technical skills, tools, programming languages, frameworks, and technologies mentioned.

Resume text:
{raw_text}
""")
        ])
        
        chain = prompt_template | get_llm()
        
        response = await chain.ainvoke({"raw_text": raw_text})
        
        # Parse response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        improved_data = json.loads(content)
        
        return improved_data
    except Exception as e:
        raise Exception(f"Error improving resume with AI: {str(e)}")

async def improve_resume_with_data(
    resume_data: Dict[str, Any], 
    improvement_context: str = "",
    tone: str = "professional"
) -> Dict[str, Any]:
    """
    Improve resume using AI with structured data (better than raw text).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        ChatPromptTemplate = _get_chat_prompt_template()
        
        # Build structured context from resume data
        context_parts = []
        
        if resume_data.get("name"):
            context_parts.append(f"Name: {resume_data.get('name')}")
        if resume_data.get("email"):
            context_parts.append(f"Email: {resume_data.get('email')}")
        if resume_data.get("phone"):
            context_parts.append(f"Phone: {resume_data.get('phone')}")
        if resume_data.get("linkedin"):
            context_parts.append(f"LinkedIn: {resume_data.get('linkedin')}")
        if resume_data.get("github"):
            context_parts.append(f"GitHub: {resume_data.get('github')}")
        if resume_data.get("website"):
            context_parts.append(f"Website: {resume_data.get('website')}")
        
        if resume_data.get("summary"):
            context_parts.append(f"\nSummary:\n{resume_data.get('summary')}")
        
        # Format experiences
        if resume_data.get("experiences"):
            context_parts.append("\nWork Experience:")
            for exp in resume_data.get("experiences", []):
                exp_text = f"- {exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get('period'):
                    exp_text += f" ({exp.get('period')})"
                context_parts.append(exp_text)
                if exp.get('description'):
                    context_parts.append(f"  Description: {exp.get('description')}")
                if exp.get('achievements'):
                    for ach in exp.get('achievements', []):
                        context_parts.append(f"  • {ach}")
        
        # Format education
        if resume_data.get("education"):
            context_parts.append("\nEducation:")
            for edu in resume_data.get("education", []):
                edu_text = f"- {edu.get('degree', '')} from {edu.get('institution', '')}"
                if edu.get('year'):
                    edu_text += f" ({edu.get('year')})"
                if edu.get('gpa'):
                    edu_text += f" - GPA: {edu.get('gpa')}"
                context_parts.append(edu_text)
        
        # Format skills - handle both strings and objects
        if resume_data.get("skills"):
            skills_list = resume_data.get('skills', [])
            # Convert to strings if needed
            skills_strings = []
            for skill in skills_list:
                if isinstance(skill, str):
                    skills_strings.append(skill)
                elif isinstance(skill, dict):
                    # If skill is a dict, try to get name or just convert to string
                    skills_strings.append(str(skill.get('name', skill.get('skill', str(skill)))))
                else:
                    skills_strings.append(str(skill))
            if skills_strings:
                context_parts.append(f"\nSkills: {', '.join(skills_strings)}")
        
        # Format projects
        if resume_data.get("projects"):
            context_parts.append("\nProjects:")
            for proj in resume_data.get("projects", []):
                # Handle both dict and string project formats
                if isinstance(proj, str):
                    context_parts.append(f"- {proj}")
                elif isinstance(proj, dict):
                    proj_text = f"- {proj.get('name', 'Project')}"
                    if proj.get('description'):
                        proj_text += f": {proj.get('description')}"
                    if proj.get('technologies'):
                        tech_list = proj.get('technologies')
                        if isinstance(tech_list, list):
                            # Convert technologies to strings
                            tech_strings = []
                            for tech in tech_list:
                                if isinstance(tech, str):
                                    tech_strings.append(tech)
                                elif isinstance(tech, dict):
                                    tech_strings.append(str(tech.get('name', tech.get('technology', str(tech)))))
                                else:
                                    tech_strings.append(str(tech))
                            if tech_strings:
                                proj_text += f" (Tech: {', '.join(tech_strings)})"
                        else:
                            proj_text += f" (Tech: {str(tech_list)})"
                    context_parts.append(proj_text)
                else:
                    context_parts.append(f"- {str(proj)}")
        
        # Format certifications - handle both strings and objects
        if resume_data.get("certifications"):
            certs_list = resume_data.get('certifications', [])
            if isinstance(certs_list, list):
                # Convert to strings if needed
                cert_strings = []
                for cert in certs_list:
                    if isinstance(cert, str):
                        cert_strings.append(cert)
                    elif isinstance(cert, dict):
                        # If cert is a dict, try to get name or just convert to string
                        cert_strings.append(str(cert.get('name', cert.get('certification', str(cert)))))
                    else:
                        cert_strings.append(str(cert))
                if cert_strings:
                    context_parts.append(f"\nCertifications: {', '.join(cert_strings)}")
            else:
                context_parts.append(f"\nCertifications: {str(certs_list)}")
        
        # Format languages - handle both strings and objects
        if resume_data.get("languages"):
            langs_list = resume_data.get('languages', [])
            if isinstance(langs_list, list):
                # Convert to strings if needed
                lang_strings = []
                for lang in langs_list:
                    if isinstance(lang, str):
                        lang_strings.append(lang)
                    elif isinstance(lang, dict):
                        # If lang is a dict, try to get name or just convert to string
                        lang_strings.append(str(lang.get('name', lang.get('language', str(lang)))))
                    else:
                        lang_strings.append(str(lang))
                if lang_strings:
                    context_parts.append(f"\nLanguages: {', '.join(lang_strings)}")
            else:
                context_parts.append(f"\nLanguages: {str(langs_list)}")
        
        # Fallback to raw_text if no structured data
        if not context_parts and resume_data.get("raw_text"):
            context_parts.append(resume_data.get("raw_text"))
        
        structured_context = "\n".join(context_parts)
        
        # Build prompt with tone and improvement context
        tone_instruction = f"Write in a {tone} tone." if tone != "professional" else "Write in a professional tone."
        
        # Build the prompt message directly using f-strings to avoid template variable conflicts
        # Then escape curly braces for LangChain template (use {{ and }} for literal braces)
        json_example_text = """{
    "name": "Full Name",
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": "",
    "website": "",
    "summary": "2-3 sentence professional summary highlighting key achievements and value proposition",
    "experiences": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "period": "Start Date - End Date",
            "bullets": ["Achievement 1 with quantifiable metrics", "Achievement 2 with metrics", "Achievement 3 with impact"]
        }
    ],
    "skills": ["Technical Skill 1", "Technical Skill 2", "Technical Skill 3", "Technical Skill 4", "Technical Skill 5", "Technical Skill 6", "Technical Skill 7", "Technical Skill 8"],
    "education": [
        {
            "degree": "Degree Name",
            "institution": "Institution Name",
            "year": "Year",
            "gpa": "GPA if notable"
        }
    ],
    "projects": [
        {
            "name": "Project Name",
            "description": "Project description with impact",
            "technologies": "Tech stack used"
        }
    ],
    "certifications": [
        {
            "name": "Certification Name",
            "issuer": "Issuing Organization",
            "year": "Year"
        }
    ],
    "languages": ["Language 1", "Language 2", "Language 3"]
}"""
        
        # Build the full human message with f-string, then escape for LangChain template
        human_message_content = f"""Improve and enhance this resume to make it more professional, impactful, and ATS-friendly.

{tone_instruction}

{improvement_context}

Return valid JSON with the following structure:
{json_example_text}

IMPORTANT: 
- Extract and list ALL skills mentioned
- Create impactful, metric-driven bullet points
- Preserve all contact information exactly as provided
- Make the summary compelling and ATS-optimized
- Enhance achievements with quantifiable metrics where possible
- Keep all factual information accurate
- Include ALL projects, certifications, and languages from the original resume data
- Preserve all projects, certifications, and languages exactly as provided

Resume data:
{structured_context}
"""
        
        # Escape curly braces for LangChain template ({{ becomes {, }} becomes })
        human_message_template = human_message_content.replace("{", "{{").replace("}", "}}")
        # But we need {structured_context} to remain as a variable, so restore it
        human_message_template = human_message_template.replace("{{{{structured_context}}}}", "{structured_context}")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", f"You are a professional resume writer. Rewrite resumes to be concise, measurable, and action-driven. {tone_instruction} Always return valid JSON."),
            ("human", human_message_template)
        ])
        
        chain = prompt_template | get_llm()
        
        logger.info(f"Invoking AI with structured_context length: {len(structured_context)}")
        
        response = await chain.ainvoke({"structured_context": structured_context})
        
        # Parse response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        improved_data = json.loads(content)
        
        # Preserve contact info from original data
        if resume_data.get("email"):
            improved_data["email"] = resume_data.get("email")
        if resume_data.get("phone"):
            improved_data["phone"] = resume_data.get("phone")
        if resume_data.get("linkedin"):
            improved_data["linkedin"] = resume_data.get("linkedin")
        if resume_data.get("github"):
            improved_data["github"] = resume_data.get("github")
        if resume_data.get("website"):
            improved_data["website"] = resume_data.get("website")
        
        # CRITICAL FIX: Always preserve projects, certifications, and languages from original data
        # Priority: Original data > AI response > Empty list
        # This ensures we never lose data that was in the original resume
        
        # Projects: Use original if it exists and has data, otherwise use AI response, otherwise empty
        if resume_data.get("projects") and len(resume_data.get("projects", [])) > 0:
            # Original has projects with data - always preserve them
            improved_data["projects"] = resume_data.get("projects")
            logger.info(f"Preserved {len(resume_data.get('projects', []))} projects from original data")
        elif "projects" not in improved_data:
            # Not in original and not in AI response - initialize as empty
            improved_data["projects"] = []
        # If AI response has projects, keep them (but they might be empty, which will be fixed in the endpoint)
        
        # Certifications: Use original if it exists and has data, otherwise use AI response, otherwise empty
        if resume_data.get("certifications") and len(resume_data.get("certifications", [])) > 0:
            # Original has certifications with data - always preserve them
            improved_data["certifications"] = resume_data.get("certifications")
            logger.info(f"Preserved {len(resume_data.get('certifications', []))} certifications from original data")
        elif "certifications" not in improved_data:
            # Not in original and not in AI response - initialize as empty
            improved_data["certifications"] = []
        # If AI response has certifications, keep them (but they might be empty, which will be fixed in the endpoint)
        
        # Languages: Use original if it exists and has data, otherwise use AI response, otherwise empty
        if resume_data.get("languages") and len(resume_data.get("languages", [])) > 0:
            # Original has languages with data - always preserve them
            improved_data["languages"] = resume_data.get("languages")
            logger.info(f"Preserved {len(resume_data.get('languages', []))} languages from original data")
        elif "languages" not in improved_data:
            # Not in original and not in AI response - initialize as empty
            improved_data["languages"] = []
        # If AI response has languages, keep them (but they might be empty, which will be fixed in the endpoint)
        
        # Final safety check - ensure they're always lists
        if not isinstance(improved_data.get("projects"), list):
            improved_data["projects"] = []
        if not isinstance(improved_data.get("certifications"), list):
            improved_data["certifications"] = []
        if not isinstance(improved_data.get("languages"), list):
            improved_data["languages"] = []
        
        logger.info(f"Final improved_data keys: {list(improved_data.keys())}")
        logger.info(f"Final projects: {improved_data.get('projects', [])}")
        logger.info(f"Final certifications: {improved_data.get('certifications', [])}")
        logger.info(f"Final languages: {improved_data.get('languages', [])}")
        
        return improved_data
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error in improve_resume_with_data: {str(e)}")
        logger.error(f"Full traceback:\n{error_traceback}")
        raise Exception(f"Error improving resume with AI: {str(e)}")

async def tailor_resume(resume: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Tailor resume for a specific job description (legacy function using raw text).
    """
    try:
        raw_text = resume.get("raw_text", "")
        
        ChatPromptTemplate = _get_chat_prompt_template()
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a professional resume writer specializing in ATS optimization. Tailor resumes to match job descriptions perfectly. Always return valid JSON."),
            ("human", """
Tailor this resume for the given job description. Highlight relevant experiences and skills that match the job requirements.

Return valid JSON with the following structure:
{{
    "name": "Full Name",
    "summary": "Tailored 2-3 sentence summary matching job requirements",
    "experiences": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "period": "Start Date - End Date",
            "bullets": ["Relevant achievement 1 with metrics", "Relevant achievement 2 with metrics"]
        }}
    ],
    "skills": ["Relevant Skill 1", "Relevant Skill 2", "Relevant Skill 3", "Relevant Skill 4", "Relevant Skill 5", "Relevant Skill 6"],
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "Institution Name",
            "year": "Year"
        }}
    ]
}}

IMPORTANT: Include ALL skills from the original resume that are relevant to the job. Prioritize skills mentioned in the job description.

Resume text:
{raw_text}

Job Description:
{job_description}

Return tailored JSON with improved summary and relevant experiences only.
""")
        ])
        
        chain = prompt_template | get_llm()
        
        response = await chain.ainvoke({
            "raw_text": raw_text,
            "job_description": job_description
        })
        
        # Parse response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        tailored_data = json.loads(content)
        
        return tailored_data
    except Exception as e:
        raise Exception(f"Error tailoring resume with AI: {str(e)}")

async def tailor_resume_with_data(resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Tailor resume for a specific job description using structured data (better than raw text).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        ChatPromptTemplate = _get_chat_prompt_template()
        
        # Build structured context from resume data
        context_parts = []
        
        if resume_data.get("name"):
            context_parts.append(f"Name: {resume_data.get('name')}")
        if resume_data.get("email"):
            context_parts.append(f"Email: {resume_data.get('email')}")
        if resume_data.get("phone"):
            context_parts.append(f"Phone: {resume_data.get('phone')}")
        if resume_data.get("linkedin"):
            context_parts.append(f"LinkedIn: {resume_data.get('linkedin')}")
        if resume_data.get("github"):
            context_parts.append(f"GitHub: {resume_data.get('github')}")
        if resume_data.get("website"):
            context_parts.append(f"Website: {resume_data.get('website')}")
        
        if resume_data.get("summary"):
            context_parts.append(f"\nSummary:\n{resume_data.get('summary')}")
        
        # Format experiences
        if resume_data.get("experiences"):
            context_parts.append("\nWork Experience:")
            for exp in resume_data.get("experiences", []):
                exp_text = f"- {exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get('period'):
                    exp_text += f" ({exp.get('period')})"
                context_parts.append(exp_text)
                if exp.get('bullets'):
                    for bullet in exp.get('bullets', []):
                        context_parts.append(f"  • {bullet}")
                elif exp.get('description'):
                    context_parts.append(f"  Description: {exp.get('description')}")
        
        # Format education
        if resume_data.get("education"):
            context_parts.append("\nEducation:")
            for edu in resume_data.get("education", []):
                edu_text = f"- {edu.get('degree', '')} from {edu.get('institution', '')}"
                if edu.get('year'):
                    edu_text += f" ({edu.get('year')})"
                if edu.get('gpa'):
                    edu_text += f" - GPA: {edu.get('gpa')}"
                context_parts.append(edu_text)
        
        # Format skills
        if resume_data.get("skills"):
            skills_list = resume_data.get('skills', [])
            skills_strings = []
            for skill in skills_list:
                if isinstance(skill, str):
                    skills_strings.append(skill)
                elif isinstance(skill, dict):
                    skills_strings.append(str(skill.get('name', skill.get('skill', str(skill)))))
                else:
                    skills_strings.append(str(skill))
            if skills_strings:
                context_parts.append(f"\nSkills: {', '.join(skills_strings)}")
        
        # Fallback to raw_text if no structured data
        if not context_parts and resume_data.get("raw_text"):
            context_parts.append(resume_data.get("raw_text"))
        
        structured_context = "\n".join(context_parts)
        
        # Build prompt
        json_example_text = """{
    "name": "Full Name",
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": "",
    "website": "",
    "summary": "Tailored 2-3 sentence summary matching job requirements",
    "experiences": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "period": "Start Date - End Date",
            "bullets": ["Relevant achievement 1 with metrics", "Relevant achievement 2 with metrics"]
        }
    ],
    "skills": ["Relevant Skill 1", "Relevant Skill 2", "Relevant Skill 3"],
    "education": [
        {
            "degree": "Degree Name",
            "institution": "Institution Name",
            "year": "Year"
        }
    ]
}"""
        
        human_message_content = f"""Tailor this resume for the given job description. Highlight relevant experiences and skills that match the job requirements.

Return valid JSON with the following structure:
{json_example_text}

IMPORTANT: 
- Include ALL skills from the original resume that are relevant to the job
- Prioritize skills mentioned in the job description
- Tailor the summary to match job requirements
- Highlight relevant experiences and achievements

Resume data:
{structured_context}

Job Description:
{job_description}

Return tailored JSON with improved summary and relevant experiences.
"""
        
        # Escape curly braces for LangChain template
        human_message_template = human_message_content.replace("{", "{{").replace("}", "}}")
        human_message_template = human_message_template.replace("{{{{structured_context}}}}", "{{structured_context}}")
        human_message_template = human_message_template.replace("{{{{job_description}}}}", "{{job_description}}")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a professional resume writer specializing in ATS optimization. Tailor resumes to match job descriptions perfectly. Always return valid JSON."),
            ("human", human_message_template)
        ])
        
        chain = prompt_template | get_llm()
        
        logger.info(f"Invoking AI for tailoring with structured_context length: {len(structured_context)}")
        
        response = await chain.ainvoke({
            "structured_context": structured_context,
            "job_description": job_description
        })
        
        # Parse response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        tailored_data = json.loads(content)
        
        # Preserve contact info from original data
        if resume_data.get("email"):
            tailored_data["email"] = resume_data.get("email")
        if resume_data.get("phone"):
            tailored_data["phone"] = resume_data.get("phone")
        if resume_data.get("linkedin"):
            tailored_data["linkedin"] = resume_data.get("linkedin")
        if resume_data.get("github"):
            tailored_data["github"] = resume_data.get("github")
        if resume_data.get("website"):
            tailored_data["website"] = resume_data.get("website")
        
        # CRITICAL FIX: Always preserve projects, certifications, and languages from original data
        # Priority: Original data > AI response > Empty list
        if resume_data.get("projects") and len(resume_data.get("projects", [])) > 0:
            # Original has projects with data - always preserve them
            tailored_data["projects"] = resume_data.get("projects")
            logger.info(f"Preserved {len(resume_data.get('projects', []))} projects from original data")
        elif "projects" not in tailored_data:
            # Not in original and not in AI response - initialize as empty
            tailored_data["projects"] = []
        
        if resume_data.get("certifications") and len(resume_data.get("certifications", [])) > 0:
            # Original has certifications with data - always preserve them
            tailored_data["certifications"] = resume_data.get("certifications")
            logger.info(f"Preserved {len(resume_data.get('certifications', []))} certifications from original data")
        elif "certifications" not in tailored_data:
            # Not in original and not in AI response - initialize as empty
            tailored_data["certifications"] = []
        
        if resume_data.get("languages") and len(resume_data.get("languages", [])) > 0:
            # Original has languages with data - always preserve them
            tailored_data["languages"] = resume_data.get("languages")
            logger.info(f"Preserved {len(resume_data.get('languages', []))} languages from original data")
        elif "languages" not in tailored_data:
            # Not in original and not in AI response - initialize as empty
            tailored_data["languages"] = []
        
        # Final safety check - ensure they're always lists
        if not isinstance(tailored_data.get("projects"), list):
            tailored_data["projects"] = []
        if not isinstance(tailored_data.get("certifications"), list):
            tailored_data["certifications"] = []
        if not isinstance(tailored_data.get("languages"), list):
            tailored_data["languages"] = []
        
        logger.info(f"Final tailored_data keys: {list(tailored_data.keys())}")
        logger.info(f"Final projects: {tailored_data.get('projects', [])}")
        logger.info(f"Final certifications: {tailored_data.get('certifications', [])}")
        logger.info(f"Final languages: {tailored_data.get('languages', [])}")
        
        return tailored_data
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error in tailor_resume_with_data: {str(e)}")
        logger.error(f"Full traceback:\n{error_traceback}")
        raise Exception(f"Error tailoring resume with AI: {str(e)}")

async def generate_resume_from_info(personal_info: Dict[str, Any], job_description: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a complete resume from personal information using AI.
    """
    try:
        ChatPromptTemplate = _get_chat_prompt_template()
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a professional resume writer. Create compelling, ATS-friendly resumes from provided information. Always return valid JSON. If contact fields (email, phone, linkedin, github, website) are provided, include them exactly as given; otherwise return empty strings for those fields."),
            ("human", """
Create a professional resume based on the following information.

Personal Information:
- Name: {name}
- Email: {email}
- Phone: {phone}
- LinkedIn: {linkedin}
- GitHub: {github}
- Website: {website}

Summary: {summary}

Experiences:
{experiences}

Education:
{education}

Skills: {skills}

Projects:
{projects}

Certifications: {certifications}

Languages: {languages}

{job_context}

Return valid JSON with the following structure:
{{
    "name": "Full Name",
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": "",
    "website": "",
    "summary": "Professional 2-3 sentence summary highlighting key achievements and value proposition",
    "experiences": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "period": "Start Date - End Date",
            "bullets": ["Achievement 1 with quantifiable metrics", "Achievement 2 with metrics", "Achievement 3 with impact"]
        }}
    ],
    "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5", "Skill 6", "Skill 7", "Skill 8"],
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "Institution Name",
            "year": "Year"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Project description and impact",
            "technologies": "Tech stack"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification Name",
            "issuer": "Issuing Organization",
            "year": "Year"
        }}
    ],
    "languages": ["Language 1", "Language 2"]
}}

IMPORTANT: 
- Extract and list ALL skills mentioned
- Create impactful, metric-driven bullet points
- If job description is provided, tailor the resume for that specific role
- Make the summary compelling and ATS-optimized
- Preserve provided contact information exactly; do not invent contact details
- Include ALL projects, certifications, and languages from the provided information
""")
        ])
        
        # Format experiences
        exp_text = ""
        for exp in personal_info.get("experiences", []):
            exp_text += f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('period', '')})\n"
            if exp.get("description"):
                exp_text += f"  Description: {exp.get('description')}\n"
            if exp.get("achievements"):
                for ach in exp.get("achievements", []):
                    exp_text += f"  - {ach}\n"
        
        # Format education
        edu_text = ""
        for edu in personal_info.get("education", []):
            edu_text += f"- {edu.get('degree', '')} from {edu.get('institution', '')} ({edu.get('year', '')})\n"
        
        # Format projects
        proj_text = ""
        for proj in personal_info.get("projects", []):
            if isinstance(proj, dict):
                proj_text += f"- {proj.get('name', 'Project')}: {proj.get('description', '')}\n"
            else:
                proj_text += f"- {proj}\n"
        
        job_context = ""
        if job_description:
            job_context = f"\nJob Description to tailor for:\n{job_description}"
        
        chain = prompt_template | get_llm()
        
        response = await chain.ainvoke({
            "name": personal_info.get("name", ""),
            "email": personal_info.get("email", ""),
            "phone": personal_info.get("phone", ""),
            "linkedin": personal_info.get("linkedin", ""),
            "github": personal_info.get("github", ""),
            "website": personal_info.get("website", ""),
            "summary": personal_info.get("summary", ""),
            "experiences": exp_text or "None provided",
            "education": edu_text or "None provided",
            "skills": ", ".join([str(s) if isinstance(s, str) else str(s.get('name', s.get('skill', s))) if isinstance(s, dict) else str(s) for s in personal_info.get("skills", [])]) or "None provided",
            "projects": proj_text or "None provided",
            "certifications": ", ".join([str(c) if isinstance(c, str) else str(c.get('name', c.get('certification', c))) if isinstance(c, dict) else str(c) for c in personal_info.get("certifications", [])]) or "None provided",
            "languages": ", ".join([str(l) if isinstance(l, str) else str(l.get('name', l.get('language', l))) if isinstance(l, dict) else str(l) for l in personal_info.get("languages", [])]) or "None provided",
            "job_context": job_context
        })
        
        # Parse response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        generated_data = json.loads(content)
        
        return generated_data
    except Exception as e:
        raise Exception(f"Error generating resume with AI: {str(e)}")

async def calculate_ats_score(resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Calculate ATS (Applicant Tracking System) score by comparing resume against job description.
    Returns a detailed score breakdown with recommendations.
    """
    try:
        # Format resume data for analysis
        # Convert skills to strings if needed
        skills_list = resume_data.get('skills', [])
        skills_strings = []
        for skill in skills_list:
            if isinstance(skill, str):
                skills_strings.append(skill)
            elif isinstance(skill, dict):
                skills_strings.append(str(skill.get('name', skill.get('skill', str(skill)))))
            else:
                skills_strings.append(str(skill))
        
        resume_text = f"""
Name: {resume_data.get('name', '')}
Summary: {resume_data.get('summary', '')}

Skills: {', '.join(skills_strings) if skills_strings else 'None'}

Experiences:
"""
        for exp in resume_data.get('experiences', []):
            resume_text += f"- {exp.get('title', '')} at {exp.get('company', '')}\n"
            for bullet in exp.get('bullets', []):
                resume_text += f"  • {bullet}\n"
        
        resume_text += "\nEducation:\n"
        for edu in resume_data.get('education', []):
            resume_text += f"- {edu.get('degree', '')} from {edu.get('institution', '')}\n"
        
        ChatPromptTemplate = _get_chat_prompt_template()
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert ATS (Applicant Tracking System) analyzer. Analyze resumes against job descriptions and provide detailed scoring. Always return valid JSON."),
            ("human", """
Analyze this resume against the job description and calculate an ATS compatibility score.

Resume:
{resume_text}

Job Description:
{job_description}

Return valid JSON with the following structure:
{{
    "overall_score": 85,
    "score_breakdown": {{
        "skills_match": {{
            "score": 90,
            "max_score": 100,
            "description": "Percentage of required skills found in resume"
        }},
        "keyword_match": {{
            "score": 80,
            "max_score": 100,
            "description": "Relevance of keywords and phrases from job description"
        }},
        "experience_relevance": {{
            "score": 85,
            "max_score": 100,
            "description": "How well work experience matches job requirements"
        }},
        "education_match": {{
            "score": 90,
            "max_score": 100,
            "description": "Education qualifications matching job requirements"
        }},
        "formatting": {{
            "score": 95,
            "max_score": 100,
            "description": "ATS-friendly formatting and structure"
        }}
    }},
    "matched_skills": ["Python", "JavaScript", "React", "Node.js"],
    "missing_skills": ["Docker", "Kubernetes"],
    "recommendations": [
        "Add more specific technical skills mentioned in the job description",
        "Include metrics and quantifiable achievements",
        "Tailor summary to highlight relevant experience",
        "Add missing keywords from job description"
    ],
    "strengths": [
        "Strong technical skills match",
        "Relevant work experience",
        "Well-structured format"
    ],
    "weaknesses": [
        "Missing some required technologies",
        "Could add more quantifiable metrics"
    ]
}}

Calculate scores based on:
- Skills Match: Compare required skills from job description with resume skills (0-100)
- Keyword Match: Analyze how many important keywords from job description appear in resume (0-100)
- Experience Relevance: Evaluate if work experience aligns with job requirements (0-100)
- Education Match: Check if education meets job requirements (0-100)
- Formatting: Assess ATS-friendly formatting and structure (0-100)

Overall score should be a weighted average, with skills and keywords being most important.

Provide specific, actionable recommendations to improve the score.
""")
        ])
        
        chain = prompt_template | get_llm()
        
        response = await chain.ainvoke({
            "resume_text": resume_text,
            "job_description": job_description
        })
        
        # Parse response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        ats_data = json.loads(content)
        
        return ats_data
    except Exception as e:
        raise Exception(f"Error calculating ATS score: {str(e)}")
