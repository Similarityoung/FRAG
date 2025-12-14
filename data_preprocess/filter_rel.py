# 关系过滤脚本：进一步过滤手动筛选后的关系数据
# 移除不需要的关系类型（如类型关系、通用关系、sameAs关系等）

def abandon_rels(relation):
    """判断是否应该过滤掉该关系
    
    Args:
        relation: 关系字符串
        
    Returns:
        True 表示应该过滤掉，False 表示保留
    """
    # 移除不需要的关系类型（如类型关系、通用关系、sameAs关系等）
    if (relation == "type.object.type" or 
        relation == "type.object.name" or 
        relation.startswith("type.type.") or 
        relation.startswith("common.") or 
        relation.startswith("freebase.") or 
        "sameAs" in relation or 
        "sameas" in relation):
        return True


def main():
    """主函数：执行关系过滤"""
    # 输入输出文件路径
    output_file = "rel_filter.txt"  # 输出：过滤后的关系文件
    input_file = "manual_fb_filter.txt"  # 输入：手动筛选后的关系文件

    # 打开输入输出文件
    f_in = open(input_file)
    f_out = open(output_file, "w")
    num_line = 0  # 总行数计数
    num_reserve = 0  # 保留的行数计数

    # 逐行处理
    for line in f_in:
        splitline = line.strip().split("\t")
        num_line += 1
        # 跳过格式不正确的行（少于3列）
        if len(splitline) < 3:
            continue
        rel = splitline[1]  # 提取关系字段
        # 如果关系应该被过滤，跳过
        if abandon_rels(rel):
            continue
        # 保留该行
        f_out.write(line)
        # 每处理100万行打印一次进度
        if num_line % 1000000 == 0:
            print(num_line, num_reserve)

    f_in.close()
    f_out.close()
    # 打印最终统计
    print(num_line, num_reserve)


if __name__ == "__main__":
    main()
