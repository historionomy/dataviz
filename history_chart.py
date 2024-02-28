import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# IDs of OWID metrics
metrics = [
    "literacy",
    "gdp",
    "urbanization",
    "gov"
]

# Function to create a bar chart with absolute years
def create_year_chart(history_data, legend_data, stats_data, language_labels, mode, relative_status, metric):

    # we filter country datasets that are empty
    if len(history_data) > 0:

        max_display_length = 0
        for country in history_data.keys():

            # print(f"Loading histo data for {country}")
            nb_steps = len(history_data[country])

            # we will add an extra line of status at the end of the current country course, for display purposes (we want current status to be displayed *at the right* of the associated datetime)

            # "year_display" will be used for the 'hover data' of the chart
            history_data[country]['year_display'] = history_data[country]['year_start']

            # we need at least two steps to display something
            if nb_steps > 1:

                # we need to have the pivot status in the country dataset to display something - if we are in absolute mode, pivot status is BARBARIANS

                if (mode == "Absolute") or (relative_status in history_data[country]['status'].tolist()):

                    # if we are in relative mode, we will substract the year_start of the pivot status to starting year
                    country_offset = 0
                    if mode == "Relative":
                        country_offset = history_data[country].loc[history_data[country]['status'] == relative_status, 'year_start'].iloc[0]

                    # we sort all historionomical steps by ascending order of year_start, to avoid inconsistencies in the display
                    history_data[country] = history_data[country].sort_values(by='year_start', ascending=True)

                    # we concatenate an "ending_status" row at the end of the current country course, that will be used for display purposes
                    ending_status = pd.DataFrame({
                        'country' : [country],
                        'year_start' : history_data[country]['year_finish'].iloc[-1],
                        'year_display' : history_data[country]['year_start'].iloc[-1],
                        'year_finish' : history_data[country]['year_finish'].iloc[-1] + 50,
                        'status' : history_data[country]['status'].iloc[-1],
                    })
                    history_data[country] = pd.concat([history_data[country], ending_status], ignore_index=True)

                    # we compute the index of the pivot status in the current country course
                    pivot_index = 0
                    if mode == "Relative":
                        pivot_index = history_data[country][history_data[country]['status'] == relative_status].index[0]

                    for i in range(1, nb_steps + 1):
                        # we replace year_start by the number of years since precedent status, for barchart display purposes
                        # year_start[i] <- (year_start[i] - year_start[i-1]

                        # First, calculate the index to modify directly since iloc[-i] and iloc[-i-1] refer to positions from the end
                        index_to_modify = history_data[country].index[-i]
                        index_to_copy_from = history_data[country].index[-i-1]

                        diff = history_data[country]['year_start'].iloc[-i] - history_data[country]['year_start'].iloc[-i-1]
                        # we check that the difference between contiguous steps is positive to avoid problems
                        if diff >= 0:
                            if mode == "Relative":
                                # in "relative" display mode, the "year_start" needs to be NEGATIVE for steps BEFORE THE PIVOT STATUS, for display purposes, otherwise the oldest step will be displayed OVER the newest one before the pivot status
                                if country_offset >= history_data[country]['year_start'].iloc[-i]:
                                    diff = - diff
                            history_data[country].loc[index_to_modify, 'year_start'] = diff

                        # if difference between two contiguous steps is negative, there is a problem in the data, we force the difference to zero
                        else :
                            history_data[country].loc[index_to_modify, 'year_start'] = 0


                        # we shift the status of one line forward, for barchart display purposes

                        # Now, use .loc to perform the assignment, thereby avoiding the warning and modifying the original DataFrame
                        history_data[country].loc[index_to_modify, 'year_display'] = history_data[country].loc[index_to_copy_from, 'year_display']
                        history_data[country].loc[index_to_modify, 'status'] = history_data[country].loc[index_to_copy_from, 'status']

                    # first status set to 'BARBARIANS'
                    first_index = history_data[country].index[0]
                    history_data[country].loc[first_index, 'status'] = 'BARBARIANS'

                    # first year display to zero
                    history_data[country].loc[first_index, 'year_display'] = 0

                    # set offset if relative datetime
                    if mode == "Relative":
                        # print("Offsetting relative zero year")
                        # print(country_offset)
                        history_data[country].loc[first_index, 'year_start'] = history_data[country].loc[first_index, 'year_start'] - country_offset

                        last_index = history_data[country].index[-1]
                        last_year = history_data[country].loc[last_index, 'year_finish'] - country_offset

                        # we must compute the upper bound of the display window on-the-fly as the maximal last_year of ALL countries
                        max_display_length = max(max_display_length, last_year)
                        history_data[country].iloc[:pivot_index+1] = history_data[country].iloc[:pivot_index+1].iloc[::-1].values

                    # offsetting stats data
                    # print(f"Loading metric {metric} elements")
                    # print(stats_data[metric].keys())
                    if metric != "none":
                        if country in stats_data[metric].keys():
                            stats_data[metric][country]['absolute_year'] = stats_data[metric][country]['year']
                            stats_data[metric][country]['year'] = stats_data[metric][country]['year'] - country_offset

                            # add country column to stats_data
                            stats_data[metric][country]['code'] = country

        # we concatenate all historionomical courses for all countries as a single dataset for the bar chart
        history_data = {k:v for k,v in history_data.items() if len(v)>1}
        data = pd.concat(history_data.values(), ignore_index=True)

        # if a metric has been set, we do the same for OWID data for all countries
        owid_data = {}
        if metric != "none":
            stats_data = {k:v for k,v in stats_data[metric].items() if len(v)>1}

            if len(stats_data)>0:
                owid_data = pd.concat(stats_data.values(), ignore_index=True)

        # computing the display bounds depending on the display mode
        if mode == language_labels['absolute_display_mode_label']:
            display_year_not_barbarians = data[data['status'] != 'BARBARIANS']['year_display'].tolist()

            min_time = min(display_year_not_barbarians) - 50
            max_time = max(display_year_not_barbarians) + 50
        if mode == language_labels['relative_display_mode_label']:
            min_time = min(data['year_start'].tolist())
            max_time = max_display_length

        # remap status to language label
        status_mapping = pd.Series(legend_data[language_labels['label_column']].values,index=legend_data['code']).to_dict()

        data['status'] = data['status'].map(status_mapping)

        # Define color scale and legend
        legend_data['code'] = legend_data['code'].map(status_mapping)
        domain = legend_data['code'].tolist()
        legend_range = legend_data['color'].tolist()

        color_map = {key: value for key, value in zip(domain, legend_range)}

        # rename columns for hover data consistency
        data.rename(columns={
            'status': language_labels['status'], 
            'year': language_labels['year'],
            'country': language_labels['country'],
            'year_display': language_labels['year_display'],
            }, inplace=True)

        fig = px.bar(data, 
                    x='year_start', 
                    y=language_labels['country'], 
                    color=language_labels['status'], 
                    category_orders={language_labels['label_column']: legend_data[language_labels['label_column']]},
                    color_discrete_map = color_map,
                    orientation="h", 
                    title=language_labels['timeline_chart_title'],
                    hover_data = [
                        language_labels['country'], 
                        language_labels['status'], 
                        language_labels['year_display']
                        ],
                    labels={
                        'year_start': language_labels['x_label'],
                        language_labels['country']: language_labels['y_label']
                        }
                    )


        # Customize the layout
        fig.update_layout(xaxis_range=[min_time,max_time])
        fig.update_layout(xaxis_title="year", yaxis_title="country")
        fig.update_layout(bargap=0.1)

        fig2 = None

        if len(owid_data)>0:
            # rename columns for hover data consistency
            owid_data.rename(columns={
                'absolute_year': language_labels['year'],
                'year' : 'relative_year',
                'code' : language_labels['country'],
                metric + "_data": language_labels['stats_title'][metric]['label'],
                }, inplace=True)
            
            owid_data = owid_data.sort_values(by='relative_year')

            # figure of OWID statistics
            if metric != "none":
                fig2 = px.line(owid_data, x='relative_year', y= language_labels['stats_title'][metric]['label'], color=language_labels['country'], 
                    title=language_labels['stats_title'][metric]['title'],
                    labels={'relative_year': language_labels['stats_year_label']},
                    markers=True,
                    hover_data = [
                            language_labels['country'], 
                            language_labels['stats_title'][metric]['label'], 
                            language_labels['year']
                            ]
                    )

                fig2.update_layout(xaxis_range=[min_time,max_time])

        return fig, fig2

