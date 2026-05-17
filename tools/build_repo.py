from __future__ import annotations

from hashlib import md5
from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET

GITHUB_USERNAME = "1advent"
REPO_NAME = "kodiskin"
HELPER_ADDON_ID = "script.fentastic.helper"
SKIN_ADDON_ID = "skin.fentastic.oneadvent"
REPO_ADDON_ID = "repository.oneadvent"
REPO_VERSION = "1.2.3"
PAGES_BASE = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}"

ROOT = Path(__file__).resolve().parent.parent
HELPER_DIR = ROOT / HELPER_ADDON_ID
SKIN_DIR = ROOT / "src"
REPO_DIR = ROOT / REPO_ADDON_ID
DOCS_DIR = ROOT / "docs"
ZIPS_DIR = DOCS_DIR / "zips"
HELPER_VERSION = ET.parse(HELPER_DIR / "addon.xml").getroot().attrib["version"]
SKIN_VERSION = ET.parse(SKIN_DIR / "addon.xml").getroot().attrib["version"]


def write_repository_addon_xml() -> None:
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<addon id="{REPO_ADDON_ID}" version="{REPO_VERSION}" name="Oneadvent Repository"
	provider-name="Oneadvent">
	<extension point="xbmc.addon.repository" name="Oneadvent Repository">
        <dir>
            <info compressed="false">{PAGES_BASE}/addons.xml</info>
            <checksum>{PAGES_BASE}/addons.xml.md5</checksum>
            <datadir zip="true">{PAGES_BASE}/zips/</datadir>
        </dir>
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
            <screenshot>icon.png</screenshot>
            <screenshot>icon.png</screenshot>
            <screenshot>icon.png</screenshot>
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


def copy_addon_assets(addon_dir: Path, addon_id: str) -> None:
    out_dir = ZIPS_DIR / addon_id
    addon_xml = ET.parse(addon_dir / "addon.xml").getroot()
    assets = addon_xml.find("./extension[@point='xbmc.addon.metadata']/assets")
    if assets is None:
        return
    for node in assets:
        if not node.text:
            continue
        rel = Path(node.text.strip())
        src = addon_dir / rel
        if not src.exists() or src.is_dir():
            continue
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def read_addon_xml_without_declaration(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines).strip() + "\n"


def build_addons_xml() -> None:
    body = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n"
    for addon_xml in [HELPER_DIR / "addon.xml", SKIN_DIR / "addon.xml"]:
        addon_text = read_addon_xml_without_declaration(addon_xml)
        indented = "\n".join(("  " + line) if line else "" for line in addon_text.splitlines())
        body += indented + "\n"
    body += "</addons>\n"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "addons.xml").write_text(body, encoding="utf-8")
    (DOCS_DIR / "addons.xml.md5").write_text(md5(body.encode("utf-8")).hexdigest(), encoding="utf-8")


def write_site_index() -> None:
    repo_zip = f"{REPO_ADDON_ID}-{REPO_VERSION}.zip"
    helper_zip = f"{HELPER_ADDON_ID}-{HELPER_VERSION}.zip"
    skin_zip = f"zips/{SKIN_ADDON_ID}/{SKIN_ADDON_ID}-{SKIN_VERSION}.zip"
    content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Fentastic Oneadvent Skin</title>
</head>
<body>
    <h1>Fentastic Oneadvent Skin</h1>
    <p>Custom Kodi skin build based on FENtastic by Ivar Brandt.</p>

    <h2>Install in Kodi</h2>
    <ol>
        <li>Add this source in Kodi File Manager: {PAGES_BASE}/</li>
        <li>Open Install from zip file</li>
        <li>Select {REPO_ADDON_ID}-{REPO_VERSION}.zip</li>
        <li>Open Oneadvent Repository, then Look and feel, then Skin</li>
        <li>Install Fentastic Oneadvent Skin</li>
    </ol>

    <p>The helper add-on required by the skin is bundled in this repository.</p>

    <h2>Files</h2>
    <ul>
        <li><a href="{repo_zip}">{REPO_ADDON_ID}-{REPO_VERSION}.zip</a></li>
        <li><a href="{helper_zip}">{HELPER_ADDON_ID}-{HELPER_VERSION}.zip</a></li>
        <li><a href="{skin_zip}">{SKIN_ADDON_ID}-{SKIN_VERSION}.zip</a></li>
        <li><a href="addons.xml">addons.xml</a></li>
        <li><a href="addons.xml.md5">addons.xml.md5</a></li>
    </ul>

    <h2>Credits</h2>
    <p>Based on <a href="https://github.com/ivarbrandt/skin.fentastic">FENtastic</a> by <a href="https://github.com/ivarbrandt">Ivar Brandt</a>.</p>

    <h2>Source</h2>
    <p><a href="https://github.com/{GITHUB_USERNAME}/{REPO_NAME}">https://github.com/{GITHUB_USERNAME}/{REPO_NAME}</a></p>
</body>
</html>
'''
    (DOCS_DIR / "index.html").write_text(content, encoding="utf-8")
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    if ZIPS_DIR.exists():
        shutil.rmtree(ZIPS_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ZIPS_DIR.mkdir(parents=True, exist_ok=True)

    for pattern in (
        f"{REPO_ADDON_ID}-*.zip",
        f"{HELPER_ADDON_ID}-*.zip",
        f"{SKIN_ADDON_ID}-*.zip",
    ):
        for path in DOCS_DIR.glob(pattern):
            path.unlink()

    write_repository_addon_xml()
    helper_zip_path = zip_addon(HELPER_DIR, HELPER_ADDON_ID, HELPER_VERSION)
    skin_zip_path = zip_addon(SKIN_DIR, SKIN_ADDON_ID, SKIN_VERSION)
    repo_zip_path = zip_addon(REPO_DIR, REPO_ADDON_ID, REPO_VERSION)
    copy_addon_assets(HELPER_DIR, HELPER_ADDON_ID)
    copy_addon_assets(SKIN_DIR, SKIN_ADDON_ID)
    copy_addon_assets(REPO_DIR, REPO_ADDON_ID)
    shutil.copy2(helper_zip_path, DOCS_DIR / helper_zip_path.name)
    shutil.copy2(repo_zip_path, DOCS_DIR / repo_zip_path.name)
    build_addons_xml()
    write_site_index()
    print("Build complete")


if __name__ == "__main__":
    main()
