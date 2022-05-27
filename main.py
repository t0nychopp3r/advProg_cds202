import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.colors as mcolors
import streamlit as st
from PIL import Image
import time

DATA_PATH = os.path.join("MetroMapsEyeTracking", "all_fixation_data_cleaned_up_utf8.csv")
st.set_page_config(layout="wide")  # Page layout

# Load Page-Style from file (CSS)
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@st.cache  # Caching data that needs to be loaded
def load_data(nrows, encoding):  # Load data to dataframe and return it
    data = pd.read_csv(DATA_PATH, sep=';', encoding=encoding, nrows=nrows)
    return data


data = load_data(150000, 'utf-8')  # Load data from file

st.markdown('# Eye Tracking Dashboard')  # Title of webpage

# Page dropdown to display different content
page = st.selectbox("Choose your page", ["Scanpath visualization", "Scatterplot visualization"])

if page == "Scanpath visualization":  # Page with first visualization

    st.markdown('## Scanpath visualization')
    placeholderAnimationInfo = st.empty()
    placeholderPlot = st.empty()  # Placeholder for plot that gets inserted later

    # Figure of scanpath plot
    def loadScanpathPlot(stimuliFilter, personFilter, filtered_data):
        STIMULI_PATH = os.path.join("MetroMapsEyeTracking", "stimuli")
        stimuliImgPath = os.path.join(STIMULI_PATH, stimuliFilter)  # Get image of stimuli

        # Check if image exists
        if not os.path.exists(stimuliImgPath):
            st.error('Image not found!')
            return

        stimuliImg = plt.imread(stimuliImgPath)  # Load image of stimuli as plot "friendly" data

        # Get resolution of stimuli image (map)
        im = Image.open(stimuliImgPath)
        width, height = im.size
        extent = [0, width, height, 0]  # Setting axes size

        fig, ax = plt.subplots()
        ax.imshow(stimuliImg, extent=extent,
                  origin='upper')  # Image background of stimuli (map), origin='upper' to flip image
        ax.scatter(filtered_data["MappedFixationPointX"], filtered_data["MappedFixationPointY"],
                   s=85, c="red", edgecolors="lightgray", alpha=0.75)  # Plot of fixation points (c = color, alpha = transparency, s = size of dots)
        ax.xaxis.tick_top()  # Put x-axis on top
        rcParams['xtick.labelsize'] = 6  # x-axis labels font size
        rcParams['ytick.labelsize'] = 6  # y-axis labels font size
        plt.title(stimuliFilter + ' | person ' + str(personFilter), pad=25)  # Plot title (pad = padding)
        placeholderPlot.pyplot(fig)  # Replace Plot with new plot
        im.close()  # Close image

    # ---------------------------- Filter for scanpath plot ----------------------------- #
    with st.sidebar.container():  # All filter-commands to sidebar
        st.markdown('### Filter')
        highestUserIndex = []
        for i in data["user"].unique().tolist():
            userIndex = i.split('p')
            highestUserIndex.append(int(userIndex[1]))
        highestUserIndex = sorted(highestUserIndex)[-1]  # Get highest user index for slider size

        personFilter = st.slider('Person Filter', 1, highestUserIndex, 1)  # Person filter (slider)
        personData = data[(data["user"] == "p" + str(personFilter))]  # Filter data according to slider

        stimuliFilter = st.selectbox("Stimuli", personData["StimuliName"].unique().tolist())  # Stimuli filter (dropdown)
        stimuliData = personData[personData["StimuliName"] == stimuliFilter]  # Filter data according to dropdown

        if st.button('Start animation'):  # Automatic animation of eye tracking plot
            fixationIndexList = sorted(stimuliData["FixationIndex"].tolist())
            if not st.button('Stop animation'):
                count = 0
                totalDuration = 0  # Total duration of animation
                for i in fixationIndexList:
                    filtered_data = stimuliData[stimuliData["FixationIndex"] == i]
                    fixationDuration = filtered_data['FixationDuration'].values[0]
                    placeholderAnimationInfo.text('Step: ' + str(count) + ' of animation')
                    plt.close('all')  # Close all plots to save memory
                    loadScanpathPlot(stimuliFilter, personFilter, filtered_data)
                    time.sleep(fixationDuration / 1000.0)  # Show the point in true duration -> converted from milliseconds to seconds
                    count += 1
                    totalDuration += fixationDuration
            st.info('The animation finished! (Total duration in seconds: '+str(totalDuration/1000.0)+')')
            placeholderAnimationInfo.empty()
            loadScanpathPlot(stimuliFilter, personFilter, stimuliData)

        else:
            if st.checkbox('Show all data Points', value=True):  # Show all scatter points
                filtered_data = stimuliData
                loadScanpathPlot(stimuliFilter, personFilter, filtered_data)
            else:  # show scatter points according to slider (timestamp/index)
                fixationIndexFilter = st.slider('Timeslider', int(stimuliData["FixationIndex"].min()), int(stimuliData["FixationIndex"].max()), int(stimuliData["FixationIndex"].min()))  # Timestamp filter (slider)
                fixationIndexData = stimuliData[stimuliData["FixationIndex"] == fixationIndexFilter]  # Filter data according to slider
                filtered_data = fixationIndexData  # Filtered Dataframe
                loadScanpathPlot(stimuliFilter, personFilter, filtered_data)
    # ----------------------------- End of scanpath plot filter ------------------------------ #

    if st.checkbox('Show filtered map data'):
        st.write(filtered_data)  # Show filtered_data as interactive table

