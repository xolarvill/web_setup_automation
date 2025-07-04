import keyring
import json

# 使用一个固定的服务名称来存储所有相关的凭证
SERVICE_NAME = "WSA_AWS_Credentials"

def save_credentials(access_key: str, secret_key: str, region: str):
    """
    将AWS凭证安全地保存到操作系统的凭证管理器中。
    我们将所有凭证打包成一个JSON字符串进行存储。
    """
    credentials = {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region_name": region
    }
    # Keyring希望用户名为字符串，我们用一个固定的key来存储整个JSON包
    keyring.set_password(SERVICE_NAME, "aws_credentials", json.dumps(credentials))

def load_credentials() -> dict | None:
    """
    从操作系统的凭证管理器中加载AWS凭证。
    返回一个包含凭证的字典，如果找不到则返回None。
    """
    try:
        credentials_json = keyring.get_password(SERVICE_NAME, "aws_credentials")
        if credentials_json:
            return json.loads(credentials_json)
        return None
    except Exception as e:
        # 在某些环境下（如无头服务器），keyring可能会失败
        print(f"无法从凭证管理器加载凭证: {e}")
        return None

def delete_credentials():
    """
    从操作系统的凭证管理器中删除已存储的AWS凭证。
    """
    try:
        keyring.delete_password(SERVICE_NAME, "aws_credentials")
    except keyring.errors.PasswordDeleteError:
        # 如果凭证不存在，某些后端会抛出错误，可以安全地忽略
        pass
