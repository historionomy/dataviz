import streamlit as st
import os
import yaml
import snowflake.connector
import pandas as pd
import geopandas as gpd
import plotly.express as px
from PIL import Image
from text_content import content_translations
from backend import login, load_data, load_data_debug
from history_chart import history_chart
import io
import re
# import fsspec
from io import BytesIO
import requests
import zipfile

# MODE = "debug"
MODE = "run"

backend_tables = [
    "countries",
    "legend",
    "labels",
    "stages",
    "koinons",
    "history"
]

owid_datasets = {
    "literacy": "cross-country-literacy-rates",
    "gdp" : "gdp-per-capita-penn-world-table",
    "urbanization" : "long-term-urban-population-region",
    "gov" : "historical-gov-spending-gdp"
}

# Load markdown content
def load_markdown_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    return content

# Display mardown with images included
def st_markdown(markdown_string):
    parts = re.split(r"!\[(.*?)\]\((.*?)\)", markdown_string)
    for i, part in enumerate(parts):
        if i % 3 == 0:
            st.markdown(part, unsafe_allow_html=True)
        elif i % 3 == 1:
            title = part
        else:
            # Center the image with HTML and CSS
            cols = st.columns([1, 4, 1])
            custom_width = 1000
            if "archaique" in part:
                custom_width = 600
            if "anthropologie" in part:
                custom_width = 800
            if "europe" in part:
                custom_width = 600
            with cols[1]:
                st.image(part, width=custom_width)  # Add caption if you want -> , caption=title)

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
def load_image(mode):
    # Load historionomical stages image

    if mode != "debug":
        # Load your WebP image
        image_path = './historionomical_stages.webp'  # Replace with your image path
        webp_image = Image.open(image_path)

        # Convert the image to a format Streamlit can display (e.g., PNG)
        img_byte_arr = io.BytesIO()
        webp_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        return img_byte_arr
    
    else:
        return "debug"


@st.cache_data(ttl=3600)
def load_world_map(mode):
    # Load your GeoPandas DataFrame
    if mode != "debug":

        zip_file_path = "assets/ne_110m_admin_0_countries.zip"

        # Step 1: Extract the contents of the ZIP file
        extract_path = "natural_earth_data"  # Local directory to extract the data
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # Step 2: Find the .shp file inside the extracted folder
        # Assuming the .shp file is the main file you want to load with GeoPandas
        for file_name in os.listdir(extract_path):
            if file_name.endswith(".shp"):
                shapefile_path = os.path.join(extract_path, file_name)
                break

        # Step 3: Load the shapefile into a GeoDataFrame
        world = gpd.read_file(shapefile_path)

        # Reset some failed data in dataset
        # Set ISO_A3 to 'FRA' where SOVEREIGNT is 'France'
        world.loc[world['SOVEREIGNT'] == 'France', 'ISO_A3'] = 'FRA'
        world.loc[world['SOVEREIGNT'] == 'Norway', 'ISO_A3'] = 'NOR'

        # Convert the GeoPandas geometries to GeoJSON
        geojson = world.__geo_interface__

        ### Load historionomical data

        # First, countries' status
        raw_data = pd.read_csv(st.secrets["historionomy_data_source"], usecols=['alpha_3', 'stage', 'reboot', 'subEntities'], na_filter=False)

        # Second, extract legend
        legend = pd.read_csv(st.secrets["historionomy_legend_source"], usecols=['code', 'label_fr', 'label_en', 'color', 'stripeColor'], na_filter=False)
        legend = legend[legend.code != ""]

        # Merge with the countries DataFrame
        data = raw_data.merge(legend, left_on='stage', right_on='code', how='left')
        data = data.drop('code', axis=1)

        world_merged = world.merge(data, left_on='ISO_A3', right_on="alpha_3", how='left')

        # Default color for other countries
        world_merged['color'].fillna('lightgrey', inplace=True)
        world_merged.loc[pd.isna(world_merged['stripeColor']), 'stripeColor'] = ''
        world_merged['stripe'] = world_merged['stripeColor'] != ''
        world_merged.loc[world_merged['stripeColor'] == '', 'stripeColor'] = '#00000000'

        # Color Scale
        color_scale = {
            "FR": dict(zip(legend['label_fr'], legend['color'])),
            "EN": dict(zip(legend['label_en'], legend['color']))
        }

        return world_merged, geojson, color_scale, legend

    else:
        return "debug"

