import secrets


def generate_executor_id(prefix: str = "exec_") -> str:
    """
    生成执行器唯一标识符。
    格式: exec_ + 8位随机十六进制字符
    """
    # 使用 secrets 生成 4 字节的随机数并转换为十六进制 (8位)
    random_suffix = secrets.token_hex(4)
    return f"{prefix}{random_suffix}"


def generate_api_key(prefix: str = "ek_") -> str:
    """
    生成高熵的 API Key。
    格式: ek_ + 32位随机十六进制字符
    """
    # 使用 secrets 生成 16 字节的随机数并转换为十六进制 (32位)
    random_key = secrets.token_hex(16)
    return f"{prefix}{random_key}"
