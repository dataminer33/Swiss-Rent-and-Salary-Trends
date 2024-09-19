import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os

# Set page config for a more professional look
st.set_page_config(page_title="Swiss Rental Price Analysis", layout="wide", initial_sidebar_state="expanded")

# Function to encode the image
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Set background image from local file
def set_bg_hack(main_bg):
    '''
    A function to unpack an image from file and set as bg.
    Returns
    -------
    The background.
    '''
    # Check if the file exists
    if not os.path.exists(main_bg):
        st.error(f"Background image file not found: {main_bg}")
        return

    bin_str = get_base64_of_bin_file(main_bg)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
    }
    .css-1d391kg {
        background-color: rgba(251, 251, 251, 0.8);
    }
    .css-1lcbmhc {
        background-color: rgba(251, 251, 251, 0.8);
    }
    .css-18e3th9 {
        padding: 2rem 1rem;
        background-color: rgba(251, 251, 251, 0.8);
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .css-1y0tads {
        padding: 1rem;
        border-radius: 10px;
        background-color: rgba(251, 251, 251, 0.6);
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)


background_image_path = 'static/images/background.jpg'

# Apply the background
set_bg_hack(background_image_path)

# Load the rent data
@st.cache_data
def load_data():
    data = pd.read_excel('data/processed/miete_processed.xlsx')
    
    def to_float(x):
        if isinstance(x, str):
            x = ''.join(c for c in x if c.isdigit() or c == '.')
        return pd.to_numeric(x, errors='coerce')
    
    price_columns = [col for col in data.columns if col.startswith('Price') or col.startswith('Total AVG') or col.startswith('Intervall')]
    
    for col in price_columns:
        data[col] = data[col].apply(to_float)
    
    return data

# Load salary data
@st.cache_data
def load_salary_data():
    salary_data = pd.read_excel('data/processed/monthly_salary_processed.xlsx') 
    salary_data['Gross Salary'] = pd.to_numeric(salary_data['Gross Salary'])
    salary_data['Year'] = pd.to_numeric(salary_data['Year'])
    return salary_data

data = load_data()
salary_data = load_salary_data()

# Sidebar for navigation
st.sidebar.title('Navigation')
page = st.sidebar.radio('Choose a page', ['Price Trends', 'General Facts', 'Salary Rent Comparison', 'Salary Trends'])

if page == 'General Facts':
    st.title('Overview of Swiss Rental Prices 2010 - 2022')
    
    
    data_2019 = data[data['Year'] == 2019]
    data_2022 = data[data['Year'] == 2022]
    
    price_change = pd.merge(data_2019, data_2022, on='Kanton', suffixes=('_2019', '_2022'))
    price_change['Price_Change'] = price_change['Total AVG Price_2022'] - price_change['Total AVG Price_2019']
    price_change = price_change.sort_values('Price_Change', ascending=False)
    
    fig_price_change = px.bar(price_change, 
                              x='Kanton', 
                              y='Price_Change',
                              labels={'Price_Change': 'Price Change (CHF)', 'Kanton': 'Canton'},
                              color='Price_Change',
                              color_continuous_scale='RdBu_r')
    fig_price_change.update_xaxes(tickfont=dict(color='black', size=16))
    fig_price_change.update_yaxes(tickfont=dict(color='black', size=14))
    fig_price_change.update_layout(
        title=dict(text='Price Change from 2019 to 2022 by Canton', font=dict(size=20)),
        title_x = 0.32,
        xaxis_tickangle=45,
        xaxis_title_font=dict(color='black', size=20),
        yaxis_title_font=dict(color='black', size=20), 
        plot_bgcolor='rgba(255,255,255,0.8)',
        paper_bgcolor='rgba(255,255,255,0.8)'
    )
    st.plotly_chart(fig_price_change)

    highest = data.loc[data['Total AVG Price'].idxmax()]
    lowest = data.loc[data['Total AVG Price'].idxmin()]
        
    fig = go.Figure(data=[
        go.Bar(name='Highest', x=['Highest'], y=[highest['Total AVG Price']], text=[highest['Kanton']]),
        go.Bar(name='Lowest', x=['Lowest'], y=[lowest['Total AVG Price']], text=[lowest['Kanton']])
    ])

    fig.update_xaxes(tickfont=dict(color='black', size=16))
    fig.update_yaxes(tickfont=dict(color='black', size=14))
    fig.update_layout(
        title=dict(text='Highest vs Lowest Average Rent', font=dict(size=20)),
        title_x = 0.35,
        plot_bgcolor='rgba(255,255,255,0.8)',
        paper_bgcolor='rgba(255,255,255,0.8)'
    )

    fig.update_traces(textposition='outside')
    st.plotly_chart(fig)
    
    
    st.title('Descriptive Statistics')
    st.dataframe(data.describe().style.background_gradient(cmap='Blues'))
    
elif page == 'Price Trends':
    st.title('Price Trends Over Years')
    
    if 'Year' not in data.columns:
        st.error("The 'Year' column is missing from the data. Please ensure your dataset includes yearly information.")
    else:
        cantons = data['Kanton'].unique()
        years = sorted(data['Year'].unique())
        
        selected_cantons = st.multiselect('Select Cantons', cantons, default=cantons[:5])
        
        fig = go.Figure()
        for canton in selected_cantons:
            canton_data = data[data['Kanton'] == canton]
            fig.add_trace(go.Scatter(x=canton_data['Year'], y=canton_data['Total AVG Price'],
                                     mode='lines+markers', name=canton))
        fig.update_xaxes(tickangle=45,tickfont=dict(color='black', size=16))
        fig.update_yaxes(tickfont=dict(color='black', size=16))
        fig.update_layout(
            title=dict(text='Rental Price Trends by Canton', font=dict(size=20)),
            title_x=0.40,
            xaxis_title='Year',
            yaxis_title='Average Price (CHF)',
            xaxis_title_font=dict(color='black', size=20),
            yaxis_title_font=dict(color='black', size=20), 
            plot_bgcolor='rgba(255,255,255,0.8)',
            paper_bgcolor='rgba(255,255,255,0.8)',
        )
        
        st.plotly_chart(fig)

        st.subheader(' ')
        construction_periods = [col.replace('Price ', '') for col in data.columns if col.startswith('Price') and col != 'Total AVG Price']
        period_prices = data[[f'Price {period}' for period in construction_periods]].mean().sort_values(ascending=False)
        fig_construction = px.bar(x=period_prices.index, y=period_prices.values,
                              title='Average Rental Prices by Construction Period',
                              labels={'x': 'Construction Period', 'y': 'Average Price (CHF)'})
        fig_construction.update_xaxes(tickfont=dict(color='black', size=16))
        fig_construction.update_yaxes(tickfont=dict(color='black', size=14))
        fig_construction.update_layout(
            title=dict(text="Average Rental Prices by Construction Period", font=dict(size=20)),
            title_x=0.35,
            xaxis_title_font=dict(color='black', size=20),
            yaxis_title_font=dict(color='black', size=20), 
            plot_bgcolor='rgba(255,255,255,0.8)',
            paper_bgcolor='rgba(255,255,255,0.8)'
        )
        st.plotly_chart(fig_construction)


elif page == 'Salary Rent Comparison':
    st.title('Salary vs Rent Comparison')

    # Merge rent and salary data
    merged_data = pd.merge(data, salary_data, on=['Year', 'Region'])

    # Select region for comparison
    regions = merged_data['Region'].unique()
    selected_region = st.selectbox('Select a region', regions)

    # Filter data for selected region
    region_data = merged_data[merged_data['Region'] == selected_region]

    # Create line plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=region_data['Year'], y=region_data['Total AVG Price'],
                             mode='lines+markers', name='Average Rent'))
    fig.add_trace(go.Scatter(x=region_data['Year'], y=region_data['Gross Salary'],
                             mode='lines+markers', name='Average Salary'))

    fig.update_layout(
        title=f'Rent vs Salary Trends in {selected_region}',
        xaxis_title='Year',
        yaxis_title='Amount (CHF)',
        legend_title='Metric',
        plot_bgcolor='rgba(255,255,255,0.8)',
        paper_bgcolor='rgba(255,255,255,0.8)'
    )

    st.plotly_chart(fig)

    # Calculate and display percentage increases
    start_year = region_data['Year'].min()
    end_year = region_data['Year'].max()
    rent_increase = (region_data.loc[region_data['Year'] == end_year, 'Total AVG Price'].values[0] /
                     region_data.loc[region_data['Year'] == start_year, 'Total AVG Price'].values[0] - 1) * 100
    salary_increase = (region_data.loc[region_data['Year'] == end_year, 'Gross Salary'].values[0] /
                       region_data.loc[region_data['Year'] == start_year, 'Gross Salary'].values[0] - 1) * 100

    st.write(f"Rent increase from {start_year} to {end_year}: {rent_increase:.2f}%")
    st.write(f"Salary increase from {start_year} to {end_year}: {salary_increase:.2f}%")

