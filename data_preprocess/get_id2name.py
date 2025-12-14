# 从 Freebase 数据中提取实体ID到名称的映射
# 通过筛选 type.object.name 关系来获取实体的人类可读名称


def main():
    """主函数：提取实体ID到名称的映射"""
    # 输入输出文件路径
    input_file = "data/fb_en.txt"  # 输入：原始 Freebase 数据文件
    output_file = "process_data/id2name.txt"  # 输出：实体ID到名称的映射文件

    f_out = open(output_file, "w")

    # 目标关系：实体名称关系
    relation = "type.object.name"

    # 逐行读取输入文件
    with open(input_file, "r") as fp:
        for line in fp.readlines():
            split_line = line.strip().split("\t")
            # 只保留名称关系的三元组（格式：实体ID \t type.object.name \t 实体名称）
            if split_line[1] == relation:
                f_out.write(line)

    f_out.close()


if __name__ == "__main__":
    main()
