import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

# 📌 1. Carregar les dades
@st.cache_data
def carregar_dades():
    df = pd.read_csv("Oficines_minim.csv")  # Assegura't que el fitxer és accessible
    df["Longitud"] = df["Longitud"].astype(float)
    df["Latitud"] = df["Latitud"].astype(float)
    df["Codi_Districte"] = df["Codi_Districte"].fillna(0)
    return df

df = carregar_dades()
#convertim les columnes de Longitud i Latitud a float i Codi_Districte a int i assignim 0 si Codi_Districte és buit
df["Longitud"] = df["Longitud"].astype(float)
df["Latitud"] = df["Latitud"].astype(float)
df["Codi_Districte"] = df["Codi_Districte"].astype(int)
df["Codi_Districte"] = df["Codi_Districte"].fillna(0)

# 📌 2. Generar colors únics per cada Codi_Districte
districtes = df["Codi_Districte"][df["Codi_Districte"]>=0].unique()
colors = plt.cm.get_cmap("tab20b", len(districtes))
#definim un diccionari de 11 colors segons Codi_Districte
#on codi és la clau entera i colors(i) és el valor i 50% de transparència
color_map = {codi: f"rgba{colors(i, 0.5)}" for i, codi in enumerate(districtes)}
color_map[0] = "rgba(255, 255, 0, 1)"  # Color per defecte
st.write(districtes)


# 📌 3. Generar diagrama de Voronoi
points = df[["Longitud", "Latitud"]][df["Codi_Districte"]>0].values  # Coordenades (x, y)
vor = Voronoi(points)

# 📌 4. Funció per obtenir els polígons Voronoi
def voronoi_regions(vor, df):
    regions = []
    for i, region_idx in enumerate(vor.point_region):
        vertices = [vor.vertices[j] for j in vor.regions[region_idx] if j != -1]
        if len(vertices) > 0:
            regions.append({"coords": np.array(vertices), "codi_districte": df.iloc[i]["Codi_Districte"]})
    return regions

regions = voronoi_regions(vor, df)

#converteix les regions en un kmz
import simplekml
kml = simplekml.Kml()
for region in regions:
    pol = kml.newpolygon(name=f"Districte {region['codi_districte']}")
    pol.outerboundaryis = region["coords"].tolist()
kml.save("voronoi.kmz") 

#converteix els punts df["Codi_Districte"]=0 en un kmz
kml = simplekml.Kml()
for i, row in df[df["Codi_Districte"]==0].iterrows():
    pnt = kml.newpoint(name=f"Oficina {i}", coords=[(row["Longitud"], row["Latitud"])])
kml.save("punts0.kmz")

#converteix els punts df["Codi_Districte"]>0 en un kmz
kml = simplekml.Kml()
for i, row in df[df["Codi_Districte"]>0].iterrows():
    pnt = kml.newpoint(name=f"Oficina {i}", coords=[(row["Longitud"], row["Latitud"])])
kml.save("punts.kmz")


# 📌 5. Crear la interfície de Streamlit
st.title("Mapa de Voronoi d'Oficines per Districte")

# 🎛️ Filtres d'interacció
selected_districts = st.multiselect("Selecciona districtes:", districtes, default=districtes)
show_points = st.checkbox("Mostrar punts d'oficines", value=True)

# 📌 6. Crear la visualització amb Plotly
fig = go.Figure()

# 🔷 Dibuixar polígons Voronoi
for region in regions:
    if region["codi_districte"] in selected_districts:
        polygon = region["coords"]
        fig.add_trace(go.Scatter(
            x=polygon[:, 0], y=polygon[:, 1],
            fill="toself",
            line=dict(color="black"),
            fillcolor=color_map[region["codi_districte"]],
            name=f"Districte {region['codi_districte']}"
        ))

# 🔷 Afegir punts d’oficines
if show_points:
    for codi in selected_districts:
        df_district = df[df["Codi_Districte"] == codi]
        fig.add_trace(go.Scatter(
            x=df_district["Longitud"], y=df_district["Latitud"],
            mode="markers",
            marker=dict(size=10, color=color_map[codi]),
            name=f"Punts districte {codi}"
        ))

# 📌 7. Ajustar el format del gràfic
fig.update_layout(
    title="Diagrama de Voronoi d'Oficines per Districte",
    xaxis_title="Longitud",
    yaxis_title="Latitud",
    showlegend=True,
    xaxis=dict(scaleanchor="y")  # Manté la proporció entre coordenades
)

# 📌 8. Mostrar el gràfic a Streamlit
st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

