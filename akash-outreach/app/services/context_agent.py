"""
Context Agent Service
AI-powered context management and admin chat assistant
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from ..models.context_info import get_active_context_info, search_context_info

class ContextAgent:
    """AI agent for context management and admin assistance"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_admin_message(self, message: str, context: Optional[str] = None, user: str = "admin") -> Dict[str, Any]:
        """
        Process admin message and generate response
        This is a basic implementation - will be enhanced with proper AI in Day 3
        """
        
        message_lower = message.lower()
        
        # Simple keyword-based responses for now
        if any(word in message_lower for word in ["course", "program", "degree"]):
            return {
                "message": "I can help you manage course information. You can add new courses, update existing ones, or search through our course catalog. What specific course information would you like to add or update?",
                "suggested_actions": [
                    "Add new course information",
                    "Update existing course details",
                    "View all courses"
                ],
                "extracted_info": {
                    "topic": "courses",
                    "action_needed": "course_management"
                },
                "confidence": 0.8
            }
        
        elif any(word in message_lower for word in ["fee", "cost", "price", "tuition"]):
            return {
                "message": "I can help you update fee structure information. This includes tuition fees, hostel fees, exam fees, and any other charges. What fee information needs to be updated?",
                "suggested_actions": [
                    "Update tuition fees",
                    "Add hostel fee details",
                    "Update scholarship information"
                ],
                "extracted_info": {
                    "topic": "fees",
                    "action_needed": "fee_update"
                },
                "confidence": 0.9
            }
        
        elif any(word in message_lower for word in ["admission", "apply", "application"]):
            return {
                "message": "I can help you manage admission process information. This includes application deadlines, required documents, eligibility criteria, and admission procedures.",
                "suggested_actions": [
                    "Update admission deadlines",
                    "Add document requirements",
                    "Update eligibility criteria"
                ],
                "extracted_info": {
                    "topic": "admission",
                    "action_needed": "admission_info_update"
                },
                "confidence": 0.85
            }
        
        elif any(word in message_lower for word in ["hostel", "accommodation", "facility"]):
            return {
                "message": "I can help you update information about hostel facilities, accommodation options, mess services, and campus amenities.",
                "suggested_actions": [
                    "Update hostel room types",
                    "Add mess menu information",
                    "Update facility details"
                ],
                "extracted_info": {
                    "topic": "facilities",
                    "action_needed": "facility_update"
                },
                "confidence": 0.8
            }
        
        elif any(word in message_lower for word in ["search", "find", "look"]):
            # Extract search terms
            search_terms = message.replace("search", "").replace("find", "").replace("look", "").strip()
            if search_terms:
                results = search_context_info(self.db, search_terms)
                return {
                    "message": f"I found {len(results)} items matching '{search_terms}'. Here are the relevant context items I found in our knowledge base.",
                    "suggested_actions": [
                        "View search results",
                        "Refine search",
                        "Add new information"
                    ],
                    "extracted_info": {
                        "search_query": search_terms,
                        "results_count": len(results)
                    },
                    "confidence": 0.9
                }
        
        else:
            # Generic helpful response
            return {
                "message": "I'm here to help you manage the knowledge base for our Outreach System. I can help you add course information, update fees, manage admission details, and organize any other information that might be useful for parent calls. What would you like to work on?",
                "suggested_actions": [
                    "Add course information",
                    "Update fee structure",
                    "Manage admission details",
                    "Search existing information"
                ],
                "extracted_info": None,
                "confidence": 0.6
            }
    
    async def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search through context information
        Basic implementation - will be enhanced with AI embeddings later
        """
        
        # For now, use simple text search
        results = search_context_info(self.db, query, include_inactive=False)
        
        # Format results
        formatted_results = []
        for item in results[:limit]:
            formatted_results.append({
                "id": item.id,
                "topic": item.topic,
                "information": item.information[:200] + "..." if len(item.information) > 200 else item.information,
                "priority": item.priority,
                "tags": item.tags,
                "relevance_score": 0.8  # Placeholder - would be calculated by AI
            })
        
        return formatted_results
    
    async def suggest_missing_info(self) -> List[str]:
        """Suggest what information might be missing from the knowledge base"""
        
        existing_context = get_active_context_info(self.db)
        existing_topics = {item.topic.lower() for item in existing_context}
        
        # Common topics that should be covered
        important_topics = {
            "course_information",
            "fee_structure", 
            "admission_process",
            "scholarship_details",
            "hostel_facilities",
            "placement_statistics",
            "faculty_information",
            "infrastructure",
            "contact_information",
            "application_deadlines"
        }
        
        missing_topics = important_topics - existing_topics
        
        suggestions = []
        for topic in missing_topics:
            topic_formatted = topic.replace("_", " ").title()
            suggestions.append(f"Add {topic_formatted} information")
        
        return suggestions[:5]  # Return top 5 suggestions

    async def construct_calling_context(self, student_data: dict, campaign_data: dict, context_notes: List[dict]) -> str:
        """
        Construct natural language context for AI caller using student data and context notes
        """
        
        # Extract key information
        student_name = student_data.get('student_name', 'the student')
        phone_number = student_data.get('phone_number', '')
        scholarship_type = student_data.get('scholarship_type', 'scholarship')
        
        # Group context notes by category
        categorized_notes = {}
        for note in context_notes:
            category = note.get('tags', ['Other'])[0] if note.get('tags') else 'Other'
            if category not in categorized_notes:
                categorized_notes[category] = []
            categorized_notes[category].append(note)
        
        # Build natural language context
        context_parts = []
        
        # Introduction and student identification
        context_parts.append(f"""
