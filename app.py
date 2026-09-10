"""
Détecteur de bonnes affaires - Cartes de sport (NBA en priorité)
------------------------------------------------------------------
Cette application interroge l'API eBay (Browse API) pour une liste
de recherches définies par l'utilisateur, calcule un prix "marché"
(médiane des annonces actives) et met en évidence les annonces
sensiblement moins chères que ce prix de référence.

Limitation connue : l'API Browse d'eBay ne donne accès qu'aux
annonces ACTIVES (pas aux ventes conclues). Le prix de référence
est donc calculé à partir des annonces en cours, pas de l'historique
des ventes. C'est une bonne approximation mais pas parfaite -
à affiner avec le temps si besoin (ex: accès à l'API Marketplace
Insights, soumise à validation par eBay).
"""

import base64
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Chasseur de bonnes affaires - Cartes NBA", layout="wide")

EBAY_OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"


@st.cache_data(ttl=3000, show_spinner=False)
def get_ebay_token(client_id: str, client_secret: str) -> str:
    """Récupère un jeton d'accès OAuth2 (valable ~2h, mis en cache 50 min)."""
    credentials = f"{client_id}:{client_secret}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    response = requests.post(EBAY_OAUTH_URL, headers=headers, data=data, timeout=15)
    response.raise_for_status()
    return response.json()["access_token"]


def search_ebay(token: str, query: str, category_id: str, limit: int = 50) -> list:
    """Recherche des annonces actives pour une requête donnée."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_FR",
    }
    params = {
        "q": query,
        "limit": limit,
        "sort": "price",
    }
    if category_id:
        params["category_ids"] = category_id

    response = requests.get(EBAY_SEARCH_URL, headers=headers, params=params, timeout=15)
    if response.status_code != 200:
        st.error(f"Erreur eBay pour '{query}' : {response.status_code} - {response.text[:200]}")
        return []

    items = response.json().get("itemSummaries", [])
    results = []
    for item in items:
        try:
            price = float(item["price"]["value"])
        except (KeyError, TypeError, ValueError):
            continue
        results.append({
            "recherche": query,
            "titre": item.get("title", ""),
            "prix": price,
            "devise": item.get("price", {}).get("currency", ""),
            "etat": item.get("condition", ""),
            "url": item.get("itemWebUrl", ""),
            "image": item.get("image", {}).get("imageUrl", ""),
        })
    return results


def analyser_recherche(df_query: pd.DataFrame, seuil_pct: float) -> pd.DataFrame:
    """Calcule la médiane et marque les annonces en-dessous du seuil défini."""
    mediane = df_query["prix"].median()
    df_query = df_query.copy()
    df_query["prix_median_reference"] = round(mediane, 2)
    df_query["ecart_pct"] = round(((mediane - df_query["prix"]) / mediane) * 100, 1)
    df_query["bonne_affaire"] = df_query["ecart_pct"] >= seuil_pct
    return df_query


# ---------------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------------

st.title("🏀 Chasseur de bonnes affaires - Cartes de sport")
st.caption("Usage personnel uniquement · Données issues d'eBay (annonces actives)")

with st.sidebar:
    st.header("Configuration")

    client_id = st.secrets.get("EBAY_CLIENT_ID", "")
    client_secret = st.secrets.get("EBAY_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        st.warning(
            "Clé API eBay non configurée. Ajoute EBAY_CLIENT_ID et "
            "EBAY_CLIENT_SECRET dans les 'Secrets' de ton appli "
            "(voir README)."
        )

    category_id = st.text_input(
        "Catégorie eBay (optionnel)",
        value="214",
        help="214 = Basketball Cards sur eBay. Laisse vide pour chercher toutes catégories.",
    )

    seuil_pct = st.slider(
        "Seuil de bonne affaire (% en dessous de la médiane)",
        min_value=5, max_value=60, value=25, step=5,
    )

    nb_resultats = st.slider(
        "Nombre d'annonces à analyser par recherche", 10, 100, 50, step=10,
    )

    st.markdown("---")
    st.subheader("Cartes à surveiller")
    recherches_texte = st.text_area(
        "Une recherche par ligne (ex: nom du joueur + set + année)",
        value=(
            "Victor Wembanyama Prizm rookie\n"
            "LeBron James Optic\n"
            "Luka Doncic Select"
        ),
        height=150,
    )

    lancer = st.button("🔍 Lancer la recherche", type="primary", use_container_width=True)

if lancer:
    if not client_id or not client_secret:
        st.error("Impossible de lancer la recherche : clé API eBay manquante.")
    else:
        requetes = [r.strip() for r in recherches_texte.splitlines() if r.strip()]

        if not requetes:
            st.warning("Ajoute au moins une recherche dans la barre latérale.")
        else:
            with st.spinner("Connexion à eBay..."):
                try:
                    token = get_ebay_token(client_id, client_secret)
                except Exception as e:
                    st.error(f"Échec de l'authentification eBay : {e}")
                    st.stop()

            toutes_les_bonnes_affaires = []
            tous_les_resultats = []

            progress = st.progress(0.0)
            for i, requete in enumerate(requetes):
                resultats = search_ebay(token, requete, category_id, nb_resultats)
                if resultats:
                    df_requete = pd.DataFrame(resultats)
                    df_analysee = analyser_recherche(df_requete, seuil_pct)
                    tous_les_resultats.append(df_analysee)
                    toutes_les_bonnes_affaires.append(df_analysee[df_analysee["bonne_affaire"]])
                progress.progress((i + 1) / len(requetes))
                time.sleep(0.2)  # éviter de saturer l'API

            progress.empty()

            if tous_les_resultats:
                df_final = pd.concat(tous_les_resultats, ignore_index=True)
                df_bonnes_affaires = pd.concat(toutes_les_bonnes_affaires, ignore_index=True) if toutes_les_bonnes_affaires else pd.DataFrame()

                st.success(f"{len(df_final)} annonces analysées sur {len(requetes)} recherche(s) - {datetime.now().strftime('%d/%m/%Y %H:%M')}")

                st.subheader(f"💰 Bonnes affaires détectées ({len(df_bonnes_affaires)})")
                if not df_bonnes_affaires.empty:
                    df_affichage = df_bonnes_affaires.sort_values("ecart_pct", ascending=False)[
                        ["recherche", "titre", "prix", "devise", "prix_median_reference", "ecart_pct", "etat", "url"]
                    ]
                    st.dataframe(
                        df_affichage,
                        column_config={"url": st.column_config.LinkColumn("Lien")},
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Aucune annonce ne dépasse le seuil défini pour l'instant. Essaie de baisser le seuil ou relance plus tard.")

                with st.expander("Voir toutes les annonces analysées"):
                    st.dataframe(
                        df_final.sort_values("ecart_pct", ascending=False)[
                            ["recherche", "titre", "prix", "prix_median_reference", "ecart_pct", "etat", "url"]
                        ],
                        column_config={"url": st.column_config.LinkColumn("Lien")},
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.warning("Aucun résultat trouvé. Vérifie tes termes de recherche ou l'ID de catégorie.")
else:
    st.info("Configure tes recherches dans la barre latérale à gauche, puis clique sur 'Lancer la recherche'.")