def get_translation(locale):
    return content_translations.get(locale, {})

# Create a Plotly figure
@st.cache_data(ttl=3600)
def create_map(mode, _world_merged, geojson, color_scale, legend, language):

    if mode != "debug":
        fig = px.choropleth(_world_merged, geojson=geojson, locations=_world_merged.index, 
                        color=languages_map_labels[language]['label_column'], 
                        color_discrete_map=color_scale[language],
                        labels={languages_map_labels[language]['label_column']:languages_map_labels[language]['legend_name']},
                        category_orders={languages_map_labels[language]['label_column']: legend[languages_map_labels[language]['label_column']]},
                        projection='natural earth')

        return fig
    else:
        return "debug"
    
# Collect backend data
@st.cache_data(ttl=3600)
def load_backend_data():

    backend_data = {}
    for table in backend_tables:
        if MODE == "debug":
            backend_data[table] = load_data_debug(table)
        else:
            backend_data[table] = load_data(table)

    for table_id, table_name in owid_datasets.items():
        if MODE == "debug":
            backend_data[table_id] = load_data_debug(table_name)
        else:
            backend_data[table_id] = load_data(table_id)
        backend_data[table_id].columns.values[3] = table_id + "_data"

    # customize history data
    num_records = len(backend_data['history'])

    num_countries = (num_records - 1) // 4
    print(f"Nb countries : {num_countries}")

    history_dataframes = {}

    # get list of country codes
    all_country_codes = backend_data['countries']['alpha_3'].dropna().tolist()
    all_country_codes = [
        str(ctry) for ctry in all_country_codes if (str(ctry) != "Modèle" and str(ctry) is not None)
    ]

    # for i in range(num_countries):
    for j in range(len(backend_data['history'])):
        if backend_data['history'].iloc[j] is not None:
            i = j - 1
            if (i + 3) < len(backend_data['history']):
                country_code = backend_data['history'].iloc[i+1]['alpha_3']
                country_region = backend_data['history'].iloc[i+1]['region']
                country_age = backend_data['history'].iloc[i+1]['age']
                country_famille = backend_data['history'].iloc[i+1]['famille']
                if country_code is not None:
                    if country_code in all_country_codes:
                        year_start = backend_data['history'].iloc[i+2, 5:].tolist()
                        year_finish = backend_data['history'].iloc[i+3, 5:].tolist()
                        status = backend_data['history'].iloc[0, 5:].tolist()
                        comment = backend_data['history'].iloc[i+4, 5:].tolist()
                        history_status = pd.DataFrame({"year_start": year_start, "year_finish": year_finish,"status": status})
                        history_status['country'] = country_code
                        history_status['region'] = country_region
                        history_status['age'] = country_age
                        history_status['family'] = country_famille
                        history_status['comment'] = comment
                        history_status['year_start'] = pd.to_numeric(history_status['year_start'], errors='coerce')
                        history_status['year_finish'] = pd.to_numeric(history_status['year_finish'], errors='coerce')
                        history_status = history_status.dropna(subset=['year_start', 'status'])
                        history_status['year_finish'] = history_status['year_finish'].fillna(2024)
                        history_status = history_status.reset_index(drop=True)
                        history_status['year_start'] = history_status['year_start'].astype(int)
                        history_status['year_finish'] = history_status['year_finish'].astype(int)
                        history_status = history_status.sort_values(by='year_start', ascending=True).reset_index(drop=True)
                        history_dataframes[country_code] = history_status

    stats_dataframes = {}
    for table_id in owid_datasets.keys():
        stats_dataframes[table_id] = {
            code: group[['year', table_id + "_data"]].reset_index(drop=True) 
            for code, group in backend_data[table_id].groupby('code')
        }

    return backend_data, history_dataframes, stats_dataframes

# Capture click events
@st.cache_data()
def get_click_data():
    return {}

