IMMOZEN — TEST SUR RENDER (PRIVÉ)
================================
1) Dans GitHub, ouvrir le dépôt immozen-test (branche main).
2) Ajouter à la RACINE du dépôt les fichiers suivants :
   - index.html
   - server.py
   - requirements.txt
3) Dans Render > Web Service > Configuration :
   Language: Python 3
   Branch: main
   Region: Frankfurt
   Root Directory: VIDE
   Build Command: pip install -r requirements.txt
   Start Command: python server.py
   Instance: Free (0 $)
4) Dans Render > Environment Variables, AJOUTER :
   Clé: IMMOZEN_TEST_PASSWORD
   Valeur: choisir un mot de passe long, nouveau et privé.
   Ne jamais inclure ce mot de passe dans GitHub ou dans un message ChatGPT.
5) Cliquer Deploy. Lorsque l'URL HTTPS est active, le navigateur demandera
   un identifiant : immozen, et le mot de passe choisi.

LIMITES
- Ceci est un prototype de TEST, pas un service de production.
- Le serveur ne peut lire que les annonces et images accessibles publiquement.
- Les restrictions des plateformes restent applicables.
- L'OCR dépend d'une bibliothèque externe chargée dans le navigateur.
- Les données cadastrales nationales peuvent nécessiter des téléchargements importants,
  et l'offre gratuite a des limites de ressources.
- Ne pas communiquer l'URL privée et éviter d'y importer des données personnelles.
- La reconnaissance de paysage, les données Sitadel/DMPC et un index national PostGIS
  ne sont pas intégrés automatiquement.
