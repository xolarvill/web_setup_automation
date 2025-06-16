import os
import boto3
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError


class ImageUploader:
    """
    AWS S3图片上传器，支持批量上传和CDN链接获取
    """
    
    def __init__(self, 
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 bucket_name: Optional[str] = None,
                 cdn_domain: Optional[str] = None,
                 region: str = 'us-east-1',
                 folder_prefix: str = 'images/'):
        """
        初始化上传器
        
        Args:
            access_key: AWS访问密钥ID
            secret_key: AWS秘密访问密钥
            bucket_name: S3存储桶名称
            cdn_domain: CDN域名
            region: AWS区域
            folder_prefix: S3中的文件夹前缀
        """
        # 从参数或环境变量获取配置
        self.access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.bucket_name = bucket_name or os.getenv('AWS_S3_BUCKET')
        self.cdn_domain = cdn_domain or os.getenv('CDN_DOMAIN')
        self.region = region
        self.folder_prefix = folder_prefix.rstrip('/') + '/'
        
        # 状态变量
        self.is_activated = False
        self.s3_client = None
        self.uploaded_files = {}  # 存储已上传文件的映射
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        
        # 支持的图片格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    
    def activate(self) -> bool:
        """
        激活上传器，验证AWS凭证和配置
        
        Returns:
            bool: 激活是否成功
        """
        try:
            # 验证必要参数
            if not all([self.access_key, self.secret_key, self.bucket_name]):
                self.logger.error("缺少必要的AWS配置参数")
                return False
            
            # 创建S3客户端
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            # 测试连接和权限
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            self.is_activated = True
            self.logger.info(f"ImageUploader已激活，连接到存储桶: {self.bucket_name}")
            return True
            
        except NoCredentialsError:
            self.logger.error("AWS凭证无效")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.logger.error(f"存储桶不存在: {self.bucket_name}")
            elif error_code == '403':
                self.logger.error("没有访问存储桶的权限")
            else:
                self.logger.error(f"AWS客户端错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"激活失败: {e}")
            return False
    
    def _generate_file_key(self, file_path: str) -> str:
        """
        生成S3文件键名
        
        Args:
            file_path: 本地文件路径
            
        Returns:
            str: S3文件键名
        """
        file_name = Path(file_path).name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 使用文件内容的MD5哈希确保唯一性
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        
        name, ext = os.path.splitext(file_name)
        unique_name = f"{name}_{timestamp}_{file_hash}{ext}"
        
        return f"{self.folder_prefix}{unique_name}"
    
    def _is_image_file(self, file_path: str) -> bool:
        """
        检查文件是否为支持的图片格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为支持的图片格式
        """
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: MD5哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def check_if_uploaded(self, file_path: str) -> Optional[str]:
        """
        检查文件是否已经上传过
        
        Args:
            file_path: 本地文件路径
            
        Returns:
            Optional[str]: 如果已上传返回CDN链接，否则返回None
        """
        if not os.path.exists(file_path):
            return None
        
        file_hash = self._get_file_hash(file_path)
        return self.uploaded_files.get(file_hash)
    
    def _generate_cdn_url(self, s3_key: str) -> str:
        """
        生成CDN链接
        
        Args:
            s3_key: S3文件键名
            
        Returns:
            str: CDN链接
        """
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{s3_key}"
        else:
            # 如果没有CDN域名，返回S3直链
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
    
    def upload_single_image(self, file_path: str, 
                           custom_key: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        上传单个图片文件
        
        Args:
            file_path: 本地文件路径
            custom_key: 自定义S3键名（可选）
            metadata: 文件元数据（可选）
            
        Returns:
            Tuple[bool, str]: (是否成功, CDN链接或错误信息)
        """
        if not self.is_activated:
            return False, "上传器未激活，请先调用activate()"
        
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        
        if not self._is_image_file(file_path):
            return False, f"不支持的文件格式: {file_path}"
        
        try:
            # 检查是否已上传
            existing_url = self.check_if_uploaded(file_path)
            if existing_url:
                self.logger.info(f"文件已存在，返回现有链接: {existing_url}")
                return True, existing_url
            
            # 生成S3键名
            s3_key = custom_key or self._generate_file_key(file_path)
            
            # 准备上传参数
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Filename': file_path,
                'ExtraArgs': {
                    'ContentType': self._get_content_type(file_path),
                    'ACL': 'public-read'  # 设置为公开可读
                }
            }
            
            # 添加元数据
            if metadata:
                upload_args['ExtraArgs']['Metadata'] = metadata
            
            # 执行上传
            self.s3_client.upload_file(**upload_args)
            
            # 生成CDN链接
            cdn_url = self._generate_cdn_url(s3_key)
            
            # 记录已上传文件
            file_hash = self._get_file_hash(file_path)
            self.uploaded_files[file_hash] = cdn_url
            
            self.logger.info(f"上传成功: {file_path} -> {cdn_url}")
            return True, cdn_url
            
        except ClientError as e:
            error_msg = f"AWS上传错误: {e}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"上传失败: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _get_content_type(self, file_path: str) -> str:
        """
        根据文件扩展名获取Content-Type
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: MIME类型
        """
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.tiff': 'image/tiff'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def uploadandget(self, file_paths: List[str], 
                    progress_callback: Optional[callable] = None) -> Dict[str, Dict]:
        """
        批量上传图片并获取CDN链接
        
        Args:
            file_paths: 文件路径列表
            progress_callback: 进度回调函数，接收(current, total, file_path)参数
            
        Returns:
            Dict[str, Dict]: 上传结果，格式为:
            {
                'file_path': {
                    'success': bool,
                    'cdn_url': str,
                    'error': str  # 仅在失败时存在
                }
            }
        """
        if not self.is_activated:
            raise RuntimeError("上传器未激活，请先调用activate()")
        
        results = {}
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            if progress_callback:
                progress_callback(i, total_files, file_path)
            
            success, result = self.upload_single_image(file_path)
            
            if success:
                results[file_path] = {
                    'success': True,
                    'cdn_url': result
                }
            else:
                results[file_path] = {
                    'success': False,
                    'error': result
                }
        
        if progress_callback:
            progress_callback(total_files, total_files, "完成")
        
        return results
    
    def batch_upload_from_directory(self, directory_path: str,
                                   recursive: bool = True,
                                   progress_callback: Optional[callable] = None) -> Dict[str, Dict]:
        """
        从目录批量上传图片
        
        Args:
            directory_path: 目录路径
            recursive: 是否递归子目录
            progress_callback: 进度回调函数
            
        Returns:
            Dict[str, Dict]: 上传结果
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        # 收集所有图片文件
        image_files = []
        path_obj = Path(directory_path)
        
        if recursive:
            for ext in self.supported_formats:
                image_files.extend(path_obj.rglob(f"*{ext}"))
                image_files.extend(path_obj.rglob(f"*{ext.upper()}"))
        else:
            for ext in self.supported_formats:
                image_files.extend(path_obj.glob(f"*{ext}"))
                image_files.extend(path_obj.glob(f"*{ext.upper()}"))
        
        # 转换为字符串路径
        image_paths = [str(f) for f in image_files]
        
        self.logger.info(f"在目录 {directory_path} 中找到 {len(image_paths)} 个图片文件")
        
        return self.uploadandget(image_paths, progress_callback)
    
    def get_upload_stats(self) -> Dict:
        """
        获取上传统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'total_uploaded': len(self.uploaded_files),
            'is_activated': self.is_activated,
            'bucket_name': self.bucket_name,
            'cdn_domain': self.cdn_domain
        }


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建上传器实例
    uploader = ImageUploader(
        # 这些参数也可以通过环境变量设置
        access_key="AKIA4R7O5HD37MCR2L6J",
        secret_key="w0QOkYqzgwKMAxniXUOCenY5F2LWyDOc2phVfyGA", 
        bucket_name="pacdora-upload",
        cdn_domain="your-cdn-domain.com",
        region="us-east-2"
    )
    
    # 激活上传器
    if uploader.activate():
        print("上传器激活成功！")
        
        # 单个文件上传示例
        success, result = uploader.upload_single_image("path/to/your/image.jpg")
        if success:
            print(f"上传成功！CDN链接: {result}")
        else:
            print(f"上传失败: {result}")
        
        # 批量上传示例
        file_list = ["image1.jpg", "image2.png", "image3.gif"]
        
        def progress_callback(current, total, file_path):
            print(f"进度: {current}/{total} - 当前文件: {file_path}")
        
        results = uploader.uploadandget(file_list, progress_callback)
        
        # 输出结果
        for file_path, result in results.items():
            if result['success']:
                print(f"✓ {file_path}: {result['cdn_url']}")
            else:
                print(f"✗ {file_path}: {result['error']}")
    
    else:
        print("上传器激活失败！请检查配置。")