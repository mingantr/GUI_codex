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
- Cases: cochez `/init`, `/status`, `JSON`, `Resume --last` (présentées en 2 colonnes) pour préfixer le prompt ou ajuster la sortie.
- Approvals: choisissez « Ask », « Auto » ou « Full Access » dans la liste déroulante. Chaque option décrit exactement les permissions accordées (texte identique au CLI non interactif).
- Envoyer: cliquez « Envoyer » ou utilisez Ctrl+Enter. L’appli transmet désormais le prompt au Codex CLI configuré (voir ci‑dessous) et affiche la sortie capturée.

### Historique et base de données
- L’application journalise chaque échange dans une base SQLite (par défaut `~/.codex_gui/history.sqlite3`).
- Le champ « Base de données » permet de choisir un autre fichier via « Parcourir… ».
- Cliquez sur « Ouvrir… » pour consulter l’historique dans un tableau à deux colonnes (Prompt / Réponse), sans recourir à des onglets.

### Intégration Codex CLI
L’application pilote Codex en mode non‑interactif via `codex exec` (par défaut) et passe le prompt comme argument, dans le dossier courant choisi. Vous pouvez aussi basculer en mode stdin.

ℹ️ Compatibilité CLI: si la commande échoue avec `--no-tui` ou `--cd`, l’application relance automatiquement l’exécution sans ce flag ou avec l’ancien `-C`, afin de rester compatible avec les versions récentes et historiques du binaire.

#### Lancer des slash-commands hors TUI
Les slash-commands (`/init`, `/status`, `/approvals`, `/model`, etc.) sont uniquement du texte injecté au début du prompt. Hors session interactive, il suffit de les inclure dans l’argument transmis à `codex exec`.

```powershell
codex exec -C "D:\devs\mon_projet" `
  -m gpt-5-codex `
  -s workspace-write `
  -a on-request `
  "/init fastapi --package taolenn_api --with-tests
  Configure un endpoint /healthz et un CI GitHub Actions"
```

Depuis Python, même principe via `subprocess.run`:

```python
import subprocess
import textwrap

prompt = textwrap.dedent(
    """
/init react vite typescript --eslint --vitest
Ajoute un formulaire de login (mock) et une page /about.
"""
)
result = subprocess.run(
    [
        "codex",
        "exec",
        "-C",
        "D:\\devs\\mon_app",
        "-m",
        "gpt-5-codex",
        "-s",
        "workspace-write",
        "-a",
        "on-request",
        prompt,
    ],
    capture_output=True,
    text=True,
)
print(result.stdout)
```

Les commandes sont interprétées côté agent exactement comme dans la TUI.

1) Configurez `.env` (copiez d’abord `.env.example`):

   - Commande: `CODEX_CLI=npx -y @openai/codex` (ou `codex` si présent dans le PATH)
   - Mode: `CODEX_MODE=exec` (par défaut) ou `stdin`
   - Approvals modernes: `CODEX_APPROVAL_MODE=auto` (transmis en `--approval-mode`; l’UI utilise cette valeur)
   - Approvals legacy: `CODEX_APPROVALS=on-request` (repli automatique si `--approval-mode` n’est pas reconnu)
   - Sandbox: `CODEX_SANDBOX=workspace-write` ajoute `-s/--sandbox workspace-write`
   - Modèle: `CODEX_MODEL=gpt-5-codex` ajoute `-m/--model`
   - Sans TUI: `CODEX_NO_TUI=1` tente `--no-tui` en mode exec (repli automatique si non reconnu)
   - Full auto (optionnel): `CODEX_FULL_AUTO=1` ajoute `--full-auto` (≡ sandbox workspace-write + approvals on-failure)
   - YOLO (dangereux): `CODEX_YOLO=1` ajoute `--yolo` (désactive sandbox + approvals)
   - Profil: `CODEX_PROFILE=my-profile` (ajoute `--profile my-profile`)
   - JSON: `CODEX_JSON=1` (ajoute `--json`)
   - Sortie: `CODEX_OUTPUT=path\to\last.txt` (ajoute `-o <path>`)
   - Reprendre: `CODEX_RESUME_LAST=1` (ajoute `exec resume --last`)
   - Flags extra: `CODEX_FLAGS=...` pour transmettre des options supplémentaires
   - Shell forcé: `CODEX_USE_SHELL=1` exécute via `shell=True` (par défaut seulement sur Windows lorsque nécessaire)

2) Variables nécessaires (ex. `OPENAI_API_KEY`) si votre outil en requiert.

3) Lancez l’app (`run.bat`). Au clic sur « Envoyer », la sortie stdout/stderr est affichée. Timeout 120s.

#### Approvals & sandbox
- `--approval-mode`: valeurs `ask`, `auto`, `full-access`. L’UI expose ces modes avec le même texte explicatif que le CLI (par ex. « Auto – Codex can read files, make edits... »).
- `--ask-for-approval`: valeurs `never`, `on-request`, `on-failure`, `untrusted` (utilisées automatiquement si le CLI ne connaît pas encore `--approval-mode`).
- `-s/--sandbox`: choisissez `sandbox`, `workspace-write`, `workspace-read`, etc., selon le niveau d’accès disque souhaité.
- `--full-auto`: équivaut à `-s workspace-write` + `-a on-failure`.
- `--yolo`: désactive sandbox et approvals (dangereux, à réserver aux environnements de test).

#### Sorties scriptables
- `--json`: flux d’événements JSONL pour chaîner l’exécution dans vos outils.
- `-o <path>`: sauvegarde le dernier message (exposé via le bouton « Sortie » de l’UI).
- `exec resume --last`: relance la dernière exécution (coche « Resume --last »).
- `codex exec --json --output events.jsonl "..."`: capture structurée prête pour CI/CD.

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

#### Erreur « Not inside a trusted directory »
Lorsque Codex retourne ce message (ou l’équivalent localisé), le dossier courant n’est pas marqué comme sûr. Le backend relance automatiquement la commande avec `--skip-git-repo-check` (mode `auto` par défaut) et affiche une note informative. Si la vérification reste bloquante, appliquez l’une des solutions suivantes:
1. Relancer avec `--skip-git-repo-check` forcé (`CODEX_SKIP_GIT_CHECK=1`) pour contourner la vérification.
2. Initialiser un dépôt Git dans le dossier (`git init && git add . && git commit`) pour que Codex le considère comme versionné.
3. Ajouter le chemin à la section `[trust]` de `~/.codex/config.toml` (ou `%USERPROFILE%\.codex\config.toml` sous Windows).

## Captures d’écran
![Aperçu](assets/screenshot.png)

Ajoutez votre capture dans `assets/screenshot.png` (un fichier placeholder est fourni). Le projet reste portable: tous les chemins sont relatifs, vous pouvez copier/renommer le dossier sans modification.

## Build binaire (Windows)
- Prérequis: PyInstaller (`pip install pyinstaller`).
- Construire: `scripts\build.bat`. Résultat: `dist\PyQtTemplate\PyQtTemplate.exe`.
