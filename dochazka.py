import streamlit as st
import pandas as pd
import datetime
import os
import pytz

# --- KONFIGURACE DAT ---
DATA_FILE = 'dochazka_data.csv'
DIET_RATES = {
    '5_12': 166,
    '12_18': 256,
    '18+': 398
}
# --- Konec konfigurace ---

# Funkce pro načtení a uložení dat
def load_data():
    """Načte data z CSV, nebo vytvoří prázdný DataFrame, pokud soubor neexistuje."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Zajištění, že sloupec Datum je správného typu, i po načtení
        df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
        return df
    else:
        return pd.DataFrame(columns=['id', 'Datum', 'Od', 'Do', 'Odpracováno (h)', 'Doprava', 'Diety (Kč)'])

def save_data(df):
    """Uloží DataFrame do CSV souboru."""
    # Před uložením převedeme Datum zpět na formát řetězce (pro snadné čtení v Excelu/manuálně)
    df['Datum_str'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df_to_save = df.drop(columns=['Datum'])
    df_to_save.rename(columns={'Datum_str': 'Datum'}, inplace=True)
    
    # Zajištění správného pořadí sloupců před uložením
    cols = ['id', 'Datum', 'Od', 'Do', 'Odpracováno (h)', 'Doprava', 'Diety (Kč)']
    df_to_save = df_to_save[cols]
    
    df_to_save.to_csv(DATA_FILE, index=False)
    
def calculate_diet(duration_hours, has_diet):
    """Vypočítá výši diet podle odpracovaných hodin."""
    if not has_diet:
        return 0
    if duration_hours < 5:
        return 0
    elif duration_hours < 12:
        return DIET_RATES['5_12']
    elif duration_hours < 18:
        return DIET_RATES['12_18']
    else:
        return DIET_RATES['18+']

# Nastavení stránky
st.set_page_config(
    page_title="Evidence docházky ČT",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Načtení dat při spuštění aplikace
df_dochazka = load_data()


# --- HLAVA (Header) A STYL ---
st.markdown("""
<style>
.header-container {
    background: #0033A0;
    padding: 20px;
    border-radius: 12px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}
