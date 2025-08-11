"""
基于SimpleLLMFunc的智能函数生成器
结合了SimpleLLMFunc的优势和动态代码生成能力
"""

from typing import Callable, Dict, Any, Optional, List, Union
import ast
import inspect
from functools import wraps
from pydantic import BaseModel, Field
from SimpleLLMFunc import llm_function, OpenAICompatible, app_log
from SimpleLLMFunc.logger import log_context

# 定义代码生成的返回类型
class GeneratedFunction(BaseModel):
    function_code: str = Field(..., description="完整的Python函数代码，包含def关键字")
    function_name: str = Field(..., description="生成的函数名")
    description: str = Field(..., description="函数功能描述")
    parameters: List[str] = Field(..., description="函数参数列表")
    return_type: str = Field(..., description="返回值类型说明")
    imports: List[str] = Field(default=[], description="需要的导入语句列表")

class FunctionMetadata(BaseModel):
    name: str
    description: str
    parameters: Dict[str, str]
    return_type: str
    source_code: str

class SimpleLLMFuncCodeGenerator:
    """基于SimpleLLMFunc的代码生成器"""
    
    def __init__(self, llm_interface, cache_functions: bool = True):
        """
        初始化代码生成器
        
        Args:
            llm_interface: SimpleLLMFunc的LLM接口实例
            cache_functions: 是否缓存生成的函数
        """
        self.llm_interface = llm_interface
        self.function_cache = {} if cache_functions else None
        self.generated_functions_registry = {}
    
    @llm_function
    def _generate_function_structure(self, instruction: str, function_name: str = None) -> GeneratedFunction:
        """你是一个专业的Python代码生成专家。根据用户需求生成完整、高质量的Python函数。
        
        生成要求：
        1. 函数必须完整且可直接执行
        2. 包含适当的错误处理和边界检查
        3. 添加清晰的文档字符串和类型注解
        4. 使用Python最佳实践
        5. 确保代码的可读性和可维护性
        6. 只生成函数定义，不要包含示例调用代码
        7. 如果需要导入模块，在imports字段中列出
        
        代码风格要求：
        - 使用4空格缩进
        - 变量名使用snake_case
        - 函数名具有描述性
        - 适当的注释说明复杂逻辑
        
        Args:
            instruction: 用户对函数功能的详细描述
            function_name: 指定的函数名（可选）
            
        Returns:
            包含完整函数信息的GeneratedFunction对象
        """
        pass
    
    def generate_function(self, instruction: str, function_name: str = None, 
                         cache: bool = True) -> Callable:
        """
        生成可执行的Python函数
        
        Args:
            instruction: 函数功能描述
            function_name: 指定函数名
            cache: 是否使用缓存
            
        Returns:
            生成的可调用函数对象
        """
        cache_key = f"{function_name or 'auto'}:{hash(instruction)}"
        
        # 检查缓存
        if cache and self.function_cache and cache_key in self.function_cache:
            app_log(f"从缓存中获取函数: {cache_key}")
            return self.function_cache[cache_key]
        
        with log_context(function_name="generate_function"):
            try:
                app_log(f"开始生成函数: {instruction[:50]}...")
                
                # 使用SimpleLLMFunc生成函数结构
                self._generate_function_structure.__wrapped__.__globals__['llm_interface'] = self.llm_interface
                generated = self._generate_function_structure(instruction, function_name)
                
                app_log(f"生成的函数名: {generated.function_name}")
                app_log(f"函数描述: {generated.description}")
                
                # 创建可执行函数
                executable_func = self._create_executable_function(generated)
                
                # 缓存函数
                if cache and self.function_cache:
                    self.function_cache[cache_key] = executable_func
                
                # 注册到函数注册表
                self.generated_functions_registry[generated.function_name] = FunctionMetadata(
                    name=generated.function_name,
                    description=generated.description,
                    parameters={param: "auto-detected" for param in generated.parameters},
                    return_type=generated.return_type,
                    source_code=generated.function_code
                )
                
                return executable_func
                
            except Exception as e:
                app_log(f"函数生成失败: {str(e)}", level="ERROR")
                raise RuntimeError(f"函数生成失败: {str(e)}")
    
    def _create_executable_function(self, generated: GeneratedFunction) -> Callable:
        """从GeneratedFunction对象创建可执行函数"""
        try:
            # 验证代码语法
            ast.parse(generated.function_code)
            
            # 准备执行环境
            namespace = self._create_safe_namespace()
            
            # 处理导入语句
            for import_stmt in generated.imports:
                try:
                    exec(import_stmt, namespace)
                except ImportError as e:
                    app_log(f"导入失败，跳过: {import_stmt}, 错误: {e}", level="WARNING")
            
            # 执行函数定义
            exec(generated.function_code, namespace)
            
            # 查找生成的函数
            if generated.function_name in namespace:
                func = namespace[generated.function_name]
                
                # 添加元数据
                func._generated_metadata = {
                    'description': generated.description,
                    'parameters': generated.parameters,
                    'return_type': generated.return_type,
                    'source_code': generated.function_code
                }
                
                return func
            else:
                raise ValueError(f"未找到函数: {generated.function_name}")
                
        except SyntaxError as e:
            raise RuntimeError(f"生成的代码语法错误: {str(e)}\n代码:\n{generated.function_code}")
        except Exception as e:
            raise RuntimeError(f"函数创建失败: {str(e)}")
    
    def _create_safe_namespace(self) -> Dict[str, Any]:
        """创建安全的代码执行环境"""
        return {
            '__builtins__': {
                # 基本函数
                'len': len, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
                'sum': sum, 'max': max, 'min': min, 'abs': abs,
                'round': round, 'sorted': sorted, 'reversed': reversed,
                
                # 类型相关
                'int': int, 'float': float, 'str': str, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'type': type, 'isinstance': isinstance,
                
                # 异常处理
                'Exception': Exception, 'ValueError': ValueError,
                'TypeError': TypeError, 'IndexError': IndexError,
                'KeyError': KeyError,
                
                # 输出
                'print': print
            },
            # 常用模块
            'math': __import__('math'),
            'random': __import__('random'),
            'datetime': __import__('datetime'),
            're': __import__('re'),
            'json': __import__('json'),
            'collections': __import__('collections'),
            'itertools': __import__('itertools'),
        }
    
    def create_decorator(self, instruction: str, function_name: str = None):
        """创建装饰器，可以替换现有函数"""
        def decorator(dummy_func=None):
            actual_name = function_name or (dummy_func.__name__ if dummy_func else "generated_func")
            generated_func = self.generate_function(instruction, actual_name)
            
            # 保留原函数的一些属性
            if dummy_func:
                generated_func.__module__ = dummy_func.__module__
                generated_func.__qualname__ = dummy_func.__qualname__
            
            return generated_func
        
        return decorator
    
    def get_function_info(self, function_name: str) -> Optional[FunctionMetadata]:
        """获取生成函数的元数据信息"""
        return self.generated_functions_registry.get(function_name)
    
    def list_generated_functions(self) -> List[str]:
        """列出所有已生成的函数名"""
        return list(self.generated_functions_registry.keys())
    
    def get_function_source(self, function_name: str) -> Optional[str]:
        """获取生成函数的源代码"""
        metadata = self.get_function_info(function_name)
        return metadata.source_code if metadata else None