languages_map_labels = {
    "FR" : {
        "label_column" : "label_fr",
        "legend_name" : "stade historionomique",
        "x_label" : "année",
        "y_label" : "pays",
        "timeline_chart_title" : "Stade historionomique par pays et par année",
        "status": "statut",
        "year": "durée",
        "comment": "notes",
        "country" : "pays",
        "year_display": "année",
        "timeline_display_label": "alignement des parcours",
        "owid_data_display_label": "métrique",
        "country_selection_label": "choisir les pays",
        "all_countries_selection_label": "tous les pays",
        "region_selection_label": "choisir les régions",
        "family_selection_label": "choisir les types familiaux",
        "age_selection_label": "choisir l'âge historionomique",
        "country_search_label" : "chercher pays",
        "relative_status_label" : "aligner les parcours sur l'étape",
        "order_courses_label" : "trier les pays selon cette étape",
        "absolute_display_mode_label" : "Absolu",
        "relative_display_mode_label" : "Relatif",
        "stats_year_label" : "année",
        "stats_title" : {
            "none" : {
                "label": "aucun"
            },
            "gov" : {
                "title" : "Dépenses publiques en pourcentage du PIB",
                "label" : "Dep. gouv. percent PIB"
            },
            "literacy" : {
                "title" : "Taux d'alphabétisation",
                "label" : "percent PIB"
            },
            "gdp" : {
                "title" : "PIB/habitant en $ PPA corrigé de l'inflation",
                "label" : "PIB/hab PPA"
            },
            "urbanization" : {
                "title" : "Taux d'urbanisation",
                "label" : "Taux d'urbanisation"
            }
        }
    },
    "EN" : {
        "label_column" : "label_en",
        "legend_name" : "historionomical stage",
        "x_label" : "year",
        "y_label" : "country",
        "timeline_chart_title" : "Historionomical stage by year and country",
        "status" : "status",
        "year" : "duration",
        "comment": "comment",
        "country" : "country",
        "year_display": "year",
        "timeline_display_label": "courses chronological alignment",
        "owid_data_display_label": "metric",
        "country_selection_label": "choose countries",
        "all_countries_selection_label": "all countries",
        "region_selection_label": "choose regions",
        "family_selection_label": "choose family types",
        "age_selection_label": "choose historionomic age",
        "country_search_label" : "search country",
        "relative_status_label" : "Align courses on status",
        "order_courses_label" : "Sort countries on this status",
        "absolute_display_mode_label" : "Absolute",
        "relative_display_mode_label" : "Relative",
        "stats_year_label" : "year",
        "stats_title" : {
            "none" : {
                "label": "none"
            },
            "gov" : {
                "title" : "Government spending in pct of GDP",
                "label" : "Gov. spend. percent GDP"
            },
            "literacy" : {
                "title" : "Literacy rate",
                "label" : "Literacy rate"
            },
            "gdp" : {
                "title" : "GDP PPA per capita (constant $)",
                "label" : "GDP PPA per capita"
            },
            "urbanization" : {
                "title" : "Urbanization rate",
                "label" : "Urbanization rate"
            }
        }
    }
}

#############
# APP START #
#############

st.set_page_config(layout="centered")

### DATA LOADING AND PREPROCESSING

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

### load data
if MODE != "debug":

    world_merged, geojson, color_scale, legend = load_world_map(MODE)

    historionomical_stages_img = load_image(MODE)

### load backend data
backend_data, history_data, stats_data = load_backend_data()

stats_data = {
    mtr: {
        k: v for k, v in dat.items() if k in history_data.keys()
    } for mtr, dat in stats_data.items()
}

### extra data file for translation of metada
data_file = "data.yml"

custom_data_content = {}
with open(data_file, "r") as file:
    custom_data_content = yaml.load(file, Loader=yaml.FullLoader)

for lang in ['FR', 'EN']:
    for custom_dataset in ['region', 'family_type', 'alpha_3_name_mapping']:
        languages_map_labels[lang][custom_dataset] =  custom_data_content[custom_dataset].get(lang, {})

### extract legend data
legend_data = backend_data['labels'][['code', 'label_fr', 'label_en', 'color', 'stripecolor']]
legend_data = legend_data[legend_data.code != ""]

