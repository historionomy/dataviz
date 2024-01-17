import streamlit as st
import os
import snowflake.connector
import pandas as pd
import geopandas as gpd
import plotly.express as px

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

content_translations = {
    "EN": {
        "title" : "Historionomy Data Visualization App",
        "intro_title" : "What is historionomy ?",
        "intro_content" : """
Historionomy is another way of reading History, and thereby of reading the world.

In its prospective aspect, it is not about divining or approaching History as a mystical or teleological phenomenon; it is not a question of giving an ultimate meaning to history, but simply of observing how it unfolds, presenting structural effects, the 'patterns' or 'cycles' or 'historical models', which must be analyzed as the product of underlying laws.

The approach to identifying these historical patterns is essentially comparative, because comparatism is an extremely useful tool in sciences where controlled experimentation is impossible (for example, in astronomy) and where only the multiplicity of recorded examples allows for the isolation of variables, the establishment of categories, and the differentiation between what is determinant and what is negligible.
""",
        "map_title" : "Historionomy World Map",
        "map_content" : "This map illustrates the situation of each country in the current historionomic process of nation-states.",
        "resources_title" : "Resources and links",
        "resources_content" : """
<a href="http://historionomie.net">Historionomy official site</a>
<a href="http://historionomie.canalblog.com">Philippe Fabry's old blog</a>
<a href="https://www.youtube.com/@PhilippeFabry">Historionomy Youtube chain (in english)</a>
<a href="https://www.youtube.com/redirect?event=channel_description&redir_token=QUFFLUhqbUY3Qm05RFhZeWNWREpsWk1fd1Bub2JFdHhQUXxBQ3Jtc0tuYS1zSTRJYTNodjRwSnBvaWMwcjFZRDdhNUlKTDhHclhpUFluMHlPSmJ2RmJ1dTg4SGRhdzdLc0RuWXlrRmFFdDltWkpmemFRNlpyOWpOSFY2RmV0MWwzOHVaUXBBNFZZRXVDMFFsMUNWVGhwUUdTQQ&q=https%3A%2F%2Fwww.twitter.com%2FHistorionome">Philippe Fabry's Twitter/X account</a>
<a href="https://www.youtube.com/redirect?event=channel_description&redir_token=QUFFLUhqbjNHYWNqdjIyY0dOQTl3Z1Z6a210Uk13VkxSQXxBQ3Jtc0trVTBxXzJfbkNUeE9nNUMxOVdZQzEtbTBOU2lhWlA4a2ZtOFZlSWpSemx2WC1JbXVJMzR1d3lOVVRZSklPRURmNzBoU3ZpOER1dmJndUt0Unl0SW83c0lZQkZDWURmLUU0dmE0bFY1Q1Q2dmlrM0dETQ&q=https%3A%2F%2Fwww.amazon.fr%2FPhilippe-Fabry%2Fe%2FB00KMY6LRA%3Fref%3Dsr_ntt_srch_lnk_2%26qid%3D1677943195%26sr%3D8-2">The books</a>
""",
    },
    "FR": {
        "title" : "Historionomie : infographies",
        "intro_title" : "Qu'est ce que l'historionomie ?",
        "intro_content" : """
L’historionomie est une autre façon de lire l'Histoire, et par là-même de lire le monde.

Dans son volet prospectif, il ne s'agit pas de faire de la divination ou d'aborder l'Histoire comme un phénomène mystique ou finaliste ; il n’est pas question de donner un sens ultime à l'histoire, simplement de constater comment elle se fait, présentant des effets structurels, les « schémas » ou « cycles » ou « modèles » historiques, que l’on doit analyser comme le produit de lois sous-jacentes.

La démarche pour identifier ces schémas historiques est essentiellement comparatiste, car le comparatisme est un outil extrêmement utile dans les sciences où l'expérience contrôlée est impossible (par exemple en astronomie) et où seule la multiplicité des exemples recensés permet d'isoler des variables, de dresser des catégories, de faire le tri entre le déterminant et le négligeable.
""",
        "map_title" : "Carte historionomique mondiale",
        "map_content" : "Cette carte illustre la situation de chaque pays dans le processus historionomique des états-nations à l'heure actuelle.",
        "resources_title" : "Ressources et liens",
        "resources_content" : """
<a href="http://historionomie.net">Site officiel de l'historionomie</a>
<a href="http://historionomie.canalblog.com">Ancien blog de Philippe Fabry</a>
<a href="https://www.youtube.com/@PhilippeFabry">Chaîne Youtube de l'historionomie (en français)</a>
<a href="https://www.youtube.com/redirect?event=channel_description&redir_token=QUFFLUhqbUY3Qm05RFhZeWNWREpsWk1fd1Bub2JFdHhQUXxBQ3Jtc0tuYS1zSTRJYTNodjRwSnBvaWMwcjFZRDdhNUlKTDhHclhpUFluMHlPSmJ2RmJ1dTg4SGRhdzdLc0RuWXlrRmFFdDltWkpmemFRNlpyOWpOSFY2RmV0MWwzOHVaUXBBNFZZRXVDMFFsMUNWVGhwUUdTQQ&q=https%3A%2F%2Fwww.twitter.com%2FHistorionome">Compte Twitter/X de Philippe Fabry</a>
<a href="https://www.youtube.com/redirect?event=channel_description&redir_token=QUFFLUhqbjNHYWNqdjIyY0dOQTl3Z1Z6a210Uk13VkxSQXxBQ3Jtc0trVTBxXzJfbkNUeE9nNUMxOVdZQzEtbTBOU2lhWlA4a2ZtOFZlSWpSemx2WC1JbXVJMzR1d3lOVVRZSklPRURmNzBoU3ZpOER1dmJndUt0Unl0SW83c0lZQkZDWURmLUU0dmE0bFY1Q1Q2dmlrM0dETQ&q=https%3A%2F%2Fwww.amazon.fr%2FPhilippe-Fabry%2Fe%2FB00KMY6LRA%3Fref%3Dsr_ntt_srch_lnk_2%26qid%3D1677943195%26sr%3D8-2">Les livres</a>
"""
    }
}

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

    introduction_tab, world_map_tab, resources_tab = st.tabs([
        language_content.get("intro_title", "Introduction Title"),
        language_content.get("map_title", "Map Title"),
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

    with resources_tab:

        st.header(language_content.get("resources_title", "Resources Title"))

        st.markdown(format('<div class="word-wrap">%s</div>' % language_content.get("resources_content", "Lorem Ipsum")), unsafe_allow_html=True)
