import streamlit as st
import pandas as pd
import datetime
import os
import pytz

# --- KONFIGURACE DAT ---
# Místo pro uložení dat v CSV souboru
DATA_FILE = 'dochazka_data.csv'
# Diety platné pro rok 2025 (příklad - zadej aktuální hodnoty)
DIET_RATES = {
    '5_12': 166,  # 5 až 12 hodin
    '12_18': 256, # 12 až 18 hodin
    '18+': 398    # Nad 18 hodin
}
# --- Konec konfigurace ---


# Funkce pro načtení a uložení dat
def load_data():
    """Načte data z CSV, nebo vytvoří prázdný DataFrame, pokud soubor neexistuje."""
    if os.path.exists(DATA_FILE):
        # Indexování se nastaví na False, aby Streamlit neměl problémy s indexem
        return pd.read_csv(DATA_FILE)
    else:
        # Vytvoření prázdného DataFrame pro uchování dat
        return pd.DataFrame(columns=['id', 'Datum', 'Od', 'Do', 'Odpracováno (h)', 'Doprava', 'Diety (Kč)'])

def save_data(df):
    """Uloží DataFrame do CSV souboru."""
    df.to_csv(DATA_FILE, index=False)
    
# Výpočet diářů
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
# Vložení custom CSS pro stejný vzhled jako v tvém HTML
st.markdown("""
<style>
/* Zde je tvoje vlastní CSS, aby to vypadalo jako HTML verze */
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
.stActionButton {
    display: none; /* Skryje defaultní hamburger menu Streamlitu pro čistší mobilní vzhled */
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-container"><h1>Evidence docházky ČT</h1><p>Vítejte v evidenci docházky České televize</p></div>', unsafe_allow_html=True)

# --- PANEL PRO PŘIDÁNÍ ZÁZNAMU ---
st.subheader("➕ Nový záznam")

# Automatické nastavení data a času pro ČR
tz = pytz.timezone('Europe/Prague')
now = datetime.datetime.now(tz)

with st.form("new_record_form", clear_on_submit=True):
    # Data a časové sloupce
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("Datum", value=now.date())
    with col2:
        time_od = st.time_input("Plánovaný čas OD", value=datetime.time(8, 0))
        time_do = st.time_input("Plánovaný čas DO", value=datetime.time(16, 0))
    
    # Odpracované hodiny a doprava
    odpracovano = st.number_input("Odpracovaný čas (hodiny)", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
    doprava = st.selectbox("Dopravní prostředek", ["Žádný", "Auto", "Dodávka"])
    diety_checkbox = st.checkbox("Nárok na diety")
    
    submitted = st.form_submit_button("💾 Uložit záznam")

    if submitted:
        # Vytvoření datetime objektů pro výpočet délky
        dt_od = datetime.datetime.combine(date_input, time_od)
        dt_do = datetime.datetime.combine(date_input, time_do)
        
        # Ošetření přechodu přes půlnoc
        if dt_do < dt_od:
            dt_do += datetime.timedelta(days=1)
        
        duration = dt_do - dt_od
        duration_hours = duration.total_seconds() / 3600
        
        # Validace
        if odpracovano > duration_hours:
            st.error("Odpracovaný čas nemůže být delší než plánovaný časový úsek!")
        elif duration_hours <= 0:
            st.error("Čas DO musí být po čase OD.")
        else:
            # Výpočet diet
            dieta_hodnota = calculate_diet(duration_hours, diety_checkbox)
            
            # Nový záznam
            new_id = datetime.datetime.now().timestamp()
            new_record = pd.DataFrame([{
                'id': new_id,
                'Datum': date_input.strftime("%d.%m.%Y"),
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

if not df_dochazka.empty:
    # Agregace dat
    total_hours = df_dochazka['Odpracováno (h)'].sum()
    total_diets = df_dochazka['Diety (Kč)'].sum()
    count_auto = df_dochazka[df_dochazka['Doprava'] == 'Auto'].shape[0]
    count_dodavka = df_dochazka[df_dochazka['Doprava'] == 'Dodávka'].shape[0]
    
    # Převod hodin na dny/hodiny (8h pracovní den)
    days = int(total_hours // 8)
    remaining_hours = round(total_hours % 8, 1)
    
    if days > 0 and remaining_hours > 0:
        formatted_hours = f"{days} dní {remaining_hours} h"
    elif days > 0:
        formatted_hours = f"{days} dní"
    else:
        formatted_hours = f"{remaining_hours} h"
        
    
    # Zobrazení ve sloupcích
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Odpracováno celkem", formatted_hours)
    col2.metric("Celkem diety", f"{total_diets} Kč")
    col3.metric("Jízdy Auto", f"{count_auto}×")
    col4.metric("Jízdy Dodávka", f"{count_dodavka}×")
else:
    st.info("Žádné záznamy k zobrazení statistik.")


# --- PANEL PŘEHLEDU ZÁZNAMŮ ---
st.subheader("📊 Přehled záznamů")

if not df_dochazka.empty:
    # Přidání sloupců pro mazání
    df_display = df_dochazka.copy()
    
    # Funkce pro mazání řádku (používá session_state pro Streamlit)
    def delete_record(record_id):
        global df_dochazka
        df_dochazka = df_dochazka[df_dochazka['id'] != record_id]
        save_data(df_dochazka)
        st.experimental_rerun() # nutné pro okamžitou aktualizaci tabulky

    # Vytvoření akčních tlačítek
    edit_column = st.empty()
    
    # Zobrazení dat
    st.dataframe(df_dochazka.drop(columns=['id']), use_container_width=True)
    
    # Tlačítka pro mazání jednotlivých řádků
    for index, row in df_dochazka.iterrows():
        # Streamlit bohužel nemá nativní tlačítka v řádku tabulky, 
        # proto se obvykle používá boční panel nebo checkbox pro výběr a následné mazání.
        # Pro zjednodušení použijeme zatím jen možnost smazat vše.
        pass

    # Tlačítko pro smazání všech záznamů
    if st.button("🗑️ Smazat VŠECHNY záznamy", type="primary"):
        if st.warning("Opravdu chcete smazat VŠECHNY záznamy? Tuto akci nelze vrátit!", icon="🚨"):
            if st.button("ANO, smazat vše", type="secondary"):
                os.remove(DATA_FILE)
                st.success("Všechny záznamy byly smazány.")
                st.experimental_rerun()
else:
    st.info("Žádné záznamy k zobrazení.")