import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from pytrends.request import TrendReq
import openai

# --- Funzioni Selenium ---
def start_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(options=options)

def get_total_results(driver):
    try:
        text = driver.find_element(By.XPATH, "//span[contains(text(),'risultati per')]").text
        num = ''.join(filter(str.isdigit, text.split(" ")[0]))
        return int(num) if num else 0
    except:
        return 0

def get_bsr_from_product_page(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        bsr_element = driver.find_element(By.XPATH, "//th[contains(text(), 'Posizione nella classifica')]/following-sibling::td/span")
        bsr_text = bsr_element.text.split(" ")[0].replace('.', '').replace('#', '')
        return int(bsr_text)
    except:
        return None

def search_amazon(keyword, max_pages=1, max_bsr=200000, max_reviews=100):
    driver = start_driver()
    books = []
    total_results = 0

    for page in range(1, max_pages + 1):
        keyword_url = keyword.replace(" ", "+")
        url = f"https://www.amazon.it/s?k={keyword_url}&i=stripbooks&page={page}"
        driver.get(url)
        time.sleep(2)

        if page == 1:
            total_results = get_total_results(driver)

        results = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

        for result in results:
            try:
                title = result.find_element(By.TAG_NAME, "h2").text
                link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                continue

            try:
                reviews = result.find_element(By.XPATH, ".//span[@class='a-size-base']").text
                reviews = int(reviews.replace('.', ''))
            except:
                reviews = 0

            bsr = get_bsr_from_product_page(driver, link)

            if bsr and bsr < max_bsr and reviews < max_reviews:
                books.append({
                    "Keyword": keyword,
                    "Titolo": title,
                    "Link": link,
                    "BSR": bsr,
                    "Recensioni": reviews
                })

    driver.quit()
    return books, total_results

# --- Streamlit UI ---
st.set_page_config(page_title="Amazon KDP Niche Finder", layout="centered")
st.title("📚 Amazon KDP Niche Finder")

keywords_input = st.text_area("🔍 Inserisci keyword separate da virgola:", "coloring book bambini, attività 3 anni")
max_pages = st.slider("📄 Numero di pagine da analizzare per keyword", 1, 5, 2)
bsr_limit = st.number_input("📉 BSR massimo", value=200000)
reviews_limit = st.number_input("⭐ Recensioni massime", value=100)

if st.button("Avvia Ricerca"):
    keyword_list = [k.strip() for k in keywords_input.split(",")]
    all_results = []

    with st.spinner("🔎 Analisi in corso..."):
        for keyword in keyword_list:
            st.write(f"Analizzando: **{keyword}**...")
            risultati, totale = search_amazon(keyword, max_pages, bsr_limit, reviews_limit)
            st.success(f"Trovati {len(risultati)} libri validi su {totale} risultati totali per '{keyword}'")
            all_results.extend(risultati)

    if all_results:
        df = pd.DataFrame(all_results)
        st.write("📊 **Risultati Filtrati**")
        st.dataframe(df)
        st.download_button("⬇️ Scarica CSV", df.to_csv(index=False), file_name="idee_kdp.csv", mime="text/csv")
    else:
        st.warning("Nessun risultato valido trovato. Prova ad allargare i filtri.")

# --- Trends ---
st.subheader("📈 Google Trends")
if st.checkbox("Mostra popolarità Google Trends"):
    pytrends = TrendReq(hl='it-IT', tz=360)
    for keyword in [k.strip() for k in keywords_input.split(",")]:
        pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo='IT')
        data = pytrends.interest_over_time()
        if not data.empty:
            st.line_chart(data[keyword])
        else:
            st.warning(f"Nessun dato per: {keyword}")

# --- GPT Idea Generator ---
st.subheader("💡 Genera Titoli Creativi con GPT")
if "OPENAI_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_KEY"]

    if st.button("🎨 Genera titoli GPT"):
        for keyword in [k.strip() for k in keywords_input.split(",")]:
            prompt = f"""Sei un autore KDP. Genera 5 titoli originali e accattivanti per un libro basato sulla keyword: "{keyword}"."""

            with st.spinner(f"✍️ Generazione titoli per '{keyword}'..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Sei un autore professionista su Amazon KDP."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7
                    )
                    titoli = response.choices[0].message.content.strip()
                    st.markdown(f"**Titoli per '{keyword}':**\n\n{titoli}")
                except Exception as e:
                    st.error(f"Errore durante la generazione: {e}")
else:
    st.warning("❗️ Aggiungi la tua API key OpenAI in Streamlit Secrets")
<PASTE APP.PY CONTENT HERE – OMITTED FOR BREVITY>
