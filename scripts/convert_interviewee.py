import pandas as pd
import os
import sys
import json
import argparse
from datetime import datetime, timezone

# ================================
# 配置变量 - 自定义列名映射
# ================================

# Excel列名映射配置，支持多个列名对应同一字段
COLUMN_MAPPING = {
    'name': ['姓名', 'name', '名字', '真实姓名', '学生姓名'],
    'sex': ['性别', 'sex', '男女', 'gender'],
    'phone_number': ['电话', '电话号码', 'phone_number', 'phone', '联系电话', '手机号', '手机号码'],
    'student_id': ['学号', 'student_id', '学生号', 'id', '学生学号'],
    'majar_text': ['专业', 'majar_text', 'major', '专业名称', '所学专业', '学生专业'],
    'introduction_text': ['自我介绍', 'introduction_text', '个人介绍', '介绍', '自述', '个人简介'],
    'accept_adjust': ['接受调剂', 'accept_adjust', '是否接受调剂', '调剂', '服从调剂'],
    'first_preference': ['第一志愿', 'first_preference', '志愿一', '首选部门', '第1志愿'],
    'second_preference': ['第二志愿', 'second_preference', '志愿二', '次选部门', '第2志愿'],
    'assigned_datetime': ['面试时间', 'assigned_datetime', '安排时间', '面试安排', '时间安排']
}

# 必需字段配置
REQUIRED_FIELDS = ['name', 'sex', 'phone_number', 'student_id', 'majar_text', 
                   'introduction_text', 'accept_adjust', 'first_preference']

# 部分信息可能对应多列的配置
# 格式: {目标字段: [列名1, 列名2, ...]} - 多列内容会用指定分隔符合并
MULTI_COLUMN_MAPPING = {
    'introduction_text': {
        'columns': ['自我介绍', '个人特长', '项目经验', '获奖情况'],
        'separator': '\n\n',  # 分隔符
        'format_template': '自我介绍：{}\n\n个人特长：{}\n\n项目经验：{}\n\n获奖情况：{}'
    },
    'majar_text': {
        'columns': ['专业', '年级', '班级'],
        'separator': ' - ',
        'format_template': '{} {} {}'
    }
}

# 接受调剂字段的真值配置
ACCEPT_ADJUST_TRUE_VALUES = ['是', 'yes', 'true', '1', 'y', '接受', '同意', '服从']
ACCEPT_ADJUST_FALSE_VALUES = ['否', 'no', 'false', '0', 'n', '不接受', '不同意', '不服从']

# 性别标准化配置
SEX_MAPPING = {
    '男': '男生',
    '女': '女生', 
    'male': '男生',
    'female': '女生',
    'm': '男生',
    'f': '女生',
    '男生': '男生',
    '女生': '女生'
}

# 默认面试时间配置（如果Excel中没有提供）
DEFAULT_INTERVIEW_TIME = datetime.now(timezone.utc)

# JSON输出配置
OUTPUT_JSON_FILE = "interviewees_data.json"  # 输出的JSON文件名
JSON_INDENT = 2  # JSON格式化缩进

# 部门ID映射（根据init_data.json中的部门配置）
DEPARTMENT_MAPPING = {
    '技术部': 1,
    '电脑诊所': 2,
    '数字媒体中心': 3
}

# 面试状态配置（对应模型中的状态）
INTERVIEW_STATUS = {
    'NOT_CHECKED_IN': 1,
    'CHECKED_IN': 2,
    'INTERVIEW_READY': 3,
    'INTERVIEW_STARTED': 4,
    'INTERVIEW_END': 5,
    'FIRST_PREFERENCE_QUEUE': 6,
    'SECOND_PREFERENCE_QUEUE': 7,
    'FINAL_QUEUE': 8,
    'ADMITTED': 9
}

# ================================
# 脚本主体
# ================================


def normalize_column_names(df):
    """
    根据配置将DataFrame的列名标准化
    
    参数:
        df: pandas DataFrame
    
    返回:
        标准化列名后的DataFrame和找到的列名映射
    """
    found_mapping = {}
    columns_to_rename = {}
    
    # 遍历配置中的每个字段
    for target_field, possible_names in COLUMN_MAPPING.items():
        for col_name in df.columns:
            if col_name in possible_names:
                columns_to_rename[col_name] = target_field
                found_mapping[target_field] = col_name
                break
    
    # 重命名列
    df_renamed = df.rename(columns=columns_to_rename)
    
    return df_renamed, found_mapping