class SmartFunctionFactory:
    """智能函数工厂，提供更高级的功能"""
    
    def __init__(self, llm_interface):
        self.generator = SimpleLLMFuncCodeGenerator(llm_interface)
        self.function_templates = {}
    
    def register_template(self, name: str, template: str):
        """注册函数模板"""
        self.function_templates[name] = template
    
    def generate_from_template(self, template_name: str, **kwargs) -> Callable:
        """基于模板生成函数"""
        if template_name not in self.function_templates:
            raise ValueError(f"未找到模板: {template_name}")
        
        template = self.function_templates[template_name]
        instruction = template.format(**kwargs)
        
        return self.generator.generate_function(instruction)
    
    def generate_batch_functions(self, instructions: List[Dict[str, str]]) -> Dict[str, Callable]:
        """批量生成函数"""
        results = {}
        
        for item in instructions:
            name = item.get('name', 'generated_func')
            instruction = item['instruction']
            
            try:
                func = self.generator.generate_function(instruction, name)
                results[name] = func
                app_log(f"成功生成函数: {name}")
            except Exception as e:
                app_log(f"生成函数失败 {name}: {str(e)}", level="ERROR")
        
        return results
    
    def create_interactive_generator(self):
        """创建交互式函数生成器"""
        def interactive():
            while True:
                try:
                    print("\n=== 智能函数生成器 ===")
                    print("输入 'quit' 退出")
                    print("输入 'list' 查看已生成函数")
                    
                    user_input = input("请描述您需要的函数功能: ").strip()
                    
                    if user_input.lower() == 'quit':
                        break
                    elif user_input.lower() == 'list':
                        functions = self.generator.list_generated_functions()
                        print(f"已生成的函数: {', '.join(functions)}")
                        continue
                    
                    func_name = input("函数名（留空自动生成）: ").strip() or None
                    
                    print("正在生成函数...")
                    func = self.generator.generate_function(user_input, func_name)
                    
                    print(f"\n生成成功！函数名: {func.__name__}")
                    print("函数源码:")
                    print("-" * 50)
                    print(inspect.getsource(func))
                    print("-" * 50)
                    
                    # 询问是否测试函数
                    test = input("是否要测试函数？(y/n): ").strip().lower()
                    if test == 'y':
                        print("请按照函数签名输入测试参数...")
                        # 这里可以添加更复杂的测试逻辑
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"错误: {str(e)}")
        
        return interactive

