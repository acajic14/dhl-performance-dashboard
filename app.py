Absolutely! Here's the **complete updated script** with all the changes made:

```python
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import io
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import zipfile
import tempfile
import os

# DHL Brand Colors
DHL_YELLOW = "#FFCC00"
DHL_RED = "#D40511"

# Page configuration
st.set_page_config(
    page_title="DHL Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for styling
st.markdown(f"""

    .main-header {{
        background-color: {DHL_YELLOW};
        padding: 8px 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    }}
    .header-title {{
        color: {DHL_RED} !important;
        font-size: 32px;
        font-weight: bold;
        margin: 0;
        display: inline-block;
    }}
    .header-slogan {{
        color: {DHL_RED} !important;
        font-size: 14px;
        font-style: italic;
        margin: 0;
        display: inline-block;
        margin-left: 10px;
        margin-top: 8px;
    }}
    .header-date {{
        color: {DHL_RED} !important;
        font-size: 16px;
        font-weight: bold;
        float: right;
        margin-top: 8px;
    }}
    
    /* Navigation buttons */
    .nav-buttons {{
        text-align: center;
        margin: 20px 0;
        padding: 10px;
    }}
    
    /* Custom KPI styling */
    .custom-kpi {{
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        text-align: center;
        background-color: #f8f9fa;
        border-left: 4px solid {DHL_RED};
        min-height: 80px;
    }}
    
    /* Transparent/blurred empty slots */
    .empty-kpi-slot {{
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        text-align: center;
        background-color: transparent;
        border: 2px dashed #e0e0e0;
        min-height: 80px;
        opacity: 0.3;
        filter: blur(0.5px);
    }}
    
    /* Empty picture slots */
    .empty-picture-slot {{
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        background-color: transparent;
        border: 2px dashed #e0e0e0;
        min-height: 200px;
        opacity: 0.3;
        filter: blur(0.5px);
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    /* Picture info styling */
    .picture-info {{
        background-color: #e7f3ff;
        border-left: 4px solid {DHL_RED};
        padding: 10px;
        margin: 8px 0;
        border-radius: 5px;
    }}
    
    /* Excel table styling */
    .excel-container {{
        border: 2px solid {DHL_RED};
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        background-color: white;
    }}
    
    /* Hide sidebar during screenshot */
    .screenshot-mode .stSidebar {{
        display: none !important;
    }}
    
    /* Hide navigation buttons during screenshot */
    .screenshot-mode .nav-buttons {{
        display: none !important;
    }}

""", unsafe_allow_html=True)

# Initialize session state for data persistence
def init_session_state():
    if 'team_data' not in st.session_state:
        st.session_state.team_data = {
            'Team PUD': {
                'kpis': [], 
                'performance_image': None,
                'kpi_font_size': 24,
                'safety_news': [],
                'team_news': [],
                'ideas_actions': [],
                'additional_pages': {}
            },
            'Team WTH': {
                'kpis': [], 
                'performance_image': None,
                'kpi_font_size': 24,
                'safety_news': [],
                'team_news': [],
                'ideas_actions': [],
                'additional_pages': {}
            }
        }
    
    # Initialize page management
    if 'available_pages' not in st.session_state:
        st.session_state.available_pages = ["Dashboard", "Additional Content"]
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    if 'screenshot_mode' not in st.session_state:
        st.session_state.screenshot_mode = False

# Helper functions for page navigation
def get_next_page():
    current_idx = st.session_state.available_pages.index(st.session_state.current_page)
    if current_idx + 1 = 0:
        return st.session_state.available_pages[current_idx - 1]
    else:
        return st.session_state.available_pages[-1]

def add_new_page():
    count = 1
    new_page_name = f"Additional Page {count}"
    while new_page_name in st.session_state.available_pages:
        count += 1
        new_page_name = f"Additional Page {count}"
    
    st.session_state.available_pages.append(new_page_name)
    
    for team in st.session_state.team_data:
        st.session_state.team_data[team]['additional_pages'][new_page_name] = {
            'pictures': [],
            'picture_info': [],
            'excel_files': []  # New field for Excel files
        }
    
    return new_page_name

def remove_page(page_name):
    if page_name in st.session_state.available_pages and page_name not in ['Dashboard', 'Additional Content']:
        st.session_state.available_pages.remove(page_name)
        
        for team in st.session_state.team_data:
            if page_name in st.session_state.team_data[team]['additional_pages']:
                del st.session_state.team_data[team]['additional_pages'][page_name]
        
        if st.session_state.current_page == page_name:
            st.session_state.current_page = "Dashboard"
        
        return True
    return False

# Excel processing function
def process_excel_file(excel_file, max_rows=25):
    """Process Excel file and return first sheet with header and top rows"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, nrows=max_rows)
        
        # Get basic info
        file_info = {
            'filename': excel_file.name,
            'shape': df.shape,
            'columns': list(df.columns),
            'data': df
        }
        
        return file_info
    except Exception as e:
        st.error(f"Error processing Excel file: {str(e)}")
        return None

# Screenshot export function
def create_manual_screenshot_guide(team_name, available_pages):
    """Create a text guide for manual screenshots"""
    guide_content = f"""
# {team_name} Dashboard Screenshot Guide

## Instructions for Creating Dashboard Export:

### Method 1: Browser Screenshots
1. **Hide Sidebar**: Use the arrow (>) at the top-left to collapse the sidebar
2. **Full Screen**: Press F11 for full-screen mode (optional)
3. **Take Screenshots**: Use your browser's screenshot tool or:
   - **Chrome**: Ctrl+Shift+I → Ctrl+Shift+P → type "screenshot" → "Capture full size screenshot"
   - **Firefox**: Right-click → "Take Screenshot" → "Save full page"
   - **Windows**: Windows+Shift+S for snipping tool
   - **Mac**: Cmd+Shift+4 for area selection

### Pages to Capture:
"""
    
    for i, page in enumerate(available_pages, 1):
        guide_content += f"{i}. **{page}**\n"
    
    guide_content += f"""

### File Naming Suggestion:
- {team_name}_Dashboard_Page1.png
- {team_name}_Additional_Content_Page2.png
- etc.

### Tips:
- Ensure full page is visible before screenshot
- Use landscape orientation for best results
- Hide browser bookmarks bar for cleaner look
- Take screenshots at consistent zoom level (100%)

Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}
"""
    
    return guide_content

# Function to determine KPI performance and format value
def get_kpi_performance(value, target, higher_is_better=True, is_percentage=False):
    if target == 0:
        return "N/A", "", False, "black"
    
    if higher_is_better:
        achieved = value >= target
        percentage = ((value - target) / target) * 100
    else:
        achieved = value {sign}{abs(percentage):.1f}%'
    
    if is_percentage:
        formatted_value = f"{value:.1f}%"
        formatted_target = f"{target:.1f}%"
    else:
        formatted_value = f"{value:.1f}"
        formatted_target = f"{target:.1f}"
    
    return performance_text, achieved, formatted_value, formatted_target, result_color

init_session_state()

# Sidebar with TEAM SELECTION AT TOP
with st.sidebar:
    # TEAM SELECTION FIRST (moved to top as requested)
    st.markdown("### 👥 Team Selection")
    team_options = ["Team PUD", "Team WTH"]
    selected_team = st.selectbox("Select Team:", team_options)
    
    # Convert back to full names for header display
    if selected_team == "Team PUD":
        header_title = "PUD Performance Dialogue"
    else:
        header_title = "WTH Performance Dialogue"
    
    # Get current team data
    current_team_data = st.session_state.team_data[selected_team]
    
    # Add additional_pages field if it doesn't exist (backward compatibility)
    if 'additional_pages' not in current_team_data:
        current_team_data['additional_pages'] = {}
    
    st.markdown("---")
    
    # EXPORT FUNCTIONALITY - SCREENSHOT BASED
    st.markdown("### 📸 Export Dashboard")
    
    st.info("💡 **Tip**: For best results, collapse this sidebar using the arrow (>) before taking screenshots!")
    
    # Manual screenshot guide
    if st.button("📋 Download Screenshot Guide", use_container_width=True):
        guide_content = create_manual_screenshot_guide(header_title, st.session_state.available_pages)
        st.download_button(
            label="⬇️ Download Guide (TXT)",
            data=guide_content,
            file_name=f"{selected_team}_Screenshot_Guide_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.success("Screenshot guide generated!")
    
    # Browser screenshot instructions
    with st.expander("🖥️ Browser Screenshot Instructions", expanded=False):
        st.markdown("""
        **Chrome/Edge:**
        1. Press `Ctrl+Shift+I` (F12)
        2. Press `Ctrl+Shift+P`
        3. Type "screenshot"
        4. Select "Capture full size screenshot"
        
        **Firefox:**
        1. Right-click on page
        2. Select "Take Screenshot"
        3. Choose "Save full page"
        
        **Any Browser:**
        - Use `Windows+Shift+S` (Windows)
        - Use `Cmd+Shift+4` (Mac)
        """)
    
    # Hide sidebar toggle
    if st.button("👁️ Toggle Sidebar for Screenshots", use_container_width=True):
        st.session_state.screenshot_mode = not st.session_state.screenshot_mode
        if st.session_state.screenshot_mode:
            st.success("Sidebar hidden! Take your screenshots now.")
        else:
            st.info("Sidebar restored!")
        st.rerun()
    
    st.markdown("---")
    
    # PAGE NAVIGATION
    st.markdown("### 📋 Navigation")
    st.session_state.current_page = st.selectbox("Select Page:", st.session_state.available_pages, 
                                                 index=st.session_state.available_pages.index(st.session_state.current_page))
    
    # Page Management
    st.markdown("---")
    st.markdown("### 📄 Page Management")
    
    if st.button("➕ Add New Page"):
        new_page = add_new_page()
        st.success(f"Added {new_page}")
        st.rerun()
    
    # Show delete buttons for additional pages
    additional_pages = [p for p in st.session_state.available_pages if p not in ['Dashboard', 'Additional Content']]
    if additional_pages:
        st.markdown("**Delete Pages:**")
        for page in additional_pages:
            if st.button(f"🗑️ Delete {page}", key=f"delete_{page}"):
                remove_page(page)
                st.success(f"Deleted {page}")
                st.rerun()
    
    st.markdown("---")

    # REST OF SIDEBAR CONTENT (your existing management sections)
    # Show different sidebar content based on current page
    if st.session_state.current_page == "Dashboard":
        # Dashboard management (your existing code)
        st.markdown("### 📈 Performance Management")
        
        # KPI Font Size Control
        current_team_data['kpi_font_size'] = st.slider("KPI Font Size", 16, 40, current_team_data['kpi_font_size'])
        
        if st.button("➕ Add New KPI"):
            if len(current_team_data['kpis']) .stSidebar { display: none !important; }', unsafe_allow_html=True)

# Header with DHL brand text and page number
current_date = datetime.now().strftime("%B %d, %Y")
if st.session_state.current_page == "Dashboard":
    header_right = current_date
else:
    page_number = st.session_state.available_pages.index(st.session_state.current_page)
    header_right = f"Page {page_number}"

st.markdown(f"""

    
        {header_title}
        Excellence. Simply delivered.
    
    {header_right}
    

""", unsafe_allow_html=True)

# Display content based on current page
if st.session_state.current_page == "Dashboard":
    # DASHBOARD PAGE CONTENT (your existing dashboard code)
    
    # Top row using pure Streamlit containers
    col1, col2 = st.columns([1, 1])

    with col1:
        # Upper Left: Performance using Streamlit container
        with st.container(border=True):
            st.markdown("### 📈 Performance")
            
            # Display performance image if exists
            if current_team_data['performance_image'] is not None:
                st.image(current_team_data['performance_image'], width=460)
            
            # Display KPIs with color coding and dynamic font size
            if current_team_data['performance_image'] is not None:
                # If image exists, show only 1 row (2 KPIs)
                kpi_cols = st.columns(2)
                
                # First KPI
                with kpi_cols[0]:
                    if len(current_team_data['kpis']) > 0:
                        kpi = current_team_data['kpis'][0]
                        performance_text, achieved, formatted_value, formatted_target, result_color = get_kpi_performance(
                            kpi['value'], kpi['target'], 
                            kpi.get('higher_is_better', True),
                            kpi.get('is_percentage', False)
                        )
                        
                        kpi_html = f"""
                        
                            {kpi['name']}
                            {formatted_value}
                            Target: {formatted_target}
                            {performance_text}
                        
                        """
                        st.markdown(kpi_html, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        
                            Empty Slot
                        
                        """, unsafe_allow_html=True)
                
                # Second KPI
                with kpi_cols[1]:
                    if len(current_team_data['kpis']) > 1:
                        kpi = current_team_data['kpis'][1]
                        performance_text, achieved, formatted_value, formatted_target, result_color = get_kpi_performance(
                            kpi['value'], kpi['target'], 
                            kpi.get('higher_is_better', True),
                            kpi.get('is_percentage', False)
                        )
                        
                        kpi_html = f"""
                        
                            {kpi['name']}
                            {formatted_value}
                            Target: {formatted_target}
                            {performance_text}
                        
                        """
                        st.markdown(kpi_html, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        
                            Empty Slot
                        
                        """, unsafe_allow_html=True)
            else:
                # No image - show all 6 KPI slots (3 rows)
                for i in range(0, 6, 2):
                    kpi_cols = st.columns(2)
                    
                    # First KPI
                    with kpi_cols[0]:
                        if i 
                                {kpi['name']}
                                {formatted_value}
                                Target: {formatted_target}
                                {performance_text}
                            
                            """
                            st.markdown(kpi_html, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            
                                Empty Slot
                            
                            """, unsafe_allow_html=True)
                    
                    # Second KPI
                    with kpi_cols[1]:
                        if i + 1 
                                {kpi['name']}
                                {formatted_value}
                                Target: {formatted_target}
                                {performance_text}
                            
                            """
                            st.markdown(kpi_html, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            
                                Empty Slot
                            
                            """, unsafe_allow_html=True)

    with col2:
        # Upper Right: Safety & News using Streamlit container
        with st.container(border=True):
            st.markdown("### 🛡️ Safety & News")
            
            if current_team_data['safety_news']:
                for item in current_team_data['safety_news']:
                    if item['type'] == 'Safety':
                        st.warning(f"**Safety:** {item['content']}")
                    else:
                        st.info(f"**News:** {item['content']}")
            else:
                st.info("No safety or news items added yet.")

    # Bottom row using pure Streamlit containers
    col3, col4 = st.columns([1, 1])

    with col3:
        # Bottom Left: Ideas & Actions using Streamlit container
        with st.container(border=True):
            st.markdown("### 💡 Ideas & Actions")
            
            if current_team_data['ideas_actions']:
                # Create a DataFrame for table display
                df_data = []
                for action in current_team_data['ideas_actions']:
                    status_display = action['status']
                    if action['status'] == 'Completed':
                        status_display = f"✅ {action['status']}"
                    elif action['status'] == 'In Progress':
                        status_display = f"🟡 {action['status']}"
                    
                    df_data.append({
                        'Idea': action['idea'],
                        'To Do': action['todo'],
                        'Who': action['who'],
                        'Till When': action['when'],
                        'Status': status_display
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No ideas or actions added yet.")

    with col4:
        # Bottom Right: Team News using Streamlit container
        with st.container(border=True):
            st.markdown("### 👥 Team News")
            
            if current_team_data['team_news']:
                for news in current_team_data['team_news']:
                    st.markdown(f"📢 {news['content']}")
            else:
                st.info("No team news added yet.")

else:
    # ADDITIONAL CONTENT PAGE OR ADDITIONAL PAGES
    
    # Get page data
    if st.session_state.current_page == "Additional Content":
        if 'pictures' not in current_team_data:
            current_team_data['pictures'] = []
        if 'picture_info' not in current_team_data:
            current_team_data['picture_info'] = []
        if 'excel_files' not in current_team_data:
            current_team_data['excel_files'] = []
        page_data = {
            'pictures': current_team_data['pictures'],
            'picture_info': current_team_data['picture_info'],
            'excel_files': current_team_data['excel_files']
        }
    else:
        if st.session_state.current_page not in current_team_data['additional_pages']:
            current_team_data['additional_pages'][st.session_state.current_page] = {
                'pictures': [],
                'picture_info': [],
                'excel_files': []
            }
        page_data = current_team_data['additional_pages'][st.session_state.current_page]
        
        # Add excel_files field if it doesn't exist (backward compatibility)
        if 'excel_files' not in page_data:
            page_data['excel_files'] = []
    
    # Count actual pictures and excel files
    actual_pictures = [p for p in page_data['pictures'] if p is not None]
    actual_excel_files = [e for e in page_data['excel_files'] if e is not None]
    num_pictures = len(actual_pictures)
    num_excel_files = len(actual_excel_files)
    
    # Create layout: Pictures/Excel on left, Info on right
    col_content, col_info = st.columns([2, 1])
    
    with col_content:
        # Display Pictures
        if num_pictures == 1 and num_excel_files == 0:
            # Single picture - stretch to full width
            st.image(actual_pictures[0], width=600, caption="Picture 1")
        elif num_pictures > 1 or num_excel_files > 0:
            # Multiple items - arrange in grid
            
            # Display pictures first
            if num_pictures > 0:
                if num_pictures == 1:
                    st.image(actual_pictures[0], width=600, caption="Picture 1")
                else:
                    # Multiple pictures in 2x2 grid
                    pic_cols_top = st.columns(2)
                    with pic_cols_top[0]:
                        if num_pictures >= 1:
                            st.image(actual_pictures[0], width=300, caption="Picture 1")
                    
                    with pic_cols_top[1]:
                        if num_pictures >= 2:
                            st.image(actual_pictures[1], width=300, caption="Picture 2")
                    
                    if num_pictures > 2:
                        pic_cols_bottom = st.columns(2)
                        with pic_cols_bottom[0]:
                            if num_pictures >= 3:
                                st.image(actual_pictures[2], width=300, caption="Picture 3")
                        
                        with pic_cols_bottom[1]:
                            if num_pictures >= 4:
                                st.image(actual_pictures[3], width=300, caption="Picture 4")
            
            # Display Excel files
            if num_excel_files > 0:
                st.markdown("---")
                for i, excel_info in enumerate(actual_excel_files):
                    st.markdown(f"""
                    
                        📊 {excel_info['filename']}
                        Rows: {excel_info['shape'][0]} | Columns: {excel_info['shape'][1]}
                    
                    """, unsafe_allow_html=True)
                    
                    # Display the Excel data (first 25 rows)
                    st.dataframe(excel_info['data'], use_container_width=True, height=400)
        else:
            # No content - show empty grid
            st.info("No pictures or Excel files uploaded yet. Use the sidebar to add content.")
            
            # Show empty grid structure
            pic_cols_top = st.columns(2)
            with pic_cols_top[0]:
                st.markdown('Empty Content Slot', unsafe_allow_html=True)
            with pic_cols_top[1]:
                st.markdown('Empty Content Slot', unsafe_allow_html=True)
    
    with col_info:
        # Picture Information quadrant
        with st.container(border=True):
            st.markdown("### 📝 Content Information")
            
            if page_data['picture_info']:
                for info in page_data['picture_info']:
                    st.markdown(f"""
                    
                        {info['content']}
                    
                    """, unsafe_allow_html=True)
            else:
                st.info("No content information added yet.")

# Navigation buttons at the bottom (hidden in screenshot mode)
if not st.session_state.screenshot_mode:
    st.markdown("---")
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if st.button("⬅️ Previous Page", use_container_width=True):
            st.session_state.current_page = get_prev_page()
            st.rerun()

    with nav_col2:
        st.markdown(f"Current: {st.session_state.current_page}", 
                    unsafe_allow_html=True)

    with nav_col3:
        if st.button("Next Page ➡️", use_container_width=True):
            st.session_state.current_page = get_next_page()
            st.rerun()
```

## Changes Made:

✅ **"Pictures" renamed to "Additional Content"** throughout the entire script  
✅ **Excel functionality added** to the "Additional Content" page  
✅ **Consistent behavior** - now all non-Dashboard pages support Excel files  
✅ **Updated page protection** - only Dashboard and Additional Content are protected from deletion  

**Simply copy this entire script, paste it into your GitHub `app.py` file, commit the changes, and it will automatically deploy with the new name and Excel functionality!**[1][2]

[1] tools.streamlit
[2] preferences.ai_interaction
