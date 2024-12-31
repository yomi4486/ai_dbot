"""
エナジー教授
./index.py
"""
import ocr,os,asyncio,re,discord,datetime,requests,imageCreater,json,sys,math,threading
from urlextract import URLExtract
from discord import app_commands
from os.path import join, dirname
from dotenv import load_dotenv
from openai import OpenAI # ローカルAPIとの通信に必須
from googletrans import Translator
from logging import StreamHandler,getLogger
from webContent import get_content#,get_wikipedia_description
from daruemon_docker import compose_container
import concurrent.futures

logger = getLogger(__name__)
handler = StreamHandler()
logger.addHandler(handler)
logger.setLevel('ERROR')

# envを読み取るための設定
load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")
APPLICATION_ID = os.environ.get("APPLICATION_ID")
BASE_URL = os.environ.get("base_url")
DEEPL_API_LEY = os.environ.get("DEEPL_API_KEY")

trans_mode = {}
image_mode = {}
kaiwa_dict = {}
weekday_list = ["月","火","水","木","金","土","日"]
lang_list = ["Python","NodeJS","C"] # 実行対応言語一覧
# 実行環境の詳細
lang_param = {
    "python":{
        "version":"3.11-slim",
        "os":"Alpine"
    },
    "nodejs":{
        "version":"v21.6.1",
        "os":"Alpine"
    },
    "c":{
        "version":"N/A",
        "os":"AlpineLinux 3.14"
    }
}

openAI_client = OpenAI(base_url=BASE_URL, api_key="not-needed")

# Discordクライアントインスタンス
client = discord.Client(intents = discord.Intents.all())
intents = discord.Intents.default()
intents.message_content = True
tree = app_commands.CommandTree(client)
translator = Translator()
extractor = URLExtract()

async def get_completion(message:list,ja_prompt:str=""):
    
    # wiki_word_list = f''
    # j={}
    # if not len(ja_prompt) == 0:
    #     word_list = get_wikipedia_description(prompt=ja_prompt,force_prompt=re.findall(r'"(.*?)"',f"{ja_prompt}",re.DOTALL))
    # else:
    #     word_list = []
    # print(word_list)
    # # Wikipediaで検索して結果をsysetmロールとして提供
    # if not len(word_list) ==0:
    #     with open("./cache.json","r",encoding="utf-8") as file:
    #         cache_dict = dict(json.load(file))
    #     for i in word_list:
    #         hoge = cache_dict[f"{str(i).lower()}"]
    #         title = hoge["title"]
    #         description = hoge["description"]
    #         wiki_word_list = f"{wiki_word_list} \n{title}:{description}"

    #     messages = [{"role":"system","content":f"{wiki_word_list}"}]
    #     for a in message:
    #         j.update(dict(a))
    #     messages.append(j)
    # else:
    #     messages = message
    def get_res():
        response = openAI_client.chat.completions.create(
            model=f"{os.environ.get('model')}",
            messages=message,
            temperature=0 # this is the degree of randomness of the model's output
        )
        return response.choices[0].message.content
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(get_res)
        completion = future.result()
        return completion