# 使用示例
def main():
    """使用SimpleLLMFunc代码生成器的示例"""
    
    # 从配置文件加载LLM接口
    try:
        # 这里需要您自己的provider.json配置文件
        provider_interfaces = OpenAICompatible.load_from_json_file("provider.json")
        llm_interface = provider_interfaces["your_provider"]["your_model"]
        
        # 创建代码生成器
        generator = SimpleLLMFuncCodeGenerator(llm_interface)
        
        # 示例1: 生成数据分析函数
        print("=== 示例1: 生成数据分析函数 ===")
        analyze_func = generator.generate_function(
            "创建一个函数，接收数字列表，返回包含平均值、中位数、标准差和最大最小值的统计信息字典",
            "analyze_statistics"
        )
        
        test_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = analyze_func(test_data)
        print(f"统计结果: {result}")
        print(f"函数源码:\n{inspect.getsource(analyze_func)}")
        
        # 示例2: 使用装饰器模式
        print("\n=== 示例2: 装饰器模式 ===")
        
        @generator.create_decorator(
            "创建一个函数，判断给定字符串是否为有效的邮箱地址，支持常见的邮箱格式验证",
            "is_valid_email"
        )
        def email_validator():
            pass
        
        test_emails = ["test@example.com", "invalid.email", "user@domain.co.uk"]
        for email in test_emails:
            is_valid = email_validator(email)
            print(f"{email}: {'有效' if is_valid else '无效'}")
        
        # 示例3: 智能函数工厂
        print("\n=== 示例3: 智能函数工厂 ===")
        factory = SmartFunctionFactory(llm_interface)
        
        # 注册模板
        factory.register_template(
            "sort_algorithm",
            "创建一个{algorithm}排序算法的实现，支持{order}排序，函数名为{func_name}"
        )
        
        # 基于模板生成
        quick_sort = factory.generate_from_template(
            "sort_algorithm",
            algorithm="快速",
            order="升序和降序",
            func_name="enhanced_quick_sort"
        )
        
        test_array = [64, 34, 25, 12, 22, 11, 90]
        sorted_array = quick_sort(test_array.copy())
        print(f"原数组: {test_array}")
        print(f"排序后: {sorted_array}")
        
        # 查看生成的函数信息
        print("\n=== 生成的函数注册表 ===")
        for func_name in generator.list_generated_functions():
            info = generator.get_function_info(func_name)
            print(f"函数名: {func_name}")
            print(f"描述: {info.description}")
            print(f"参数: {info.parameters}")
            print(f"返回类型: {info.return_type}")
            print("-" * 30)
            
    except FileNotFoundError:
        print("请创建 provider.json 配置文件")
        print("示例配置：")
        print("""
{
    "your_provider": {
        "your_model": {
            "api_keys": ["your-api-key"],
            "base_url": "https://api.your-provider.com/v1",
            "model": "your-model-name"
        }
    }
}
        """)
    except Exception as e:
        print(f"示例运行失败: {str(e)}")

if __name__ == "__main__":
    main()