import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import math

# Authentication configuration
USERNAME = "admin"
PASSWORD = "snaplogic123"

def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Check if already authenticated
    if st.session_state.get("password_correct", False):
        return True
    
    # Show login form
    st.markdown("## 🔐 Sales Engagement Dashboard Login")
    if st.session_state.get("password_correct") == False:
        st.error("😕 Username or password incorrect. Please try again.")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Use a form to handle the login properly
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if username == USERNAME and password == PASSWORD:
                    st.session_state["password_correct"] = True
                    st.session_state["authenticated_user"] = username
                    st.rerun()
                else:
                    st.session_state["password_correct"] = False
                    st.rerun()
    
    return False

# Check authentication first
if not check_password():
    st.stop()  # Stop execution if not authenticated

# Page config (after authentication)
st.set_page_config(page_title="Sales Engagement Dashboard", layout="wide")

# API configuration
API_URL = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/SLoS_Prod/Echo_Sales_Coach/Echo_Sales_Coach/engagement_api"
API_HEADERS = {
    "Authorization": "Bearer 12345",
    "Content-Type": "application/json"
}

# Custom CSS for expander styling and link styling
st.markdown("""
<style>
/* Make main content expander text larger and more prominent */
div[data-testid="stExpander"]:not(.sidebar div[data-testid="stExpander"]) details summary p {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #0066cc !important;
}
/* Keep sidebar expanders normal */
.element-container .sidebar div[data-testid="stExpander"] details summary p {
    font-size: 14px !important;
    font-weight: 400 !important;
    color: inherit !important;
}
/* Style for quick links */
.quick-link {
    background-color: #0066cc;
    color: white !important;
    padding: 8px 16px;
    border-radius: 6px;
    text-decoration: none !important;
    display: inline-block;
    margin: 4px 0;
    font-weight: 600;
    border: none;
}
.quick-link:hover {
    background-color: #0052a3;
    color: white !important;
    text-decoration: none !important;
}
/* Style download buttons to match quick links */
div[data-testid="stDownloadButton"] button {
    background-color: #0066cc !important;
    color: white !important;
    padding: 8px 16px !important;
    border-radius: 6px !important;
    border: none !important;
    font-weight: 600 !important;
    margin: 4px 0 !important;
    display: inline-block !important;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #0052a3 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# Data fetching with improved timeout and error handling
@st.cache_data(ttl=300)
def get_data():
    try:
        # Increase timeout to 60 seconds for larger datasets
        with st.spinner("Loading data from API... This may take a moment for large datasets."):
            response = requests.get(API_URL, headers=API_HEADERS, timeout=60)
        
        # Check for specific HTTP errors
        if response.status_code == 500:
            st.error("⚠️ Server timeout (500 error) - The dataset may be too large. Try filtering by date range or contact your administrator.")
            return pd.DataFrame()
        elif response.status_code == 502:
            st.error("⚠️ Bad Gateway (502 error) - API server may be overloaded. Please try again in a few minutes.")
            return pd.DataFrame()
        elif response.status_code == 504:
            st.error("⚠️ Gateway Timeout (504 error) - Request took too long. Try filtering to a smaller date range.")
            return pd.DataFrame()
        
        response.raise_for_status()
        
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
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out after 60 seconds. The dataset may be too large. Try filtering by a smaller date range.")
        return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection error. Please check your internet connection and try again.")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        st.error(f"🔴 HTTP Error {response.status_code}: {str(e)}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"🔴 Request failed: {str(e)}")
        return pd.DataFrame()
    except json.JSONDecodeError:
        st.error("📄 Invalid JSON response from API. Please contact your administrator.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return pd.DataFrame()

# Helper functions
def safe_get_dict(data):
    """Safely get dictionary data that's already parsed"""
    if pd.isna(data) or data is None or data == '':
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except:
            return {}
    return {}

def safe_get_list(data):
    """Safely get list data that's already parsed"""
    if pd.isna(data) or data is None or data == '':
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, list) else []
        except:
            return []
    return []

def get_platform_label(engagement_type):
    return "Outreach" if engagement_type == "dialer" else "Chorus"

def extract_all_snaplogic_participants(df):
    """Extract all unique SnapLogic participants from the dataframe"""
    snaplogic_participants = {}
    
    for idx, row in df.iterrows():
        participants = row.get('participants', [])
        if not isinstance(participants, list):
            participants = safe_get_list(participants)
        
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
    
    return snaplogic_participants