async def kaiwa_dict_update(message:discord.Message,msg,user_prompt:str,log_dict:dict,code_list:list,lang_mode:int=0):
    """
    message:Discord messageオブジェクト
    msg:リプライ元のメッセージ
    ja_user_prompt:日本語のプロンプト
    user_prompt:ユーザープロンプト
    log_dict:daruemon_dockerの返り値
    """
    global kaiwa_dict,trans_mode
    ja_user_prompt = user_prompt
    try:
        user_prompt = user_prompt.replace(f"```{lang_list[lang_mode].lower()}","").replace("```","")
        user_prompt = translate_ignore_code(base_text=user_prompt,mode="en")
    except:
        pass
    
    if message.attachments:
        if len(user_prompt) == 0:
            user_prompt = "\nWhat is the image?"
        user_prompt += await ocr.get_content(message.attachments)

    if f"{message.author.name}" in kaiwa_dict :
        if len(kaiwa_dict[message.author.name]) >= 6:
            del kaiwa_dict[message.author.name][0]
            del kaiwa_dict[message.author.name][0]
    if msg is None:
        if not f"{message.author.name}" in kaiwa_dict :
            kaiwa_dict.update({f"{message.author.name}":[{"role":"user","content":user_prompt}]})
        else:
            kaiwa_dict[f"{message.author.name}"].append({"role":"user","content":user_prompt})
        if not len(code_list) == 0 and not lang_mode == -1:
            kaiwa_dict[f"{message.author.name}"].append({"role":"user","content":f"This is the result of executing the code written by the user on the system below. Please use it to give advice to users. Language:{lang_list[lang_mode]} \nversion:{lang_param[f'{str(lang_list[lang_mode]).lower()}']['version']} \nexit_code{log_dict['exit_code']}({log_dict['status_label']})\nlogs:\n```{log_dict['logs'][:1000]}```"})
        result = await get_completion(kaiwa_dict[f"{message.author.name}"],ja_prompt=ja_user_prompt)
    else:
        if msg.author.id == APPLICATION_ID:
            result = await get_completion([{"role":"assistant","content":f"{msg.content}"},{"role":"user","content":user_prompt}],ja_prompt=ja_user_prompt)
        else:
            result = await get_completion([{"role":"system","content":f"{msg.content}\nThe message is created by '{msg.author.display_name}'."},{"role":"user","content":user_prompt}],ja_prompt=ja_user_prompt)
        if not f"{message.author.name}" in kaiwa_dict :
            kaiwa_dict.update({f"{message.author.name}":[{"role":"assistant","content":result}]})
        else:
            kaiwa_dict[f"{message.author.name}"].append({"role":"assistant","content":result})
    return result

class MyView(discord.ui.View):
    def __init__(self,url:str="https://www.deepl.com/ja/your-account/usage",label:str="DeepL APIアカウントページを開く"):
        super().__init__()
        # URLを含むボタンを作成
        self.add_item(discord.ui.Button(label=f"{label}", url=f"{url}"))

async def disconnect(message:discord.Message):
    await message.guild.voice_client.disconnect()

def half_num_to_full(text:str):
    num_list = ["０","１","２","３","４","５","６","７","８","９"]
    for i in num_list:
        text = text.replace(i,f"{int(i)}")
    return text

def translate_ignore_code(base_text:str,mode:str):
    """
    バッククオートで囲まれたコードや固有名詞を除外して翻訳を行う関数です
    """
    # base_textにはAIが出力したプロンプトを入れる    
    code_list = re.findall(r'```(.*?)```',f"{base_text}",re.DOTALL) # コードがある場合は検出し、抜き出す

    hoge0 = ["a","b","c","d","e","f","g","h","i","j"]
    hoge1 = ["k","l","m","n","o","p","q","r","s","t","u","v","w","x","z","a1","a2","a3","a4","a5","a6","a7","a8","a9","a0"]
    p1 = 0 # カウント用の仮の変数
    for i in code_list:
        base_text = base_text.replace(f"```{i}```",f"__{hoge0[p1]}__") # コードを仮文字に置き換える
        p1 +=1
    
    p2 = 0
    section_list = re.findall(r'`(.*?)`',f"{base_text}",re.DOTALL)
    for i in section_list:
        base_text = base_text.replace(f"`{i}`",f"{hoge1[p2]}&") # コードを仮文字に置き換える
        p2 +=1
    try:
        params = {
            'auth_key':DEEPL_API_LEY,
            'text':base_text,
            'target_lang': f'{mode.upper()}'
        }
        request = requests.post("https://api-free.deepl.com/v2/translate",data=params)
        res = request.json()
        translated_text = res["translations"][0]["text"]
    except:
        translated_text = translator.translate(base_text,dest=mode).text
    translated_text = half_num_to_full(str(translated_text).replace("＆","&")) # 仮文字のが全角になることがあるため対策
    p3 = 0 # 初期化
    for i in code_list:
        translated_text = translated_text.replace(f"__{hoge0[p3]}__",f"```{i}```\n-# AIによって生成されたコードです。慎重にご利用ください。\n").replace(f"__{str(hoge0[p3]).upper()}__",f"```{i}```\n-# AIによって生成されたコードです。慎重にご利用ください。\n") # 翻訳時に仮文字が大文字になることがあるので、修正
        p3+=1
    
    p4 = 0 # 初期化
    for i in section_list:
        translated_text = translated_text.replace(f"{hoge1[p4]}&",f"`{i}`").replace(f"{str(hoge1[p4]).upper()}&",f"`{i}`")
        p4 +=1
    lines = translated_text.splitlines(keepends=True)
    if(len(lines)>1 and not "#" in lines[0]):
        translated_text = translated_text.replace(f"{lines[0]}",f"## > {lines[0]}",1)
        if "**" in lines[0]:
            translated_text = translated_text.replace("**","",2)
        if "」。" in lines[0]:
            translated_text = translated_text.replace("」。","",1)
    if "####" in translated_text: # Discord未対応のMDを取り除く
        translated_text = translated_text.replace("####","###")
    for l in lines:
        if "```" in l and l[0:3] != "```":
            new_l = l.replace('```','\n```')
            translated_text = translated_text.replace(l,new_l)

    return translated_text