CALL CONTEXT FOR: {student_name} (Phone: {phone_number})

You are calling on behalf of Akash Institute regarding their {scholarship_type} qualification.
""")
        
        # Add institutional information
        if "About Institution" in categorized_notes:
            context_parts.append("ABOUT AKASH INSTITUTE:")
            for note in categorized_notes["About Institution"]:
                context_parts.append(f"- {note['information']}")
            context_parts.append("")
        
        # Add ANTHE information
        if "About ANTHE" in categorized_notes:
            context_parts.append("ABOUT ANTHE PROGRAM:")
            for note in categorized_notes["About ANTHE"]:
                context_parts.append(f"- {note['information']}")
            context_parts.append("")
        
        # Add scholarship details
        if "Scholarship Information" in categorized_notes:
            context_parts.append(f"SCHOLARSHIP DETAILS FOR {student_name}:")
            for note in categorized_notes["Scholarship Information"]:
                context_parts.append(f"- {note['information']}")
            # Add student-specific scholarship data
            if 'scholarship_amount' in student_data:
                context_parts.append(f"- Amount: ₹{student_data['scholarship_amount']}")
            if 'scholarship_percentage' in student_data:
                context_parts.append(f"- Coverage: {student_data['scholarship_percentage']}")
            context_parts.append("")
        
        # Add program details
        if "Program Details" in categorized_notes:
            context_parts.append("PROGRAM INFORMATION:")
            for note in categorized_notes["Program Details"]:
                context_parts.append(f"- {note['information']}")
            context_parts.append("")
        
        # Add next steps
        if "Next Steps" in categorized_notes:
            context_parts.append("NEXT STEPS TO DISCUSS:")
            for note in categorized_notes["Next Steps"]:
                context_parts.append(f"- {note['information']}")
            context_parts.append("")
        
        # Add success stories
        if "Success Stories" in categorized_notes:
            context_parts.append("SUCCESS STORIES TO SHARE:")
            for note in categorized_notes["Success Stories"]:
                context_parts.append(f"- {note['information']}")
            context_parts.append("")
        
        # Add contact information
        if "Contact Information" in categorized_notes:
            context_parts.append("CONTACT DETAILS TO PROVIDE:")
            for note in categorized_notes["Contact Information"]:
                context_parts.append(f"- {note['information']}")
            context_parts.append("")
        
        # Add conversation guidelines
        context_parts.append("""
CONVERSATION GUIDELINES:
- Be warm, professional, and congratulatory
- Emphasize the achievement and opportunity
- Address parent concerns about quality and value
- Provide clear next steps and deadlines
- Offer to schedule a counseling session
- Be ready to answer questions about courses, fees, and facilities
""")
        
        return "\n".join(context_parts)

    async def preview_calling_context(self, student_data: dict, context_notes: List[dict]) -> str:
        """
        Preview context construction for testing purposes
        """
        
        # Create a mock campaign for preview
        mock_campaign = {
            "name": "Preview Campaign",
            "description": "Preview context construction"
        }
        
        return await self.construct_calling_context(student_data, mock_campaign, context_notes)

    def extract_context_categories(self, context_notes: List[dict]) -> Dict[str, int]:
        """
        Extract and count context categories for analytics
        """
        
        categories = {}
        for note in context_notes:
            category = note.get('tags', ['Other'])[0] if note.get('tags') else 'Other'
            categories[category] = categories.get(category, 0) + 1
        
        return categories

    def prioritize_context_notes(self, context_notes: List[dict], max_notes: int = 10) -> List[dict]:
        """
        Prioritize context notes based on priority and relevance
        """
        
        # Sort by priority (descending) and then by creation date
        sorted_notes = sorted(
            context_notes,
            key=lambda x: (-x.get('priority', 0), x.get('created_at', ''))
        )
        
        return sorted_notes[:max_notes]
