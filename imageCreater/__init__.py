import uuid,base64,requests,os,discord
from googletrans import Translator
from os.path import join, dirname
from dotenv import load_dotenv
translator = Translator()
load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

imageapi_base_url = os.environ.get("imageapi_base_url")

async def createImg(prompt:str,message:discord.Message):
    """
    promptに、プロンプト
    messageにDiscordのmessageオブジェクト
    """
    user_prompt = prompt
    if 'コード' in user_prompt or 'ツール' in user_prompt or '教えて' in user_prompt or 'プログラム' in user_prompt: #除外ワード
        pass
    elif 'イラスト' in user_prompt or 'イメージ' in user_prompt or '絵' in user_prompt or '画像' in user_prompt or '写真' in user_prompt:
        width_value,height_value = 512,512
        msg = await message.channel.send('🎨 作成中です...')
        prompt = user_prompt.replace('送って','').replace('作って','').replace('つくって','').replace('かいて','').replace('描いて','').replace('ください','').replace('下さい','').replace('のイメージを','').replace('の画像を','').replace('のイメージ','').replace('の画像','').replace('イメージを','').replace('画像を','').replace('イメージ','').replace('画像','')
        if '縦長' in prompt or '縦向き' in prompt:
            width_value = 512
            height_value = 768
            prompt = prompt.replace('の縦長','').replace('縦長','').replace('縦向き','').replace('の縦向き','')
        elif '横長' in prompt or '横向き' in prompt:
            width_value = 768
            height_value = 512
            prompt = prompt.replace('の横長','').replace('横長','').replace('横向き','').replace('の横向き','')


        #if len(re.findall(r'[^a-zA-Z_0-9\u0020-\u0040]',prompt,re.DOTALL)) == 0:
        if len(prompt) ==0:
            prompt="random"
        else:
            prompt = f"{translator.translate(prompt,dest='en').text}"

        payload = {
            "prompt": f"{prompt} ,high quality, 8k",
            "steps": 20,
            "width":width_value,
            "height":height_value,
            "batch_size": 1,
            "cfg_scale": 7,
            "restore_faces": True,
            "negative_prompt": "nsfw,low quality,blurry,lowres,duplicate,morbid,deformed,monochrome,greyscale,comic,4koma,2koma,sepia,simple background,rough,unfinished,horror,duplicate legs,duplicate arms,error,worst quality,normal quality",
        }
        try:
            response = requests.post(url=f'{imageapi_base_url}', json=payload,headers={"Content-Type": "application/json"})
        except:
            await message.reply('現在スケッチを利用できません！')
            return 0
        r = response.json()
        filename = uuid.uuid4()
        with open(f"./imageCreater/result/{filename}.png", 'wb') as f:
            f.write(base64.b64decode(r['images'][0]))
        await msg.delete()
        reply_message = await message.reply('',file=discord.File(f'./imageCreater/result/{filename}.png'))
        await reply_message.add_reaction("👍")
        await reply_message.add_reaction("👎")
        await reply_message.add_reaction("🗑️")
        os.remove(f'./imageCreater/result/{filename}.png')
        return 0

print("Ready: imageCreater")