import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import numpy as np

# Function to create a bar chart with absolute years
def create_absolute_year_chart(history_data, legend_data, language_labels):

    
    # print(domain)
    # status_color_scale = alt.Scale(domain=['A', 'B'], range=['#1f77b4', '#ff7f0e'])
    # legend = alt.Legend(title="Status", orient="right")
    # status_color_scale = alt.Scale(domain=domain, range=legend_range)
    # legend = alt.Legend(title="Status", orient="right")

    # List to store all individual charts
    # charts = []

    # all_data = pd.DataFrame({
    #     'country': [],
    #     'year': [],
    #     'status': []
    # })
    # Iterate over each dataframe
    # history_data = [

    # ]
    # data = history_data['FRA']
    # print(data)
    for country in history_data.keys():
        # history_data[country].dropna(subset="year")
        # history_data[country] = history_data[country].reset_index(drop=True)
        # print(country)
        nb_steps = len(history_data[country])
        # we will add an extra line of status at the end of the current country course, for display purposes (we want current status to be displayed *at the right* of the associated datetime)
        print(nb_steps)
        print(country)
        history_data[country]['year_display'] = history_data[country]['year_start']
        if nb_steps > 1:
            history_data[country] = history_data[country].sort_values(by='year_start', ascending=True)
            ending_status = pd.DataFrame({
                'country' : [country],
                'year_start' : history_data[country]['year_finish'].iloc[-1],
                'year_display' : history_data[country]['year_finish'].iloc[-1],
                'year_finish' : history_data[country]['year_finish'].iloc[-1] + 50,
                'status' : history_data[country]['status'].iloc[-1],
            })
            for i in range(1, nb_steps):
                # we replace year_start by the number of years since precedent status, for barchart display purposes
                # year_start[i] <- (year_start[i] - year_start[i-1]

                # First, calculate the index to modify directly since iloc[-i] and iloc[-i-1] refer to positions from the end
                index_to_modify = history_data[country].index[-i]
                index_to_copy_from = history_data[country].index[-i-1]

                diff = history_data[country]['year_start'].iloc[-i] - history_data[country]['year_start'].iloc[-i-1]
                if diff >= 0:
                    history_data[country].loc[index_to_modify, 'year_start'] = diff
                    # history_data[country]['year_start'].iloc[-i] = diff
                else :
                    history_data[country].loc[index_to_modify, 'year_start'] = 0
                    # history_data[country]['year_start'].iloc[-i] = 0

                # we shift the status of one line forward, for barchart display purposes

                # Now, use .loc to perform the assignment, thereby avoiding the warning and modifying the original DataFrame
                history_data[country].loc[index_to_modify, 'year_display'] = history_data[country].loc[index_to_copy_from, 'year_display']
                history_data[country].loc[index_to_modify, 'status'] = history_data[country].loc[index_to_copy_from, 'status']
                # history_data[country]['status'].iloc[-i] = history_data[country]['status'].iloc[-i-1]
                # history_data[country]['year_display'].iloc[-i] = history_data[country]['year_display'].iloc[-i-1]
                # history_data[country].loc[i, 'year'] = history_data[country].loc[i-1, 'year'] - (history_data[country].loc[i, 'year'] - history_data[country].loc[i-1, 'year'])
            # history_data
            # print(history_data[country])
            # first status set to 'BARBARIANS'
            first_index = history_data[country].index[0]
            history_data[country].loc[first_index, 'status'] = 'BARBARIANS'
            # history_data[country]['status'].iloc[0] = 'BARBARIANS'
            history_data[country].loc[first_index, 'year_display'] = 0
            # history_data[country]['year_display'].iloc[0] = 0
            # adding extra line at the end for display purposes
            history_data[country] = pd.concat([history_data[country], ending_status], ignore_index=True)

    history_data = {k:v for k,v in history_data.items() if len(v)>1}
    data = pd.concat(history_data.values(), ignore_index=True)
    # data = history_data['GBR']
    print(data)
    # data = data.loc[:10]
    # print('****************')
    # print(data)
    # data['year_start'] = pd.to_datetime(data['year_start'], format='%Y')
    # data['year_finish'] = pd.to_datetime(data['year_finish'], format='%Y')

    # print(data)

    # fig = px.timeline(data, x_start="year_start", x_end="year_finish", y="country", color="status", title="Project Timelines")

    # fig = px.bar(data, x="year_start", y="Task", color="Category", title="Project Timeline by Year")

    # # Generate a DataFrame where each row represents a year in the timeline for each task
    # timeline_data = []
    # for _, row in data.iterrows():
    #     for year in range(row["year_start"], row["year_finish"] + 1):
    #         timeline_data.append({"country": row["country"], "year": year, "status": row["status"]})


    # timeline_df = pd.DataFrame(timeline_data)
    # print(timeline_df)

    # Plotting with Plotly Express
    # fig = px.bar(timeline_df, x="year", y="country", color="status", title="Project Timeline by Year")

    print(data['year_start'])

    display_year_not_barbarians = data[data['status'] != 'BARBARIANS']['year_display'].tolist()

    min_time = min(display_year_not_barbarians) - 50
    max_time = max(display_year_not_barbarians) + 50

    # remap status to language label
    status_mapping = pd.Series(legend_data[language_labels['label_column']].values,index=legend_data['code']).to_dict()

    data['status'] = data['status'].map(status_mapping)

    # Define color scale and legend
    legend_data['code'] = legend_data['code'].map(status_mapping)
    domain = legend_data['code'].tolist()
    legend_range = legend_data['color'].tolist()

    print(domain)
    print(legend_range)
    color_map = {key: value for key, value in zip(domain, legend_range)}
    print(color_map)

    # rename columns for hover data consistency
    data.rename(columns={
        'status': language_labels['status'], 
        'year': language_labels['year'],
        'country': language_labels['country'],
        'year_display': language_labels['year_display'],
        }, inplace=True)


    fig = px.bar(data, 
                 x='year_start', 
                 y="country", 
                 color="status", 
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
    print(min_time)
    fig.update_layout(xaxis_range=[min_time,max_time])
    fig.update_layout(xaxis_title="year", yaxis_title="country")
    fig.update_layout(bargap=0.1)
    # fig.update_layout(height=300)


    # fig.update_layout(xaxis_title='Time', yaxis_title='Country', xaxis=dict(tickformat="%Y"), yaxis={'categoryorder':'total ascending'})

    # data = data.dropna(subset="year")
    # for i in range(1, len(data)):
    #     data.loc[i, 'year'] = data.loc[i-1, 'year'] - (data.loc[i, 'year'] - data.loc[i-1, 'year'])
    # print(data)
    # for country, df in history_data.items():
    #     df['country'] = country
    #     all_data = pd.concat(all_data)
    #     data = {
    #         'year': [2018, 2019, 2020, 2021],
    #         'status': ['NATIONAL_REVOLUTION_3', None, 'NATIONAL_REVOLUTION_6', np.nan]
    #     }
    #     domain = data['status']
    #     legend_range = ['#1f77b4', '#ff7f0e']
    #     df = pd.DataFrame(data)
    #     df = df.dropna(subset="status")
    #     data = pd.DataFrame({
    #         'category': ['A', 'A', 'B', 'B', 'C', 'C'],
    #         'sub_category': ['X', 'Y', 'X', 'Y', 'X', 'Y'],
    #         'value': [10, 20, 30, 40, 50, 60]
    #     })
        # Convert DataFrame to Altair chart
        # chart = alt.Chart(df).mark_bar().encode(
        #     x=alt.X(f'year:O', axis=alt.Axis(title='Year')),
        #     y=alt.Y(f'status:N', axis=alt.Axis(title='Status')),
        #     color=alt.Color(f'status:N', scale=status_color_scale, legend=legend),
        #     tooltip=['year', 'status']
        # ).properties(
        #     title=f'DataFrame {country}',
        #     width=300,
        #     height=300
        # )
    # chart = alt.Chart(data).mark_bar().encode(
    #     x='year:Q',
    #     y=alt.Y('country:N', axis=alt.Axis(title='Country')),
    #     color=alt.Color('status:N', scale=status_color_scale, legend=alt.Legend(title='Country'))
    # ).properties(
    #     width=600,
    #     height=300
    # )
    # chart = alt.Chart(data).mark_bar().encode(
    #     x='year:Q',
    #     y=alt.Y('country:N', axis=alt.Axis(title='Country')),
    #     color='status:N'
    # ).properties(
    #     width=600,
    #     height=300
    # )
        # charts.append(chart)
        # break

    # Concatenate all charts horizontally
    # combined_chart = alt.hconcat(*charts)

    return fig

# # Function to create a bar chart with aligned years based on selected status
# def create_aligned_year_chart(dataframes, selected_status, legend_data):
#     # Filter dataframes based on selected status
#     filtered_dataframes = [df[df['status'] == selected_status] for df in dataframes if selected_status in df['status'].unique()]

#     filtered_countries = {
#         country : country_data
#         for country, country_data in dataframes.items()
#         if selected_status in country_data['status'].unique()
#     }

#     domain = legend_data['code'].tolist()
#     range = legend_data['color'].tolist()

#     # List to store all individual charts
#     charts = []

#     # Iterate over each filtered dataframe
#     for country, df in filtered_countries.items():
#         df = df.dropna(subset="status")
#         # Determine the aligned year for the selected status
#         aligned_year = df['year'].iloc[0]

#         # Add a new column for aligned years
#         df['aligned_year'] = df['year'] - aligned_year

#         # Convert DataFrame to Altair chart
#         chart = alt.Chart(df).mark_bar().encode(
#             x=alt.X(f'aligned_year:O', axis=alt.Axis(title='Aligned Year')),
#             y=alt.Y(f'year:O', axis=alt.Axis(title='Year'), sort='descending'),
#             color=alt.Color(f'status:N', scale=alt.Scale(domain=domain, range=range), legend=None),
#             tooltip=['year', 'status']
#         ).properties(
#             title=f'DataFrame {country}',
#             width=300,
#             height=300
#         )
#         charts.append(chart)

#     # Concatenate all charts horizontally
#     combined_chart = alt.hconcat(*charts)

#     return combined_chart

# Main function to run the Streamlit app
def history_chart(history_data, legend_data, language_labels):

    # st.title('Comparison of Different Display Modes')

    # Top Menu :
    # select absolute / relative timeline
    # relative => choose a specific stage for relative display
    top_menu = st.columns(3)
    with top_menu[0]:
        timeline_type = st.selectbox("Sort By", options=["Absolute", "Relative"])
    if timeline_type == "Relative":
        relative_status = st.selectbox("Align courses on status", options=legend_data['code'].tolist())
    # # Sidebar to upload files
    # uploaded_files = st.sidebar.file_uploader("Upload CSV files", accept_multiple_files=True)

    # # List to store dataframes
    # dataframes = []

    # # Read uploaded files and store dataframes
    # for uploaded_file in uploaded_files:
    #     df = pd.read_csv(uploaded_file)
    #     dataframes.append(df)

    # Radio button to choose display mode
    # display_mode = st.sidebar.radio("Select Display Mode", ["Absolute Years", "Aligned Years"])

    # if dataframes:
    # st.write("Sample DataFrames:")
    # for country, df in history_data.items():
    #     st.write(f"Country {country}:")
        # st.write(df)

    # st.altair_chart(create_absolute_year_chart(history_data, legend_data), use_container_width=True)

    # st.write("Horizontal Bar Charts:")
    # if display_mode == "Absolute Years":
    # create_absolute_year_chart(history_data, legend_data)
    print(language_labels)
    st.plotly_chart(create_absolute_year_chart(history_data, legend_data, language_labels), use_container_width=True)
    #     # create_absolute_year_chart(history_data, legend_data)
    #     st.altair_chart(create_absolute_year_chart(history_data, legend_data), use_container_width=True)
    # elif display_mode == "Aligned Years":
    #     # Dropdown to select a status
    #     selected_status = st.sidebar.selectbox("Select Status", legend_data['code'])
    #     st.altair_chart(create_aligned_year_chart(history_data, legend_data, selected_status), use_container_width=True)
