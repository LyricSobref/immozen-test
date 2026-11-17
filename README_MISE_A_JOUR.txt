ImmoZen — correctifs v8 (recherche du 17 novembre 2026)

Remplacer index.html et server.py dans le dépôt GitHub immozen-test, puis valider avec Commit changes.
Ne pas remplacer requirements.txt (identique). Render redéploie automatiquement.
Après affichage Live, Ctrl+F5. Vérifier que l’onglet du navigateur porte le titre « ImmoZen — Recherche améliorée v8 » et que la page indique « Recherche améliorée · mise à jour v8 ».

Corrections:
- Barre de progression flottante visible pendant l'analyse (pas d'affichage Photo x sur y dans le parcours public).
- Les résultats DPE affichent un indice en pourcentage, et la première proposition est montrée sans faire sauter automatiquement le défilement.
- Earth ouvre sur des coordonnées explicites, sans interprétation textuelle; lien distinct pour télécharger un repère KML à ouvrir dans Google Earth.
- Les cinq premières propositions DPE sont rapprochées de l'adresse géocodée BAN de la commune; si le point ADEME est éloigné, la position est rectifiée sur l’adresse vérifiée.

Limites : la barre mesure les étapes accomplies et non les chances de succès. Earth Web ne garantit pas de repère automatique à partir d’un simple lien; importer le KML pour faire apparaître un point. Sans adresse officielle sûre, une proposition reste à vérifier.
