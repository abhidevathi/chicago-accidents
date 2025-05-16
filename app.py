import streamlit as st
import pandas as pd
import numpy as np
import requests

# Replace 'YOUR_API_KEY' with your actual API key
API_KEY = 'YOUR_API_KEY'
API_URL = 'https://data.cityofchicago.org/resource/85ca-t3if.geojson'

# Fetch data from the City of Chicago API
def fetch_data(api_url, api_key):
    headers = {
        'X-App-Token': api_key
    }
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

# Fetch the data
data = fetch_data(API_URL, API_KEY)


st.write("Hello World")

cols = 3
rows = 20
dataframe = pd.DataFrame(
    np.random.randn(rows, cols), # create a random dataframe with 5 columns and 20 rows with values between 0 and 1
    columns=('col %d' % i for i in range(cols)))

st.dataframe(dataframe.style.highlight_max(axis=0)) # Dataframe with highlights

# st.table(dataframe) # Static Table

st.header("Line Chart", divider='blue')

chart_data = pd.DataFrame(
     np.random.randn(rows, cols),
     columns=['a', 'b', 'c'])

st.line_chart(chart_data)


st.header("Map", divider='blue')
map_data = pd.DataFrame(
    np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
    columns=['lat', 'lon'])

st.map(map_data)

st.header("Widget", divider="blue")

x = st.slider('x')
st.write(x, 'squared is', x * x)