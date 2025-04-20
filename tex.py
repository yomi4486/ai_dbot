import base64,requests,sys

if(len(sys.argv) != 2):
    print("must be argment.")
    sys.exit()
def interrogete():
    with open("tex.png","rb")as f :
        content = base64.b64encode(f.read()).decode('utf-8')
    payload = {
        "image": content,
        "model": "clip"
    }
    response = requests.post(url=f'http://127.0.0.1:7861/sdapi/v1/interrogate', json=payload,headers={"Content-Type": "application/json"},)
    r = response.json()
    return r["caption"]
content = interrogete()
print(content)

if sys.argv[1] in content:
    print("exist")
else:
    print("not exits.")