import docker,yaml
lang_list = ["python","nodeJS","c"]
lang_list_file_path = ["experiment/python/main.py","experiment/NodeJS/main.js","experiment/C/main.c"]

def compose_container(mode:int,code:str,lib:list):
    """
    ### modeについて
    0:Python
    1:Node

    ### codeについて 
    codeには、ソースコードをStr型で渡してください。
    
    ### libについて 
    使うライブラリをリスト型で渡してください。
    """
    lang = lang_list[mode]
    # Load the docker-compose.yml file
    with open(f'experiment/{lang}/docker-compose.yml', 'r',encoding="utf-8") as f:
        compose_file = yaml.safe_load(f)
    file_name = f'{lang_list_file_path[mode]}'
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(code)

    with open(file_name,encoding='utf-8') as f:
        text_list = f.readlines()
    with open(file_name, "w",encoding='utf-8') as f:
        f.write("".join(text_list[1:]))

    # Get the service name and image name from the docker-compose.yml file
    service_name = list(compose_file['services'].keys())[0]
    image_name = compose_file['services'][service_name]['build']['context']

    # Create a new Docker client object
    client = docker.from_env()

    # Build the image using the Dockerfile
    try:
        image, _ = client.images.build(path=f"{image_name}", tag="latest",timeout=5)
    except Exception as e:
        print(e)
        return dict({"exit_code":1,"status_label":" returned a non-zero code: 1","logs":"コードスニペットの実行フローで例外的な問題が発生しました。"})
    container_id = None
    for service in compose_file['services'].values():
        if 'container_name' in service:
            container_id = service['container_name']
            break

    # Start the container using the image and container ID
    container = client.containers.run(image, detach=True, name=container_id)

    # print(f"Container ID: {container.id}")
    # print(f"Container Name: {container.name}")

    # Wait for the container to finish running
    try:
        exit_code = container.wait(timeout=5)["StatusCode"]
    except:
        return dict({"exit_code":1,"status_label":"TimeOut","logs":"The execution environment provided by エナジー教授 does not allow processing to last longer than 5 seconds. This error is due to a limitation of the environment and cannot be resolved."})

    logs = container.logs(stream=False).decode('utf-8')
    if not exit_code == 0:
        status_label = "Exception occurred"
    else:
        status_label = "successful termination"
    # print(f"Exit Code: {exit_code}({status_label})")
    try:
        container.remove()
    except:
        pass
    return dict({"exit_code":int(exit_code),"status_label":str(status_label),"logs":str(logs)})

print("Ready: daruemon_docker")