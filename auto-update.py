import requests
import base64
import os

# GitHub Secrets-இல் இருந்து பாதுகாப்பாக விவரங்களை எடுக்கிறது
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MAC = os.getenv("MAC")
SN = os.getenv("SN")
DID = os.getenv("DID")

# கான்பிகரேஷன்
SOURCE_M3U_URL = "https://raw.githubusercontent.com/megadevid2-creator/mega-devid/refs/heads/main/Regular%20Use.m3u"
REPO_OWNER = "megadevid2-creator"
REPO_NAME = "Stylish-Rolex"
FILE_PATH = "Testing.m3u"
BASE_URL = "http://tv.turbo4k.cc/stalker_portal"
UA = "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3"

REPLACE_MAP = {
    "Colors Tamil HD": "COLORS TAMIL HD",
    "Jaya TV HD": "JAYA TV HD",
    "KTV HD": "KTV 4K",
    "Sun TV HD": "SUN TV HD",
    "Star Vijay HD": "STAR VIJAY INDIA HD",
    "Vijay Super HD": "VIJAY SUPER FHD",
    "Zee Thirai HD": "ZEE THIRAI",
    "Sun Music HD": "SUN MUSIC HD"
}

def is_link_working(url):
    """GitHub-இல் உள்ள பழைய லிங்க் வேலை செய்கிறதா எனச் சோதிக்கும்"""
    try:
        r = requests.head(url, timeout=5, headers={"User-Agent": UA})
        return r.status_code == 200
    except:
        return False

def get_portal_links():
    """போர்ட்டலில் இருந்து புதிய லிங்குகளை எடுக்கும்"""
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Cookie": f"mac={MAC}; stb_lang=en;"})
    try:
        api = f"{BASE_URL}/server/load.php"
        r = s.get(f"{api}?type=stb&action=handshake&JsHttpRequest=1-xml").json()
        token = r.get("js", {}).get("token")
        s.get(f"{api}?type=stb&action=get_profile&stb_type=MAG250&sn={SN}&device_id={DID}&JsHttpRequest=1-xml", headers={"Authorization": f"Bearer {token}"})
        c_res = s.get(f"{api}?type=itv&action=get_all_channels&JsHttpRequest=1-xml", headers={"Authorization": f"Bearer {token}"}).json()
        channels = c_res.get("js", {}).get("data", [])
        
        links = {}
        for ch in channels:
            p_name = ch.get("name", "")
            if p_name in REPLACE_MAP.values():
                cmd = ch.get("cmds", [{}])[0].get("url", "")
                l_res = s.get(f"{api}?type=itv&action=create_link&cmd={cmd}&JsHttpRequest=1-xml", headers={"Authorization": f"Bearer {token}"}).json()
                real_url = l_res.get("js", {}).get("cmd", "").replace("ffrt ", "").replace("ffmpeg ", "")
                if real_url.startswith("http"):
                    links[p_name] = real_url
        return links
    except:
        return {}

def run_automation():
    print(">>> Checking Link Health...")
    response = requests.get(SOURCE_M3U_URL)
    lines = response.text.splitlines()
    broken_list = []
    
    # லிங்குகளைச் சோதித்தல்
    for i, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            m_name = line.split(",")[-1].strip()
            if m_name in REPLACE_MAP and i + 1 < len(lines):
                if not is_link_working(lines[i+1]):
                    broken_list.append(m_name)

    if broken_list:
        print(f"Found Broken Links: {broken_list}. Fetching new ones...")
        portal_links = get_portal_links()
        
        updated_m3u = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#EXTINF"):
                m_name = line.split(",")[-1].strip()
                updated_m3u.append(line)
                p_target = REPLACE_MAP.get(m_name)
                if m_name in broken_list and p_target in portal_links:
                    updated_m3u.append(portal_links[p_target])
                else:
                    updated_m3u.append(lines[i+1])
                i += 1
            else:
                updated_m3u.append(line)
            i += 1
        
        # GitHub-இல் புதிய கோப்பை அப்லோட் செய்தல்
        content = "\n".join(updated_m3u)
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        sha = requests.get(url, headers=headers).json().get('sha')
        
        data = {"message": f"Auto-Repair: {broken_list}", "content": base64.b64encode(content.encode()).decode(), "sha": sha}
        requests.put(url, headers=headers, json=data)
        print("Success: Links updated on GitHub!")
    else:
        print("Everything is working fine. No update needed.")

if __name__ == "__main__":
    run_automation()

