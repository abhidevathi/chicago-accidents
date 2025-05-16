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
    # Add bin widgth options
    bin_width_options = {
        '1K': 1000,
        '5K': 5000,
        '10K': 10000,
        '20K': 20000
    }
    bin_width_key = st.selectbox(
        "Salary Range Width:",
        options=list(bin_width_options.keys()),
        index=2,
        help="Adjust the width of salary ranges in the histogram"
    )
    bin_width = bin_width_options[bin_width_key]

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

st.subheader("🎯 Key Metrics")
metric1, metric2, metric3 = st.columns(3)
with metric1:
    st.metric("Average Salary", f"${filtered_data['annual_pay'].mean():,.0f}")
with metric2:
    st.metric("Total Employees", f"{len(filtered_data):,}")
with metric3:
    st.metric("Departments", f"{len(departments)}")


# Dashboard layout
col1, col2 = st.columns(2)

with col1:

    st.subheader("📊 Salary Distribution")    
    # salary_range = filtered_data['annual_pay'].max() - filtered_data['annual_pay'].min()
    
    
    min_value = bin_width * np.floor(filtered_data['annual_pay'].min() / bin_width)
    max_value = bin_width * np.ceil(filtered_data['annual_pay'].max() / bin_width)
    # st.write(f"Min value: {min_value}, Max value: {max_value}")
    num_bins = int((max_value - min_value) / bin_width)
    # st.write(f"Number of bins: {num_bins} (Width: ${bin_width})")
    
    bin_edges = np.linspace(
        min_value,
        max_value,
        num_bins + 1
    )

    fig_dist = px.histogram(
        filtered_data,
        x="annual_pay", 
        nbins=num_bins, 
        title="Salary Distribution",
        labels={'annual_pay': 'Annual Pay'},
        barmode='relative',
        opacity=0.8,
        )
    
    bin_starts=bin_edges[:-1]
    bin_ends=bin_edges[1:]

    fig_dist.update_traces(
        hovertemplate="<b>Salary Range:</b><br>" +
        "$%{customdata[0]:,.0f} - $%{customdata[1]:,.0f}<br>" +
        "Employee Count: %{y:,}<br>" +
        "<extra></extra>",
        customdata=np.column_stack((bin_starts, bin_ends))
    )

    fig_dist.update_layout(
        xaxis_title="Annual Pay ($)", 
        yaxis_title="Employee Count",
        bargap=0.2,
        )

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
st.subheader("🏆 Top Highest-Paid Employees")
top_n_selector = st.number_input("Number of top employees to display (1-100):", 
                                min_value=1, 
                                max_value=100, 
                                value=10,
                                step=1,
                                help="Enter a number between 1 and 100")
top_n = filtered_data.nlargest(top_n_selector, 'annual_pay').sort_values('annual_pay', ascending=False)
top_n['rank'] = range(1, len(top_n) + 1)
# Create a custom table with better formatting
fig_top_n = go.Figure(data=[
    go.Table(
        header=dict(
            values=['<b>Rank</b>', '<b>Name</b>', '<b>Job Title</b>', '<b>Department</b>', '<b>Annual Pay</b>'],
            fill_color='#1E88E5',
            align=['center', 'left', 'left', 'left', 'right'],
            font=dict(color='white', size=14),
            height=40,
            line_color='#2b2b2b',
            line_width=2,
            
        ),
        cells=dict(
            values=[
                top_n['rank'].astype(str).values,
                top_n['name'].values, 
                top_n['job_title'].values,
                top_n['department'].values,
                top_n['annual_pay'].apply(lambda x: f"${x:,.2f}").values
            ],
            align=['center', 'left', 'left', 'left', 'right'],
            font=dict(color='white',size=13),
            height=24,
            fill_color=[
                ['#2b2b2b' if i%2 == 0 else '#3d3d3d' for i in range(len(top_n))]
            ] * 5,
            # columnwidth=[1,4,4,4,2],
            line_color='#1E88E5',
            line_width=1
        ),
        columnwidth=[1,4,4,4,2],
    )
])

# Update layout for better visibility
fig_top_n.update_layout(
    margin=dict(l=20, r=20, t=20, b=20),
    autosize=True,
)

# Create metrics for top earner stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Highest Salary", 
        f"${top_n['annual_pay'].max():,.0f}",
        f"Top {(top_n['annual_pay'].max() / filtered_data['annual_pay'].mean() - 1):,.1%} above average"
    )
with col2:
    st.metric(
        "Most Common Department", 
        f"{top_n['department'].mode()[0]}",
        f"{len(top_n[top_n['department'] == top_n['department'].mode()[0]])} employees"
    )
with col3:
    st.metric(
        f"Average Top {top_n_selector} Salary", 
        f"${top_n['annual_pay'].mean():,.0f}",
        f"${top_n['annual_pay'].mean() - filtered_data['annual_pay'].mean():,.0f} above average"
    )

# Create container with custom class
st.plotly_chart(fig_top_n, use_container_width=True)
