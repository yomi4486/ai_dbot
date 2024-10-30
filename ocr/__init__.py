# ocr_card_crop.py
import os
from PIL import Image,ImageOps
# import pytesseract
import uuid,base64,requests

# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# # インストール済みのTesseractのパスを通す
# path_tesseract = "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"
# if path_tesseract not in os.environ["PATH"].split(os.pathsep):
#     os.environ["PATH"] += path_tesseract

def interrogete(data:str):
    payload = {
        "image": data,
        "model": "clip"
    }
    response = requests.post(url=f'http://127.0.0.1:7861/sdapi/v1/interrogate', json=payload,headers={"Content-Type": "application/json"},)
    r = response.json()
    return r["caption"]

async def get_content(attachment:list):
    result= "User submitted image:\n"
    num = 0
    try:
        for img in attachment:
            num += 1
            filename = f"{uuid.uuid4()}"
            # Convert the image to grayscale
            await img.save(f"{filename}.png")
            with open(f"{filename}.png", "rb") as image_file:
                data = base64.b64encode(image_file.read()).decode()
            # Invert the image (make black areas white and vice versa)

            
            # img_bytes = io.BytesIO()
            # try:
            #     image.save(img_bytes, format='JPEG')
            # except:
            #     image.save(img_bytes, format="PNG")
            # img_bytes.seek(0)
            # data = base64.b64encode(img_bytes.getvalue()).decode()
            res = interrogete(data)
            # text = pytesseract.image_to_string(ImageOps.invert(image.convert('L')), lang='jpn', timeout=10)
            result += f"{num}:\ndescription: {res}\n\n".replace("Aya Goda","")
            print(result)
            try:
                os.remove(f"{filename}.png")
            except Exception as e:
                print(e)
    
    except Exception as e:
        print(e)
        result = "有効ではない画像またはファイルがアップロードされました"
    if len(result) == 0:
        result = "画像にはなにも含まれていません"
    return result


print("Ready: ocr")