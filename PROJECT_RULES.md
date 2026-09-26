# Règles de travail — PhytoPulse

## Outils de travail

- Éditeur de code : Notepad++.
- Terminal éventuel : Windows PowerShell.
- Claude n’est pas utilisé pour ce projet.
- Les recherches techniques, licences et informations actuelles sont vérifiées avant décision.

## Principes impératifs

1. Analyser avant de modifier.
2. Définir le périmètre, les risques, les critères de réussite et les exclusions.
3. Attendre une validation explicite avant toute écriture, installation, téléchargement,
   authentification, appel réseau, appel d’API, lancement de service ou action Git modifiante.
4. Préférer les changements minimaux, testables et réversibles.
5. Ne jamais versionner, copier ou exposer de secret, jeton, mot de passe, clé API ou fichier `.env`.
6. Ne jamais présenter une hypothèse, une fonction prévue ou un test partiel comme une validation complète.
7. Documenter une fonctionnalité publique uniquement lorsqu’elle est réellement implémentée et testée.
8. Utiliser des données ouvertes dans le respect de leur licence et de leurs règles d’attribution.
9. Préférer les traitements locaux et limiter les téléchargements aux données nécessaires.
10. Examiner systématiquement les limites scientifiques, les coûts, les dépendances, la confidentialité et les risques.

## Règle de communication

Chaque étape doit indiquer clairement :

- ce qui est confirmé ;
- ce qui reste une hypothèse ;
- les risques connus ;
- ce que le test prouve ;
- ce que le test ne prouve pas ;
- la marche arrière éventuelle.