import os
import re
import json
import pytesseract
import configparser
from openai import OpenAI
from pdf2image import convert_from_path

# 设置url和apikey
config = configparser.ConfigParser()
config.read("config.ini")
api_key = config["API"]["api_key"]
base_url = config["API"]["base_url"]
# 设置Tesseract可执行文件路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # 修改为你的Tesseract路径

# PDF路径
pdf_path = r"plants2.pdf"

# 创建一个临时目录用于保存图像文件
output_folder = "temp_images"
os.makedirs(output_folder, exist_ok=True)

# 将PDF页面转换为图像
pages = convert_from_path(pdf_path, 300, output_folder=output_folder)
# 遍历每一页图像并提取文本
# 由于token溢出，使用列表装2页一个的文本

full_text = []
per_text = ""
for i, page_image in enumerate(pages):
    # 循环存入文本
    if i % 2 == 0:
        full_text.append(per_text)
        per_text = ""

    # 将图像保存为临时文件
    image_path = os.path.join(output_folder, f"page_{i + 1}.png")
    page_image.save(image_path, 'PNG')

    # 使用Tesseract OCR提取文本
    text = pytesseract.image_to_string(page_image, lang='chi_sim')
    per_text += text + "\n\n"

    print(f"Text from page {i + 1}:\n{text}\n{'-' * 40}")
    # 最后存入不足2页的文本
    if i == len(pages) - 1:
        full_text.append(per_text)

# 删除临时图像文件
for image_file in os.listdir(output_folder):
    os.remove(os.path.join(output_folder, image_file))

# 删除临时目录
os.rmdir(output_folder)

# 打印提取的完整文本
print("Extracted text:\n", full_text)
"""下面是提取"""
# 三元组提取
json_tri_raw = []
for per_text in full_text:
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system",
             "content": "你是一个番茄种植方面的农业专家，现在要你根据给出的文本，识别与番茄  种植有关的命名实体，以及实体间的关系,格式<实体,关系,实体>,尽可能多抽取实体和关系三元组，具体例子如下:<盐水选种,方法,将种子与20%的盐水充分搅拌均匀>。"},
            {"role": "user", "content": per_text},
        ],
        stream=False,
        temperature=0.7
    )
    pattern_tri = "<([^,]+),([^,]+),([^,]+)>"
    tri_list = re.findall(pattern_tri, response.choices[0].message.content)
    for s, v, o in tri_list:
        json_tri_raw.append({"subject": s, "predicate": v, "object": o})
with open("./triple.json", "w+", encoding="utf-8") as wf:
    # 这里储存成utf还是纯中文
    json.dump(json_tri_raw, wf, indent=2, ensure_ascii=False)