def display_engagement_details(row):
    """Display detailed engagement information"""
    qual_data = safe_get_dict(row.get('qualification_data', {}))
    participants = row.get('participants', [])
    if not isinstance(participants, list):
        participants = safe_get_list(participants)
    
    # Create columns for basic info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Call Information")
        st.write(f"**Platform:** {get_platform_label(row['engagement_type'])}")
        st.write(f"**Company:** {row['external_company']}")
        st.write(f"**Owner:** {row['call_owner']}")
        st.write(f"**Date:** {pd.to_datetime(row['created_at']).strftime('%m/%d/%Y %H:%M')}")
    
    with col2:
        st.markdown("### Participants")
        if participants:
            for p in participants:
                if isinstance(p, dict):
                    name = p.get('name', 'Unknown')
                    company = p.get('company_name', '')
                    if company:
                        st.write(f"• {name} ({company})")
                    else:
                        st.write(f"• {name}")
        else:
            st.write("No participants listed")
    
    with col3:
        st.markdown("### Quick Links")
        if pd.notna(row.get('opp_id')):
            sf_url = f"https://snaplogic.lightning.force.com/lightning/r/Opportunity/{row['opp_id']}/view"
            st.markdown(f'<a href="{sf_url}" target="_blank" class="quick-link">Salesforce</a>', unsafe_allow_html=True)
        
        if pd.notna(row.get('chorus_link')):
            st.markdown(f'<a href="{row["chorus_link"]}" target="_blank" class="quick-link">Recording</a>', unsafe_allow_html=True)
        
        if pd.notna(row.get('pdf_tool_analysis_url')):
            st.markdown(f'<a href="{row["pdf_tool_analysis_url"]}" target="_blank" class="quick-link">Coaching Feedback</a>', unsafe_allow_html=True)
        
        # Download Transcript button styled to match quick links
        transcript = row.get('transcript', '')
        if transcript and transcript != '':
            transcript_filename = f"transcript_{row['external_company'].replace(' ', '_')}_{pd.to_datetime(row['created_at']).strftime('%Y%m%d')}.txt"
            
            # Create a styled download button using HTML/CSS
            st.markdown(f"""
                <style>
                .download-transcript-btn {{
                    background-color: #0066cc;
                    color: white !important;
                    padding: 8px 16px;
                    border-radius: 6px;
                    text-decoration: none !important;
                    display: inline-block;
                    margin: 4px 0;
                    font-weight: 600;
                    border: none;
                    cursor: pointer;
                }}
                .download-transcript-btn:hover {{
                    background-color: #0052a3;
                    color: white !important;
                    text-decoration: none !important;
                }}
                </style>
            """, unsafe_allow_html=True)
            
            st.download_button(
                label="Download Transcript",
                data=transcript,
                file_name=transcript_filename,
                mime="text/plain",
                key=f"transcript_{row.get('engagement_id', idx)}",
                use_container_width=False
            )
    
    # Qualification Summary
    if qual_data:
        st.markdown("---")
        st.markdown("## Qualification Summary")
        
        # Use columns for qualification sections
        col1, col2 = st.columns(2)
        
        with col1:
            # Call Type
            if 'call_analysis' in qual_data and qual_data['call_analysis']:
                with st.expander("Call Type", expanded=False):
                    call_analysis = qual_data['call_analysis']
                    st.write(f"**Type:** {call_analysis.get('call_type', 'N/A')}")
                    if call_analysis.get('call_type_reasoning'):
                        st.caption(call_analysis['call_type_reasoning'])
            
            # Current State & Challenges
            if 'current_state_analysis' in qual_data and qual_data['current_state_analysis']:
                with st.expander("Current State & Challenges", expanded=False):
                    current_state = qual_data['current_state_analysis']
                    if current_state.get('current_state'):
                        st.write(f"**Current State:** {current_state['current_state']}")
                    if current_state.get('challenges_pain'):
                        st.write("**Key Challenges:**")
                        for pain in current_state['challenges_pain']:
                            st.write(f"• {pain}")
                    if current_state.get('desired_future_state'):
                        st.write(f"**Desired Future State:** {current_state['desired_future_state']}")
            
            # Economic Buyer
            if 'economic_buyer' in qual_data and qual_data['economic_buyer']:
                with st.expander("Economic Buyer", expanded=False):
                    buyer = qual_data['economic_buyer']
                    if buyer.get('who_is_economic_buyer'):
                        st.write(f"**Economic Buyer:** {buyer['who_is_economic_buyer']}")
                    if buyer.get('decision_process'):
                        st.write(f"**Decision Process:** {buyer['decision_process']}")
                    if buyer.get('approval_process'):
                        st.write(f"**Approval Process:** {buyer['approval_process']}")
            
            # Deal Risks
            if 'deal_risks' in qual_data and qual_data['deal_risks']:
                with st.expander("Risks", expanded=False):
                    risks = qual_data['deal_risks']
                    if risks.get('competitive_threats'):
                        st.write("**Competition:**")
                        for comp in risks['competitive_threats']:
                            st.write(f"• {comp}")
                    if risks.get('internal_obstacles'):
                        st.write("**Internal Obstacles:**")
                        for obs in risks['internal_obstacles']:
                            st.write(f"• {obs}")
            
            # Justification
            if 'justification' in qual_data and qual_data['justification']:
                with st.expander("Justification", expanded=False):
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
        
        with col2:
            # Timeline & Compelling Events
            if 'compelling_event' in qual_data and qual_data['compelling_event']:
                with st.expander("Timeline & Compelling Events", expanded=False):
                    compelling = qual_data['compelling_event']
                    if compelling.get('project_go_live_date'):
                        st.write(f"**Timeline:** {compelling['project_go_live_date']}")
                    if compelling.get('consequences_of_delay'):
                        st.write(f"**Consequences:** {compelling['consequences_of_delay']}")
                    if compelling.get('urgency_indicators'):
                        st.write("**Urgency Indicators:**")
                        for indicator in compelling['urgency_indicators']:
                            st.write(f"• {indicator}")
            
            # Business Drivers
            if 'business_drivers' in qual_data and qual_data['business_drivers']:
                with st.expander("Business Drivers", expanded=False):
                    drivers = qual_data['business_drivers']
                    if drivers.get('what_is_driving_change'):
                        st.write(f"**What's Driving Change:** {drivers['what_is_driving_change']}")
                    if drivers.get('impact'):
                        st.write(f"**Impact:** {drivers['impact']}")
                    if drivers.get('desired_outcomes'):
                        st.write("**Desired Outcomes:**")
                        for outcome in drivers['desired_outcomes']:
                            st.write(f"• {outcome}")
            
            # Stakeholder Mapping
            if 'stakeholder_mapping' in qual_data and qual_data['stakeholder_mapping']:
                with st.expander("Stakeholder Mapping", expanded=False):
                    stakeholders = qual_data['stakeholder_mapping']
                    if stakeholders.get('coach_champion'):
                        champion = stakeholders['coach_champion']
                        st.write("**Champion:**")
                        if champion.get('name_role'):
                            st.write(f"• {champion['name_role']}")
                        if champion.get('what_matters_to_them'):
                            st.write(f"• What matters: {champion['what_matters_to_them']}")
            
            # Differentiation
            if 'differentiation' in qual_data and qual_data['differentiation']:
                with st.expander("Differentiation", expanded=False):
                    diff = qual_data['differentiation']
                    if diff.get('unique_technical_differentiation'):
                        st.write("**Technical Differentiation:**")
                        for item in diff['unique_technical_differentiation']:
                            st.write(f"• {item}")
                    if diff.get('business_project_advantages'):
                        st.write("**Business Advantages:**")
                        for item in diff['business_project_advantages']:
                            st.write(f"• {item}")
            
            # Use Cases
            if 'use_cases' in qual_data and qual_data['use_cases']:
                with st.expander("Use Cases", expanded=False):
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

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'selected_engagement_id' not in st.session_state:
    st.session_state.selected_engagement_id = None

