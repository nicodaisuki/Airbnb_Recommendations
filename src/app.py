# -*- coding: utf-8 -*-
"""
Created on Tue May 12 23:50:37 2020

@author: dguan
"""
from datetime import datetime
import os
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from sklearn.preprocessing import LabelEncoder

from src.data.d_utils import sample_data, preprocess_data, load_data
from src.eval_model import predict, load_model, evaluate_model
from src.recommend import run_recommmendation
from src.visualization.recommended_countries_viz import RecommendCountry
from src import SessionState

# Module Level Constants
MODEL = './models/finalized_LRmodel.sav'
DATA_DIR = './airbnb-recruiting-new-user-bookings'
CSV_FNAMES = {
    'val': os.path.join(DATA_DIR, 'val_users.csv'),
    'val-part-merged_sessions': os.path.join(DATA_DIR, 'val_users-part-merged_sessions.csv'),
    'test_ids': os.path.join(DATA_DIR, 'test_ids.txt'),
    'age_bkt': os.path.join(DATA_DIR, 'age_gender_bkts.csv'),
    'seasons': os.path.join(DATA_DIR, 'popular_seasons.csv')
}
LABELS = './src/data/labels.txt'

# load dataset
@st.cache
def load_data_frontend(CSV_FNAMES):
    return load_data(CSV_FNAMES, features=True)

def display_predictions(predictions):
    """ Display predictions after model inference

    Predictions are listed as checkboxes where users can select them to see helpful
    information about when to visit.

    Args:
        predictions (list): Predictions ['US', 'NDF', ...]

    Returns:

    """
    #TODO test getting info from the predictions given the teest age bucket and test
    # seasons
    country_info = RecommendCountry(seasons_csv=CSV_FNAMES['seasons'])
    country_info.set_country_popular_age(csv_fname=CSV_FNAMES['age_bkt'])

    for idx, pred in enumerate(predictions):
        if st.checkbox(f'{idx + 1}. {pred}'):
            # Get country image
            st.image(country_info.get_country_image(pred), caption=pred.upper(),
                     use_column_width=True)
            # Write caption
            st.write(country_info.get_image_caption(pred))

            if pred == 'NDF' or pred == 'other':
                continue

            age = country_info.popular_age[pred]
            season, months = country_info.get_popular_seasons(pred)
            st.write('[Popular Age] Male: {} | Female: {}'.format(age['male'], age['female']))
            st.write('[Popular Season] {} | {}'.format(season.upper(), months))

def run():
    """ Runs streamlit application

    Workflow is to load the dataset in the background, then the following:
    1. Generate user id
    2. View data
    3. Run predictions
    4. View predictions

    Returns:

    """
    data, predictions, id = None, [] ,0
    ndcg = 0
    session_state = SessionState.get(id=id, data=data, predictions=predictions,
                                     ndcg=ndcg)

    # Load dataset
    dataset = load_data_frontend(CSV_FNAMES)
    #TODO select new set of test ids that show variability in the predictions
    test_ids = open(CSV_FNAMES['test_ids'], 'r').read().splitlines()

    #=== Generate USER ID button ===#
    # Get user id
    st.header('Generate User')
    if st.button('Click here to Generate User ID'):

        session_state.X, session_state.id = sample_data(dataset.users, test_ids=test_ids)
        st.write(session_state.id)

    #=== View raw data ===#
    st.subheader('Raw Data')
    if st.checkbox('Show data') and session_state.id:
        FEAT_TO_DISPLAY = ['id', 'country_destination',
                           'date_account_created', 'gender', 'age',
                           'signup_method', 'signup_app', 'language']
        show_data = session_state.X[FEAT_TO_DISPLAY]
        st.dataframe(show_data)

    #=== Recommendation button ===#
    # Recommend based off id
    st.header('Recomended Countries')
    recommend = st.button('Click here to Recommend Countries')
    if recommend:
        session_state.predictions, ndcg = run_recommmendation(dataset, session_state.id,
                                                              model_weights=MODEL)

        # Report the predictions results
        st.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | USR ID: {session_state.id}] NDCG '
                 f'Score: {ndcg["ndcg"]}')
        st.write(f'Below are the predicted country recommendations for this users '
                 f'first booking experience')

    else:
        st.write("Press the above button..")

    #=== Display predictions ===#
    display_predictions(session_state.predictions)


#=== Start Streamlit Application ===#
st.title("Airbnb Recomendation System")
st.markdown(
    """
        This is a demo of a Streamlit app that shows Airbnb recomendation for travellers.
        [See source code](https://github.com/streamlit/demo-uber-nyc-pickups/blob/master/app.py)
    """)
run()