@client.event
async def on_ready():
    # この関数はBotの起動準備が終わった際に呼び出されます
    print(f'Ready: {client.user}')
    await client.change_presence(activity = discord.CustomActivity(name=str('メンションして話しかけてください！'), type=1))
    await tree.sync()#スラッシュコマンドを同期
    if not len(sys.argv) == 1:
        if sys.argv[1] == "update":
            if os.path.exists("update.txt"):
                with open("update.txt","r",encoding="utf-8") as f:
                    update_text = f.read()
                if not len(update_text) == 0:
                    channel = client.get_channel(1109706399635738697)
                    await channel.send(update_text,silent=True)
            else:
                print("update.txtが見つかりません。")
    

@tree.command(name="help",description="Botの説明を表示します。")
async def test_command(interaction: discord.Interaction):
    embed = discord.Embed(title="使用方法",description="メンションして聞きたいことについて話してください")
    embed.add_field(name='概要', inline=False ,value='')
    embed.add_field(name='コマンド', inline=False ,value='')
    embed.add_field(name='`/translate`', value='本アシスタントは日本ユーザー向けに機械翻訳をしています。文に違和感がある時はこのコマンドで翻訳の無効・有効を切り替えられます')
    embed.add_field(name='`/clear`', value='会話をリセットします。新しいトピックについて話しましょう！')
    embed.add_field(name='`/help`', value='Botの説明を表示します。')
    embed.add_field(name='ヒント', inline=False ,value='・単語や固有名詞がなかなか伝わらないときは、ダブルクオーテーションで囲むといいよ！\n・「○○の画像を作って！」などと頼むと画像を作ってくれるよ！\n・URLを送信すると、そのサイトを要約してくれるよ！')

    await interaction.response.send_message(embed=embed,ephemeral=True)

@tree.command(name="clear",description="会話履歴を削除します")
async def test_command(interaction: discord.Interaction):
    kaiwa_dict.update({f"{interaction.user.name}":[]})
    await interaction.response.send_message(content="会話をリセットしました！新しいトピックについて話しましょう！",ephemeral=True)

@tree.command(name="translate",description="翻訳の有効・無効を切り替えます")
async def test_command(interaction: discord.Interaction):
    if not f"{interaction.user.name}" in trans_mode:
        trans_mode.update({f"{interaction.user.name}":False})
    if trans_mode[f"{interaction.user.name}"] == False:
        trans_mode.update({f"{interaction.user.name}":True}) # Trueで翻訳なし
        await interaction.response.send_message(content="翻訳を無効にしました",ephemeral=True)
    else:
        trans_mode.update({f"{interaction.user.name}":False})
        await interaction.response.send_message(content="翻訳を有効にしました",ephemeral=True)


@tree.command(name="create_img_config",description="画像生成の設定を変更します。")
async def test_command(interaction: discord.Interaction,config:str):
    if not config in ["safe_mode","disable"]:
        await interaction.response.send_message(content=f"`config`は、`safe_mode`もしくは`disable`である必要があります。",ephemeral=True)
        return
    mode_dict={"safe_mode":"セーフモード","disable":"画像生成機能の無効化"}
    if not f"{interaction.user.name}" in image_mode:
        image_mode.update({f"{interaction.user.name}":{"safe_mode":True,"disable":False}})
    if image_mode[f"{interaction.user.name}"][f"{config}"] == False:
        image_mode[f"{interaction.user.name}"][f"{config}"] = True
        await interaction.response.send_message(content=f"{mode_dict[f'{config}']}をオンにしました",ephemeral=True)
    else:
        image_mode[f"{interaction.user.name}"][f"{config}"] = False
        await interaction.response.send_message(content=f"{mode_dict[f'{config}']}をオフにしました",ephemeral=True)

