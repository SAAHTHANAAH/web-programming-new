import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import math
import folium
from streamlit_folium import folium_static

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Sistem Survey Lot PUO", layout="wide")

# --- 2. GLOBAL STYLING & ACCESSIBILITY ---
st.markdown("""
    <style>
    /* Background: Land Surveying Theme */
    .stApp { 
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url("https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=1920&q=80"); 
        background-size: cover; 
        background-attachment: fixed;
    }
    
    .login-card { 
        background: rgba(255, 255, 255, 0.05); 
        backdrop-filter: blur(15px); 
        padding: 40px; border-radius: 20px; 
        border: 1px solid rgba(255,255,255,0.1); 
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.8);
    }
    
    .profile-card { 
        background: linear-gradient(135deg, #00c6ff, #0072ff); 
        padding: 20px; border-radius: 15px; 
        text-align: center; color: white; margin-bottom: 20px;
    }

    .stButton>button { 
        width: 100%; border-radius: 8px; 
        font-weight: bold; transition: 0.3s;
    }
    
    [data-testid="stSidebar"] { background-color: #1a1c23; }
    label, p, span, h1, h2, h3 { color: white !important; }

    .leaflet-control-layers { 
        font-size: 14px !important; 
        font-family: 'Arial', sans-serif !important;
        background: rgba(255,255,255,0.9) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ENGINE ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "1": {"name": "SAAHTHANAAH", "pw": "MYadmin123"},
        "2": {"name": "YOSHINII", "pw": "MYadmin123"},
        "3": {"name": "JAYA", "pw": "MYadmin123"}
    }
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "view" not in st.session_state: st.session_state["view"] = "login"

# --- 4. MATH ENGINE (Bearing/Dist with Offset) ---
def get_survey_labels(p1, p2, offset=1.2):
    de, dn = p2[0] - p1[0], p2[1] - p1[1]
    dist = math.sqrt(de**2 + dn**2)
    angle = (math.degrees(math.atan2(de, dn)) + 360) % 360
    
    d = int(angle)
    m = int((angle - d) * 60)
    s = int((angle - d - m/60) * 3600)
    
    ux, uy = de/dist, dn/dist
    nx, ny = uy, -ux 
    
    mid_e, mid_n = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
    
    pos_brg = (mid_e + nx*offset, mid_n + ny*offset)
    pos_dist = (mid_e - nx*offset, mid_n - ny*offset)
    
    return f"{d}°{m}'{s}\"", f"{dist:.3f}m", pos_brg, pos_dist

# --- 5. AUTHENTICATION FLOW ---
if not st.session_state["authenticated"]:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        if st.session_state["view"] == "login":
            # --- LOGO INTEGRATION ---
            try:
                st.image("POLI LOGO.png", use_container_width=True)
            except:
                st.warning("Imej 'POLI LOGO.png' tidak dijumpai.")
                
            st.markdown("<h2 style='text-align:center;'>🔐 Log Masuk Survey Lot</h2>", unsafe_allow_html=True)
            uid = st.text_input("👤 Masukkan ID:")
            upw = st.text_input("🔑 Masukkan Kata Laluan:", type="password")
            if st.button("Log Masuk"):
                if uid in st.session_state["user_db"] and upw == st.session_state["user_db"][uid]["pw"]:
                    st.session_state["authenticated"] = True
                    st.session_state["uid"] = uid
                    st.rerun()
                else: st.error("ID atau Kata Laluan Salah!")
            if st.button("❓ Lupa Kata Laluan?"):
                st.session_state["view"] = "recovery"
                st.rerun()
        elif st.session_state["view"] == "recovery":
            st.markdown("<h2 style='text-align:center;'>🛠️ Set Semula Laluan</h2>", unsafe_allow_html=True)
            rid = st.text_input("ID Pengguna:")
            new_p = st.text_input("Kata Laluan Baru:", type="password")
            if st.button("Kemas Kini & Selesai"):
                if rid in st.session_state["user_db"]:
                    st.session_state["user_db"][rid]["pw"] = new_p
                    st.session_state["view"] = "login"
                    st.success("Sila log masuk dengan kata laluan baru.")
                    st.rerun()
                else: st.error("ID tidak sah.")
            if st.button("⬅️ Kembali"):
                st.session_state["view"] = "login"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. MAIN DASHBOARD ---
else:
    user = st.session_state["user_db"][st.session_state["uid"]]
    
    with st.sidebar:
        st.markdown(f'<div class="profile-card"><h3>Hai, {user["name"]}!</h3></div>', unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Kawalan Paparan")
        st_size = st.slider("Saiz Marker Stesen", 5, 40, 22)
        text_size = st.slider("Saiz Bearing/Jarak", 6, 15, 9)
        zoom_lv = st.slider("Tahap Zoom", 10, 22, 19)
        poly_color = st.color_picker("Warna Poligon", "#FFFF00")
        
        st.divider()
        st.markdown("### 💾 Eksport Data")
        if 'export_json' in st.session_state:
            st.download_button("🚀 Export to QGIS (.geojson)", st.session_state['export_json'], "survey.geojson")
        else: st.button("🚀 Export to QGIS (.geojson)", disabled=True)

        if st.button("🚪 Log Keluar"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- MAIN HEADER WITH LOGO ---
    h_col1, h_col2 = st.columns([1, 6])
    with h_col1:
        try:
            st.image("POLI LOGO.png", width=150) 
        except:
            st.info("Letak fail POLI LOGO.png di dalam folder projek.")
            
    with h_col2:
        st.markdown("<h1 style='margin-bottom:0;'>SISTEM SURVEY LOT PUO</h1><p style='color:#00c6ff !important;'>Jabatan Kejuruteraan Awam | Land Surveying Division</p>", unsafe_allow_html=True)
    
    st.divider()

    # Input Section
    col_input1, col_input2 = st.columns([1, 3])
    with col_input1: epsg = st.text_input("🌏 Kod EPSG:", "4390")
    with col_input2: uploaded_file = st.file_uploader("Upload CSV (STN, E, N)", type=['csv'])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df['STN'] = df['STN'].astype(int)
        
        # Geoprocessing
        gdf_poly = gpd.GeoDataFrame(index=[0], geometry=[Polygon(list(zip(df.E, df.N)))], crs=f"EPSG:{epsg}")
        gdf_pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.E, df.N), crs=f"EPSG:{epsg}")
        gdf_wgs = gdf_poly.to_crs(epsg=4326)
        gdf_pts_wgs = gdf_pts.to_crs(epsg=4326)
        st.session_state['export_json'] = gdf_wgs.to_json()

        # Map Initialization
        m = folium.Map(location=[gdf_wgs.geometry.centroid.y[0], gdf_wgs.geometry.centroid.x[0]], 
                        zoom_start=zoom_lv, max_zoom=22, tiles=None)
        
        folium.TileLayer('openstreetmap', name='OpenStreetMap', control=True).add_to(m)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
            attr='Google', name='Google Hybrid (Satelit)', 
            max_zoom=22, max_native_zoom=20, control=True
        ).add_to(m)

        # Feature Groups
        fg_poly = folium.FeatureGroup(name="Polygon Layer").add_to(m)
        fg_stn = folium.FeatureGroup(name="Station Markers").add_to(m)
        fg_lbl = folium.FeatureGroup(name="Bearing & Distance").add_to(m)

        # Polygon and Popup
        coords_str = "<br>".join([f"STN {row.STN}: {row.E}, {row.N}" for _, row in df.iterrows()])
        popup_html = f"<div style='color:black;'><b>Koordinat:</b><br>{coords_str}</div>"
        
        folium.GeoJson(
            gdf_wgs, 
            style_function=lambda x: {'color': poly_color, 'weight': 3, 'fillOpacity': 0.15},
            tooltip="Klik untuk koordinat"
        ).add_child(folium.Popup(popup_html, max_width=300)).add_to(fg_poly)

        # Stations and Labels Loop
        for i in range(len(df)):
            p1_geo = gdf_pts_wgs.iloc[i].geometry
            folium.Marker(
                [p1_geo.y, p1_geo.x], 
                icon=folium.DivIcon(html=f'<div style="color:white; font-family: sans-serif; font-size:10pt; font-weight:bold; background:red; border-radius:50%; width:{st_size}px; height:{st_size}px; line-height:{st_size}px; text-align:center; border:2px solid white; box-shadow: 2px 2px 5px black;">{df.iloc[i]["STN"]}</div>')
            ).add_to(fg_stn)

            next_idx = (i + 1) % len(df)
            brg, dist, pos_brg, pos_dist = get_survey_labels((df.iloc[i].E, df.iloc[i].N), (df.iloc[next_idx].E, df.iloc[next_idx].N))
            
            lbl_gdf = gpd.GeoDataFrame(geometry=[gpd.points_from_xy([pos_brg[0]], [pos_brg[1]], crs=f"EPSG:{epsg}")[0], 
                                                 gpd.points_from_xy([pos_dist[0]], [pos_dist[1]], crs=f"EPSG:{epsg}")[0]], crs=f"EPSG:{epsg}").to_crs(epsg=4326)
            
            folium.Marker([lbl_gdf.iloc[0].geometry.y, lbl_gdf.iloc[0].geometry.x], icon=folium.DivIcon(html=f'<div style="color:{poly_color}; font-size:{text_size}pt; font-weight:bold; text-shadow:1px 1px 3px black; width:120px;">{brg}</div>')).add_to(fg_lbl)
            folium.Marker([lbl_gdf.iloc[1].geometry.y, lbl_gdf.iloc[1].geometry.x], icon=folium.DivIcon(html=f'<div style="color:white; font-size:{text_size}pt; font-weight:bold; text-shadow:1px 1px 3px black; width:120px;">{dist}</div>')).add_to(fg_lbl)

        folium.LayerControl(collapsed=False).add_to(m)
        folium_static(m, width=1200, height=650)