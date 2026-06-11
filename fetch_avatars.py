import urllib.request
import json
import time
import os

avatars = ['Goku', 'Gohan', 'Vegeta', 'Bulma', 'Rangiku', 'Yoruichi', 'Tsunade', 'Itachi', 'Jiraiya', 'Naruto', 'Hinata', 'Ichigo', 'Orihime', 'Aizen', 'Luffy', 'Zoro', 'Boa Hancock', 'Robin', 'Nami', 'Sanji']

os.makedirs('ui/assets/avatars', exist_ok=True)

print("Starting avatar download...")
for name in avatars:
    url = f'https://api.jikan.moe/v4/characters?q={name.replace(" ", "%20")}&limit=1'
    filepath = f'ui/assets/avatars/{name.replace(" ", "_")}.jpg'
    
    if os.path.exists(filepath):
        print(f"Skipping {name}, already exists.")
        continue
        
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data['data']:
                img_url = data['data'][0]['images']['jpg']['image_url']
                urllib.request.urlretrieve(img_url, filepath)
                print(f'Downloaded {name}')
            else:
                print(f'No image for {name}')
    except Exception as e:
        print(f'Failed {name}: {e}')
    time.sleep(1) # rate limit
print("Finished!")