@tree.command(name="translate_usage",description="DeepLエンジンの残り文字数を確認します（開発者限定コマンド）")
async def test_command(interaction: discord.Interaction):
    if interaction.user.name == "yomi4486":
        params = {
            'auth_key':DEEPL_API_LEY
        }
        res = requests.get("https://api-free.deepl.com/v2/usage",data=params).json()
        par = math.floor((int(res["character_count"]) / int(res["character_limit"])) * 1000) / 1000
        embed = discord.Embed(color=0x162A44,title="DeepL API 残り文字数",description=f"{int(res['character_limit']) - int(res['character_count'])}文字 / {res['character_limit']}文字 ({par*100}%使用済み)")
        embed.add_field(name='使用済み', value=f'{res["character_count"]}文字')
        view = MyView()
        await interaction.response.send_message(embed=embed,ephemeral=True,view=view)
    else:
        await interaction.response.send_message(content="このコマンドは開発者限定です。",ephemeral=True)

@client.event
async def on_message(message:discord.Message):
    if message.author.bot : return
    try:
        client.get_user(int(message.author.id))
    except:
        await message.reply("ユーザーの認証に失敗しました。本Botを利用するにはサポートサーバーに参加している必要があります。\nサーバーへの参加は[こちら](https://discord.gg/9ZYeknHpxu)から。")
        return
    if message.guild is None and message.author.name =="yomi4486":
        if "makao1521" in message.content:
            user = client.get_user(1023437863779573832)
            await user.send(message.content.replace("makao1521",""))
            return
    
    if 'だるえもーん' in message.content:
        await message.reply('',file=discord.File(f'./source/main.png'))
        if not message.author.voice is None:
            if message.guild.voice_client is None:
                await message.author.voice.channel.connect()
                message.guild.voice_client.play(discord.FFmpegPCMAudio(f'./source/daruemon.wav'),after= lambda e: asyncio.run_coroutine_threadsafe(disconnect(message), client.loop))
                return
            
    if 'ころすぞ' in message.content or '殺すぞ' in message.content:
        if not message.author.voice is None:
            if message.guild.voice_client is None:
                await message.author.voice.channel.connect()
                message.guild.voice_client.play(discord.FFmpegPCMAudio(f'./source/korosuzo.mp4'),after= lambda e: asyncio.run_coroutine_threadsafe(disconnect(message), client.loop))
                return
            
    if 'ずるずる' in message.content:
        await message.reply(content='こちらが　濃厚とんこつ豚無双さんの 濃厚無双ラーメン　海苔トッピングです うっひょ～～～～～～！ 着席時　コップに水垢が付いていたのを見て 大きな声を出したら　店主さんからの誠意で チャーシューをサービスしてもらいました 俺の動画次第でこの店潰すことだって出来るんだぞってことで いただきま～～～～す！まずはスープから コラ～！ これでもかって位ドロドロの濃厚スープの中には 虫が入っており　怒りのあまり 卓上調味料を全部倒してしまいました～！ すっかり店側も立場を弁え　誠意のチャーシュー丼を貰った所で お次に　圧倒的存在感の極太麺を 啜る～！　殺すぞ～！ ワシワシとした触感の麺の中には、髪の毛が入っており さすがのSUSURUも　厨房に入って行ってしまいました～！ ちなみに、店主さんが土下座している様子は　ぜひサブチャンネルを御覧ください'.replace(" ","\n"),file=discord.File(f'./source/image.png'))
        if not message.author.voice is None:
            if message.guild.voice_client is None:
                await message.author.voice.channel.connect()
                message.guild.voice_client.play(discord.FFmpegPCMAudio(f'./source/susuru.mp4'),after= lambda e: asyncio.run_coroutine_threadsafe(disconnect(message), client.loop))
                return

    if f'<@{APPLICATION_ID}>' in message.content or not message.guild:
        async def main():
            msg = None
            try:
                msg = await message.channel.fetch_message(message.reference.message_id)
            except:
                pass
            finally:
                user_prompt = str(message.content.replace(f'<@{APPLICATION_ID}> ','').replace(f'<@{APPLICATION_ID}>',''))
                
                # メンションのみだった場合はリソース削減のためメッセージのみ送信
                if user_prompt == "" and not message.attachments:
                    await message.reply("こんにちは！私はAIアシスタントです。何かお手伝いできることがありますか？\n使い方がわからない場合は、`/help`を実行してください")
                    return
                
                code_list = re.findall(r'```(.*?)```',f"{user_prompt}",re.DOTALL)
                log_dict = {}
                lang_mode = 0
                if len(code_list)== 0: # コードにURLが含まれていることもあるので、URLがコード内に含まれていた場合はそちらを優先
                    if 'https://' in user_prompt or 'http://' in user_prompt:
                        url = extractor.find_urls(user_prompt)[0]
                        msg = await message.reply(':robot: サイトのコンテンツを取得中です…')
                        res = get_content(url)
                        if res:
                            await msg.edit(content=':robot: コンテンツの解析中です…')
                            user_prompt = user_prompt.replace(url,"").replace(" ","").replace("\n","")
                            if len(user_prompt) == 0: # メッセージの内容がURLだけだったら自動で要約してっていう
                                user_prompt = "Please summarize this content" 
                            else:
                                user_prompt = translator.translate(user_prompt,dest='en').text

                            result = await get_completion([{"role":"system","content":f"{res}"},{"role":"user","content":user_prompt}])

                            await msg.edit(content=translate_ignore_code(result,"ja"))
                        else:
                            await msg.edit(content=f'`{url}`\nというURLは見つからないか、閲覧できない状態になっています。')
                        return
                    
                    if ('つくって' in user_prompt or 'かいて' in user_prompt or '描いて' in user_prompt or '作って' in user_prompt or '送って' in user_prompt) or ('画像' in user_prompt[-2:]):
                        if f"{message.author.name}" in image_mode:
                            if image_mode[f"{message.author.name}"]["disable"] == True:
                                pass
                            else:
                                if await imageCreater.createImg(prompt=user_prompt,message=message) == 0: # 正常終了だった場合はリターン
                                    return
                        else:
                            if await imageCreater.createImg(prompt=user_prompt,message=message) == 0: # 正常終了だった場合はリターン
                                return

                if not len(code_list) == 0:
                    if '```py' in user_prompt.lower():
                        lang_mode = 0
                    elif '```node' in user_prompt.lower():
                        await message.reply(f"その言語には対応していません。(NodeJSの検証をする場合は、下記のように宣言してください。)\n\\```js\nコード\n\\```")
                        return
                    elif '```js' in user_prompt.lower():
                        lang_mode = 1
                    elif '```c' in user_prompt.lower():
                        lang_mode = 2
                    else:
                        lang_mode = -1
                    if not lang_mode == -1:
                        fname = f"{lang_list[lang_mode].lower()}.png"
                        file = discord.File(fp=f"./source/lang/{lang_list[lang_mode].lower()}.png",filename=fname,spoiler=False)
                        embed = discord.Embed(title=f"{lang_list[lang_mode]}",description=f"Version: {lang_param[f'{str(lang_list[lang_mode]).lower()}']['version']}\nOS: {lang_param[f'{str(lang_list[lang_mode]).lower()}']['os']}")
                        embed.set_thumbnail(url=f"attachment://{lang_list[lang_mode].lower()}.png")
                        if "no-reply" in user_prompt.lower():
                            in_code_alert = f"提供された{lang_list[lang_mode]}のコードを解析中です。(no-replyモード)"
                            flag = 0
                        else:
                            in_code_alert = f"提供された{lang_list[lang_mode]}のコードを解析中です。"
                            flag = 1
                        kaisekityu = await message.reply(content=f"{in_code_alert}",file=file, embed=embed)
                        log_dict = compose_container(mode=lang_mode,code=str(code_list[0]).replace(f"```{lang_list[lang_mode].lower()}","").replace("```",""),lib=[])
                        exit_label = {"successful termination":"正常終了","Exception occurred":"異常終了","TimeOut":"タイムアウト"}
                        if f"{log_dict['status_label']}" in exit_label:
                            ja_exit_label = exit_label[log_dict['status_label']]
                        else:
                            ja_exit_label = f"{log_dict['status_label']}"
                        await kaisekityu.edit(content=f"\n終了コード：{log_dict['exit_code']} ({ja_exit_label})\nログ：\n```{log_dict['logs'][:1900]}```")
                        if flag == 0:
                            return
                reply_message = await message.reply("回答を生成中です...")
                if '今日' in user_prompt:
                    dt_now = datetime.datetime.now()
                    week = weekday_list[dt_now.weekday()]
                    user_prompt = user_prompt.replace("今日",f"今日({dt_now.strftime('%Y年%m月%d日')} {week}曜日)")
                result = await kaiwa_dict_update(message=message,msg=msg,user_prompt=user_prompt,log_dict=log_dict,code_list=code_list,lang_mode=lang_mode)
                # 翻訳        
                if f"{message.author.name}" in trans_mode and trans_mode[f"{message.author.name}"] == True:
                    jp_result = result
                else:
                    try:
                        jp_result = translate_ignore_code(result,"ja")
                    except Exception as e:
                        print(e)
                        exception_type, exception_object, exception_traceback = sys.exc_info()
                        filename = exception_traceback.tb_frame.f_code.co_filename
                        line_no = exception_traceback.tb_lineno
                        jp_result = result
                        print(f"{filename}の{line_no}行目でエラーが発生しました。詳細：{e}")

                if ("違法" in jp_result and "有害" in jp_result) or ("露骨" in jp_result): # 有害な話題は打ち切る
                    kaiwa_dict.update({f"{message.author.name}":[]})
                try:
                    res_code_list = re.findall(r'```.*?```',f"{jp_result}",re.DOTALL)
                    a=""
                    b=""
                    if len(jp_result) >=2000: 
                        if len(res_code_list) !=0:
                            for i in res_code_list:
                                jp_result = jp_result.replace(i,f"$^{i}")
                            text_list = jp_result.split("$^")
                            for l in text_list:
                                if not len(a+l) >=2000:
                                    a+=l
                                else:
                                    b+=l
                            a=a.replace("$^","")
                            b=b.replace("$^","")
                        else:
                            text_list = jp_result.splitlines(keepends=True)
                            for l in text_list:
                                if not len(a+l) >= 2000:
                                    a+=l
                                else:
                                    b+=l
                        await reply_message.edit(content=f"{a}")
                        if len(b)!=0:
                            reply_message = await message.channel.send(content=f"{b[:2000]}")
                    else:    
                        await reply_message.edit(content=jp_result)
                    await reply_message.add_reaction("👍")
                    await reply_message.add_reaction("👎")
                except Exception as e:
                    print(e)
                    await reply_message.edit(content="問題が発生したため、回答を生成できませんでした。")
        threading.Thread(target=lambda:asyncio.run_coroutine_threadsafe(main(),client.loop)).start()