elif page == "Scatterplot visualization":  # Page with second visualization
    st.markdown('<style>.css-1v0mbdj.etr89bj1 img {width: 95%!important;}</style>', unsafe_allow_html=True)  # Set width of image
    st.markdown('## Scatterplot visualization')

    col1, col2 = st.columns(2)

    # Figure of scatterplot with heatmap
    def loadScatterPlot(stimuliFilter, filtered_data, col, alphaValueFilter, dataScaleFilter, colorFilter):
        STIMULI_PATH = os.path.join("MetroMapsEyeTracking", "stimuli")
        stimuliImgPath = os.path.join(STIMULI_PATH, stimuliFilter)  # Get image of stimuli

        # Check if image exists
        if not os.path.exists(stimuliImgPath):
            st.error('Image not found!')
            return

        stimuliImg = plt.imread(stimuliImgPath)  # Load image of stimuli as plot "friendly" data

        df_Sizes = filtered_data[['FixationDuration']].copy()  # Fixation Duration column
        N = int(dataScaleFilter)
        df_Sizes = 1 + (df_Sizes - df_Sizes.min()) * N / (df_Sizes.max() - df_Sizes.min())  # Scale data
        FixationDurationScaled = df_Sizes['FixationDuration'].values.tolist()  # Convert df to list

        # Get resolution of stimuli image (map)
        im = Image.open(stimuliImgPath)
        width, height = im.size
        extent = [0, width, height, 0]  # Setting axes size

        fig, ax = plt.subplots()
        ax.imshow(stimuliImg, extent=extent,
                  origin='upper', alpha=0.75)  # Image background of stimuli (map), origin='upper' to flip image
        ax.scatter(filtered_data["MappedFixationPointX"], filtered_data["MappedFixationPointY"],
                   s=FixationDurationScaled, c=colorFilter,
                   alpha=alphaValueFilter)  # Scatterplot heatmap of fixation points (c = color, alpha = transparency, s = size of dots)
        ax.xaxis.tick_top()  # Put x-axis on top
        rcParams['xtick.labelsize'] = 6  # x-axis labels font size
        rcParams['ytick.labelsize'] = 6  # y-axis labels font size
        plt.title(stimuliFilter, pad=25)  # Plot title (pad = padding)
        col.pyplot(fig)  # Replace plot with new plot
        im.close()  # Close image

    def loadHistogram(stimuliFilter, filtered_data, col, colorFilter):
        grouped_data = filtered_data.groupby(['user']).agg({'FixationDuration': 'sum'})  # Sum of fixation duration for each user
        grouped_data = grouped_data.sort_values(by=['FixationDuration'], ascending=False)  # Sort data according to fixation duration
        fig = plt.figure()
        plt.bar(grouped_data.index, grouped_data['FixationDuration'], color=colorFilter)  # Scatterplot of users and fixation duration
        plt.xlabel('User')
        plt.ylabel('Fixation duration (ms)')
        plt.title(stimuliFilter)
        col.pyplot(fig)  # Replace plot with new plot

    # ---------------------------- Filter for scatterplot with heatmap ----------------------------- #
    with st.sidebar.container():  # All filter-commands to sidebar
        st.markdown('### Filter')

        stimuliList = data["StimuliName"].unique().tolist()
        stimuliFilter = st.selectbox("Stimuli", stimuliList)  # Stimuli filter (dropdown)

        # Construct names of maps (colored, black and white)
        if stimuliFilter[2] == 'b':
            stimuliFilter_b = stimuliFilter  # Name of grayscale map
            stimuliFilter_c = stimuliFilter[:2] + stimuliFilter[3:]  # Name of colored map (without b)
        else:
            stimuliFilter_b = stimuliFilter[:2] + 'b' + stimuliFilter[2:]  # Name of grayscale map
            stimuliFilter_c = stimuliFilter  # Name of colored map

        stimuliData_c = data[data["StimuliName"] == stimuliFilter_c]  # stimuli data for colored map
        stimuliData_b = data[data["StimuliName"] == stimuliFilter_b]  # stimuli data for grayscale map

        alphaValueFilter = st.slider('Opacity of dots', min_value=0., max_value=1.0,
                                     step=0.05, value=0.2)  # Filter for alpha value (Opacity) of scatterplot
        dataScaleFilter = st.slider('Scaling of FixationDuration', min_value=100, max_value=800,
                                     step=100, value=400)  # Filter for scale of fixation duration
        colorFilter = st.selectbox("Color of plots", [c for c in mcolors.CSS4_COLORS.keys()], index=122)  # Filter for color of plots

        plt.close('all')  # Close all plots to save memory
        loadScatterPlot(stimuliFilter_c, stimuliData_c, col1, alphaValueFilter, dataScaleFilter, colorFilter)  # Load left plot (colored)
        loadScatterPlot(stimuliFilter_b, stimuliData_b, col2, alphaValueFilter, dataScaleFilter, colorFilter)  # Load right plot (grayscale)

        col1.markdown(f'Num. of Datapoints: {len(stimuliData_c)}')  # Show number of datapoints in plot
        col2.markdown(f'Num. of Datapoints: {len(stimuliData_b)}')  # Show number of datapoints in plot
        col1.markdown('---')  # Horizontal line
        col2.markdown('---')  # Horizontal line
        meanDuration_c = int(stimuliData_c["FixationDuration"].sum()) / int(len(stimuliData_c.user.unique().tolist())) # Average fixation duration for colored map
        meanDuration_b = int(stimuliData_b["FixationDuration"].sum()) / int(len(stimuliData_b.user.unique().tolist())) # Average fixation duration for grayscale map
        col1.metric('Average duration', f'{round(meanDuration_c/1000, 2)} s')  # Average fixation duration for colored map
        col2.metric('Average duration', f'{round(meanDuration_b/1000, 2)} s')  # Average fixation duration for grayscale map

        loadHistogram(stimuliFilter_c, stimuliData_c, col1, colorFilter)  # Load histogram of colored map
        loadHistogram(stimuliFilter_b, stimuliData_b, col2, colorFilter)  # Load histogram of grayscale map
    # ----------------------------- End of scatterplot with heatmap filter -------------------------- #

if page:  # insert this on all pages
    st.markdown('---')  # Horizontal line
    if st.checkbox('Show raw data'):
        st.markdown('## Raw data')
        st.write(data)  # Show raw data as interactive table
    st.markdown('---')  # Horizontal line