def process_multi_column_fields(df, row_index, row):
    """
    处理多列合并的字段
    
    参数:
        df: DataFrame
        row_index: 行索引
        row: 当前行数据
    
    返回:
        处理后的行数据字典
    """
    processed_data = {}
    
    for target_field, config in MULTI_COLUMN_MAPPING.items():
        columns = config['columns']
        separator = config.get('separator', ' ')
        format_template = config.get('format_template')
        
        # 检查是否有这些列
        available_columns = [col for col in columns if col in df.columns]
        
        if available_columns:
            # 收集非空值
            values = []
            for col in available_columns:
                value = row.get(col, '')
                if pd.notna(value) and str(value).strip():
                    values.append(str(value).strip())
            
            if values:
                if format_template and len(values) == len(columns):
                    # 使用模板格式化
                    try:
                        processed_data[target_field] = format_template.format(*values)
                    except Exception:
                        # 如果模板格式化失败，使用分隔符
                        processed_data[target_field] = separator.join(values)
                else:
                    # 使用分隔符连接
                    processed_data[target_field] = separator.join(values)
        
        # 如果多列合并没有结果，尝试使用标准单列
        if target_field not in processed_data and target_field in row:
            processed_data[target_field] = row[target_field]
    
    return processed_data


def normalize_accept_adjust(value):
    """
    标准化接受调剂字段
    """
    if pd.isna(value):
        return False
    
    value_str = str(value).strip().lower()
    
    if value_str in ACCEPT_ADJUST_TRUE_VALUES:
        return True
    elif value_str in ACCEPT_ADJUST_FALSE_VALUES:
        return False
    else:
        # 尝试布尔转换
        try:
            return bool(int(value))
        except Exception:
            return False


def normalize_sex(value):
    """
    标准化性别字段
    """
    if pd.isna(value):
        return '未知'
    
    value_str = str(value).strip().lower()
    
    for key, standard_value in SEX_MAPPING.items():
        if value_str == key.lower():
            return standard_value
    
    return str(value).strip()


