import requests
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import datetime
import requests
import time
import os


def get_population(country_name):
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        population = data[0]['population']
        return population
    else:
        print("Erreur lors de la récupération des données.")
        return None


date_aujourdhui = datetime.date.today()
st.set_option('deprecation.showPyplotGlobalUse', False)
menu = ["ACCUEIL", "REFRESH DATA", "MAP"]
choice = st.sidebar.selectbox("Menu", menu)
df_country = pd.read_csv("ISO_lat_long.csv")
repertoire_courant = os.getcwd()
database = '/database'
data_to_date = False
if choice == "ACCUEIL":
    st.write("Bienvenue sur mon streamlit, vous avez une barre déroulante sur le coté ou vous pouvez récuperer de la donnée d'aujourd'hui ou directement aller à la visualisation.")

if choice == "REFRESH DATA":
    if st.button('GET DATA'):
        for file in os.listdir(repertoire_courant+database):
            if str(date_aujourdhui) in file:
                data_to_date = True
        if data_to_date:
            st.write("Data is already up to date")
        else:
            st.write("Collecting data...")
            country_list = []
            country_population = []
            progress_bar = st.progress(0)
            total_iterations = df_country["Country"].shape[0]
            i = 0
            for country in df_country["Country"]:
                population = get_population(country)
                if population is None or population == 0:
                    print(f"{country} : not found")
                else:
                    country_list.append(country)
                    country_population.append(population)
                progress_bar.progress((i + 1) / total_iterations)
                i += 1
                time.sleep(0.05)
            df = pd.DataFrame({'Country': country_list, 'Population': country_population})
            merged_df = pd.merge(df, df_country, on='Country', how='inner')
            merged_df_clean = merged_df.dropna()
            merged_df_clean['date'] = pd.to_datetime(date_aujourdhui)
            merged_df_clean.to_csv(f'database/population_{date_aujourdhui}.csv', index=False)
            st.write("Data is up to date !")

if choice == "MAP":
    # Chemin vers le dossier contenant les fichiers CSV
    dossier = 'database/'

    # Liste pour stocker les données de tous les fichiers CSV
    donnees_totales = []

    # Parcours de tous les fichiers dans le dossier
    for fichier in os.listdir(dossier):
        if fichier.endswith('.csv'):
            chemin_fichier = os.path.join(dossier, fichier)
            # Lecture du fichier CSV et ajout des données à la liste
            donnees = pd.read_csv(chemin_fichier)
            donnees_totales.append(donnees)

    # Concaténation de toutes les données en un seul DataFrame
    merged_df_clean = pd.concat(donnees_totales, ignore_index=True)

    # Trier les dates en ordre décroissant pour que la plus récente soit en premier
    liste_dates = sorted(merged_df_clean['date'].unique(), reverse=True)

    # Sélectionner par défaut la date la plus récente
    date_selectionnee = st.selectbox('Sélectionner une date', liste_dates, index=0)

    # Filtrer les données en fonction de la date sélectionnée
    df_filtered = merged_df_clean[merged_df_clean['date'] == date_selectionnee]

    st.write(f"Carte de la démographie en {date_selectionnee}")
    m = folium.Map(location=[48, 5], zoom_start=4)

    marker_cluster = MarkerCluster().add_to(m)
    for index, row in df_filtered.iterrows():
        print(row['Latitude'], row['Longitude'], row['Country'])
        folium.Marker(location=[row['Latitude'], row['Longitude']],
                      popup=f"{row['Country']} - {row['Population']} habitants").add_to(marker_cluster)

    st_folium(m, width=725, height=500)

    # Graphique à barres des 10 pays les plus peuplés
    plt.subplot(2, 2, 1)
    top_10 = df_filtered.nlargest(10, 'Population')
    sns.barplot(x='Population', y='Country', data=top_10,
                palette='viridis')
    plt.title('Top 10 des pays les plus peuplés')
    st.pyplot()


    labels = top_10['Country']
    sizes = top_10['Population']

    # Créer le graphique camembert
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Répartition de la population parmi les 10 pays les plus peuplés')

    # Afficher le graphique
    st.pyplot()
