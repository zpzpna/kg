import json
from tqdm import tqdm
from py2neo import Graph, Node, Relationship

if __name__ == "__main__":
    # 不知道为什么默认是neo4j用户名
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "11111111",))
    graph.run("MATCH(n) "
              "DETACH DELETE n")
    with open("triple.json", "r+", encoding="UTF-8") as rf:
        data = json.load(rf)
    tri_len = len(data)
    print(f"all_tri_len:{tri_len}")
    for triple in tqdm(data):
        subject = Node("主语", text=triple["subject"])
        object = Node("宾语", text=triple["object"])
        graph.merge(subject, "主语", "text")
        graph.merge(object, "宾语", "text")
        predicate = Relationship(subject, "谓语", object, text=triple["predicate"])
        graph.merge(predicate)
