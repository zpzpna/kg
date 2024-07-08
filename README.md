# 对图片型书本pdf提取文字并且抽取实体，语料，问题制作知识图谱
- 使用tesseract ocr提取pdf中文字
    - 注意要下载tesseract本体到本地，还要配置好环境变量
    - 注意将书本pdf放到本地后修改main中书本名git
- 通过deepseek api 提取实体，语料，问答对
    - 注意写一个config.ini文件放自己的api_key和base_url,有需要的话根据具体哪家api修改openai调用部分


```ini
# config.ini文件内容
[API]
base_url = ""
api_key = "" 
```
- 基于neo4j存储实体三元组