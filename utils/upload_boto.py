import os
import uuid
import logging
import boto3
import time
import json
import socket
import ssl
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# 导入凭证管理模块
from utils.credentials import load_credentials

# 配置日志，便于调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class S3Uploader:
    """
    一个用于将文件上传到 AWS S3 并获取 CDN 链接的类。
    它按照以下优先级顺序查找 AWS 凭证：
    1. Keyring (推荐) - 从操作系统的凭证管理器中加载
    2. 环境变量 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
    3. AWS 配置文件 (~/.aws/credentials, ~/.aws/config)
    4. aws_config.json (最终备选方案)
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
        self.s3_client = None

        # 按照优先级顺序尝试初始化 S3 客户端
        logging.info(f"Initializing S3 client for region: {self.region_name}")
        
        # 1. 首先尝试从keyring加载凭证
        if self._try_initialize_with_keyring():
            return
            
        # 2. 然后尝试使用默认配置初始化客户端（环境变量、AWS配置文件等）
        if self._try_initialize_with_default():
            return
            
        # 3. 最后尝试从aws_config.json文件加载凭证
        if self._try_initialize_with_config_file():
            return
            
        # 如果所有方法都失败了，记录日志但不抛出异常
        logging.warning("Failed to initialize S3 client with any available credentials. Upload functionality will be disabled.")
        # 不抛出异常，允许程序继续运行

    def _try_initialize_with_keyring(self) -> bool:
        """
        尝试使用keyring中存储的凭证初始化S3客户端。
        返回True表示成功，False表示失败。
        """
        try:
            logging.info("Trying to load AWS credentials from keyring")
            credentials = load_credentials()
            
            if credentials:
                access_key = credentials.get('aws_access_key_id')
                secret_key = credentials.get('aws_secret_access_key')
                region = credentials.get('region_name', self.region_name)
                
                if access_key and secret_key:
                    # 使用keyring中的凭证初始化客户端
                    self.s3_client = boto3.client(
                        "s3",
                        region_name=region,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key
                    )
                    
                    # 验证凭证是否有效前先检查网络连接
                    self._check_network_connectivity()
                    self.s3_client.list_buckets()
                    logging.info("Successfully initialized S3 client using keyring credentials")
                    return True
                else:
                    logging.warning("Keyring credentials are incomplete")
            else:
                logging.info("No credentials found in keyring")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logging.error(f"AWS client error when testing keyring credentials: {error_code} - {e}")
        except Exception as e:
            logging.error(f"Unexpected error when initializing S3 client with keyring credentials: {e}")
            
        return False

    def _try_initialize_with_default(self) -> bool:
        """
        尝试使用默认配置初始化S3客户端（环境变量、AWS配置文件等）。
        返回True表示成功，False表示失败。
        """
        try:
            logging.info("Trying to initialize S3 client with default credentials")
            # 尝试使用默认配置初始化客户端
            self.s3_client = boto3.client("s3", region_name=self.region_name)
            # 验证凭证是否有效前先检查网络连接
            self._check_network_connectivity()
            self.s3_client.list_buckets()
            logging.info("Successfully initialized S3 client with default credentials")
            return True
        except NoCredentialsError:
            logging.info("No AWS credentials found in default locations")
        except PartialCredentialsError:
            logging.error("Partial AWS credentials found in default locations")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logging.error(f"AWS client error when testing default credentials: {error_code} - {e}")
        except Exception as e:
            logging.error(f"Unexpected error when initializing S3 client with default credentials: {e}")
            
        return False

    def _try_initialize_with_config_file(self) -> bool:
        """
        尝试从aws_config.json文件加载凭证并初始化S3客户端。
        返回True表示成功，False表示失败。
        """
        try:
            logging.warning("No AWS credentials found in default locations, trying aws_config.json")
            # 获取项目根目录路径
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(root_dir, 'aws_config.json')
            
            # 检查配置文件是否存在
            if not os.path.exists(config_path):
                logging.error(f"AWS config file not found at {config_path}")
                return False
            
            # 读取配置文件
            with open(config_path, 'r') as f:
                aws_config = json.load(f)
            
            # 检查必要的凭证字段
            access_key = aws_config.get('aws_access_key_id')
            secret_key = aws_config.get('aws_secret_access_key')
            
            if not access_key or not secret_key:
                logging.error("Missing required AWS credentials in aws_config.json")
                return False
            
            # 使用配置文件中的凭证初始化客户端
            self.s3_client = boto3.client(
                "s3",
                region_name=self.region_name,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            # 验证凭证是否有效前先检查网络连接
            self._check_network_connectivity()
            self.s3_client.list_buckets()
            logging.info("Successfully initialized S3 client using aws_config.json")
            return True
        except FileNotFoundError:
            logging.error("AWS config file not found")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse AWS config file: {e}")
        except NoCredentialsError:
            logging.error("Invalid AWS credentials in aws_config.json")
        except PartialCredentialsError:
            logging.error("Incomplete AWS credentials in aws_config.json")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logging.error(f"AWS client error when testing config file credentials: {error_code} - {e}")
        except Exception as e:
            logging.error(f"Failed to initialize S3 client using aws_config.json: {e}")
            
        return False

    def _check_network_connectivity(self):
        """
        检查网络连接到 AWS S3 服务端点。
        """
        # AWS S3 服务端点
        s3_endpoint = f"s3.{self.region_name}.amazonaws.com"
        port = 443  # HTTPS port
        
        logging.info(f"Checking network connectivity to {s3_endpoint}:{port}")
        
        # 检查 DNS 解析
        try:
            addr_info = socket.getaddrinfo(s3_endpoint, port)
            logging.info(f"DNS resolution successful. Address info: {addr_info[0][:2]}")
        except socket.gaierror as e:
            logging.error(f"DNS resolution failed for {s3_endpoint}: {e}")
            raise Exception(f"DNS解析失败: 无法解析 {s3_endpoint}")
        
        # 检查 TCP 连接
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 seconds timeout
            # 使用第一个解析的地址
            addr = addr_info[0][4]
            result = sock.connect_ex(addr)
            sock.close()
            
            if result == 0:
                logging.info(f"TCP connection to {addr} successful")
            else:
                logging.error(f"TCP connection to {addr} failed with error code: {result}")
                raise Exception(f"TCP连接失败: 无法连接到 {addr}")
        except Exception as e:
            logging.error(f"TCP connection test failed: {e}")
            raise Exception(f"网络连接测试失败: {e}")
        
        # 检查 SSL/TLS 连接
        try:
            context = ssl.create_default_context()
            with socket.create_connection((s3_endpoint, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=s3_endpoint) as ssock:
                    logging.info(f"SSL/TLS connection to {s3_endpoint} successful")
                    # 获取证书信息
                    cert = ssock.getpeercert()
                    logging.debug(f"Server certificate: {cert}")
        except ssl.SSLError as e:
            logging.error(f"SSL/TLS connection failed: {e}")
            raise Exception(f"SSL/TLS连接失败: {e}")
        except Exception as e:
            logging.error(f"SSL/TLS connection test failed: {e}")
            raise Exception(f"SSL/TLS连接测试失败: {e}")

    def upload_file(self, file_path: str, s3_prefix: str = "page-img/") -> str | None:
        """
        将指定文件上传到 S3 桶并返回其 CDN 链接。

        参数:
            file_path (str): 要上传的本地文件的完整路径。
            s3_prefix (str): 在 S3 桶中存储文件的路径前缀，默认为 "page-img/"。

        返回:
            str | None: 上传成功后文件的完整 CDN 链接，如果上传失败则返回 None。
        """
        # 检查S3客户端是否已初始化
        if self.s3_client is None:
            logging.warning("S3 client is not initialized. Upload functionality is disabled.")
            raise Exception("AWS S3客户端未初始化，请先配置AWS凭证以启用上传功能。")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logging.error(f"Error: File not found at '{file_path}'")
            # 抛出 FileNotFoundError 比直接返回 False 更能清晰地指示问题
            raise FileNotFoundError(f"The file was not found at {file_path}")
        
        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            logging.error(f"Error: File '{file_path}' is not readable")
            raise PermissionError(f"文件 '{file_path}' 不可读")

        # 获取文件大小
        file_size = os.path.getsize(file_path)
        logging.info(f"Uploading file '{file_path}' with size {file_size} bytes")

        # 获取文件扩展名
        file_extension = os.path.splitext(file_path)[1]
        logging.debug(f"File extension: {file_extension}")

        # 生成一个唯一的 UUID 作为文件名，并保留原始文件的扩展名
        unique_file_name = str(uuid.uuid4()) + file_extension
        logging.debug(f"Generated unique file name: {unique_file_name}")
        
        # 构建 S3 存储桶中的完整对象键 (key)
        # 确保前缀以斜杠结尾，以便 os.path.join 正确拼接路径
        if not s3_prefix.endswith('/'):
            s3_prefix += '/'
        s3_key = os.path.join(s3_prefix, unique_file_name).replace('\\', '/') # 确保使用正斜杠
        logging.debug(f"Constructed S3 key: {s3_key}")

        try:
            # 尝试上传文件，并增加简单的重试机制
            # boto3 客户端本身也内置了重试逻辑，这里是一个额外的、可控的重试层
            for attempt in range(3):  # 最多尝试 3 次 (原始尝试 + 2 次重试)
                try:
                    logging.info(f"Attempt {attempt + 1}: Uploading '{file_path}' to s3://{self.bucket_name}/{s3_key}")
                    self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
                    logging.info(f"Successfully uploaded '{file_path}' to S3.")
                    break  # 上传成功，跳出重试循环
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    logging.warning(f"Upload attempt {attempt + 1} failed for '{file_path}' with error code {error_code}: {e}")
                    
                    # 根据错误类型决定是否重试
                    if error_code in ['NoSuchBucket', 'AccessDenied']:
                        # 这些错误通常不会通过重试解决
                        logging.error(f"Non-retryable error occurred: {error_code}")
                        raise e
                    elif attempt < 2:  # 如果是可重试的错误且还有重试机会
                        logging.info(f"Retrying upload in {2 ** attempt} seconds...")
                        time.sleep(2 ** attempt)  # 指数退避
                    else:
                        # 所有重试都失败了
                        raise e
                except Exception as e:
                    logging.warning(f"Upload attempt {attempt + 1} failed for '{file_path}' with unexpected error: {e}")
                    if attempt < 2:  # 如果还有重试机会
                        logging.info(f"Retrying upload in {2 ** attempt} seconds...")
                        time.sleep(2 ** attempt)  # 指数退避
                    else:
                        # 所有重试都失败了
                        raise e
            else:
                # 如果循环正常结束（即没有在内部 break），说明所有尝试都失败了
                logging.error(f"Failed to upload file '{file_path}' to S3 after multiple attempts.")
                return None

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error(f"AWS ClientError during upload for '{file_path}': {error_code} - {error_message}")
            logging.error(f"Request ID: {e.response.get('ResponseMetadata', {}).get('RequestId', 'N/A')}")
            return None
        except FileNotFoundError as e:
            logging.error(f"File not found error during upload: {e}")
            return None
        except PermissionError as e:
            logging.error(f"Permission error during upload: {e}")
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
        logging.debug(f"Constructed CDN base: {cdn_base}")
        logging.debug(f"Final CDN link: {cdn_link}")

        logging.info(f"Generated CDN link for '{file_path}': {cdn_link}")
        return cdn_link

# example
if __name__ == "__main__":
    # 请根据您的实际情况进行修改。
    S3_BUCKET_NAME = "pacdora-upload"
    S3_BUCKET_HOST = "//cdn.pacdora.com/" # 确保以 "//" 或 "https://" 开头
    AWS_REGION = "us-east-2"

    try:
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
        except PermissionError as e:
            print(f"Permission Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            # 清理测试文件
            if os.path.exists(test_file_name):
                os.remove(test_file_name)
                logging.info(f"Cleaned up dummy file: {test_file_name}")
    except Exception as e:
        logging.error(f"Failed to initialize S3Uploader: {e}")
        print(f"S3Uploader initialization failed: {e}")