# Fentastic Oneadvent Skin — Kodi Repository

A custom Kodi skin and repository hosted via **GitHub Pages**.

## Repository Structure

```
kodiskin/
├── src/                     ← Skin source code
├── repository.oneadvent/    ← Kodi repository addon metadata
├── docs/                    ← GitHub Pages root (this is your Kodi repo URL)
│   ├── addons.xml
│   ├── addons.xml.md5
│   └── zips/
│       ├── skin.fentastic.oneadvent/
│       └── repository.oneadvent/
├── tools/
│   └── build_repo.py        ← Run to rebuild distribution
└── README.md
```

## Enabling GitHub Pages

In your GitHub repo settings → **Pages**:
- Source: **Deploy from a branch**
- Branch: `main`, folder `/docs`
- Your Kodi repo URL will be: `https://1advent.github.io/kodiskin/`

## Installing in Kodi

1. **Settings → File Manager → Add Source**
2. URL: `https://1advent.github.io/kodiskin/`
3. Name it (e.g. `Oneadvent`)
4. **Add-ons → Install from zip file** → select your source → install `repository.oneadvent-1.0.0.zip`
5. Install the skin from within that repository

## Releasing a New Version

1. Edit files in `src/`
2. Bump `SKIN_VERSION` in `tools/build_repo.py`
3. Update `src/changelog.txt`
4. Run: `python tools/build_repo.py`
5. Commit and push — done

## GitHub Repo

- GitHub repository: `https://github.com/1advent/kodiskin`
- GitHub Pages URL: `https://1advent.github.io/kodiskin/`

Run `python tools/build_repo.py` after any release change, then commit and push.
