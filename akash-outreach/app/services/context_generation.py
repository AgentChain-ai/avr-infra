"""
Context Generation Service for AI-powered personalized student outreach
"""

import logging
import openai
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ..models.student import Student
from ..models.context_info import ContextInfo
from ..config import settings

logger = logging.getLogger(__name__)

class ContextGenerationService:
    """Service for generating personalized contexts using AI"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_campaign_contexts(
        self, 
        campaign_id: int, 
        context_notes: List[ContextInfo], 
        students: List[Student]
    ) -> Dict[str, Any]:
        """Generate personalized contexts for all students in a campaign"""
        
        logger.info(f"Starting context generation for campaign {campaign_id}")
        logger.info(f"Found {len(context_notes)} context notes and {len(students)} students")
        
        # Prepare context information
        context_info = self._prepare_context_info(context_notes)
        
        # Generate contexts for each student
        personalized_contexts = {}
        
        for student in students:
            try:
                context_text = await self._generate_student_context(student, context_info)
                
                # Create structured context data
                student_data = student.student_data or {}
                context_data = {
                    "student_name": student_data.get("student_name", f"Student {student.id}"),
                    "phone_number": student_data.get("phone_number", "N/A"),
                    "context": context_text
                }
                
                personalized_contexts[str(student.id)] = context_data
                
            except Exception as e:
                logger.error(f"Failed to generate AI context for student {student.id}: {str(e)}")
                # If individual context generation fails, use fallback
                fallback_context = self._create_fallback_context(student, context_notes)
                student_data = student.student_data or {}
                
                context_data = {
                    "student_name": student_data.get("student_name", f"Student {student.id}"),
                    "phone_number": student_data.get("phone_number", "N/A"),
                    "context": fallback_context
                }
                
                personalized_contexts[str(student.id)] = context_data
        
        logger.info(f"Generated contexts for {len(personalized_contexts)} students")
        
        return personalized_contexts
    
    def _prepare_context_info(self, context_notes: List[ContextInfo]) -> str:
        """Prepare context information from context notes"""
        
        context_sections = []
        
        for note in context_notes:
            section = f"**{note.topic}**\n{note.information}"
            context_sections.append(section)
        
        return "\n\n".join(context_sections)
    
    async def _generate_student_context(self, student: Student, context_info: str) -> str:
        """Generate personalized context for a single student using AI"""
        
        # Get student data
        student_data = student.student_data or {}
        student_name = student_data.get("student_name", "the student")
        parent_name = student_data.get("parent_name", "Parent")
        scholarship_amount = student_data.get("scholarship_amount", "")
        scholarship_percentage = student_data.get("scholarship_percentage", "")
        test_score = student_data.get("test_score", "")
        rank_achieved = student_data.get("rank_achieved", "")
        
        # Create personalized prompt
        prompt = self._create_personalization_prompt(
            student_name, parent_name, scholarship_amount, 
            scholarship_percentage, test_score, rank_achieved, 
            student_data, context_info
        )
        
        try:
            logger.debug(f"Making OpenAI API call for student {student.id}")
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert educational consultant and communication specialist creating personalized conversation contexts for parent outreach calls about scholarship achievements. 

Your expertise includes:
- Educational counseling and parent communication
- Scholarship and admission processes  
- Understanding student and family concerns
- Creating natural, warm conversation guidance

Create detailed, actionable context that enables meaningful, personalized conversations. Focus on being specific, relevant, and helpful while maintaining a warm, professional tone."""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI API success for student {student.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error for student {student.id}: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _create_personalization_prompt(
        self, student_name: str, parent_name: str, 
        scholarship_amount: Any, scholarship_percentage: Any,
        test_score: Any, rank_achieved: Any,
        student_data: Dict[str, Any], context_info: str
    ) -> str:
        """Create AI prompt for personalized context generation"""
        
        # Extract additional relevant fields for better personalization
        course_interest = student_data.get('course_interested', student_data.get('preferred_course', ''))
        city = student_data.get('city', student_data.get('location', ''))
        previous_school = student_data.get('school_name', student_data.get('current_school', ''))
        
        prompt = f"""
You are creating a personalized conversation context for an AI voice agent making a congratulatory call to parents about their child's scholarship achievement. This is NOT a script - it's background context and talking points.

=== STUDENT PROFILE ===
Student: {student_name}
Parent: {parent_name}
Test Score: {test_score}
National Rank: {rank_achieved}
Scholarship Awarded: ₹{scholarship_amount} ({scholarship_percentage}% fee waiver)
Course Interest: {course_interest}
Location: {city}
School: {previous_school}

=== COMPLETE STUDENT DATA ===
{json.dumps(student_data, indent=2)}

=== INSTITUTE INFORMATION TO LEVERAGE ===
{context_info}

=== CONVERSATION CONTEXT REQUIREMENTS ===

Create a rich, personalized context that enables natural conversation. Include:

🎯 **PERSONALIZED OPENING**
- Specific congratulations mentioning their exact achievement
- Reference their rank, score, and scholarship amount specifically
- Connect to their course interest or location if relevant

📋 **KEY TALKING POINTS**
- Scholarship details: amount, percentage, what it covers
- Next steps with specific deadlines and requirements
- Course-specific benefits (if course interest is known)
- Campus facilities most relevant to this student profile
- Success stories of similar students (rank range, location, courses)

❓ **ANTICIPATED QUESTIONS & RESPONSES**
- Fee structure and payment options
- Admission timeline and documentation required
- Hostel facilities (especially if student is from out of town)
- Course curriculum and career prospects
- Comparison with other institutes

🎯 **CONVERSATION FLOW GUIDANCE**
- Start with warm congratulations and specific achievement recognition
- Transition naturally to scholarship benefits
- Address likely concerns based on student profile
- Provide clear, actionable next steps
- Maintain encouraging, professional tone throughout

💡 **PERSONALIZATION NOTES**
- Reference specific aspects of institute information that align with student's interests
- Adjust communication style based on student's background
- Highlight opportunities most relevant to their career path
- Address location-specific considerations if student is from outside local area

OUTPUT FORMAT: Write 400-600 words of rich context that the AI agent can use to conduct a natural, informed conversation. Focus on conversation guidance, not scripted dialogue.

PERSONALIZED CONVERSATION CONTEXT:
"""
        
        return prompt
    
    def _create_fallback_context(self, student: Student, context_notes: List[ContextInfo]) -> str:
        """Create fallback context when AI generation fails"""
        
        student_data = student.student_data or {}
        student_name = student_data.get("student_name", "the student")
        parent_name = student_data.get("parent_name", "Parent")
        scholarship_amount = student_data.get("scholarship_amount", "")
        scholarship_percentage = student_data.get("scholarship_percentage", "")
        test_score = student_data.get("test_score", "")
        rank_achieved = student_data.get("rank_achieved", "")
        course_interest = student_data.get("course_interested", student_data.get("preferred_course", ""))
        
        context = f"""
🎉 PERSONALIZED CONVERSATION CONTEXT FOR {student_name.upper()}

**OPENING CONGRATULATIONS**
Congratulations to {student_name} on achieving excellent results in the entrance examination! {student_name} has earned a rank of {rank_achieved} with a score of {test_score}, which qualifies for a scholarship of ₹{scholarship_amount} ({scholarship_percentage}% fee waiver).

**KEY TALKING POINTS**
- Acknowledge {student_name}'s specific achievement (rank {rank_achieved}, score {test_score})
- Scholarship Details: ₹{scholarship_amount} scholarship ({scholarship_percentage}% fee waiver)
- Course Interest: {course_interest if course_interest else 'Discuss available programs'}
- Next Steps: Complete admission formalities and document submission

**CONVERSATION GUIDANCE**
When speaking with {parent_name}:
1. Start with warm congratulations and specific achievement recognition
2. Clearly explain scholarship benefits and what it covers
3. Provide admission timeline and required documentation
4. Address questions about facilities, courses, and career prospects
5. Offer assistance with admission process and next steps

**AVAILABLE INSTITUTE INFORMATION**"""
        
        # Add available context information
        for note in context_notes:
            context += f"\n- **{note.topic}**: {note.information[:200]}..."
        
        context += f"""

**CONVERSATION OBJECTIVES**
- Ensure {parent_name} understands the scholarship value and next steps
- Address any concerns about admission process or institute facilities
- Provide clear timeline for admission completion
- Maintain warm, supportive, and professional tone throughout
- Offer ongoing support and contact information for further queries

**PERSONALIZATION NOTES**
- Use {student_name}'s name frequently to personalize the conversation
- Reference their specific achievements to build confidence
- Adapt information based on {parent_name}'s questions and concerns
- Maintain encouraging tone about {student_name}'s bright future prospects
"""
        
        return context
    
    async def generate_single_context(
        self, 
        student_id: int, 
        context_note_ids: List[int]
    ) -> str:
        """Generate context for a single student (for testing/preview)"""
        
        # Get student
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise ValueError(f"Student with ID {student_id} not found")
        
        # Get context notes
        context_notes = self.db.query(ContextInfo).filter(
            ContextInfo.id.in_(context_note_ids)
        ).all()
        
        if not context_notes:
            raise ValueError("No valid context notes found")
        
        # Generate context
        context_info = self._prepare_context_info(context_notes)
        return await self._generate_student_context(student, context_info)
