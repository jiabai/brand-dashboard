import os

import pymysql


def export_brands():
    # 数据库连接配置
    db_config = {
        "host": "192.168.31.233",
        "port": 3306,
        "user": "root",
        "password": "123456",
        "database": "geo",
        "charset": "utf8mb4",
    }

    job_id = "job_20260209_123550_e9ba00f6"
    output_file = "brands_found.txt"

    print(f"正在连接到数据库 {db_config['host']}...")

    try:
        # 连接数据库
        connection = pymysql.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            charset=db_config["charset"],
            cursorclass=pymysql.cursors.DictCursor,
        )

        with connection.cursor() as cursor:
            # 执行 SQL 查询
            sql = "select brands_found from qa_brand_state where job_id=%s"
            print(f"执行查询: {sql % job_id}")
            cursor.execute(sql, (job_id,))

            # 获取所有结果
            results = cursor.fetchall()

            if not results:
                print(f"未找到 job_id 为 {job_id} 的数据。")
                return

            print(f"查询到 {len(results)} 条记录。")

            # 提取 brands_found 并写入文件
            with open(output_file, "w", encoding="utf-8") as f:
                for row in results:
                    brands = row.get("brands_found")
                    if brands:
                        f.write(f"{brands}\n")

            print(f"成功将结果导出到 {os.path.abspath(output_file)}")

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if "connection" in locals() and connection.open:
            connection.close()
            print("数据库连接已关闭。")


if __name__ == "__main__":
    export_brands()
