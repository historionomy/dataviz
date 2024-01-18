import streamlit as st
import os
import snowflake.connector
import pandas as pd
import geopandas as gpd
import plotly.express as px
from PIL import Image
from text_content import content_translations
import io

def create_db_connection():

    # Connect to Snowflake
    ctx = snowflake.connector.connect(
        user = st.secrets["db_username"],
        password = st.secrets["db_password"],
        account = st.secrets["db_account"],
        warehouse = st.secrets["db_warehouse"],
        database = st.secrets["db_name"],
        schema = st.secrets["db_schema"],
        role = st.secrets["db_role"],
    )

    return ctx

@st.cache_data()
def load_image():
    # Load historionomical stages image
    # Load your WebP image
    image_path = './historionomical_stages.webp'  # Replace with your image path
    webp_image = Image.open(image_path)

    # Convert the image to a format Streamlit can display (e.g., PNG)
    img_byte_arr = io.BytesIO()
    webp_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


@st.cache_data()
def load_world_map():
    # Load your GeoPandas DataFrame
    # Replace this with your GeoPandas DataFrame loading
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    # Convert the GeoPandas geometries to GeoJSON
    geojson = world.__geo_interface__

    ### Load historionomical data

    # First, countries' status
    raw_data = pd.read_csv(st.secrets["historionomy_data_source"], usecols=['alpha_3', 'stage', 'reboot', 'subEntities'], na_filter=False)

    # Second, extract legend
    legend = pd.read_csv(st.secrets["historionomy_legend_source"], usecols=['code', 'label_fr', 'label_en', 'baseColor', 'stripeColor'], na_filter=False)
    legend = legend[legend.code != ""]

    # Merge with the countries DataFrame
    data = raw_data.merge(legend, left_on='stage', right_on='code', how='left')
    data = data.drop('code', axis=1)

    world_merged = world.merge(data, left_on='iso_a3', right_on="alpha_3", how='left')

    # Default color for other countries
    world_merged['baseColor'].fillna('lightgrey', inplace=True)
    world_merged.loc[pd.isna(world_merged['stripeColor']), 'stripeColor'] = ''
    world_merged['stripe'] = world_merged['stripeColor'] != ''
    world_merged.loc[world_merged['stripeColor'] == '', 'stripeColor'] = '#00000000'

    # histo_stages = legend['code']

    # Color Scale
    color_scale = {
        "FR": dict(zip(legend['label_fr'], legend['baseColor'])),
        "EN": dict(zip(legend['label_en'], legend['baseColor']))
    }

    return world_merged, geojson, color_scale, legend

def get_translation(locale):
    return content_translations.get(locale, {})

# Create a Plotly figure
@st.cache_data()
def create_map(_world_merged, geojson, color_scale, legend, language):

    fig = px.choropleth(_world_merged, geojson=geojson, locations=_world_merged.index, 
                    color=languages_map_labels[language]['label_column'], 
                    color_discrete_map=color_scale[language],
                    labels={languages_map_labels[language]['label_column']:languages_map_labels[language]['legend_name']},
                    category_orders={languages_map_labels[language]['label_column']: legend[languages_map_labels[language]['label_column']]},
                    projection='natural earth')

    return fig

# Capture click events
@st.cache_data()
def get_click_data():
    return {}

languages_map_labels = {
    "FR" : {
        "label_column" : "label_fr",
        "legend_name" : "stade historionomique"
    },
    "EN" : {
        "label_column" : "label_en",
        "legend_name" : "historionomical stage"
    }
}

# Custom CSS to force word wrap
st.markdown("""
    <style>
    .word-wrap {
        word-wrap: break-word;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize the session state for selected_language
if 'selected_language' not in st.session_state:
    st.session_state['selected_language'] = list(content_translations.keys())[0]

# Callback function to capture click data
def record_click(trace, points, selector):
    click_data['clicked_point'] = points.point_inds

# st.title(language_content.get("title", "Default Title"))

world_merged, geojson, color_scale, legend = load_world_map()

historionomical_stages_img = load_image()

with st.container():

    top_menu = st.columns(3)
    with top_menu[0]:
        st.session_state['selected_language'] = st.selectbox("Language", options=list(content_translations.keys()))

    language_content = get_translation(st.session_state['selected_language'])

    st.header(language_content.get("title", "Default Title"))

    # Create a Plotly figure
    fig = create_map(world_merged, geojson, color_scale, legend, st.session_state['selected_language'])

    # Add click callback to the plot
    for trace in fig.data:
        trace.on_click(record_click)

    click_data = get_click_data()

    introduction_tab, world_map_tab, histo_stages_tab, resources_tab = st.tabs([
        language_content.get("intro_title", "Introduction Title"),
        language_content.get("map_title", "Map Title"),
        language_content.get("stages_title", "Stages Title"),
        language_content.get("resources_title", "Resources Title"),
    ])

    with introduction_tab:

        st.header(language_content.get("intro_title", "Introduction Title"))

        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("intro_content", "Lorem Ipsum")), unsafe_allow_html=True)

    with world_map_tab:

        st.header(language_content.get("map_title", "Map Title"))

        # st.text(language_content.get("map_content", "Lorem Ipsum"))
        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("map_content", "Lorem Ipsum")), unsafe_allow_html=True)

        # Display the figure in Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # Display captured data
        if 'clicked_point' in click_data:
            clicked_index = click_data['clicked_point'][0]
            country_data = world_merged.iloc[clicked_index]
            st.write(f"You clicked on: {country_data['name']}")

    with histo_stages_tab:

        st.header(language_content.get("stages_title", "Introduction Title"))

        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("stages_content", "Lorem Ipsum")), unsafe_allow_html=True)

        # Display the image in Streamlit
        st.image(historionomical_stages_img, use_column_width=True)

        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("stages_description", "Lorem Ipsum")), unsafe_allow_html=True)

    with resources_tab:

        st.header(language_content.get("resources_title", "Resources Title"))

        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("resources_content", "Lorem Ipsum")), unsafe_allow_html=True)
