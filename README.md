# Chasseur de bonnes affaires - Cartes de sport NBA

Application web personnelle qui surveille eBay et signale les cartes
NBA en dessous du prix du marché, pour t'aider dans tes achats-reventes.

## Ce dont tu as besoin avant de commencer

- Un compte GitHub (gratuit) : https://github.com/signup
- Un compte Streamlit Community Cloud (gratuit, connexion via GitHub) : https://share.streamlit.io
- Ta clé API eBay Developer (App ID / Client ID et Cert ID / Client Secret)
  — voir les étapes données précédemment sur developer.ebay.com

Aucune installation sur ton ordinateur n'est nécessaire.

## Étape 1 - Mettre le code sur GitHub

1. Va sur https://github.com/new et crée un nouveau dépôt (repository).
   - Nom au choix, par exemple `cartes-nba-bonnes-affaires`
   - Laisse-le en "Private" si tu veux que le code reste confidentiel
   - Coche "Add a README file" n'est pas nécessaire, on a déjà le nôtre
2. Une fois le dépôt créé, clique sur "Add file" > "Upload files"
3. Glisse-dépose les 3 fichiers fournis : `app.py`, `requirements.txt`, `README.md`
4. Clique sur "Commit changes" en bas de la page

## Étape 2 - Déployer sur Streamlit Community Cloud

1. Va sur https://share.streamlit.io et connecte-toi avec ton compte GitHub
2. Clique sur "New app"
3. Sélectionne ton dépôt `cartes-nba-bonnes-affaires`, la branche `main`,
   et indique `app.py` comme fichier principal
4. Avant de cliquer sur "Deploy", clique sur "Advanced settings"
5. Dans la section "Secrets", colle ceci en remplaçant par tes vraies clés :

```toml
EBAY_CLIENT_ID = "ton_app_id_ebay"
EBAY_CLIENT_SECRET = "ton_cert_id_ebay"
```

6. Clique sur "Deploy". Après une à deux minutes, ton appli est en ligne,
   accessible via une URL du type `https://ton-nom-app.streamlit.app`
   depuis n'importe quel navigateur (ordinateur ou téléphone).

## Étape 3 - Utiliser l'appli

- Dans la barre latérale, indique les cartes que tu veux surveiller
  (une par ligne, ex: "Victor Wembanyama Prizm rookie")
- Ajuste le seuil de "bonne affaire" (% en dessous du prix médian observé)
- Clique sur "Lancer la recherche"
- Les annonces repérées comme bonnes affaires s'affichent avec un lien
  direct vers eBay

## Modifier la liste de cartes plus tard

Tu n'as rien à réinstaller : la liste de recherches se modifie directement
dans l'interface de l'appli, à chaque utilisation.

## Limitation à connaître

L'API eBay utilisée (Browse API) donne accès aux annonces **actives**,
pas à l'historique des ventes conclues. Le prix "médian" calculé par
l'appli est donc une estimation basée sur les annonces en cours, ce qui
reste un bon indicateur mais pas un prix de vente réel garanti. Si un
jour tu veux affiner (comparer aux ventes conclues), il faudrait demander
à eBay l'accès à leur API "Marketplace Insights", soumise à validation.

## Coûts

- GitHub : gratuit
- Streamlit Community Cloud : gratuit pour un usage personnel
- API eBay : gratuite jusqu'à un certain volume d'appels quotidiens
  (largement suffisant pour un usage personnel)
