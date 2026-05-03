from __future__ import annotations

from hashlib import md5
from pathlib import Path
import shutil
import zipfile

GITHUB_USERNAME = "1advent"
REPO_NAME = "kodiskin"
SKIN_ADDON_ID = "skin.fentastic.oneadvent"
SKIN_VERSION = "1.0.1"
REPO_ADDON_ID = "repository.oneadvent"
REPO_VERSION = "1.0.0"
PAGES_BASE = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}"

ROOT = Path(__file__).resolve().parent.parent
SKIN_DIR = ROOT / "src"
REPO_DIR = ROOT / REPO_ADDON_ID
DOCS_DIR = ROOT / "docs"
ZIPS_DIR = DOCS_DIR / "zips"


def write_repository_addon_xml() -> None:
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<addon id="{REPO_ADDON_ID}" version="{REPO_VERSION}" name="Oneadvent Repository"
	provider-name="Oneadvent">
	<extension point="xbmc.addon.repository" name="Oneadvent Repository">
		<info compressed="false">{PAGES_BASE}/addons.xml</info>
		<checksum>{PAGES_BASE}/addons.xml.md5</checksum>
		<datadir zip="true">{PAGES_BASE}/zips/</datadir>
	</extension>
	<extension point="xbmc.addon.metadata">
		<summary lang="en_GB">Oneadvent Kodi repository</summary>
		<summary lang="en_US">Oneadvent Kodi repository</summary>
		<summary lang="en_NZ">Oneadvent Kodi repository</summary>
		<description lang="en_GB">Repository for Fentastic Oneadvent Skin.</description>
		<description lang="en_US">Repository for Fentastic Oneadvent Skin.</description>
		<description lang="en_NZ">Repository for Fentastic Oneadvent Skin.</description>
		<platform>all</platform>
		<assets>
			<icon>icon.png</icon>
			<fanart>fanart.jpg</fanart>
		</assets>
	</extension>
</addon>
'''
    (REPO_DIR / "addon.xml").write_text(content, encoding="utf-8")


def zip_addon(addon_dir: Path, addon_id: str, version: str) -> Path:
    out_dir = ZIPS_DIR / addon_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_zip = out_dir / f"{addon_id}-{version}.zip"
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in addon_dir.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(addon_dir)
            if any(part in {".git", "dist", "__pycache__"} for part in rel.parts):
                continue
            if path.suffix.lower() in {".pyc", ".pyo"}:
                continue
            zf.write(path, (Path(addon_id) / rel).as_posix())
    return out_zip


def read_addon_xml_without_declaration(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines).strip() + "\n"


def build_addons_xml() -> None:
    body = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n"
    for addon_xml in [REPO_DIR / "addon.xml", SKIN_DIR / "addon.xml"]:
        addon_text = read_addon_xml_without_declaration(addon_xml)
        indented = "\n".join(("  " + line) if line else "" for line in addon_text.splitlines())
        body += indented + "\n"
    body += "</addons>\n"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "addons.xml").write_text(body, encoding="utf-8")
    (DOCS_DIR / "addons.xml.md5").write_text(md5(body.encode("utf-8")).hexdigest(), encoding="utf-8")


def main() -> None:
    if ZIPS_DIR.exists():
        shutil.rmtree(ZIPS_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ZIPS_DIR.mkdir(parents=True, exist_ok=True)

    write_repository_addon_xml()
    zip_addon(SKIN_DIR, SKIN_ADDON_ID, SKIN_VERSION)
    zip_addon(REPO_DIR, REPO_ADDON_ID, REPO_VERSION)
    build_addons_xml()
    print("Build complete")


if __name__ == "__main__":
    main()
