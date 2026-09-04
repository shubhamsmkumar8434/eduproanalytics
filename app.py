import streamlit as st  # type: ignore[import-not-found]
import pandas as pd
import numpy as np
import os

try:
    import plotly.express as px  # type: ignore[import-not-found]
except ImportError:
    px = None

# ---------------------------------------------------------
# 1. Page Configuration & Project Context
# ---------------------------------------------------------
st.set_page_config(page_title="EduPro Analytics", page_icon="🎓", layout="wide")

st.title("🎓 Learner Demographics & Course Enrollment Behavior Analysis on EduPro")

st.markdown("""
### Problem Statement
Despite having user and transaction data, EduPro currently lacks clear answers to:
* Which age groups are most active on the platform?
* How do enrollment patterns differ by gender?
* What course categories are preferred by different learner segments?
* Are beginner, intermediate, or advanced courses more popular among specific age groups?

Without these insights, decisions related to course creation, marketing, and platform growth remain intuition-driven rather than data-driven.
""")
st.divider()

# ---------------------------------------------------------
# 2. Data Loading & Integration
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # 1. Load the provided Users CSV file
    try:
        users = pd.read_csv('EduPro Online Platform.xlsx - Users.csv')
    except FileNotFoundError:
        st.error("Error: Could not find 'EduPro Online Platform.xlsx - Users.csv'. Please ensure it is in the same directory as this script.")
        return pd.DataFrame()

    # 2. Mocking Courses and Transactions data (Replace these with pd.read_csv when you have the files)
    # Example: courses = pd.read_csv('EduPro Online Platform.xlsx - Courses.csv')
    # Example: transactions = pd.read_csv('EduPro Online Platform.xlsx - Transactions.csv')
    
    np.random.seed(42)
    courses = pd.DataFrame({
        'CourseID': range(101, 121),
        'CourseName': [f'Course_{i}' for i in range(101, 121)],
        'CourseCategory': np.random.choice(['Programming', 'Data Science', 'Marketing', 'Design', 'Business'], 20),
        'CourseType': np.random.choice(['Video', 'Interactive', 'Live Session'], 20),
        'CourseLevel': np.random.choice(['Beginner', 'Intermediate', 'Advanced'], 20)
    })
    
    # Ensure Transactions map to the actual UserIDs from your CSV
    valid_user_ids = users['UserID'].dropna().unique() if 'UserID' in users.columns else range(1, len(users)+1)
    
    transactions = pd.DataFrame({
        'TransactionID': range(1001, 3001),
        'UserID': np.random.choice(valid_user_ids, 2000),
        'CourseID': np.random.choice(courses['CourseID'], 2000),
        'TransactionDate': pd.date_range(start='1/1/2023', periods=2000)
    })

    # Data Integration: Join Users ↔ Transactions ↔ Courses
    df = transactions.merge(users, on='UserID', how='inner').merge(courses, on='CourseID', how='inner')
    
    # Segment learners into exact age bands specified in the project requirements
    bins = [0, 18, 26, 36, 46, 100]
    labels = ['<18', '18–25', '26–35', '36–45', '45+']
    df['AgeGroup'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False)
    
    return df

df = load_data()

if df.empty:
    st.stop()

# ---------------------------------------------------------
# 3. Sidebar: User Capabilities
# ---------------------------------------------------------
st.sidebar.header("🔍 Analytical Filters")

selected_age = st.sidebar.multiselect("Age Group", options=df['AgeGroup'].dropna().unique(), default=df['AgeGroup'].dropna().unique())
selected_gender = st.sidebar.multiselect("Gender", options=df['Gender'].dropna().unique(), default=df['Gender'].dropna().unique())
selected_category = st.sidebar.multiselect("Course Category", options=df['CourseCategory'].dropna().unique(), default=df['CourseCategory'].dropna().unique())
selected_level = st.sidebar.multiselect("Course Level", options=df['CourseLevel'].dropna().unique(), default=df['CourseLevel'].dropna().unique())