# Load data
with st.spinner("Loading engagement data..."):
    df = get_data()

if df.empty:
    st.error("No data available. Please check the API connection.")
    st.stop()

# Get filter options
snaplogic_participants_dict = extract_all_snaplogic_participants(df)
snaplogic_participants = sorted(list(snaplogic_participants_dict.keys()))
opportunities = df[df['opp_name'].notna()]['opp_name'].unique()

# Header
st.title("Sales Engagement Dashboard")
st.markdown("*Track and analyze sales conversations with AI-powered insights*")
st.divider()

# Sidebar filters
with st.sidebar:
    # Add logout button at the top
    st.markdown("---")
    current_user = st.session_state.get("authenticated_user", "Unknown")
    st.caption(f"👤 Logged in as: **{current_user}**")
    
    if st.button("🚪 Logout"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.header("Filters")
    
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
    
    # Date filter
    st.subheader("Date Range")
    
    # Get date range from data
    if not df.empty and 'created_at' in df.columns:
        min_date = df['created_at'].min().date()
        max_date = df['created_at'].max().date()
        
        # Default to last 30 days or all data if less than 30 days
        default_start = max(min_date, max_date - timedelta(days=30))
        
        date_range = st.date_input(
            "Select date range",
            value=(default_start, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )
        
        # Handle single date selection
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        elif len(date_range) == 1:
            start_date = end_date = date_range[0]
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date = end_date = datetime.now().date()
    
    search_term = st.text_input("Search by company or owner")
    
    st.divider()
    
    st.header("Pagination")
    items_per_page = st.selectbox(
        "Items per page",
        options=[5, 10, 15, 20, 25, 50],
        index=0  # Default to 5
    )
    
    st.divider()
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.current_page = 1
        st.session_state.selected_engagement_id = None
        st.rerun()
    
    with st.expander("API Status"):
        st.write(f"**Records loaded:** {len(df)}")
        st.write(f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")

# Apply filters
filtered_df = df.copy()

# Apply date filter
if not filtered_df.empty and 'created_at' in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df['created_at'].dt.date >= start_date) & 
        (filtered_df['created_at'].dt.date <= end_date)
    ]

if platform_filter == "Outreach":
    filtered_df = filtered_df[filtered_df['engagement_type'] == 'dialer']
elif platform_filter == "Chorus":
    filtered_df = filtered_df[filtered_df['engagement_type'] == 'meeting']

if participant_filter != "All SnapLogic Participants":
    def check_participant(row):
        participants = row.get('participants', [])
        if not isinstance(participants, list):
            participants = safe_get_list(participants)
        
        for p in participants:
            if isinstance(p, dict):
                name = p.get('name', '')
                company = p.get('company_name', '')
                email = p.get('email', '')
                
                if name == participant_filter:
                    is_snaplogic = any([
                        'SnapLogic' in str(company),
                        'snaplogic' in str(company).lower(),
                        'snaplogic.com' in str(email).lower() if email else False
                    ])
                    if is_snaplogic:
                        return True
        return False
    
    mask = filtered_df.apply(check_participant, axis=1)
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

# Calculate pagination
total_records = len(filtered_df)
total_pages = math.ceil(total_records / items_per_page) if total_records > 0 else 1

# Ensure current page is valid
if st.session_state.current_page > total_pages:
    st.session_state.current_page = 1

start_idx = (st.session_state.current_page - 1) * items_per_page
end_idx = min(start_idx + items_per_page, total_records)

# Get current page data
current_page_df = filtered_df.iloc[start_idx:end_idx]

# Main content area
st.subheader("Recent Engagements")
if total_records > 0:
    st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_records} engagements")