@client.event
async def on_raw_reaction_add(payload:discord.Reaction):
    emoji_list = {"👎":"bad","👍":"good"}
    if f"{payload.emoji}" in emoji_list: # グッドとバッド以外のリアクションは無視
        try:
            guild = client.get_guild(payload.guild_id)
            user=guild.get_member(payload.user_id) # リアクションを付けた人を取得
            txt_channel = client.get_channel(payload.channel_id)
        except:
            return
        message = await txt_channel.fetch_message(payload.message_id) # リアクションが付けられたメッセージのメッセージオブジェクトを取得
        if (user.id == int(APPLICATION_ID)): # リアクションがエナジー教授が自動でしたものであった場合、無視
            return
        if (message.author.id == int(APPLICATION_ID) and not user.bot): # リアクション先のメッセージがエナジー教授のものであり、なおかつリアクションをした人がBotでない場合
            try:
                msg = await message.channel.fetch_message(message.reference.message_id) # リプライ元のメッセージ（質問）を取得
            except:
                return
            if(msg.author.id == payload.user_id): # 質問者とフィードバックをした人が同じであれば
                await message.reply(content=f"<@{user.id}>\nフィードバックありがとうございます！😊\n今後の精度向上に使わせていただきます！\n-# 今回のフィードバックに関して、サーバー側でユーザー情報を収集することはありません。",delete_after=5)
            else:
                return
            with open("feedback.json","r",encoding="utf-8") as f:
                data = json.load(f)
            data_as_list = list(data)

            new_data = {
                "question":f"{msg.content.replace(f'<@{int(APPLICATION_ID)}>','')}",
                "reply":f"{message.content}",
                "reaction":f"{emoji_list[f'{payload.emoji}']}"
            }
        
            data_as_list.append(new_data)
            with open(f'feedback.json', 'w',encoding="utf-8") as f:
                f.write(json.dumps(data_as_list, indent=4,ensure_ascii = False))
    elif f"{payload.emoji}" == "🗑️":
        txt_channel = client.get_channel(payload.channel_id)
        message = await txt_channel.fetch_message(payload.message_id)
        if message.attachments and payload.user_id != client.user.id:
            await message.delete()

if __name__ == "__main__":
    client.run(TOKEN)