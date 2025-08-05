import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import math

# Page config
st.set_page_config(page_title="Sales Engagement Dashboard", layout="wide")

# API configuration
API_URL = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/SLoS_Prod/Echo_Sales_Coach/Echo_Sales_Coach/engagement_api"
API_HEADERS = {
    "Authorization": "Bearer 12345",
    "Content-Type": "application/json"
}

# Custom CSS for better styling
st.markdown("""
<style>
.engagement-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: all 0.3s ease;
}
.engagement-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    border-color: #4285f4;
    transform: translateY(-2px);
}
.engagement-card.selected {
    border-color: #4285f4;
    border-width: 2px;
    background: #f8f9ff;
}
.platform-badge {
    background: #e3f2fd;
    color: #1976d2;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 8px;
}
.meeting-type-badge {
    background: #f3e5f5;
    color: #7b1fa2;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}
.pagination-info {
    text-align: center;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 4px;
    margin: 10px 0;
}
.stButton > button {
    width: 100%;
}
.debug-box {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    padding: 10px;
    margin: 10px 0;
}
.error-box {
    background: #f8d7da;
    border: 1px solid #dc3545;
    border-radius: 4px;
    padding: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# Debug function
def debug_api_response():
    """Comprehensive debug function to identify truncation point"""
    st.markdown("### 🔍 API Response Debug Analysis")
    
    try:
        # Method 1: Basic request
        st.write("**Method 1: Basic requests.get()**")
        response1 = requests.get(API_URL, headers=API_HEADERS, timeout=120)
        st.success(f"✓ Status: {response1.status_code}, Content Length: {len(response1.content):,} bytes")
        
        # Method 2: Session with no compression
        st.write("\n**Method 2: Session with no compression**")
        session = requests.Session()
        session.headers.update({
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
        })
        response2 = session.get(API_URL, headers=API_HEADERS, timeout=120)
        st.success(f"✓ Content Length: {len(response2.content):,} bytes")
        
        # Method 3: Streaming
        st.write("\n**Method 3: Streaming response**")
        response3 = requests.get(API_URL, headers=API_HEADERS, timeout=120, stream=True)
        chunks = []
        for chunk in response3.iter_content(chunk_size=8192):
            chunks.append(chunk)
        
        content3 = b''.join(chunks)
        st.success(f"✓ Content Length: {len(content3):,} bytes in {len(chunks)} chunks")
        
        # Compare methods
        st.write("\n**📊 Comparison:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Method 1", f"{len(response1.content):,} bytes")
        with col2:
            st.metric("Method 2", f"{len(response2.content):,} bytes")
        with col3:
            st.metric("Method 3", f"{len(content3):,} bytes")
        
        # Use the response with most data
        if len(content3) >= len(response1.content) and len(content3) >= len(response2.content):
            best_content = content3
        elif len(response2.content) >= len(response1.content):
            best_content = response2.content
        else:
            best_content = response1.content
        
        # Decode and analyze
        content_str = best_content.decode('utf-8', errors='ignore')
        
        # Check if JSON is complete
        st.write("\n**📋 JSON Structure Analysis:**")
        
        # Count brackets
        open_braces = content_str.count('{')
        close_braces = content_str.count('}')
        open_brackets = content_str.count('[')
        close_brackets = content_str.count(']')
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Opening braces `{{`: {open_braces}")
            st.write(f"Closing braces `}}`: {close_braces}")
            if open_braces != close_braces:
                st.error(f"⚠️ Mismatch: {open_braces - close_braces} unclosed braces")
        
        with col2:
            st.write(f"Opening brackets `[`: {open_brackets}")
            st.write(f"Closing brackets `]`: {close_brackets}")
            if open_brackets != close_brackets:
                st.error(f"⚠️ Mismatch: {open_brackets - close_brackets} unclosed brackets")
        
        # Check ending
        last_chars = content_str.strip()[-100:]
        st.write("\n**Last 100 characters:**")
        st.code(last_chars)
        
        if content_str.strip().endswith('}') or content_str.strip().endswith(']'):
            st.success("✅ JSON appears to end correctly")
        else:
            st.error("❌ JSON does NOT end with } or ]")
        
        # Try to parse
        st.write("\n**🔧 Parsing Attempt:**")
        try:
            data = json.loads(content_str)
            st.success(f"✅ Successfully parsed JSON!")
            
            # Analyze the data
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame([data])
            
            # Check qualification_data specifically
            if 'qualification_data' in df.columns:
                st.write("\n**📊 Qualification Data Analysis:**")
                for idx, row in df.iterrows():
                    qual_data = row['qualification_data']
                    if qual_data:
                        qual_len = len(str(qual_data))
                        st.write(f"Row {idx} ({row.get('external_company', 'Unknown')}): {qual_len:,} chars")
                        
                        # Check if it's truncated
                        if isinstance(qual_data, str):
                            if not qual_data.strip().endswith('}'):
                                st.error(f"  ⚠️ TRUNCATED! Ends with: ...{qual_data[-50:]}")
                            
                            # Check for specific truncation points
                            if qual_len == 8043:
                                st.error(f"  🚨 EXACTLY 8043 chars - likely a field limit!")
            
            return df
            
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON Parse Error at position {e.pos}")
            return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Debug failed: {str(e)}")
        return pd.DataFrame()

# Enhanced data fetching
@st.cache_data(ttl=300)
def get_data():
    try:
        session = requests.Session()
        session.headers.update({
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
        })
        
        response = session.get(
            API_URL,
            headers=API_HEADERS,
            timeout=120,
            stream=False
        )
        
        response.raise_for_status()
        
        raw_content = response.content
        
        try:
            content_str = raw_content.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            content_str = raw_content.decode('latin-1', errors='ignore')
        
        try:
            data = json.loads(content_str)
        except json.JSONDecodeError:
            response = session.get(API_URL, headers=API_HEADERS, timeout=120)
            data = response.json()
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            df = pd.DataFrame([data])
        
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        
        return df
        
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return pd.DataFrame()

# Helper functions
def safe_json_loads(json_str):
    """Parse JSON string with comprehensive error handling for nested JSON"""
    try:
        if pd.isna(json_str) or json_str is None or json_str == '':
            return None
        
        if isinstance(json_str, dict):
            return json_str
        
        if isinstance(json_str, str):
            if json_str.strip() == '':
                return None
            
            # Clean up the string if it contains markdown code blocks
            cleaned_str = json_str.strip()
            
            # Remove ```json and ``` markers if present
            if cleaned_str.startswith('```json'):
                cleaned_str = cleaned_str[7:]  # Remove ```json
            elif cleaned_str.startswith('```'):
                cleaned_str = cleaned_str[3:]  # Remove ```
            
            if cleaned_str.endswith('```'):
                cleaned_str = cleaned_str[:-3]  # Remove ending ```
            
            # Remove any leading/trailing whitespace again
            cleaned_str = cleaned_str.strip()
            
            # Try to parse the cleaned JSON
            try:
                parsed = json.loads(cleaned_str)
                
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
                elif isinstance(parsed, dict) and len(parsed) == 0:
                    return None
                else:
                    return parsed
            except json.JSONDecodeError as e:
                # If it still fails, check if the string itself IS valid JSON but truncated
                # Try to find where the JSON actually starts (might have other text before it)
                json_start = cleaned_str.find('{')
                if json_start > 0:
                    cleaned_str = cleaned_str[json_start:]
                    try:
                        parsed = json.loads(cleaned_str)
                        return parsed if isinstance(parsed, dict) and len(parsed) > 0 else None
                    except:
                        pass
                
                # Last resort - try to extract JSON from a potentially truncated string
                # Check if it's actually truncated or just malformed
                if len(json_str) == 8043:
                    # It IS truncated at the database limit
                    return extract_partial_json(cleaned_str)
                
                return None
                
        return None
    except Exception:
        return None

def extract_partial_json(json_str):
    """Extract as much valid JSON as possible from a truncated string"""
    result = {}
    
    # Try to extract complete top-level keys
    try:
        # Common keys we expect
        known_fields = ['call_analysis', 'current_state_analysis', 'business_drivers', 
                       'compelling_event', 'economic_buyer', 'stakeholder_mapping',
                       'justification', 'deal_risks', 'differentiation', 'use_cases']
        
        for field in known_fields:
            # Try to find and extract each field
            field_pattern = f'"{field}":'
            start_idx = json_str.find(field_pattern)
            
            if start_idx != -1:
                # Find the start of the value (after the colon)
                value_start = json_str.find('{', start_idx)
                if value_start != -1:
                    # Try to find the matching closing brace
                    brace_count = 1
                    idx = value_start + 1
                    in_string = False
                    escape_next = False
                    
                    while idx < len(json_str) and brace_count > 0:
                        char = json_str[idx]
                        
                        if escape_next:
                            escape_next = False
                        elif char == '\\':
                            escape_next = True
                        elif char == '"' and not escape_next:
                            in_string = not in_string
                        elif not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                        
                        idx += 1
                    
                    if brace_count == 0:
                        # We found a complete object
                        value_str = json_str[value_start:idx]
                        try:
                            result[field] = json.loads(value_str)
                        except:
                            pass
        
        return result if result else None
        
    except:
        return None

def safe_list_parse(data):
    """Parse list data with comprehensive error handling"""
    try:
        if pd.isna(data) or data is None or data == '':
            return []
        
        if isinstance(data, list):
            return data
        
        if isinstance(data, str):
            if data.strip() == '':
                return []
            
            parsed = json.loads(data)
            
            if isinstance(parsed, list):
                return parsed
            else:
                return []
        
        return []
    except json.JSONDecodeError:
        return []
    except Exception:
        return []

def get_platform_label(engagement_type):
    return "Outreach" if engagement_type == "dialer" else "Chorus"

def extract_all_snaplogic_participants(df):
    """Extract all unique SnapLogic participants from the dataframe"""
    snaplogic_participants = {}
    
    for idx, row in df.iterrows():
        try:
            participants = safe_list_parse(row['participants'])
            
            if isinstance(participants, list):
                for p in participants:
                    if isinstance(p, dict):
                        company = p.get('company_name', '')
                        name = p.get('name', '')
                        email = p.get('email', '')
                        
                        is_snaplogic = any([
                            'SnapLogic' in str(company),
                            'snaplogic' in str(company).lower(),
                            'snaplogic.com' in str(email).lower() if email else False
                        ])
                        
                        if is_snaplogic and name:
                            if name not in snaplogic_participants:
                                snaplogic_participants[name] = {
                                    'email': email,
                                    'company': company,
                                    'count': 1
                                }
                            else:
                                snaplogic_participants[name]['count'] += 1
        except Exception:
            continue
    
    return snaplogic_participants

# Load data
with st.spinner("Loading engagement data..."):
    df = get_data()

if df.empty:
    st.error("No data available. Please check the API connection.")
    st.stop()

# Parse JSON fields
df['participants_parsed'] = df['participants'].apply(safe_list_parse)
df['qualification_parsed'] = df['qualification_data'].apply(safe_json_loads)

# Get filter options
snaplogic_participants_dict = extract_all_snaplogic_participants(df)
snaplogic_participants = sorted(list(snaplogic_participants_dict.keys()))
opportunities = df[df['opp_name'].notna()]['opp_name'].unique()

# Header
st.title("📊 Sales Engagement Dashboard")
st.markdown("*Track and analyze sales conversations with AI-powered insights*")
st.divider()

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filters")
    
    # Debug mode
    debug_mode = st.checkbox("🔧 Debug Mode", value=False)
    
    if debug_mode:
        with st.expander("🔍 Debug Tools", expanded=True):
            if st.button("🔍 Run Full API Debug Analysis", type="primary"):
                with st.spinner("Running comprehensive debug..."):
                    debug_df = debug_api_response()
                    if not debug_df.empty:
                        st.success(f"Debug complete - {len(debug_df)} records analyzed")
            
            if st.button("📥 Download Raw Response"):
                response = requests.get(API_URL, headers=API_HEADERS, timeout=120)
                st.download_button(
                    label="Download raw_response.txt",
                    data=response.content,
                    file_name=f"raw_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            st.write("**Current Data Stats:**")
            st.write(f"• Records loaded: {len(df)}")
            
            if 'qualification_data' in df.columns:
                truncated_count = 0
                exact_8043 = 0
                
                for idx, row in df.iterrows():
                    qual_data = row['qualification_data']
                    if isinstance(qual_data, str):
                        length = len(qual_data)
                        if length == 8043:
                            exact_8043 += 1
                        if not qual_data.strip().endswith('}'):
                            truncated_count += 1
                
                if exact_8043 > 0:
                    st.info(f"📊 {exact_8043} records have exactly 8043 chars")
                
                if truncated_count > 0:
                    st.info(f"📊 {truncated_count} records may have truncated data")
    
    platform_filter = st.selectbox(
        "Platform", 
        ["All Platforms", "Outreach", "Chorus"]
    )
    
    participant_options = ["All SnapLogic Participants"] + snaplogic_participants
    participant_filter = st.selectbox(
        f"SnapLogic Participant ({len(snaplogic_participants)} found)",
        participant_options
    )
    
    opportunity_options = ["All Opportunities", "Has Opportunity", "No Opportunity"] + sorted(opportunities.tolist())
    opportunity_filter = st.selectbox(
        "Opportunity",
        opportunity_options
    )
    
    search_term = st.text_input("🔍 Search by company or owner")
    
    st.divider()
    
    st.header("📄 Pagination")
    items_per_page = st.selectbox(
        "Items per page",
        options=[5, 10, 15, 20, 25, 50],
        index=2
    )
    
    st.divider()
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        if 'current_page' in st.session_state:
            st.session_state.current_page = 1
        st.rerun()
    
    with st.expander("API Status"):
        st.write(f"**Records loaded:** {len(df)}")
        st.write(f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")

# Apply filters
filtered_df = df.copy()

if platform_filter == "Outreach":
    filtered_df = filtered_df[filtered_df['engagement_type'] == 'dialer']
elif platform_filter == "Chorus":
    filtered_df = filtered_df[filtered_df['engagement_type'] == 'meeting']

if participant_filter != "All SnapLogic Participants":
    def check_participant(participants_list, target_name):
        if not isinstance(participants_list, list):
            return False
        
        for p in participants_list:
            if isinstance(p, dict):
                name = p.get('name', '')
                company = p.get('company_name', '')
                email = p.get('email', '')
                
                if name == target_name:
                    is_snaplogic = any([
                        'SnapLogic' in str(company),
                        'snaplogic' in str(company).lower(),
                        'snaplogic.com' in str(email).lower() if email else False
                    ])
                    if is_snaplogic:
                        return True
        return False
    
    mask = filtered_df['participants_parsed'].apply(
        lambda x: check_participant(x, participant_filter)
    )
    filtered_df = filtered_df[mask]

if opportunity_filter == "Has Opportunity":
    filtered_df = filtered_df[filtered_df['opp_name'].notna()]
elif opportunity_filter == "No Opportunity":
    filtered_df = filtered_df[filtered_df['opp_name'].isna()]
elif opportunity_filter not in ["All Opportunities"]:
    filtered_df = filtered_df[filtered_df['opp_name'] == opportunity_filter]

if search_term:
    mask = (
        filtered_df['external_company'].str.contains(search_term, case=False, na=False) |
        filtered_df['call_owner'].str.contains(search_term, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

# Sort by created_at descending
filtered_df = filtered_df.sort_values('created_at', ascending=False)

# Initialize session state
if 'selected_engagement_id' not in st.session_state:
    st.session_state.selected_engagement_id = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# Calculate pagination
total_records = len(filtered_df)
total_pages = math.ceil(total_records / items_per_page) if total_records > 0 else 1

if st.session_state.current_page > total_pages:
    st.session_state.current_page = 1

start_idx = (st.session_state.current_page - 1) * items_per_page
end_idx = min(start_idx + items_per_page, total_records)

current_page_df = filtered_df.iloc[start_idx:end_idx]

# Main layout
col1, col2 = st.columns([1.5, 1])

with col1:
    col_header, col_pagination = st.columns([2, 1])
    
    with col_header:
        st.subheader(f"📞 Recent Engagements")
        if total_records > 0:
            st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_records} engagements")
        else:
            st.caption("No engagements found")
    
    with col_pagination:
        if total_pages > 1:
            st.markdown(f"**Page {st.session_state.current_page} of {total_pages}**")
    
    if filtered_df.empty:
        st.info("No engagements match your current filters.")
    else:
        for idx, row in current_page_df.iterrows():
            qual_data = safe_json_loads(row['qualification_data'])
            call_type = qual_data.get('call_analysis', {}).get('call_type', '') if qual_data else ''
            
            is_selected = st.session_state.selected_engagement_id == row['engagement_id']
            
            button_label = f"{row['external_company']} - {get_platform_label(row['engagement_type'])}"
            if call_type:
                button_label += f" - {call_type}"
            
            if st.button(
                button_label,
                key=f"eng_{row['engagement_id']}",
                type="primary" if is_selected else "secondary",
                use_container_width=True
            ):
                st.session_state.selected_engagement_id = row['engagement_id']
                st.rerun()
            
            with st.container():
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.caption(f"📧 {row['call_owner'].split('@')[0]}")
                with col_info2:
                    st.caption(f"📅 {pd.to_datetime(row['created_at']).strftime('%m/%d/%Y')}")
                
                if pd.notna(row['opp_name']):
                    st.caption(f"💼 {row['opp_name']}")
                
                st.caption(f"📝 {row['subject']}")
                
                action_links = []
                if pd.notna(row['pdf_tool_analysis_url']):
                    action_links.append(f'<a href="{row["pdf_tool_analysis_url"]}" target="_blank">📄 Analysis</a>')
                if pd.notna(row['chorus_link']):
                    action_links.append(f'<a href="{row["chorus_link"]}" target="_blank">🎥 Recording</a>')
                
                if action_links:
                    st.markdown(" | ".join(action_links), unsafe_allow_html=True)
                
                st.divider()
        
        if total_pages > 1:
            st.markdown("---")
            
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            
            with col_prev:
                if st.button("⬅️ Previous", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with col_info:
                page_options = list(range(1, total_pages + 1))
                selected_page = st.selectbox(
                    "Go to page:",
                    options=page_options,
                    index=st.session_state.current_page - 1,
                    key="page_selector"
                )
                
                if selected_page != st.session_state.current_page:
                    st.session_state.current_page = selected_page
                    st.rerun()
            
            with col_next:
                if st.button("Next ➡️", disabled=(st.session_state.current_page == total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()
            
            st.markdown(
                f'<div class="pagination-info">Page {st.session_state.current_page} of {total_pages} '
                f'({total_records} total records, showing {items_per_page} per page)</div>',
                unsafe_allow_html=True
            )

with col2:
    st.subheader("📋 Engagement Details")
    
    if st.session_state.selected_engagement_id:
        selected_eng_data = df[df['engagement_id'] == st.session_state.selected_engagement_id]
        
        if selected_eng_data.empty:
            st.warning("Selected engagement not found.")
            st.session_state.selected_engagement_id = None
        else:
            selected_eng = selected_eng_data.iloc[0]
            
            if debug_mode:
                with st.expander("🔧 Debug Information", expanded=False):
                    st.write("**Engagement ID:**", selected_eng['engagement_id'])
                    raw_qual = selected_eng['qualification_data']
                    if raw_qual:
                        st.write(f"**Qualification data length:** {len(str(raw_qual))} chars")
                        if isinstance(raw_qual, str):
                            # Check for markdown code block markers
                            if '```json' in raw_qual or '```' in raw_qual:
                                st.info("📝 Data contains markdown code block markers (```json)")
                            
                            if len(raw_qual) == 8043:
                                st.error("🚨 Data truncated at EXACTLY 8043 chars - DATABASE LIMIT!")
                            
                            # Check how the string ends
                            last_chars = raw_qual.strip()[-20:]
                            st.write(f"**Last 20 chars:** `{last_chars}`")
                            
                            if not raw_qual.strip().endswith('}') and not raw_qual.strip().endswith('```'):
                                st.error("Data appears truncated!")
                                st.code(f"Last 100 chars: ...{raw_qual[-100:]}")
            
            qual_data = safe_json_loads(selected_eng['qualification_data'])
            
            with st.container():
                st.markdown("### 📞 Call Information")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Platform:** {get_platform_label(selected_eng['engagement_type'])}")
                    st.write(f"**Company:** {selected_eng['external_company']}")
                    st.write(f"**Owner:** {selected_eng['call_owner']}")
                
                with col_b:
                    st.write(f"**Date:** {pd.to_datetime(selected_eng['created_at']).strftime('%m/%d/%Y %H:%M')}")
                
                participants = safe_list_parse(selected_eng['participants'])
                if participants:
                    participant_names = [p.get('name', 'Unknown') for p in participants if isinstance(p, dict)]
                    st.write(f"**Participants:** {', '.join(participant_names)}")
                
                st.markdown("**Quick Links:**")
                link_cols = st.columns(3)
                
                if pd.notna(selected_eng['opp_id']):
                    with link_cols[0]:
                        sf_url = f"https://snaplogic.lightning.force.com/lightning/r/Opportunity/{selected_eng['opp_id']}/view"
                        st.markdown(f"[💼 Salesforce]({sf_url})")
                
                if pd.notna(selected_eng['chorus_link']):
                    with link_cols[1]:
                        st.markdown(f"[🎥 Recording]({selected_eng['chorus_link']})")
                
                if pd.notna(selected_eng['pdf_tool_analysis_url']):
                    with link_cols[2]:
                        st.markdown(f"[📄 Analysis]({selected_eng['pdf_tool_analysis_url']})")
            
            st.divider()
            
            if qual_data and isinstance(qual_data, dict) and len(qual_data) > 0:
                has_meaningful_data = any(
                    key in qual_data and qual_data[key]
                    for key in ['call_analysis', 'compelling_event', 'current_state_analysis', 
                               'business_drivers', 'economic_buyer', 'stakeholder_mapping',
                               'justification', 'deal_risks', 'differentiation', 'use_cases']
                )
                
                if has_meaningful_data:
                    st.markdown("### 📋 Qualification Summary")
                    
                    if 'call_analysis' in qual_data and qual_data['call_analysis']:
                        with st.expander("📋 Call Type", expanded=True):
                            call_analysis = qual_data['call_analysis']
                            st.write(f"**Type:** {call_analysis.get('call_type', 'N/A')}")
                            if call_analysis.get('call_type_reasoning'):
                                st.caption(call_analysis['call_type_reasoning'])
                    
                    if 'compelling_event' in qual_data and qual_data['compelling_event']:
                        with st.expander("⏰ Timeline & Compelling Events"):
                            compelling = qual_data['compelling_event']
                            if compelling.get('project_go_live_date'):
                                st.write(f"**Timeline:** {compelling['project_go_live_date']}")
                            if compelling.get('consequences_of_delay'):
                                st.write(f"**Consequences:** {compelling['consequences_of_delay']}")
                            if compelling.get('urgency_indicators'):
                                st.write("**Urgency Indicators:**")
                                for indicator in compelling['urgency_indicators']:
                                    st.write(f"• {indicator}")
                    
                    if 'current_state_analysis' in qual_data and qual_data['current_state_analysis']:
                        with st.expander("🏢 Current State & Challenges"):
                            current_state = qual_data['current_state_analysis']
                            if current_state.get('current_state'):
                                st.write(f"**Current State:** {current_state['current_state']}")
                            if current_state.get('challenges_pain'):
                                st.write("**Key Challenges:**")
                                for pain in current_state['challenges_pain']:
                                    st.write(f"• {pain}")
                            if current_state.get('desired_future_state'):
                                st.write(f"**Desired Future State:** {current_state['desired_future_state']}")
                    
                    if 'business_drivers' in qual_data and qual_data['business_drivers']:
                        with st.expander("🚀 Business Drivers"):
                            drivers = qual_data['business_drivers']
                            if drivers.get('what_is_driving_change'):
                                st.write(f"**What's Driving Change:** {drivers['what_is_driving_change']}")
                            if drivers.get('impact'):
                                st.write(f"**Impact:** {drivers['impact']}")
                            if drivers.get('desired_outcomes'):
                                st.write("**Desired Outcomes:**")
                                for outcome in drivers['desired_outcomes']:
                                    st.write(f"• {outcome}")
                    
                    if 'economic_buyer' in qual_data and qual_data['economic_buyer']:
                        with st.expander("💰 Economic Buyer & Decision Process"):
                            buyer = qual_data['economic_buyer']
                            if buyer.get('who_is_economic_buyer'):
                                st.write(f"**Economic Buyer:** {buyer['who_is_economic_buyer']}")
                            if buyer.get('decision_process'):
                                st.write(f"**Decision Process:** {buyer['decision_process']}")
                            if buyer.get('approval_process'):
                                st.write(f"**Approval Process:** {buyer['approval_process']}")
                    
                    if 'stakeholder_mapping' in qual_data and qual_data['stakeholder_mapping']:
                        with st.expander("👥 Stakeholder Mapping"):
                            stakeholders = qual_data['stakeholder_mapping']
                            if stakeholders.get('coach_champion'):
                                champion = stakeholders['coach_champion']
                                st.write("**Champion:**")
                                if champion.get('name_role'):
                                    st.write(f"• {champion['name_role']}")
                                if champion.get('what_matters_to_them'):
                                    st.write(f"• What matters: {champion['what_matters_to_them']}")
                            if stakeholders.get('blocker'):
                                blocker = stakeholders['blocker']
                                if blocker.get('name_role') and blocker['name_role'] != 'Not explicitly identified':
                                    st.write("**Potential Blocker:**")
                                    st.write(f"• {blocker['name_role']}")
                                    if blocker.get('concerns'):
                                        st.write(f"• Concerns: {blocker['concerns']}")
                    
                    if 'justification' in qual_data and qual_data['justification']:
                        with st.expander("💡 Justification"):
                            justification = qual_data['justification']
                            if justification.get('hard_dollars'):
                                hard = justification['hard_dollars']
                                st.write("**Hard Dollar Benefits:**")
                                for key, value in hard.items():
                                    if value and isinstance(value, list):
                                        st.write(f"**{key.replace('_', ' ').title()}:**")
                                        for item in value:
                                            st.write(f"• {item}")
                            if justification.get('soft_dollars'):
                                soft = justification['soft_dollars']
                                st.write("**Soft Dollar Benefits:**")
                                for key, value in soft.items():
                                    if value and isinstance(value, list):
                                        st.write(f"**{key.replace('_', ' ').title()}:**")
                                        for item in value:
                                            st.write(f"• {item}")
                    
                    if 'deal_risks' in qual_data and qual_data['deal_risks']:
                        with st.expander("⚠️ Risks"):
                            risks = qual_data['deal_risks']
                            if risks.get('competitive_threats'):
                                st.write("**Competition:**")
                                for comp in risks['competitive_threats']:
                                    st.write(f"• {comp}")
                            if risks.get('internal_obstacles'):
                                st.write("**Internal Obstacles:**")
                                for obs in risks['internal_obstacles']:
                                    st.write(f"• {obs}")
                            if risks.get('other_risks'):
                                st.write("**Other Risks:**")
                                for risk in risks['other_risks']:
                                    st.write(f"• {risk}")
                    
                    if 'differentiation' in qual_data and qual_data['differentiation']:
                        with st.expander("🌟 Differentiation"):
                            diff = qual_data['differentiation']
                            if diff.get('unique_technical_differentiation'):
                                st.write("**Technical Differentiation:**")
                                for item in diff['unique_technical_differentiation']:
                                    st.write(f"• {item}")
                            if diff.get('business_project_advantages'):
                                st.write("**Business Advantages:**")
                                for item in diff['business_project_advantages']:
                                    st.write(f"• {item}")
                    
                    if 'use_cases' in qual_data and qual_data['use_cases']:
                        with st.expander("💡 Use Cases"):
                            for key, use_case in qual_data['use_cases'].items():
                                if isinstance(use_case, dict) and use_case.get('description'):
                                    st.write(f"**{use_case['description']}**")
                                    if use_case.get('data_volume'):
                                        st.write(f"• Volume: {use_case['data_volume']}")
                                    if use_case.get('frequency'):
                                        st.write(f"• Frequency: {use_case['frequency']}")
                                    if use_case.get('technical_requirements'):
                                        st.write("• Requirements:")
                                        for req in use_case['technical_requirements']:
                                            st.write(f"  - {req}")
                                    st.divider()
                    
                    if debug_mode:
                        with st.expander("📊 View All Qualification Data"):
                            st.json(qual_data)
                else:
                    st.info("Qualification data contains no meaningful information.")
            else:
                st.info("No qualification data available for this engagement.")
    else:
        st.info("👆 Select an engagement from the list to view details")

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total engagements: {len(df)}")
