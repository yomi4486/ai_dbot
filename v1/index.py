import os
import discord
from discord import app_commands
from os.path import join, dirname
from dotenv import load_dotenv
import requests
from openai import OpenAI 
from translate import Translator
from logging import StreamHandler
from logging import getLogger
import datetime
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

# APIでStreamで受け取るときに便利
openAI_client = OpenAI(base_url=BASE_URL, api_key="not-needed")

# Discordクライアントインスタンス
client = discord.Client(intents = discord.Intents.all())
intents = discord.Intents.default()
intents.message_content = True
tree = app_commands.CommandTree(client)
translator = Translator(from_lang = 'ja', to_lang = 'en')

def get_completion(message, model="local-model", temperature=0):
    messages = message
    response = openAI_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0 # this is the degree of randomness of the model's output
    )
    return response.choices[0].message.content

kaiwa_dict = {}
weekday_list = ["月","火","水","木","金","土","日"]
trans_mode = {}
@client.event
async def on_ready():
    # この関数はBotの起動準備が終わった際に呼び出されます
    print('{0.user}'.format(client) ,"がログインしました")
    await client.change_presence(activity = discord.CustomActivity(name=str('メンションして話しかけてください！'), type=1))
    await tree.sync()#スラッシュコマンドを同期
    logger.disabled = True

@tree.command(name="help",description="Botの説明を表示します。")
async def test_command(interaction: discord.Interaction):
    embed = discord.Embed(title="使用方法",description="メンションして聞きたいことについて話してください")
    embed.add_field(name='概要', inline=False ,value='')
    embed.add_field(name='コマンド', inline=False ,value='')
    embed.add_field(name='`/translate`', value='本アシスタントは日本ユーザー向けに機械翻訳をしています。文に違和感がある時はこのコマンドで翻訳の無効・有効を切り替えられます')
    embed.add_field(name='`/clear`', value='会話をリセットします。新しいトピックについて話しましょう！')
    embed.add_field(name='`/help`', value='Botの説明を表示します。')

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

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if f'<@{APPLICATION_ID}>' in message.content or not message.guild:
        msg = None
        try:
            msg = await message.channel.fetch_message(message.reference.message_id)
        except:
            pass
        finally:
            user_prompt = message.content.replace(f'<@{APPLICATION_ID}> ','').replace(f'<@{APPLICATION_ID}>','')
            
            # メンションのみだった場合はリソース削減のためメッセージのみ送信
            if user_prompt == "":
                await message.reply("こんにちは！私はAIアシスタントです。何かお手伝いできることがありますか？\n使い方がわからない場合は、`/help`を実行してください")
                return
            if '今日' in user_prompt:
                dt_now = datetime.datetime.now()
                week = weekday_list[dt_now.weekday()]
                user_prompt = user_prompt.replace("今日",f"今日({dt_now.strftime('%Y年%m月%d日')} {week}曜日)")
            
            reply_message = await message.reply("回答を生成中です...")

            if len(user_prompt) >= 500:
                try:
                    params = {
                        'auth_key':DEEPL_API_LEY,
                        'text':user_prompt,
                        'source_lang': 'EN',
                        'target_lang': 'JA'
                    }
                    request = requests.post("https://api-free.deepl.com/v2/translate",data=params)
                    res = request.json()
                    user_prompt = res["translations"][0]["text"]
                except:
                    pass
            else:
                try:
                    user_prompt = translator.translate(user_prompt)
                except:
                    pass

            if f"{message.author.name}" in kaiwa_dict :
                if len(kaiwa_dict[message.author.name]) >= 4:
                    del kaiwa_dict[message.author.name][0]
                    del kaiwa_dict[message.author.name][0]
            #kaiwa.append({"role":"user","content":user_prompt})
            if msg is None:
                if not f"{message.author.name}" in kaiwa_dict :
                    kaiwa_dict.update({f"{message.author.name}":[{"role":"user","content":user_prompt}]})
                else:
                    kaiwa_dict[f"{message.author.name}"].append({"role":"user","content":user_prompt})
                result = get_completion(kaiwa_dict[f"{message.author.name}"])
                kaiwa_dict[f"{message.author.name}"].append({"role":"assistant","content":result})
            else:
                if msg.author.id == APPLICATION_ID:
                    result = get_completion([{"role":"assistant","content":f"{msg.content}"},{"role":"user","content":user_prompt}])
                else:
                    result = get_completion([{"role":"system","content":f"{msg.content}\nThe message is created by {msg.author.display_name}."},{"role":"user","content":user_prompt}])
                if not f"{message.author.name}" in kaiwa_dict :
                    kaiwa_dict.update({f"{message.author.name}":[{"role":"assistant","content":result}]})
                else:
                    kaiwa_dict[f"{message.author.name}"].append({"role":"assistant","content":result})
                    
            
            # 翻訳        
            if f"{message.author.name}" in trans_mode and trans_mode[f"{message.author.name}"] == True:
                jp_result = result
            else:
                try:
                    jp_result = result
                    params = {
                        'auth_key':DEEPL_API_LEY,
                        'text':result,
                        'source_lang': 'EN',
                        'target_lang': 'JA'
                    }
                    request = requests.post("https://api-free.deepl.com/v2/translate",data=params)
                    res = request.json()
                    jp_result = res["translations"][0]["text"]
                except:
                    jp_result = result
            # 有害な話題は打ち切る
            if ("違法" in jp_result and "有害" in jp_result) or ("露骨" in jp_result):
                kaiwa_dict.update({f"{message.author.name}":[]})
            try:
                # 文字数が2000文字を超えていたら残りも送る
                await reply_message.edit(content=jp_result[:2000])
                if len(jp_result) >=2000:
                    await message.channel.send(content=jp_result[2000:])
            except:
                await reply_message.edit(content="問題が発生したため、回答を生成できませんでした。")

client.run(TOKEN)