def convert_excel_to_json(excel_file_path, sheet_name=0, output_file=None):
    """
    从Excel文件读取面试者数据并生成JSON文件
    
    参数:
        excel_file_path: Excel文件路径
        sheet_name: 工作表名称或索引，默认为第一个工作表
        output_file: 输出JSON文件路径，默认使用配置中的文件名
    
    支持的列名配置在脚本顶部的COLUMN_MAPPING中定义
    支持多列合并的字段配置在MULTI_COLUMN_MAPPING中定义
    """
    
    if output_file is None:
        output_file = OUTPUT_JSON_FILE
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        print(f"成功读取Excel文件，共 {len(df)} 行数据")
        print(f"原始列名: {list(df.columns)}")
        
        # 标准化列名
        df, found_mapping = normalize_column_names(df)
        print(f"找到的列名映射: {found_mapping}")
        
        # 验证必需列是否存在
        missing_fields = []
        for required_field in REQUIRED_FIELDS:
            if required_field not in df.columns and required_field not in found_mapping:
                missing_fields.append(required_field)
        
        if missing_fields:
            print(f"错误：缺少必需的字段: {missing_fields}")
            print(f"标准化后的列名: {list(df.columns)}")
            print("请检查以下配置的列名是否在Excel中存在：")
            for field in missing_fields:
                print(f"  {field}: {COLUMN_MAPPING.get(field, [])}")
            return False
        
        # 显示可用部门
        print(f"可用部门: {list(DEPARTMENT_MAPPING.keys())}")
        
        interviewees_data = []
        created_count = 0
        error_count = 0
        next_pk = 1  # 开始的主键ID
        
        for index, row in df.iterrows():
            try:
                # 处理多列合并字段
                multi_column_data = process_multi_column_fields(df, index, row)
                
                # 合并数据
                row_data = {**row.to_dict(), **multi_column_data}
                
                # 标准化各个字段
                name = str(row_data.get('name', '')).strip()
                if not name:
                    print(f"警告：第 {index + 2} 行，姓名为空")
                    continue
                
                sex = normalize_sex(row_data.get('sex'))
                phone_number = str(row_data.get('phone_number', '')).strip()
                student_id = str(row_data.get('student_id', '')).strip()
                majar_text = str(row_data.get('majar_text', '')).strip()
                introduction_text = str(row_data.get('introduction_text', '')).strip()
                
                # 处理接受调剂字段
                accept_adjust = normalize_accept_adjust(row_data.get('accept_adjust'))
                
                # 处理第一志愿
                first_pref_name = str(row_data.get('first_preference', '')).strip()
                first_preference_id = DEPARTMENT_MAPPING.get(first_pref_name)
                if not first_preference_id:
                    print(f"警告：第 {index + 2} 行，未找到第一志愿部门: {first_pref_name}")
                    continue
                
                # 处理第二志愿（可选）
                second_preference_id = None
                if 'second_preference' in row_data and pd.notna(row_data['second_preference']):
                    second_pref_name = str(row_data['second_preference']).strip()
                    second_preference_id = DEPARTMENT_MAPPING.get(second_pref_name)
                    if not second_preference_id:
                        print(f"警告：第 {index + 2} 行，未找到第二志愿部门: {second_pref_name}")
                
                # 处理面试时间
                assigned_datetime = DEFAULT_INTERVIEW_TIME
                if 'assigned_datetime' in row_data and pd.notna(row_data['assigned_datetime']):
                    try:
                        if isinstance(row_data['assigned_datetime'], str):
                            assigned_datetime = datetime.strptime(row_data['assigned_datetime'], '%Y-%m-%d %H:%M')
                            assigned_datetime = assigned_datetime.replace(tzinfo=timezone.utc)
                        elif isinstance(row_data['assigned_datetime'], datetime):
                            assigned_datetime = row_data['assigned_datetime']
                            if assigned_datetime.tzinfo is None:
                                assigned_datetime = assigned_datetime.replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        print(f"警告：第 {index + 2} 行，时间格式错误: {e}")
                
                # 创建JSON数据结构（符合Django fixture格式）
                interviewee_data = {
                    "model": "interview.Interviewee",
                    "pk": next_pk,
                    "fields": {
                        "name": name,
                        "sex": sex,
                        "phone_number": phone_number,
                        "student_id": student_id,
                        "majar_text": majar_text,
                        "introduction_text": introduction_text,
                        "interview_status": INTERVIEW_STATUS['NOT_CHECKED_IN'],
                        "accept_adjust": accept_adjust,
                        "first_preference": first_preference_id,
                        "second_preference": second_preference_id,
                        "admitted_department": None,
                        "assigned_room": None,
                        "assigned_datetime": assigned_datetime.isoformat(),
                        "start_datetime": None,
                        "end_datetime": None
                    }
                }
                
                interviewees_data.append(interviewee_data)
                next_pk += 1
                created_count += 1
                print(f"✓ 成功处理面试者: {name} (学号: {student_id})")
                
            except Exception as e:
                error_count += 1
                print(f"✗ 第 {index + 2} 行数据处理失败: {e}")
                continue
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(interviewees_data, f, ensure_ascii=False, indent=JSON_INDENT)
        
        print("\n转换完成:")
        print(f"成功处理: {created_count} 个面试者")
        print(f"失败: {error_count} 个")
        print(f"JSON文件已保存: {output_file}")
        return True
        
    except Exception as e:
        print(f"处理Excel文件时发生错误: {e}")
        return False


def parse_arguments():
    """
    解析命令行参数
    """
    
    # 预格式化帮助信息的参数
    help_params = {
        'name_cols': ', '.join(COLUMN_MAPPING['name'][:3]) + '...',
        'sex_cols': ', '.join(COLUMN_MAPPING['sex'][:3]) + '...',
        'phone_cols': ', '.join(COLUMN_MAPPING['phone_number'][:3]) + '...',
        'student_id_cols': ', '.join(COLUMN_MAPPING['student_id'][:3]) + '...',
        'major_cols': ', '.join(COLUMN_MAPPING['majar_text'][:3]) + '...',
        'intro_cols': ', '.join(COLUMN_MAPPING['introduction_text'][:3]) + '...',
        'adjust_cols': ', '.join(COLUMN_MAPPING['accept_adjust'][:3]) + '...',
        'first_pref_cols': ', '.join(COLUMN_MAPPING['first_preference'][:3]) + '...',
        'second_pref_cols': ', '.join(COLUMN_MAPPING['second_preference'][:3]) + '...',
        'datetime_cols': ', '.join(COLUMN_MAPPING['assigned_datetime'][:3]) + '...',
        'departments': ', '.join(DEPARTMENT_MAPPING.keys())
    }
    
    epilog_text = """
示例用法:
  python convert_interviewee.py input.xlsx                    # 转换input.xlsx，输出到默认文件
  python convert_interviewee.py input.xlsx -o output.json     # 转换input.xlsx，输出到output.json
  python convert_interviewee.py -c                            # 显示当前配置信息
  python convert_interviewee.py --help                        # 显示此帮助信息

支持的Excel列名:
  姓名: {name_cols}
  性别: {sex_cols}
  电话: {phone_cols}
  学号: {student_id_cols}
  专业: {major_cols}
  自我介绍: {intro_cols}
  接受调剂: {adjust_cols}
  第一志愿: {first_pref_cols}
  第二志愿: {second_pref_cols}
  面试时间: {datetime_cols}

部门映射: {departments}
    """.format(**help_params)
    
    parser = argparse.ArgumentParser(
        description='从Excel文件读取面试者数据并生成JSON文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text
    )
    
    parser.add_argument(
        'excel_file',
        nargs='?',
        help='Excel文件路径'
    )
    
    parser.add_argument(
        '-o', '--output',
        default=OUTPUT_JSON_FILE,
        help=f'输出JSON文件路径 (默认: {OUTPUT_JSON_FILE})'
    )
    
    parser.add_argument(
        '-s', '--sheet',
        default=0,
        help='Excel工作表名称或索引 (默认: 0 - 第一个工作表)'
    )
    
    parser.add_argument(
        '-c', '--config',
        action='store_true',
        help='显示当前配置信息'
    )
    
    parser.add_argument(
        '--indent',
        type=int,
        default=JSON_INDENT,
        help=f'JSON格式化缩进空格数 (默认: {JSON_INDENT})'
    )
    
    parser.add_argument(
        '--encoding',
        default='utf-8',
        help='Excel文件编码 (默认: utf-8)'
    )
    
    return parser.parse_args()


