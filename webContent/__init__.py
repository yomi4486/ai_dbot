from bs4 import BeautifulSoup
import wikipedia,json,datetime,spacy,os,requests,re
from urllib.parse import quote
from googletrans import Translator
translator = Translator()
nlp = spacy.load("ja_ginza")
def get_content(url:str):
    """
    引数にURLを指定してください。タグを除いたブラウザ上のコンテンツを日本語に翻訳してかえします。
    
    """
    try:
        response = requests.get(url)
        if 200 <= response.status_code < 304:
            response.encoding = 'utf-8'
            content = BeautifulSoup(response.text, "html.parser")
            description = str(content.find("meta", property="description"))
            body = content.find("body")
            script = content.find_all("script")

            title = content.find('title')
            title = str(title).replace("<title>","").replace("</title>","")
            for i in script:
                body = str(body).replace(str(i),'')

            main_text = re.sub(r'<.*?>', '', str(body))
            main_text = str(main_text).replace("    ","").replace("\n\n","")
            main_text = translator.translate(f"title: {title[:50]} sub_title: {description[:200]} content: {main_text[:4000]}",dest='en').text
            return main_text 
        else:
            return False
    except Exception as e:
        print(e)
        return False

    
def get_wikipedia_description(prompt:str,force_prompt:list):

    """
    引数promptに、ユーザーからのプロンプトを直接入れてください。翻訳済みのテキストだと想定の動作を外れます。
    force-promptに入れられた単語は、テキストマイニングを無視して強制的に単語として認識します。
    返り値はそれぞれの単語の説明を含めたJSON型で返されます。len関数で返り値の長さを取得し、0であればパス、1以上であればシステムプロンプトに追加する、などの処理をとると効率的に処理できると思います
    """
    print(force_prompt)
    if len(prompt) == 0:
        return
    for a in force_prompt:
        prompt = prompt.replace(f"{a}","")
    result_list = []
    if not len(force_prompt) == 0:
        doc = force_prompt
    else:
        doc = nlp(prompt)
    if not os.path.exists("./cache.json"):
        with open("./cache.json","w") as file:
            file.write(json.dumps({}, indent=4,ensure_ascii = False))

    for l in doc:
        try:
            if "普通名詞" in l.tag_ or "固有名詞" in l.tag_:
                siki = True
            else:
                siki = False
        except:
            siki = True
        if siki:
            print(f"「{l}」についての情報の取得中です。")
            try:
                with open("./cache.json","r",encoding="utf-8") as file:
                    cache_dict = dict(json.load(file))
            
                if not f"{str(l).lower()}" in cache_dict:
                    
                    try:
                        title_text = wikipedia.search(str(l).lower(),results=1)[0]
                        content_text = wikipedia.summary(str(l).lower(), sentences=0)
                    except:
                        with open("./cache.json","w",encoding="utf-8") as file:
                            file.write(json.dumps(cache_dict, indent=4,ensure_ascii = False))
                        break
                    new_data = {
                        f"{str(l).lower()}": {
                            "title":f"{title_text}",
                            "description":f"{content_text}",
                            "last_update":int(datetime.datetime.now().strftime('%m'))
                        }
                    }
                    cache_dict.update(new_data)
                    with open("./cache.json","w",encoding="utf-8") as file:
                        file.write(json.dumps(cache_dict, indent=4,ensure_ascii = False))
                else:
                    if not int(cache_dict[f"{str(l).lower()}"]["last_update"]) == int(datetime.datetime.now().strftime('%m')):
                        try:
                            title_text = wikipedia.search(str(l).lower(),results=1)[0]
                            content_text = wikipedia.summary(str(l).lower(), sentences=0)
                        except:
                            with open("./cache.json","w",encoding="utf-8") as file:
                                file.write(json.dumps(cache_dict, indent=4,ensure_ascii = False))
                            break
                        new_data = {
                            f"{str(l).lower()}": {
                                "title":f"{title_text}",
                                "description":f"{content_text}",
                                "last_update":int(datetime.datetime.now().strftime('%m'))
                            }
                        }
                        cache_dict.update(new_data)
                        with open("./cache.json","w",encoding="utf-8") as file:
                            file.write(json.dumps(cache_dict, indent=4,ensure_ascii = False))
                    else:
                        try:
                            title_text = wikipedia.search(str(l).lower(),results=1)[0]
                            content_text = wikipedia.summary(str(l).lower(), sentences=0)
                        except:
                            pass
                        with open("./cache.json","w",encoding="utf-8") as file:
                            file.write(json.dumps(cache_dict, indent=4,ensure_ascii = False))
                result_list.append(f"{title_text}")
            except Exception as e:
                print(e)
    return result_list

print("Ready: webContent")