else:
    st.caption("No engagements found")

if filtered_df.empty:
    st.info("No engagements match your current filters.")
else:
    # Display engagements with expandable details
    for idx, row in current_page_df.iterrows():
        # Get qualification data
        qual_data = safe_get_dict(row.get('qualification_data', {}))
        call_type = qual_data.get('call_analysis', {}).get('call_type', '') if qual_data else ''
        
        # Check if this engagement is selected
        is_selected = (st.session_state.selected_engagement_id == row['engagement_id'])
        
        # Create expander for each engagement - simplified label without platform and date
        expander_label = f"**{row['external_company']}**"
        
        with st.expander(expander_label, expanded=is_selected):
            # Quick info at the top
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Owner:** {row['call_owner'].split('@')[0]}")
                if call_type:
                    st.write(f"**Call Type:** {call_type}")
            
            with col2:
                if pd.notna(row.get('opp_name')):
                    st.write(f"**Opportunity:** {row['opp_name']}")
                else:
                    st.write("**Opportunity:** None")
            
            with col3:
                if pd.notna(row.get('subject')):
                    st.write(f"**Subject:** {row['subject'][:50]}")
            
            st.markdown("---")
            
            # Display full details
            display_engagement_details(row)
    
    # Pagination controls
    if total_pages > 1:
        st.markdown("---")
        
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("Previous", disabled=(st.session_state.current_page == 1)):
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
            if st.button("Next", disabled=(st.session_state.current_page == total_pages)):
                st.session_state.current_page += 1
                st.rerun()

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total engagements: {len(df)}")
