import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Chicago Employee Salary Dashboard",
    page_icon="💰",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .title-text {
        font-size: 40px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Load and process data
@st.cache_data
def get_data():
    df = pd.read_csv('data/Current_Employee_Names__Salaries__and_Position_Titles_20250413.csv')
    df.columns=['name', 'job_title', 'department', 'full_part_time', 'salary_hourly', 
                'typical_hours', 'annual_salary', 'hourly_rate']
    df['annual_pay'] = np.where(df['salary_hourly']=='SALARY', 
                               df['annual_salary'],
                               np.where(df['salary_hourly']=='HOURLY', 
                                      df['hourly_rate']*df['typical_hours']*50, 0))
    return df

# Main layout
st.markdown('<p class="title-text">Chicago Employee Salary Dashboard</p>', unsafe_allow_html=True)
st.markdown("---")

# Load data
data = get_data()

# Sidebar filters
with st.sidebar:
    st.header("📊 Filters")

    all_departments = sorted(data['department'].unique())
    select_all_depts = st.checkbox("Select All Departments", value=True)
    if select_all_depts:
        departments = all_departments
    else:
        departments = st.multiselect(
            "Select Department:",
            options=sorted(data['department'].unique()),
            default=sorted(data['department'].unique()),
        )
    
    employment_type = st.multiselect(
        "Employment Type:",
        options=sorted(data['full_part_time'].astype(str).unique()),
        default=data['full_part_time'].astype(str).unique()
    )
    
    min_salary, max_salary = st.slider(
        "Annual Pay Range ($):", 
        int(data['annual_pay'].min()), 
        int(data['annual_pay'].max()), 
        (int(data['annual_pay'].min()), int(data['annual_pay'].max()))
    )

# Filter data
filtered_data = data[
    (data['department'].isin(departments)) &
    (data['full_part_time'].isin(employment_type)) &
    (data['annual_pay'].between(min_salary, max_salary))
]


# Calculate department statistics for use in charts
dept_df = (filtered_data.groupby('department')
           .agg({
               'annual_pay': ['count', 'mean', 'min', 'max']
           })
           .round(2))
# Flatten column names and rename
dept_df.columns = ['employee_count', 'avg_salary', 'min_salary', 'max_salary']
dept_df = dept_df.reset_index()

# Add percentage column
dept_df['percentage'] = (dept_df['employee_count'] / len(filtered_data) * 100).round(1)

# Sort by employee count descending
dept_df = dept_df.sort_values('employee_count', ascending=True)

# Dashboard layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Key Metrics")
    metric1, metric2, metric3 = st.columns(3)
    with metric1:
        st.metric("Average Salary", f"${filtered_data['annual_pay'].mean():,.0f}")
    with metric2:
        st.metric("Total Employees", f"{len(filtered_data):,}")
    with metric3:
        st.metric("Departments", f"{len(departments)}")

    st.subheader("📊 Salary Distribution")
    fig_dist = px.histogram(filtered_data, x="annual_pay", 
                            nbins=40, 
                            title="Salary Distribution")
    fig_dist.update_layout(xaxis_title="Annual Pay ($)", 
                           yaxis_title="Count")
    st.plotly_chart(fig_dist, use_container_width=True)

with col2:
    st.subheader("💼 Average Salary by Department")

    fig_dept = px.bar(
        dept_df.sort_values('avg_salary', ascending=True),
        x='avg_salary',
        y='department',
        orientation='h',
        title="Average Salary by Department",
        hover_data={
            'avg_salary': ':$,.0f',
            'employee_count': ':,',
            'min_salary': ':$,.0f',
            'max_salary': ':$,.0f',
            'department': False
            },
        custom_data=['employee_count', 'min_salary', 'max_salary']
    )
    fig_dept.update_traces(
        hovertemplate="<b>%{y}</b><br>" +
        "Average Salary: %{x:$,.0f}<br>" +
        "Employees: %{customdata[0]:,}<br>" +
        "Range: %{customdata[1]:$,.0f} - %{customdata[2]:$,.0f}<extra></extra>"
    )

    fig_dept.update_layout(
        xaxis_title="Average Annual Pay ($)",
        yaxis_title="Department",
        showlegend=False
    )

    st.plotly_chart(fig_dept, use_container_width=True)

# Employee Distribution by Department
st.subheader("👥 Employee Distribution by Department")

fig_dept_dist = px.bar(
    dept_df.sort_values('employee_count', ascending=True),
    x='employee_count',
    y='department',
    orientation='h',
    title="Number of Employees by Department",
    hover_data={
        'employee_count': ':,',  # Format with thousand separator
        'percentage': ':.1f%',  # Format as percentage
        'avg_salary': ':$,.0f',  # Format as currency
        'department': False  # Hide department from tooltip since it's already visible
    },
    custom_data=['percentage','avg_salary']
)

fig_dept_dist.update_traces(
    hovertemplate="<b>%{y}</b><br>" +
    "Employees: %{x:,}<br>" +
    "Percentage: %{customdata[0]:.1f}%<br>" +
    "Average Salary: %{customdata[1]:$,.0f}<br>" 
)


fig_dept_dist.update_layout(
    xaxis_title="Number of Employees",
    yaxis_title="Department",
    height=400,
    showlegend=False,
    yaxis={'categoryorder': 'total ascending'}  # This ensures bars are sorted by value
)

st.plotly_chart(fig_dept_dist, use_container_width=True)

# Top earners
st.subheader("🏆 Top 10 Highest-Paid Employees")
top_10 = filtered_data.nlargest(10, 'annual_pay')
fig_top10 = go.Figure(data=[
    go.Table(
        header=dict(values=['Name', 'Job Title', 'Department', 'Annual Pay'],
                   fill_color='#1E88E5',
                   align='left',
                   font=dict(color='white')),
        cells=dict(values=[top_10['name'], 
                          top_10['job_title'],
                          top_10['department'],
                          top_10['annual_pay'].apply(lambda x: f"${x:,.2f}")],
                  align='left'))
])
st.plotly_chart(fig_top10, use_container_width=True)

# Raw data with toggle
if st.checkbox("Show Raw Data"):
    st.dataframe(filtered_data.style.format({'annual_pay': '${:,.2f}'}))

