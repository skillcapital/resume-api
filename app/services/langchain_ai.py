import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import OPENAI_API_KEY
from typing import Dict, Any, Optional

# Initialize LLM lazily to avoid errors if API key is missing
llm = None

def get_llm():
    """Get or create LLM instance."""
    global llm
    if llm is None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Please set it in environment variables.")
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

async def tailor_resume(resume: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    Tailor resume for a specific job description.
    """
    try:
        raw_text = resume.get("raw_text", "")
        
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

async def generate_resume_from_info(personal_info: Dict[str, Any], job_description: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a complete resume from personal information using AI.
    """
    try:
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
    ]
}}

IMPORTANT: 
- Extract and list ALL skills mentioned
- Create impactful, metric-driven bullet points
- If job description is provided, tailor the resume for that specific role
- Make the summary compelling and ATS-optimized
 - Preserve provided contact information exactly; do not invent contact details
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
            "skills": ", ".join(personal_info.get("skills", [])) or "None provided",
            "projects": proj_text or "None provided",
            "certifications": ", ".join(personal_info.get("certifications", [])) or "None provided",
            "languages": ", ".join(personal_info.get("languages", [])) or "None provided",
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
        resume_text = f"""
Name: {resume_data.get('name', '')}
Summary: {resume_data.get('summary', '')}

Skills: {', '.join(resume_data.get('skills', []))}

Experiences:
"""
        for exp in resume_data.get('experiences', []):
            resume_text += f"- {exp.get('title', '')} at {exp.get('company', '')}\n"
            for bullet in exp.get('bullets', []):
                resume_text += f"  • {bullet}\n"
        
        resume_text += "\nEducation:\n"
        for edu in resume_data.get('education', []):
            resume_text += f"- {edu.get('degree', '')} from {edu.get('institution', '')}\n"
        
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
