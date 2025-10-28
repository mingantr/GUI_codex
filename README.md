# Codex GUI (PyQt5)

Une interface PyQt5 simple pour utiliser Codex: zone de prompt, zone de réponse en lecture seule, cases à cocher pour insérer des commandes (`/init`, `/status`, `/approvals`), et gestion du dossier courant avec historique des dossiers visités.

## Installation
- Windows: exécuter `install.bat` (crée `.venv`, installe `requirements.txt`).
- Lancement: `run.bat` (utilise `.venv` si présent) ou `python -m app` depuis `src` inclus dans `PYTHONPATH`.

## Raccourcis utiles
- Ctrl+Enter: Envoyer le prompt
- Ctrl+N: Vider le prompt
- Ctrl+O / Ctrl+S: Ouvrir/Enregistrer le prompt depuis/vers un fichier
- Ctrl+T: Basculer le thème (clair/sombre)
- Alt+F4: Quitter

## Style, thème et icône
- Thèmes QSS: `assets/dark.qss` et `assets/light.qss` (chargés selon préférence).
- Menu View > Toggle (Ctrl+T) pour basculer clair/sombre. Préférence persistée.
- Icône fenêtre: `assets/icon.svg`.

## Utilisation
- Dossier: sélectionner via le bouton « Changer… » ou choisir dans l'historique.
- Cases: cochez `/init`, `/status`, `/approvals` pour préfixer votre prompt.
- Envoyer: cliquez « Envoyer » ou utilisez Ctrl+Enter. L’appli transmet désormais le prompt au Codex CLI configuré (voir ci‑dessous) et affiche la sortie capturée.

### Intégration Codex CLI
L’application pilote Codex en mode non‑interactif via `codex exec` (par défaut) et passe le prompt comme argument, dans le dossier courant choisi. Vous pouvez aussi basculer en mode stdin.

1) Configurez `.env` (copiez d’abord `.env.example`):

   - Commande: `CODEX_CLI=npx -y @openai/codex` (ou `codex` si présent dans le PATH)
   - Mode: `CODEX_MODE=exec` (par défaut) ou `stdin`
   - Approvals: `CODEX_APPROVALS=on-request` (transmis en `-a/--ask-for-approval`), ou via la liste déroulante de l’UI
   - Sans TUI: `CODEX_NO_TUI=1` ajoute `--no-tui` en mode exec
   - Full auto (optionnel): `CODEX_FULL_AUTO=1` ajoute `--full-auto` (≡ sandbox workspace-write + approvals on-failure)
   - YOLO (dangereux): `CODEX_YOLO=1` ajoute `--yolo` (désactive sandbox + approvals)
   - Profil: `CODEX_PROFILE=my-profile` (ajoute `--profile my-profile`)
   - JSON: `CODEX_JSON=1` (ajoute `--json`)
   - Sortie: `CODEX_OUTPUT=path\to\last.txt` (ajoute `-o <path>`)
   - Reprendre: `CODEX_RESUME_LAST=1` (ajoute `exec resume --last`)
   - Flags extra: `CODEX_FLAGS=...` pour transmettre des options supplémentaires

2) Variables nécessaires (ex. `OPENAI_API_KEY`) si votre outil en requiert.

3) Lancez l’app (`run.bat`). Au clic sur « Envoyer », la sortie stdout/stderr est affichée. Timeout 120s.

Notes:
- Les « slash‑commands » comme `/init` et `/status` sont insérées au début du prompt depuis l’UI.
- La politique d’« approvals » se règle via la liste déroulante (ou `CODEX_APPROVALS` → `-a`).
 - L’UI propose aussi: JSON, Profil, Resume --last, et un sélecteur de fichier pour `-o`.

### Configuration persistante de Codex
Codex peut aussi lire un fichier de configuration persistant:
- Windows: `%USERPROFILE%\.codex\config.toml`
- Unix: `~/.codex/config.toml`

Exemple `config.toml`:
```
approval_policy = "on-request"
sandbox_mode    = "workspace-write"
model           = "gpt-5-codex"
```
L’UI/Backend n’écrivent pas ce fichier; c’est lu côté Codex CLI.

### Profils et sorties exploitables
- Profils: définissez-les côté Codex et passez-les avec `--profile` (ou `CODEX_PROFILE`).
- Sortie JSONL: cochez "JSON" dans l'UI ou `CODEX_JSON=1` pour `--json`.
- Sauvegarder le dernier message: utilisez le bouton "Sortie" (ajoute `-o <path>`), ou `CODEX_OUTPUT`.
- Reprendre une exécution: cochez "Resume --last" (ajoute `exec resume --last`) et entrez un prompt de continuation.

## Captures d’écran
![Aperçu](assets/screenshot.png)

Ajoutez votre capture dans `assets/screenshot.png` (un fichier placeholder est fourni). Le projet reste portable: tous les chemins sont relatifs, vous pouvez copier/renommer le dossier sans modification.

## Build binaire (Windows)
- Prérequis: PyInstaller (`pip install pyinstaller`).
- Construire: `scripts\build.bat`. Résultat: `dist\PyQtTemplate\PyQtTemplate.exe`.
