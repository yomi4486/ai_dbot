def main():
    try:
        import daruemon_docker
    except ImportError:
        print("メソッドの取得に失敗しました。このスクリプトはプロジェクトのルートディレクトリで実行してください。")
        return
    import requests
    try:
        daruemon_docker.compose_container(mode=0,code="print('test')",lib=[])
        status_d = "ok!"
    except ImportError as e:
        status_d = "failed: 必要なライブラリがインストールされていません。\npip install -r requirements.txtからインストールしてください。"
    except:
        status_d = "failed: dockerの実行環境が整っていません" 
    try:
        requests.get("http://127.0.0.1:7861/sdapi/v1/options")
        status_s = "ok!"
    except:
        status_s = "failed: 画像生成API（StableDiffusion Forgeを推奨）が利用できません。画像生成と画像認識は利用できません。"
    try:
        requests.get("http://localhost:60045/v1/models")
        status_l = "ok!"
    except:
        status_l = "failed: LMStudioのAPIが起動していません。"
    print(f"画像生成エンジン: {status_s}\nコード実行環境: {status_d}\nLMStudio: {status_l}")
    if status_l == status_d == status_s:
        print("実行環境はすべて整っています！")


if __name__ == "__main__":
    main()