def main():
    """
    主函数 - 使用命令行参数
    """
    args = parse_arguments()
    
    # 如果指定了config参数，显示配置信息
    if args.config:
        print_configuration()
        return
    
    # 检查是否提供了Excel文件路径
    if not args.excel_file:
        print("错误：请提供Excel文件路径")
        print("使用 --help 查看详细用法")
        return
    
    excel_file = args.excel_file
    
    if not os.path.exists(excel_file):
        print(f"错误：Excel文件不存在: {excel_file}")
        print("\n当前配置支持的列名映射:")
        for field, column_names in COLUMN_MAPPING.items():
            required_mark = "（必需）" if field in REQUIRED_FIELDS else "（可选）"
            print(f"- {field}{required_mark}: {', '.join(column_names)}")
        
        print("\n多列合并配置:")
        for field, config in MULTI_COLUMN_MAPPING.items():
            print(f"- {field}: 可合并列 {config['columns']}")
            print(f"  分隔符: '{config['separator']}'")
            if 'format_template' in config:
                print(f"  格式模板: {config['format_template']}")
        
        print(f"\n接受调剂真值: {ACCEPT_ADJUST_TRUE_VALUES}")
        print(f"接受调剂假值: {ACCEPT_ADJUST_FALSE_VALUES}")
        print(f"性别映射: {SEX_MAPPING}")
        print(f"部门映射: {DEPARTMENT_MAPPING}")
        return
    
    # 设置全局JSON缩进
    global JSON_INDENT
    JSON_INDENT = args.indent
    
    print(f"📁 输入文件: {excel_file}")
    print(f"📄 输出文件: {args.output}")
    print(f"📊 工作表: {args.sheet}")
    print(f"🔧 JSON缩进: {args.indent}")
    print()
    
    # 转换Excel数据为JSON
    success = convert_excel_to_json(excel_file, args.sheet, args.output)
    
    if success:
        print("\n✅ Excel数据转换成功！")
        print(f"📄 JSON文件已生成: {args.output}")
        print("\n使用方法:")
        print(f"  python manage.py loaddata {args.output}")
    else:
        print("❌ Excel数据转换失败！")


def print_configuration():
    """
    打印当前配置信息
    """
    print("=== 当前配置信息 ===")
    print("\n1. 列名映射配置:")
    for field, column_names in COLUMN_MAPPING.items():
        required_mark = "（必需）" if field in REQUIRED_FIELDS else "（可选）"
        print(f"   {field}{required_mark}: {', '.join(column_names)}")
    
    print("\n2. 多列合并配置:")
    for field, config in MULTI_COLUMN_MAPPING.items():
        print(f"   {field}:")
        print(f"     - 合并列: {config['columns']}")
        print(f"     - 分隔符: '{config['separator']}'")
        if 'format_template' in config:
            print(f"     - 格式模板: {config['format_template']}")
    
    print(f"\n3. 接受调剂配置:")
    print(f"   真值: {ACCEPT_ADJUST_TRUE_VALUES}")
    print(f"   假值: {ACCEPT_ADJUST_FALSE_VALUES}")
    
    print(f"\n4. 性别标准化配置:")
    for key, value in SEX_MAPPING.items():
        print(f"   '{key}' -> '{value}'")


if __name__ == "__main__":
    main()