### DRAWING FRONTEND

# Create a top menu
extra_top_menu = st.columns(3)

with extra_top_menu[2]:
    # Simulate a popup for login
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        with st.container():
            with st.expander("Login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Login"):
                    token, error = login(username, password)
                    if error:
                        st.error(f"Login failed: {error}")
                    else:
                        st.session_state['logged_in'] = True
                        st.session_state['token'] = token
                        st.session_state['username'] = username
                        st.success("Logged in successfully!")

    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        username = st.session_state.get("username", "Undefined user")
        st.write(f"Logged in as {username}")

with st.container():

    top_menu = st.columns(3)
    with top_menu[0]:
        st.session_state['selected_language'] = st.selectbox("Language", options=list(content_translations.keys()))

    language_content = get_translation(st.session_state['selected_language'])

    st.header(language_content.get("title", "Default Title"))

    if MODE != "debug":
        # Create a Plotly figure
        fig = create_map(MODE, world_merged, geojson, color_scale, legend, st.session_state['selected_language'])

        # Add click callback to the plot
        for trace in fig.data:
            trace.on_click(record_click)

        click_data = get_click_data()

    # Create main tabs
    introduction_tab, world_map_tab, histo_stages_tab, data_tab, extra_tab, resources_tab = st.tabs([
        language_content.get("intro_tab", "Introduction Title"),
        language_content.get("map_tab", "Map Title"),
        language_content.get("stages_tab", "Stages Title"),
        language_content.get("data_tab", "Extra Title"),
        language_content.get("extra_tab", "Data Title"),
        language_content.get("resources_tab", "Resources Title"),
    ])

    with introduction_tab:

        st.header(language_content.get("intro_title", "Introduction Title"))

        # st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("intro_content", "Lorem Ipsum")), unsafe_allow_html=True)
        
        # Get markdown content
        markdown_content = load_markdown_file(f"text_content/intro_{st.session_state['selected_language']}.md")
        # Display the markdown content in the app
        # st.markdown(markdown_content, unsafe_allow_html=True)
        st_markdown(markdown_content)

    with world_map_tab:

        st.header(language_content.get("map_title", "Map Title"))

        # st.text(language_content.get("map_content", "Lorem Ipsum"))
        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("map_content", "Lorem Ipsum")), unsafe_allow_html=True)

        if MODE != "debug":
            # Display the figure in Streamlit
            st.plotly_chart(fig, use_container_width=True)

            # Display captured data
            if 'clicked_point' in click_data:
                clicked_index = click_data['clicked_point'][0]
                country_data = world_merged.iloc[clicked_index]
                st.write(f"You clicked on: {country_data['name']}")

    with data_tab:

        st.header(language_content.get("data_title", "Data Title"))

        history_chart(history_data, legend_data, stats_data, languages_map_labels)

        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("data_content", "Lorem Ipsum")), unsafe_allow_html=True)

    with extra_tab:

        st.header(language_content.get("extra_title", "Extra Title"))

        # Get markdown content
        markdown_content = load_markdown_file(f"text_content/extra_models_{st.session_state['selected_language']}.md")
        # Display the markdown content in the app
        # st.markdown(markdown_content, unsafe_allow_html=True)
        st_markdown(markdown_content)

    with histo_stages_tab:

        st.header(language_content.get("stages_title", "Introduction Title"))

        # st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("stages_content", "Lorem Ipsum")), unsafe_allow_html=True)

        # if MODE != "debug":
        #     # Display the image in Streamlit
        #     st.image(historionomical_stages_img, use_column_width=True)

        # st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("stages_description", "Lorem Ipsum")), unsafe_allow_html=True)

        # Get markdown content
        markdown_content = load_markdown_file(f"text_content/anthropo_{st.session_state['selected_language']}.md")
        # Display the markdown content in the app
        # st.markdown(markdown_content, unsafe_allow_html=True)
        st_markdown(markdown_content)


    with resources_tab:

        st.header(language_content.get("resources_title", "Resources Title"))

        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("resources_content", "Lorem Ipsum")), unsafe_allow_html=True)