elif page == 'Salary Trends':
    st.title('Salary Trends Across Regions')

    # Group salary data by year and region
    #salary_trends = salary_data.groupby(['Year', 'Region'])['Gross Salary'].mean().reset_index()

    # Create line plot for all regions
    fig = px.line(salary_data, x='Year', y='Gross Salary', color='Region',
                  title='Salary Trends Across Regions')

    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Gross Salary (CHF)',
        legend_title='Region',
        plot_bgcolor='rgba(255,255,255,0.8)',
        paper_bgcolor='rgba(255,255,255,0.8)'
    )

    st.plotly_chart(fig)

    # Calculate and display overall salary increase for each region
    start_year = salary_data['Year'].min()
    end_year = salary_data['Year'].max()

    salary_increases = []
    for region in salary_data['Region'].unique():
        region_data = salary_data[salary_data['Region'] == region]
        start_salary = region_data.loc[region_data['Year'] == start_year, 'Gross Salary'].values[0]
        end_salary = region_data.loc[region_data['Year'] == end_year, 'Gross Salary'].values[0]
        increase = (end_salary / start_salary - 1) * 100
        salary_increases.append({'Region': region, 'Increase': increase})

    salary_increases_df = pd.DataFrame(salary_increases)
    salary_increases_df = salary_increases_df.sort_values('Increase', ascending=False)

    st.write(f"Salary increases from {start_year} to {end_year} by region:")
    st.dataframe(salary_increases_df.style.format({'Increase': '{:.2f}%'}))

# Run the Streamlit app
if __name__ == '__main__':
    st.sidebar.info('Navigate through different analyses using the radio buttons above.')
    st.sidebar.write('This app provides an interactive exploration of Swiss rental prices across different cantons and years.')