# Apply filters
filtered_df = df[
    (df['AgeGroup'].isin(selected_age)) &
    (df['Gender'].isin(selected_gender)) &
    (df['CourseCategory'].isin(selected_category)) &
    (df['CourseLevel'].isin(selected_level))
]

# ---------------------------------------------------------
# 4. Key Performance Indicators (KPIs)
# ---------------------------------------------------------
st.markdown("### 📈 Key Performance Indicators (KPIs)")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(label="Total Enrollments", value=len(filtered_df), help="Platform engagement indicator")
kpi2.metric(label="Unique Active Learners", value=filtered_df['UserID'].nunique())

# Gender Participation Ratio (Majority Gender)
majority_gender = filtered_df['Gender'].mode()[0] if not filtered_df.empty else "N/A"
kpi3.metric(label="Primary Demographics", value=majority_gender, help="Inclusivity metric")

# Category Popularity Index
top_category = filtered_df['CourseCategory'].mode()[0] if not filtered_df.empty else "N/A"
kpi4.metric(label="Top Category", value=top_category, help="Course demand metric")

st.divider()

# ---------------------------------------------------------
# 5. Core Modules: Data Visualizations
# ---------------------------------------------------------
col1, col2 = st.columns(2)

# Module 1: Learner Demographic Overview
with col1:
    st.subheader("Gender Participation Ratio")
    if not filtered_df.empty:
        gender_dist = filtered_df['Gender'].value_counts().reset_index()
        gender_dist.columns = ['Gender', 'Count']
        
        fig_gender = px.pie(gender_dist, names='Gender', values='Count', hole=0.4, 
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_gender, use_container_width=True)
    else:
        st.info("No data available.")

# Module 2: Age-wise Enrollment Charts
with col2:
    st.subheader("Enrollments by Age Group")
    if not filtered_df.empty:
        age_dist = filtered_df['AgeGroup'].value_counts().reset_index()
        age_dist.columns = ['Age Group', 'Enrollments']
        age_dist['Age Group'] = pd.Categorical(age_dist['Age Group'], categories=['<18', '18–25', '26–35', '36–45', '45+'], ordered=True)
        age_dist = age_dist.sort_values('Age Group')
        
        fig_age = px.bar(age_dist, x='Age Group', y='Enrollments', text_auto=True, 
                         color='Age Group', color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_age, use_container_width=True)
    else:
        st.info("No data available.")

col3, col4 = st.columns(2)

# Module 3: Course Category Popularity Visuals
with col3:
    st.subheader("Category Popularity Index")
    if not filtered_df.empty:
        cat_dist = filtered_df['CourseCategory'].value_counts().reset_index()
        cat_dist.columns = ['Category', 'Enrollments']
        fig_cat = px.bar(cat_dist, x='Enrollments', y='Category', orientation='h', text_auto=True,
                         color='Category', color_discrete_sequence=px.colors.qualitative.Set2)
        fig_cat.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("No data available.")

# Module 4: Gender-based Course Preference Analysis
with col4:
    st.subheader("Demographics × Course Preference")
    if not filtered_df.empty:
        gen_cat = filtered_df.groupby(['CourseCategory', 'Gender']).size().reset_index(name='Enrollments')
        fig_gen_cat = px.bar(gen_cat, x='CourseCategory', y='Enrollments', color='Gender', barmode='group',
                             color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_gen_cat, use_container_width=True)
    else:
        st.info("No data available.")

# Module 5: Level Preference Distribution
st.divider()
st.subheader("Level Preference Distribution (Skill Maturity)")
if not filtered_df.empty:
    level_dist = filtered_df['CourseLevel'].value_counts().reset_index()
    level_dist.columns = ['Course Level', 'Enrollments']
    fig_level = px.funnel(level_dist, x='Enrollments', y='Course Level', 
                          color='Course Level', color_discrete_sequence=px.colors.qualitative.Vivid)
    st.plotly_chart(fig_level, use_container_width=True)
else:
    st.info("No data available.")
