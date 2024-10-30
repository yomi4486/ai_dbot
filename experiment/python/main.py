a,b="",""
jp_result = """
hello
i'm yomi4486
good bye
"""
text_list = jp_result.splitlines(keepends=True)
for l in text_list:
    if not len(a+l) >= 2000:
        a+=l
    else:
        b+=l
    print(a)