# 语料提取
json_corpus_list = []
for per_text in full_text:
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system",
             "content": "- 角色: 农业技术文本编辑和信息提取专家；"
                        "- 背景: 需要润色并提取番茄种植技术文本中的长段文本；"
                        "- 简介: 您是具有农业专业知识的文本编辑专家，能够理解并优化相关文本；"
                        "- 技能: 农业知识、文本编辑、信息提取、语言润色；"
                        "- 目标: 提供文本润色服务，提取与番茄种植相关的长段文本，丢弃介绍图片的文本,尽量多的抽取长段文本；"
                        "- 限制: 保持专业性和可读性，确保提取的段落具有应用价值；"
                        "- 输出格式: 润色后提取的长段文本，每一段文本都要用一个[]包装(提取出的文本要放在[]内部而不是把括号作为序号)；"
                        "- 输出例子: "
                        "[在番茄种植技术中，穴盘育苗是一种常见的育苗方法，通过使用调节剂处理可以产生无籽果实，而授粉器处理则可以产生有籽果实。此外，番茄的花序处理方式也会影响果实的形成和品质。在现代农业中，管道栽培和温室滴灌技术也被广泛应用于番茄的种植，以提高产量和品质。],"
                        "[番茄灰霉病是一种常见的番茄病害，主要影响番茄的叶片。发病初期，叶片上会出现水浸状的小斑点，随着病情的发展，斑点逐渐扩大并形成灰色的霉层。如果不及时防治，病害会迅速蔓延至整个植株，导致叶片枯萎和果实腐烂。防治措施包括使用抗病品种、保持田间通风透光、及时清除病残体和使用化学药剂进行防治。],"
                        "[番茄叶霉病是另一种常见的番茄病害，主要特征是叶片背面出现灰绿色至黑褐色的霉层。发病初期，叶片正面会出现黄色斑点，随后霉层覆盖整个叶片背面，导致叶片卷曲和枯死。防治方法包括选用抗病品种、合理密植、保持田间湿度适宜以及使用杀菌剂进行防治。]"
                        "- 工作流程: 1. 阅读并理解原始文本；2. 进行语言润色；3. 提取关键长段文本；"
                        "- 初始化: 开始润色服务，请发送文本。"},
            {"role": "user", "content": per_text},
        ],
        stream=False,
        temperature=0.7
    )
    pattern_corpus = "\\[(.+?)\\]"
    corpus_list = re.findall(pattern_corpus, response.choices[0].message.content)
    for text in corpus_list:
        json_corpus_list.append(text)

with open("corpus_bk.json", "w+", encoding="utf-8") as wf:
    # 这里储存成utf还是纯中文
    json.dump(json_corpus_list, wf, indent=2, ensure_ascii=False)

# 问答对提取
json_qa_raw = []
for i, per_text in enumerate(full_text, start=1):
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system",
             "content": """- Role: 番茄种植技术专家
                           - Background: 您是一位经验丰富的番茄种植技术专家，拥有丰富的知识和实践经验。
                           - Profile: 您熟悉番茄的生长习性、土壤需求、病虫害防治等相关知识。
                           - Skills: 您具备分析文本、提出问题、解答问题的能力，能够根据文本内容生成相关的自问自答对话。
                           - Goals: 根据番茄种植技术文本生成多轮自问自答对话，以教育和分享番茄种植知识。
                           - Constrains: 对话应保持专业性和准确性，同时语言要通俗易懂，适合不同层次的读者。
                           - OutputFormat: [问题文本;回答文本;对话轮次数]。
                           - Workflow:
                               1. 阅读并理解番茄种植技术文本。
                               2. 提出与文本内容相关的问题。
                               3. 根据文本内容给出相应的答案。
                               4. 继续提出下一个问题，并回答，形成多轮对话。尽量让对话的问题之间具有层次性和深入性,且对话轮次尽可能多，并且有一点随机性
                           - Examples:
                           [Q: 番茄种植的最佳土壤pH值是多少？; A: 番茄种植的最佳土壤pH值在6.0到6.8之间，这有利于番茄根系的吸收和生长。;1]
                           [Q: 番茄需要多少日照时间？;A: 番茄是喜光植物，每天需要至少6到8小时的直射日光。;2]
                           - Initialization: 欢迎来到番茄种植技术交流，我是您的种植顾问。让我们一起探讨如何种植出健康美味的番茄吧！请发送我您想要了解的番茄种植问题。"""},
            {"role": "user", "content": per_text},
        ],
        stream=False,
        temperature=0.7
    )
    pattern_qa = "\\[([^;]*?);([^;]*?);([^;]*?)\\]"
    qa_extract = re.findall(pattern_qa, response.choices[0].message.content)
    qa_list = []
    for j, (q, a, _idx) in enumerate(qa_extract, start=1):
        qa_list.append({"id": j,
                        "Q": q,
                        "A": a})
    json_qa_raw.append({"conversation": i,
                        "QAs": qa_list})
with open("./qa.json", "w+", encoding="utf-8") as wf:
    json.dump(json_qa_raw, wf, indent=2, ensure_ascii=False)
