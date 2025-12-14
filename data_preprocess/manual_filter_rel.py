# 手动关系过滤脚本：基于黑名单过滤不需要的关系域
# 移除音乐、书籍、电视等特定领域的关系，保留核心知识图谱关系

import sys


def main():
    """主函数：执行手动关系过滤"""
    # 定义要过滤的关系域黑名单
    filter_domain = [
        'music.release',  # 音乐发行
        'authority.musicbrainz',  # 音乐数据库
        '22-rdf-syntax-ns#type',  # RDF 类型
        'book.isbn',  # 书籍 ISBN
        'common.licensed_object',  # 许可对象
        'tv.tv_series_episode',  # 电视剧集
        'type.namespace',  # 命名空间
        'type.content',  # 内容类型
        'type.permission',  # 权限类型
        'type.object.key',  # 对象键
        'type.object.permission',  # 对象权限
        'type.type.instance',  # 类型实例
        'topic_equivalent_webpage',  # 等价网页
        'dataworld.freeq'  # 数据世界
    ]

    filter_set = set(filter_domain)  # 转换为集合以加快查询速度

    # 输入输出文件路径
    input = "data/fb_en.txt"  # 输入：原始 Freebase 数据文件
    output = "process_data/manual_fb_filter.txt"  # 输出：手动过滤后的关系文件

    f_in = open(input)
    f_out = open(output, "w")
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
        flag = False
        
        # 检查关系是否包含黑名单中的任何域
        for domain in filter_set:
            if domain in rel:
                flag = True
                break
        
        # 如果关系在黑名单中，跳过
        if flag:
            continue
        
        # 保留该行
        f_out.write(line)
        num_reserve += 1
        
        # 每处理100万行打印一次进度
        if num_line % 1000000 == 0:
            print(num_line, num_reserve)

    f_in.close()
    f_out.close()
    # 打印最终统计：总行数和保留的行数
    print(num_line, num_reserve)


if __name__ == "__main__":
    main()
