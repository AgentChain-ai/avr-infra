"""
AI Context management page - Context Notes for Natural Language Construction
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from config.context_config import get_context_categories

def show_context():
    """Display AI context management page with context notes system"""
    
    st.title("🤖 AI Context Management")
    st.markdown("Create and manage context notes for personalized AI calling campaigns.")
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Context Notes", "➕ Create Note", "📊 Analytics", "🔧 Manage Categories"])
    
    with tab1:
        show_context_notes_list(api_client)
    
    with tab2:
        show_create_context_note(api_client)
    
    with tab3:
        show_context_analytics(api_client)
        
    with tab4:
        show_category_management(api_client)

def show_context_notes_list(api_client):
    """Display list of context notes with management options"""
    
    st.subheader("📝 Context Notes Library")
    
    try:
        # Get context notes from API
        with st.spinner("📊 Loading context notes..."):
            context_notes = api_client.get_context_notes()
        
        if not context_notes:
            st.info("📝 No context notes found. Create your first context note using the 'Create Note' tab!")
            return
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Notes", len(context_notes))
        
        with col2:
            active_notes = len([n for n in context_notes if n.get('is_active', True)])
            st.metric("Active Notes", active_notes)
        
        with col3:
            categories = set(n.get('category', 'Uncategorized') for n in context_notes)
            st.metric("Categories", len(categories))
        
        with col4:
            high_priority = len([n for n in context_notes if n.get('priority', 0) >= 8])
            st.metric("High Priority", high_priority)
        
        st.markdown("---")
        
        # Category filter
        categories = ['All'] + sorted(set(n.get('category', 'Uncategorized') for n in context_notes))
        selected_category = st.selectbox("Filter by Category", categories)
        
        # Filter notes
        filtered_notes = context_notes
        if selected_category != 'All':
            filtered_notes = [n for n in context_notes if n.get('category') == selected_category]
        
        # Display notes as cards
        for note in filtered_notes:
            render_context_note_card(note, api_client)
        
    except Exception as e:
        st.error(f"❌ Error loading context notes: {str(e)}")

def render_context_note_card(note: Dict[str, Any], api_client):
    """Render a single context note as a card"""
    
    with st.container():
        # Header with status and priority
        col1, col2 = st.columns([4, 1])
        
        with col1:
            status_icon = "🟢" if note.get('is_active', True) else "🔴"
            priority = note.get('priority', 0)
            priority_color = "🔴" if priority >= 8 else "🟡" if priority >= 5 else "⚪"
            
            st.markdown(f"""
            **{status_icon} {note.get('title', 'Untitled Note')} {priority_color}**
            
            **Category:** {note.get('category', 'Uncategorized')} | **Priority:** {priority}/10
            """)
        
        with col2:
            # Action buttons
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button("✏️", key=f"edit_note_{note.get('id')}", help="Edit Note"):
                    st.session_state[f"editing_note_{note.get('id')}"] = True
                    st.rerun()
            
            with col_delete:
                if st.button("🗑️", key=f"delete_note_{note.get('id')}", help="Delete Note", type="secondary"):
                    if st.session_state.get(f"confirm_delete_note_{note.get('id')}"):
                        delete_context_note(note.get('id'), api_client)
                    else:
                        st.session_state[f"confirm_delete_note_{note.get('id')}"] = True
                        st.rerun()
        
        # Content preview
        content = note.get('content', '')
        preview = content[:200] + "..." if len(content) > 200 else content
        st.markdown(f"📄 **Content Preview:** {preview}")
        
        # Tags
        tags = note.get('tags', [])
        if tags:
            tag_str = " ".join([f"`{tag}`" for tag in tags])
            st.markdown(f"🏷️ **Tags:** {tag_str}")
        
        # Show confirmation for delete
        if st.session_state.get(f"confirm_delete_note_{note.get('id')}"):
            st.warning("⚠️ Click Delete again to confirm removal")
        
        # Show edit form if editing
        if st.session_state.get(f"editing_note_{note.get('id')}"):
            show_edit_context_note_form(note, api_client)
        
        st.markdown("---")

def show_create_context_note(api_client):
    """Display form to create new context note"""
    
    st.subheader("➕ Create New Context Note")
    
    with st.form("create_context_note", clear_on_submit=True):
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Note Title *",
                placeholder="e.g., About Akash Institute",
                help="Short, descriptive title for this context note"
            )
            
            category = st.selectbox(
                "Category *",
                options=get_context_categories(),
                help="Categorize this context for better organization"
            )
        
        with col2:
            priority = st.slider(
                "Priority Level",
                min_value=1,
                max_value=10,
                value=5,
                help="1 = Low priority, 10 = High priority"
            )
            
            is_active = st.checkbox("Active", value=True, help="Include in context construction")
        
        # Content
        content = st.text_area(
            "Context Content *",
            placeholder="Write the detailed context information that the AI caller should know...",
            height=200,
            help="This content will be used to build natural language prompts for AI callers"
        )
        
        # Tags
        tags_input = st.text_input(
            "Tags (comma-separated)",
            placeholder="e.g., admission, fees, scholarship, jee",
            help="Add tags for easy searching and filtering"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Context Note", type="primary")
        
        if submitted:
            # Validation
            if not title or not content:
                st.error("❌ Title and content are required")
                return
            
            try:
                # Prepare context note data
                tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
                
                note_data = {
                    "title": title,
                    "content": content,
                    "category": category,
                    "priority": priority,
                    "tags": tags,
                    "is_active": is_active
                }
                
                # Create context note
                api_client.create_context_note(note_data)
                
                st.success(f"✅ Context note '{title}' created successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error creating context note: {str(e)}")

def show_edit_context_note_form(note: Dict[str, Any], api_client):
    """Display inline edit form for context note"""
    
    st.markdown("### ✏️ Edit Context Note")
    
    with st.form(f"edit_note_{note.get('id')}"):
        # Pre-populate with existing values
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Note Title", value=note.get('title', ''))
            category = st.selectbox(
                "Category",
                options=get_context_categories(),
                index=0 if not note.get('category') else (
                    get_context_categories().index(note.get('category')) 
                    if note.get('category') in get_context_categories() 
                    else get_context_categories().index('Other')
                )
            )
        
        with col2:
            priority = st.slider("Priority Level", 1, 10, note.get('priority', 5))
            is_active = st.checkbox("Active", value=note.get('is_active', True))
        
        content = st.text_area("Context Content", value=note.get('content', ''), height=150)
        
        existing_tags = ', '.join(note.get('tags', []))
        tags_input = st.text_input("Tags (comma-separated)", value=existing_tags)
        
        # Submit buttons
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            save_submitted = st.form_submit_button("💾 Save Changes", type="primary")
        
        with col_cancel:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.pop(f"editing_note_{note.get('id')}", None)
                st.rerun()
        
        if save_submitted:
            try:
                # Prepare update data
                tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
                
                update_data = {
                    "title": title,
                    "content": content,
                    "category": category,
                    "priority": priority,
                    "tags": tags,
                    "is_active": is_active
                }
                
                # Update context note
                api_client.update_context_note(note.get('id'), update_data)
                
                st.success(f"✅ Context note '{title}' updated successfully!")
                st.session_state.pop(f"editing_note_{note.get('id')}", None)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error updating context note: {str(e)}")

def show_context_analytics(api_client):
    """Display context notes analytics and usage statistics"""
    
    st.subheader("📊 Context Analytics")
    
    try:
        # Get context notes for analytics
        context_notes = api_client.get_context_notes()
        
        if not context_notes:
            st.info("📝 No context notes available for analytics")
            return
        
        # Category distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Notes by Category")
            category_counts = {}
            for note in context_notes:
                cat = note.get('category', 'Uncategorized')
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            df_categories = pd.DataFrame(list(category_counts.items()), columns=['Category', 'Count'])
            st.bar_chart(df_categories.set_index('Category'))
        
        with col2:
            st.markdown("#### 🎯 Priority Distribution")
            priority_ranges = {'Low (1-3)': 0, 'Medium (4-6)': 0, 'High (7-10)': 0}
            for note in context_notes:
                priority = note.get('priority', 0)
                if priority <= 3:
                    priority_ranges['Low (1-3)'] += 1
                elif priority <= 6:
                    priority_ranges['Medium (4-6)'] += 1
                else:
                    priority_ranges['High (7-10)'] += 1
            
            df_priority = pd.DataFrame(list(priority_ranges.items()), columns=['Priority', 'Count'])
            st.bar_chart(df_priority.set_index('Priority'))
        
        # Recent activity
        st.markdown("#### 📅 Recent Context Notes")
        df_notes = pd.DataFrame(context_notes)
        if not df_notes.empty:
            # Show latest 5 notes
            recent_notes = df_notes.head(5)[['title', 'category', 'priority', 'is_active']]
            st.dataframe(recent_notes, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

def delete_context_note(note_id: int, api_client):
    """Delete a context note"""
    
    try:
        if api_client.delete_context_note(note_id):
            st.success("✅ Context note deleted successfully!")
            # Clear confirmation state
            if f"confirm_delete_note_{note_id}" in st.session_state:
                del st.session_state[f"confirm_delete_note_{note_id}"]
            st.rerun()
        else:
            st.error("❌ Failed to delete context note")
    except Exception as e:
        st.error(f"❌ Error deleting context note: {str(e)}")


def show_category_management(api_client):
    """Display category management interface with database backend"""
    
    st.subheader("⚙️ Category Management")
    st.markdown("Manage context categories with real-time database updates.")
    
    try:
        # Get categories from database
        with st.spinner("Loading categories..."):
            categories = api_client.get_context_categories(include_inactive=True)
        
        # Display current categories
        st.markdown("### 📋 Current Categories")
        
        if categories:
            # Create a nice display of categories
            for category in categories:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        status_icon = "🟢" if category.get('is_active') else "🔴"
                        system_badge = " 🔒" if category.get('is_system') else ""
                        color = category.get('color', '#607d8b')
                        
                        st.markdown(f"""
                        <div style="
                            background-color: {color}20; 
                            border-left: 4px solid {color}; 
                            padding: 12px; 
                            margin: 5px 0; 
                            border-radius: 8px;
                            display: flex;
                            align-items: center;
                        ">
                            <strong>{status_icon} {category['name']}{system_badge}</strong>
                            {f"<br><small style='opacity: 0.7;'>{category.get('description', '')}</small>" if category.get('description') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Color indicator
                        st.markdown(f"""
                        <div style="
                            width: 30px; 
                            height: 30px; 
                            background-color: {category.get('color', '#607d8b')}; 
                            border-radius: 50%; 
                            margin: 10px auto;
                        "></div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        # Edit button
                        if st.button("✏️", key=f"edit_cat_{category['id']}", help="Edit Category"):
                            st.session_state[f"editing_category_{category['id']}"] = True
                            st.rerun()
                    
                    with col4:
                        # Delete button (only for non-system categories)
                        if not category.get('is_system', False):
                            if st.button("🗑️", key=f"delete_cat_{category['id']}", help="Delete Category", type="secondary"):
                                if st.session_state.get(f"confirm_delete_cat_{category['id']}"):
                                    try:
                                        if api_client.delete_context_category(category['id']):
                                            st.success(f"✅ Category '{category['name']}' deleted!")
                                            st.rerun()
                                        else:
                                            st.error("❌ Failed to delete category")
                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")
                                else:
                                    st.session_state[f"confirm_delete_cat_{category['id']}"] = True
                                    st.rerun()
                        else:
                            st.markdown("🔒")
                    
                    # Show confirmation for delete
                    if st.session_state.get(f"confirm_delete_cat_{category['id']}"):
                        st.warning("⚠️ Click Delete again to confirm removal")
                    
                    # Show edit form if editing
                    if st.session_state.get(f"editing_category_{category['id']}"):
                        show_edit_category_form(category, api_client)
                    
                    st.markdown("---")
        else:
            st.info("No categories found. Create your first category below.")
        
        st.markdown("---")
        
        # Add new category form
        st.markdown("### ➕ Add New Category")
        
        with st.form("create_category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Category Name*", placeholder="e.g., Financial Aid")
                description = st.text_area("Description", placeholder="Brief description of this category...")
            
            with col2:
                color = st.color_picker("Category Color", value="#607d8b")
                sort_order = st.number_input("Sort Order", value=0, min_value=0, max_value=100)
            
            submitted = st.form_submit_button("➕ Create Category", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("❌ Category name is required")
                    return
                
                try:
                    category_data = {
                        "name": name,
                        "description": description,
                        "color": color,
                        "sort_order": sort_order
                    }
                    
                    api_client.create_context_category(category_data)
                    st.success(f"✅ Category '{name}' created successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating category: {str(e)}")
        
    except Exception as e:
        st.error(f"❌ Error loading categories: {str(e)}")

def show_edit_category_form(category, api_client):
    """Display inline edit form for category"""
    
    st.markdown("### ✏️ Edit Category")
    
    with st.form(f"edit_category_{category['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Category Name", value=category.get('name', ''))
            description = st.text_area("Description", value=category.get('description', ''))
        
        with col2:
            color = st.color_picker("Category Color", value=category.get('color', '#607d8b'))
            sort_order = st.number_input("Sort Order", value=category.get('sort_order', 0), min_value=0, max_value=100)
            is_active = st.checkbox("Active", value=category.get('is_active', True))
        
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
        
        with col_cancel:
            cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if save_clicked:
            if not name:
                st.error("❌ Category name is required")
                return
            
            try:
                update_data = {
                    "name": name,
                    "description": description,
                    "color": color,
                    "sort_order": sort_order,
                    "is_active": is_active
                }
                
                api_client.update_context_category(category['id'], update_data)
                st.success(f"✅ Category '{name}' updated successfully!")
                
                # Clear editing state
                if f"editing_category_{category['id']}" in st.session_state:
                    del st.session_state[f"editing_category_{category['id']}"]
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error updating category: {str(e)}")
        
        if cancel_clicked:
            # Clear editing state
            if f"editing_category_{category['id']}" in st.session_state:
                del st.session_state[f"editing_category_{category['id']}"]
            st.rerun()
