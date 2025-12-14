# 数据预处理第0步：处理 ComplexWebQuestions 数据集
# 从原始 JSON 数据中提取问题、答案、实体，并将实体ID转换为名称
# 数据可从 https://github.com/lanyunshi/KBQA-GST 下载

import json
import os
from tqdm import tqdm
import re


def is_ent(tp_str):
    """判断字符串是否为 Freebase 实体ID
    
    Args:
        tp_str: 待判断的字符串
        
    Returns:
        True 如果是实体ID（以 m. 或 g. 开头），False 否则
    """
    if len(tp_str) < 3:
        return False
    if tp_str.startswith("m.") or tp_str.startswith("g."):
        print(tp_str)
        return True
    return False


def find_entity(sparql_str):
    """从 SPARQL 查询字符串中提取实体ID
    
    Args:
        sparql_str: SPARQL 查询字符串
        
    Returns:
        包含所有提取到的实体ID的集合
    """
    str_lines = sparql_str.split("\n")
    ent_set = set()
    unend_flag = False
    unend_text = None
    
    # 逐行解析 SPARQL 查询
    for line in str_lines[1:]:
        if "ns:" not in line:
            continue

        spline = line.strip().split(" ")
        for item in spline:
            # 提取 ns: 前缀后的实体ID
            ent_str = item[3:].replace("(", "")
            ent_str = ent_str.replace(")", "")
            if is_ent(ent_str):
                ent_set.add(ent_str)

    return ent_set


def id2name(ent, ent2name, cover_count, uncover_count):
    """将实体ID转换为实体名称
    
    Args:
        ent: 实体ID
        ent2name: 实体ID到名称的映射字典
        cover_count: 覆盖的实体数（列表，用于修改）
        uncover_count: 未覆盖的实体数（列表，用于修改）
        
    Returns:
        实体名称，如果不存在则返回实体ID本身
    """
    if ent in ent2name:
        cover_count[0] += 1
        return ent2name[ent]
    else:
        uncover_count[0] += 1
        return ent


def main():
    """主函数：处理 ComplexWebQuestions 数据集"""
    # 加载实体ID到名称的映射字典
    ent2name = {}
    with open("process_data/id2name.txt", "r") as fp:
        for line in fp.readlines():
            split_line = line.strip().split("\t")
            ent2name[split_line[0]] = split_line[2]

    # 统计变量：覆盖的实体数和未覆盖的实体数（使用列表以便在函数中修改）
    cover_count = [0]
    uncover_count = [0]

    # 输入数据文件夹和文件列表
    data_folder = "origin/Freebase/CWQ/"
    data_file = [
        "ComplexWebQuestions_train.json",
        "ComplexWebQuestions_test_wans.json",
        "ComplexWebQuestions_dev.json"
    ]

    # 输出文件路径
    output_file = "process_data/CWQ/CWQ_step0.json"
    f_out = open(output_file, "w")

    # 处理每个数据文件
    for file in data_file:
        filename = os.path.join(data_folder, file)
        with open(filename) as f_in:
            data = json.load(f_in)
            # 处理每个问题对象
            for q_obj in data:
                ID = q_obj["ID"]
                
                # 处理答案列表：转换为标准格式
                answer_list_new = []
                for answer_obj in q_obj["answers"]:
                    new_obj = {}
                    new_obj["kb_id"] = answer_obj["answer_id"]
                    new_obj["text"] = answer_obj["answer"]
                    answer_list_new.append(new_obj)
                
                # 提取问题和 SPARQL 查询
                question = q_obj["question"]
                sparql_str = q_obj["sparql"]
                
                # 从 SPARQL 中提取实体，并将ID转换为名称
                ent_set = find_entity(sparql_str)
                ent_list = [
                    {"kb_id": ent, "text": id2name(ent, ent2name, cover_count, uncover_count)} for ent in ent_set
                ]
                
                # 构建输出对象
                new_obj = {
                    "id": ID,
                    "answers": answer_list_new,
                    "question": question,
                    "entities": ent_list,
                }
                
                # 写入输出文件（每行一个 JSON 对象）
                f_out.write(json.dumps(new_obj) + "\n")

    f_out.close()

    # 打印统计信息：覆盖的实体数和未覆盖的实体数
    print(cover_count[0], " ", uncover_count[0])


if __name__ == "__main__":
    main()

