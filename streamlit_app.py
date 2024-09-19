import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os
from sklearn . preprocessing import MinMaxScaler

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
page = st.sidebar.radio('Choose a page', ['Rent Price Trends', 'General Rental Facts', 'Salary Rent Comparison', 'Salary Trends'])

if page == 'General Rental Facts':
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
    
elif page == 'Rent Price Trends':
    st.title('Rent Price Trends Over Years')
    
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
        fig.update_xaxes(tickfont=dict(color='black', size=16))
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
    scaler_salary = MinMaxScaler()
    scaler_rent = MinMaxScaler()
    merged_data['Gross Salary scaled'] = scaler_salary.fit_transform(merged_data[['Gross Salary']])
    merged_data['Total AVG Price scaled'] = scaler_rent.fit_transform(merged_data[['Total AVG Price']])
    # Select region for comparison
    regions = merged_data['Region'].unique()
    selected_region = st.selectbox('Select a region', regions)

    # Filter data for selected region
    region_data = merged_data[merged_data['Region'] == selected_region]
    region_data_scaled = region_data.groupby('Year').agg({'Total AVG Price scaled': 'mean', 'Gross Salary scaled': 'mean'}).reset_index()
    region_data = region_data.groupby('Year').agg({'Total AVG Price': 'mean', 'Gross Salary': 'mean'}).reset_index()

    # Create line plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=region_data_scaled['Year'], y=region_data_scaled['Total AVG Price scaled'],
                             mode='lines+markers', name='Average Rent'))
    fig.add_trace(go.Scatter(x=region_data_scaled['Year'], y=region_data_scaled['Gross Salary scaled'],
                             mode='lines+markers', name='Average Salary'))
    fig.update_xaxes(tickfont=dict(color='black', size=16))
    fig.update_yaxes(tickfont=dict(color='black', size=14))
    fig.update_layout(
        title=dict(text=f'Rent vs Salary Trends in {selected_region}', font=dict(size=20)),
            title_x=0.05,
        xaxis_title='Year',
        yaxis_title='Amount (CHF)',
        xaxis_title_font=dict(color='black', size=20),
        yaxis_title_font=dict(color='black', size=20), 
        legend_title='Metric',
        plot_bgcolor='rgba(255,255,255,0.8)',
        paper_bgcolor='rgba(255,255,255,0.8)'
    )

    st.plotly_chart(fig)

    start_year = region_data['Year'].min()
    end_year = region_data['Year'].max()
    rent_increase = (region_data.loc[region_data['Year'] == end_year, 'Total AVG Price'].values[0] /
                     region_data.loc[region_data['Year'] == start_year, 'Total AVG Price'].values[0] - 1) * 100
    salary_increase = (region_data.loc[region_data['Year'] == end_year, 'Gross Salary'].values[0] /
                       region_data.loc[region_data['Year'] == start_year, 'Gross Salary'].values[0] - 1) * 100

    # Define the colors based on positive or negative growth
    rent_color = 'green' if rent_increase > 0 else 'red'
    salary_color = 'green' if salary_increase > 0 else 'red'

    # Format the output using Streamlit's markdown with rich text and emoji/icons
    st.markdown(f"""
        <div style="background-color: rgba(255, 255, 255, 0.8); padding: 20px; border-radius: 10px; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);">
            <h3 style="text-align:left;">Rent vs Salary Increase (from {start_year} to {end_year})</h3>       
            <p style="font-size: 18px;">
                🏠 <strong>Rent Increase:</strong> 
                <span style="color:{rent_color}; font-weight:bold;">{rent_increase:.2f}%</span>  
            </p>      
            <p style="font-size: 18px;">
                💼 <strong>Salary Increase:</strong> 
                <span style="color:{salary_color}; font-weight:bold;">{salary_increase:.2f}%</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

elif page == 'Salary Trends':
    st.title('Salary Trends Across Regions')

    # Group salary data by year and region
    #salary_trends = salary_data.groupby(['Year', 'Region'])['Gross Salary'].mean().reset_index()

    # Create line plot for all regions
    fig = px.line(salary_data, x='Year', y='Gross Salary', color='Region')

    # Shorten legend names
    short_names = {
        'Switzerland': 'Switzerland',
        'Région lémanique (Genf, Waadt, Wallis)': 'Lémanique',
        'Espace Mittelland (Bern, Fribourg, Jura, Neuenburg, Solothurn)': 'Mittelland',
        'Northwestern Switzerland (Aargau, Baselland, Basel Stadt)': 'Northwestern',
        'Zurich': 'Zurich',
        'Eastern Switzerland (Appenzell A.Rh, Appenzell I.Rh, Glarus, Graubünden, St. Gallen, Schaffhausen, Thurgau)': 'Eastern',
        'Central Switzerland (Luzern, Nidwalden, Obwalden, Schwyz, Uri, Zug)': 'Central',
        'Tessin': 'Tessin'
    }

    # Update legend labels
    fig.for_each_trace(lambda trace: trace.update(name=short_names.get(trace.name, trace.name)))


    fig.update_xaxes(tickfont=dict(color='black', size=16))
    fig.update_yaxes(tickfont=dict(color='black', size=14))
    fig.update_layout(
        title=dict(text='Salary Trends Across Regions', font=dict(size=20)),
        title_x = 0.38,
        xaxis_title='Year',
        yaxis_title='Gross Salary (CHF)',
        xaxis_title_font=dict(color='black', size=20),
        yaxis_title_font=dict(color='black', size=20), 
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



    html_code = f"""
            <div style="background-color: rgba(251, 251, 251, 0.8); padding: 5px; border-radius: 3px;">
                <h2>Salary increases from {start_year} to {end_year} by region:</h2>
            </div>
            """

    # Render HTML in Streamlit
    st.markdown(html_code, unsafe_allow_html=True)
    #st.title(f"Salary increases from {start_year} to {end_year} by region:")
    st.dataframe(salary_increases_df.style.format({'Increase': '{:.2f}%'}))

# Run the Streamlit app
if __name__ == '__main__':
    st.sidebar.info('Navigate through different analyses using the radio buttons above.')
    st.sidebar.write('This app provides an interactive exploration of Swiss rental prices across different cantons and years.')