import os
import uuid
import logging
import boto3
import time
import json

# 配置日志，便于调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class S3Uploader:
    """
    一个用于将文件上传到 AWS S3 并获取 CDN 链接的类。
    它依赖于已在本地 AWS CLI 中配置的凭证（例如，通过 ~/.aws/credentials 文件或环境变量）。
    """

    def __init__(
        self,
        bucket_name: str = "pacdora-upload",
        bucket_host: str = "//cdn.pacdora.com/",
        region_name: str = "us-east-2"
    ):
        """
        初始化 S3Uploader 实例。

        参数:
            bucket_name (str): S3 桶的名称。
            bucket_host (str): CDN 的主机名，例如 "cdn.pacdora.com/"。
                                 它应该以 "//" 或 "http(s)://" 开头，否则会自动添加 "//"。
            region_name (str): AWS S3 桶所在的区域，默认为 "us-east-2"。
        """
        self.bucket_name = bucket_name
        self.bucket_host = bucket_host
        self.region_name = region_name

        # 初始化 S3 客户端。
        # boto3 会自动查找 AWS 凭证，优先级通常是：
        # 1. 环境变量 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
        # 2. AWS 配置文件 (~/.aws/credentials, ~/.aws/config)
        # 3. ECS/EC2 实例配置文件
        logging.info(f"Initializing S3 client for region: {self.region_name}")
        
        try:
            # 尝试使用默认配置初始化客户端
            self.s3_client = boto3.client("s3", region_name=self.region_name)
        except:
            # 如果默认配置失败，尝试从项目根目录读取aws_config.json
            try:
                # 获取项目根目录路径
                root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(root_dir, 'aws_config.json')
                
                # 读取配置文件
                with open(config_path, 'r') as f:
                    aws_config = json.load(f)
                
                # 使用配置文件中的凭证初始化客户端
                self.s3_client = boto3.client(
                    "s3",
                    region_name=self.region_name,
                    aws_access_key_id=aws_config.get('aws_access_key_id'),
                    aws_secret_access_key=aws_config.get('aws_secret_access_key')
                )
                logging.info("Successfully initialized S3 client using aws_config.json")
            except Exception as e:
                logging.error(f"Failed to initialize S3 client using aws_config.json: {e}")
                raise Exception("无法初始化S3客户端，请检查AWS配置")
        

    def upload_file(self, file_path: str, s3_prefix: str = "page-img/") -> str | None:
        """
        将指定文件上传到 S3 桶并返回其 CDN 链接。

        参数:
            file_path (str): 要上传的本地文件的完整路径。
            s3_prefix (str): 在 S3 桶中存储文件的路径前缀，默认为 "page-img/"。

        返回:
            str | None: 上传成功后文件的完整 CDN 链接，如果上传失败则返回 None。
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logging.error(f"Error: File not found at '{file_path}'")
            # 抛出 FileNotFoundError 比直接返回 False 更能清晰地指示问题
            raise FileNotFoundError(f"The file was not found at {file_path}")

        # 获取文件扩展名
        file_extension = os.path.splitext(file_path)[1]

        # 生成一个唯一的 UUID 作为文件名，并保留原始文件的扩展名
        unique_file_name = str(uuid.uuid4()) + file_extension
        
        # 构建 S3 存储桶中的完整对象键 (key)
        # 确保前缀以斜杠结尾，以便 os.path.join 正确拼接路径
        if not s3_prefix.endswith('/'):
            s3_prefix += '/'
        s3_key = os.path.join(s3_prefix, unique_file_name).replace('\\', '/') # 确保使用正斜杠

        try:
            # 尝试上传文件，并增加简单的重试机制
            # boto3 客户端本身也内置了重试逻辑，这里是一个额外的、可控的重试层
            for attempt in range(2):  # 最多尝试 2 次 (原始尝试 + 1 次重试)
                try:
                    logging.info(f"Attempt {attempt + 1}: Uploading '{file_path}' to s3://{self.bucket_name}/{s3_key}")
                    self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
                    logging.info(f"Successfully uploaded '{file_path}' to S3.")
                    break  # 上传成功，跳出重试循环
                except Exception as e:
                    logging.warning(f"Upload attempt {attempt + 1} failed for '{file_path}': {e}")
                    if attempt < 1:  # 如果是第一次失败，等待1秒后重试
                        time.sleep(1)
                    else:
                        # 如果所有重试都失败，则重新抛出异常
                        raise e
            else:
                # 如果循环正常结束（即没有在内部 break），说明所有尝试都失败了
                logging.error(f"Failed to upload file '{file_path}' to S3 after multiple attempts.")
                return None

        except Exception as e:
            logging.error(f"An unrecoverable error occurred during upload for '{file_path}': {e}")
            return None  # 上传过程中发生任何未捕获的异常，返回 None 表示失败

        # 构建 CDN 链接
        # 确保 bucket_host 以协议头 "//" 或 "http(s)://" 开头
        cdn_base = self.bucket_host
        if not cdn_base.startswith('//') and not cdn_base.startswith('http://') and not cdn_base.startswith('https://'):
            cdn_base = "//" + cdn_base

        # 移除 bucket_host 尾部的斜杠以避免重复斜杠，并确保 s3_key 没有前导斜杠
        cdn_link = f"https:{cdn_base.rstrip('/')}/{s3_key.lstrip('/')}"

        logging.info(f"Generated CDN link for '{file_path}': {cdn_link}")
        return cdn_link

# example
if __name__ == "__main__":
    # 请根据您的实际情况进行修改。
    S3_BUCKET_NAME = "pacdora-upload"
    S3_BUCKET_HOST = "//cdn.pacdora.com/" # 确保以 "//" 或 "https://" 开头
    AWS_REGION = "us-east-2"

    # 实例化 S3Uploader
    uploader = S3Uploader(
        bucket_name=S3_BUCKET_NAME,
        bucket_host=S3_BUCKET_HOST,
        region_name=AWS_REGION
    )

    # 创建一个虚拟文件用于测试
    test_file_name = "test_image.jpg"
    try:
        with open(test_file_name, "w") as f:
            f.write("This is a test image content.")
        logging.info(f"Created a dummy file: {test_file_name}")

        # 调用 upload_file 方法进行上传
        cdn_url = uploader.upload_file(test_file_name)

        if cdn_url:
            print(f"\n文件 '{test_file_name}' 上传成功！CDN 链接: {cdn_url}")
        else:
            print(f"\n文件 '{test_file_name}' 上传失败。请检查日志和 AWS CLI 配置。")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # 清理测试文件
        if os.path.exists(test_file_name):
            os.remove(test_file_name)
            logging.info(f"Cleaned up dummy file: {test_file_name}")