def history_chart(history_data, legend_data, stats_data, language_labels):

    language_labels = language_labels[st.session_state['selected_language']]

    # Top Menu :
    # select absolute / relative timeline
    # relative => choose a specific stage for relative display
    timeline_type_labels = [
        language_labels['absolute_display_mode_label'],
        language_labels['relative_display_mode_label'],
    ]
    top_menu = st.columns(3)
    with top_menu[0]:
        timeline_type = st.selectbox(language_labels["timeline_display_label"], options=timeline_type_labels)
        relative_status = "NATIONAL_REVOLUTION_1"
        if timeline_type == "Relative":
            status_options = legend_data['code'].dropna().tolist()
            status_options.remove("BARBARIANS")
            relative_status = st.selectbox(language_labels['relative_status_label'], options=status_options)

    metrics_labels = [
        language_labels['stats_title'][metric]["label"] for metric in metrics
    ]

    # select metrics from Our World In Data
    with top_menu[1]:
        chosen_metric = st.selectbox(language_labels["timeline_display_label"], options=metrics_labels)
        label2metrics = {
            v["label"]: k for k, v in language_labels['stats_title'].items()
        }
        chosen_metric = label2metrics[chosen_metric]

    # select countries to display among available countries
    available_countries = history_data.keys()
    selected_countries = []
    countries_checkboxes = {}
    select_all_countries = False
    with top_menu[2]:
        with st.expander(language_labels["country_selection_label"]):
            select_all_countries = st.checkbox(language_labels["country_selection_label"], value = True)
            country_search = st.text_input(language_labels["country_search_label"])
            filtered_countries = [
                country for country in available_countries if country.lower().startswith(country_search.lower())
            ]
            for filtered_country in filtered_countries:
                country_selection = st.checkbox(filtered_country, key=filtered_country)
                countries_checkboxes[filtered_country] = country_selection

    if not select_all_countries:
        selected_countries = [
            ctry for ctry, selected in countries_checkboxes.items() if selected
        ]
    else:
        selected_countries = available_countries

    history_data = {
        country: history_data[country] for country in selected_countries
    }

    if len(history_data)>0:
        fig, fig2 = create_year_chart(history_data, legend_data, stats_data, language_labels, timeline_type, relative_status, chosen_metric)
        if fig2 is not None:
            st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig, use_container_width=True)
