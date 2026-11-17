IMMOZEN — CORRECTION DU MOTEUR MAISONS / DPE

Cette archive contient les fichiers de remplacement de votre serveur Render déjà opérationnel.

1. Ouvrir le dépôt GitHub LyricSobref/immozen-test.
2. Ajouter/remplacer index.html et server.py à la racine du dépôt.
3. Cliquer sur Commit changes.
4. Sur Render, vérifier que le nouveau déploiement indique "Live".
5. Ouvrir https://immozen-test.onrender.com/ et actualiser avec Ctrl+F5.
6. Tester une annonce de maison avec DPE puis une annonce de terrain.

Le moteur Maisons/Apartements affiche de nouveau un indice de correspondance (%)
par adresse candidate, calculé à partir du DPE, du GES, de la surface, de l'année
et des indices géographiques disponibles. Ce pourcentage n'est PAS une
probabilité statistique ni une adresse confirmée. Le moteur Terrains reste séparé.

La recherche ADEME côté serveur est paginée pour limiter les omissions ;
sur les grandes communes le volume peut rester partiel et le site le signale.
Le bon emplacement ne peut être garanti sans les indices de l'annonce et la
vérification des photos. Aucun mot de passe n'est inclus dans les fichiers.

COMMANDES RENDER CONSERVÉES :
Build command : pip install -r requirements.txt
Start command : python server.py
Variable : IMMOZEN_TEST_PASSWORD (déjà enregistrée dans Render)