.header-container h1 {
    font-size: 32px;
    font-weight: 800;
    margin: 0;
}
.header-container p {
    font-size: 16px;
    margin-top: 5px;
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><h1>Evidence docházky ČT</h1><p>Vítejte v evidenci docházky České televize</p></div>', unsafe_allow_html=True)

# --- PANEL PRO PŘIDÁNÍ ZÁZNAMU ---
st.subheader("➕ Nový záznam")

tz = pytz.timezone('Europe/Prague')
now = datetime.datetime.now(tz)

with st.form("new_record_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("Datum", value=now.date())
    with col2:
        time_od = st.time_input("Plánovaný čas OD", value=datetime.time(8, 0))
        time_do = st.time_input("Plánovaný čas DO", value=datetime.time(16, 0))
    
    odpracovano = st.number_input("Odpracovaný čas (hodiny)", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
    doprava = st.selectbox("Dopravní prostředek", ["Žádný", "Auto", "Dodávka"])
    diety_checkbox = st.checkbox("Nárok na diety")
    
    submitted = st.form_submit_button("💾 Uložit záznam")

    if submitted:
        dt_od = datetime.datetime.combine(date_input, time_od)
        dt_do = datetime.datetime.combine(date_input, time_do)
        
        if dt_do < dt_od:
            dt_do += datetime.timedelta(days=1)
        
        duration_hours = (dt_do - dt_od).total_seconds() / 3600
        
        if odpracovano > duration_hours:
            st.error("Odpracovaný čas nemůže být delší než plánovaný časový úsek!")
        elif duration_hours <= 0:
            st.error("Čas DO musí být po čase OD.")
        else:
            dieta_hodnota = calculate_diet(duration_hours, diety_checkbox)
            
            new_id = datetime.datetime.now().timestamp()
            new_record = pd.DataFrame([{
                'id': new_id,
                'Datum': date_input, # Uložíme jako datetime objekt
                'Od': time_od.strftime("%H:%M"),
                'Do': time_do.strftime("%H:%M"),
                'Odpracováno (h)': odpracovano,
                'Doprava': doprava,
                'Diety (Kč)': dieta_hodnota
            }])
            
            # Přidání a uložení dat
            df_dochazka = pd.concat([df_dochazka, new_record], ignore_index=True)
            save_data(df_dochazka)
            st.success(f"✅ Záznam uložen! Délka plánu: {duration_hours:.1f} h, Diety: {dieta_hodnota} Kč")


# --- PANEL STATISTIK ---
st.subheader("📈 Statistiky")
# ... (kód statistik zůstává stejný, pracuje s df_dochazka)
if not df_dochazka.empty:
    total_hours = df_dochazka['Odpracováno (h)'].sum()
    total_diets = df_dochazka['Diety (Kč)'].sum()
    count_auto = df_dochazka[df_dochazka['Doprava'] == 'Auto'].shape[0]
    count_dodavka = df_dochazka[df_dochazka['Doprava'] == 'Dodávka'].shape[0]
    
    days = int(total_hours // 8)
    remaining_hours = round(total_hours % 8, 1)
    
    if days > 0 and remaining_hours > 0:
        formatted_hours = f"{days} dní {remaining_hours} h"
    elif days > 0:
        formatted_hours = f"{days} dní"
    else:
        formatted_hours = f"{total_hours:.1f} h" if total_hours > 0 else "0 h"
        
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Odpracováno celkem", formatted_hours)
    col2.metric("Celkem diety", f"{total_diets} Kč")
    col3.metric("Jízdy Auto", f"{count_auto}×")
    col4.metric("Jízdy Dodávka", f"{count_dodavka}×")
else:
    st.info("Žádné záznamy k zobrazení statistik.")

# --- PANEL PŘEHLEDU ZÁZNAMŮ (Upraveno pro filtrování) ---
st.subheader("📊 Přehled záznamů")

if not df_dochazka.empty:
    
    # 1. Vytvoření seznamu dostupných měsíců a let (pro selectbox)
    # Získáme unikátní kombinace Rok-Měsíc ve formátu "MMMM RRRR"
    df_dochazka['RokMěsíc'] = df_dochazka['Datum'].dt.strftime('%B %Y')
    
    # Převedeme na český název měsíce (vyžaduje Python 3.9+ a správné locale, ale na Streamlit Cloud to obvykle funguje)
    # Pro jistotu použijeme anglické názvy, pokud by české nefungovaly, a přidáme rok.
    # Budeme se držet Rok/Měsíc pro jednoduché řazení
    df_dochazka['Měsíc_ID'] = df_dochazka['Datum'].dt.strftime('%Y-%m')
    
    # Vytvoření seznamu unikátních měsíců a seřazení
    unique_months = df_dochazka[['Měsíc_ID', 'RokMěsíc']].drop_duplicates().sort_values(by='Měsíc_ID', ascending=False)
    
    # Vytvoření čitelného popisku pro výběr
    month_options = [f"{datetime.datetime.strptime(mid, '%Y-%m').strftime('%B')} {mid[:4]}" for mid in unique_months['Měsíc_ID']]
    month_keys = unique_months['Měsíc_ID'].tolist()
    
    # 2. Výběr měsíce pro filtrování
    selected_month_label = st.selectbox(
        "Zobrazit záznamy za:",
        options=month_options,
        index=0 # Defaultně vybraný nejnovější měsíc
    )
    
    # Získání Měsíc_ID z vybrané čitelné labelu
    selected_index = month_options.index(selected_month_label)
    selected_month_id = month_keys[selected_index]
    
    # 3. Filtrování tabulky
    df_filtered = df_dochazka[df_dochazka['Měsíc_ID'] == selected_month_id].copy()
    
    # Příprava tabulky pro zobrazení
    df_display = df_filtered.copy()
    
    # Odstranění pomocných sloupců a úprava formátu data
    df_display['Datum'] = df_display['Datum'].dt.strftime('%d.%m.%Y')
    df_display.drop(columns=['id', 'Měsíc_ID', 'RokMěsíc'], inplace=True)
    
    # Přejmenování sloupců pro lepší čitelnost
    df_display.rename(columns={'Odpracováno (h)': 'Hodin', 'Diety (Kč)': 'Diety'}, inplace=True)
    
    # Zobrazení nadpisu pro filtrovaný měsíc
    st.markdown(f"**Detailní přehled za {selected_month_label}:**")
    
    # 4. Zobrazení tabulky
    if not df_display.empty:
        st.dataframe(df_display, use_container_width=True)
        
        # --- Měsíční souhrn ---
        st.markdown(f"#### Souhrn za {selected_month_label}")
        mesic_hodin = df_filtered['Odpracováno (h)'].sum()
        mesic_diety = df_filtered['Diety (Kč)'].sum()
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Celkem odpracováno (h)", f"{mesic_hodin:.1f}")
        col_m2.metric("Celkem diety (Kč)", f"{mesic_diety} Kč")

    # Tlačítko pro smazání všech záznamů
    if st.button("🗑️ Smazat VŠECHNY záznamy", type="primary"):
        st.warning("Opravdu chcete smazat VŠECHNY záznamy? Tuto akci nelze vrátit!", icon="🚨")
        if st.button("ANO, smazat vše", type="secondary"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
                st.success("Všechny záznamy byly smazány.")
                st.experimental_rerun()
            else:
                st.error("Soubor s daty nebyl nalezen.")
else:
    st.info("Žádné záznamy k zobrazení.")
