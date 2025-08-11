from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, Optional
import ast
import inspect
from functools import wraps

# 基础LLM接口
class LLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        pass

# OpenAI提供者
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get('max_tokens', 1000),
            temperature=kwargs.get('temperature', 0.3)
        )
        return response.choices[0].message.content

# Claude提供者
class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get('max_tokens', 1000),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

# Google Gemini提供者
class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.model.generate_content(prompt)
        return response.text

# DeepSeek提供者（假设使用OpenAI兼容的API）
class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", 
                 model: str = "deepseek-coder"):
        import openai
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get('max_tokens', 1000),
            temperature=kwargs.get('temperature', 0.3)
        )
        return response.choices[0].message.content

# 统一的LLM函数生成器
class UniversalLLMFunctionGenerator:
    def __init__(self, provider: LLMProvider, base_prompt: Optional[str] = None):
        self.provider = provider
        self.base_prompt = base_prompt or self._default_prompt()
        self.function_cache = {}
    
    def _default_prompt(self) -> str:
        return """
你是一个专业的Python函数生成器。根据用户需求生成完整、可执行的Python函数。

要求：
1. 只返回纯Python函数代码，不要markdown格式或其他说明
2. 函数必须完整且可直接执行
3. 包含适当的错误处理和类型提示
4. 添加清晰的文档字符串
5. 使用描述性的函数名

用户需求：{instruction}

请生成Python函数：
"""
    
    def generate_function(self, instruction: str, function_name: str = None, 
                         cache: bool = True, **llm_kwargs) -> Callable:
        """生成函数"""
        cache_key = f"{function_name or 'func'}:{hash(instruction)}"
        
        if cache and cache_key in self.function_cache:
            return self.function_cache[cache_key]
        
        try:
            # 准备prompt
            prompt = self.base_prompt.format(instruction=instruction)
            if function_name:
                prompt += f"\n\n函数名必须是: {function_name}"
            
            # 调用LLM生成代码
            generated_code = self.provider.generate_text(prompt, **llm_kwargs)
            
            # 清理和处理代码
            function_code = self._clean_code(generated_code)
            
            # 创建函数对象
            func = self._create_function_from_code(function_code)
            
            if cache:
                self.function_cache[cache_key] = func
            
            return func
            
        except Exception as e:
            raise RuntimeError(f"生成函数失败: {str(e)}")
    
    def _clean_code(self, code: str) -> str:
        """清理生成的代码"""
        # 移除markdown代码块标记
        if code.strip().startswith("```python"):
            code = code.strip()[9:]
        elif code.strip().startswith("```"):
            code = code.strip()[3:]
        
        if code.strip().endswith("```"):
            code = code.strip()[:-3]
        
        return code.strip()
    
    def _create_function_from_code(self, code: str) -> Callable:
        """从代码创建函数对象"""
        try:
            # 验证代码语法
            ast.parse(code)
            
            # 创建安全的执行环境
            namespace = {
                '__builtins__': __builtins__,
                # 可以添加一些安全的内置函数和模块
                'math': __import__('math'),
                're': __import__('re'),
                'json': __import__('json'),
                'datetime': __import__('datetime'),
            }
            
            # 执行代码
            exec(code, namespace)
            
            # 查找生成的函数
            functions = {name: obj for name, obj in namespace.items() 
                        if callable(obj) and not name.startswith('_') 
                        and name not in ['math', 're', 'json', 'datetime']}
            
            if not functions:
                raise ValueError("代码中没有找到有效的函数定义")
            
            # 返回第一个找到的函数
            return list(functions.values())[0]
            
        except SyntaxError as e:
            raise RuntimeError(f"生成的代码语法错误: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"创建函数失败: {str(e)}")
    
    def create_decorator(self, instruction: str, function_name: str = None):
        """创建装饰器"""
        def decorator(dummy_func=None):
            actual_name = function_name or (dummy_func.__name__ if dummy_func else "generated_func")
            return self.generate_function(instruction, actual_name)
        return decorator

# 多提供者管理器
class MultiProviderLLMGenerator:
    def __init__(self):
        self.providers = {}
        self.generators = {}
    
    def add_provider(self, name: str, provider: LLMProvider):
        """添加LLM提供者"""
        self.providers[name] = provider
        self.generators[name] = UniversalLLMFunctionGenerator(provider)
    
    def generate_with_provider(self, provider_name: str, instruction: str, 
                             function_name: str = None, **kwargs) -> Callable:
        """使用指定提供者生成函数"""
        if provider_name not in self.generators:
            raise ValueError(f"未知的提供者: {provider_name}")
        
        return self.generators[provider_name].generate_function(
            instruction, function_name, **kwargs
        )
    
    def generate_with_fallback(self, instruction: str, function_name: str = None,
                             provider_order: list = None, **kwargs) -> Callable:
        """带回退机制的函数生成"""
        if not provider_order:
            provider_order = list(self.providers.keys())
        
        last_error = None
        for provider_name in provider_order:
            try:
                return self.generate_with_provider(
                    provider_name, instruction, function_name, **kwargs
                )
            except Exception as e:
                last_error = e
                print(f"提供者 {provider_name} 失败，尝试下一个...")
                continue
        
        raise RuntimeError(f"所有提供者都失败了。最后的错误: {last_error}")

# 使用示例
def main():
    # 创建多提供者管理器
    multi_gen = MultiProviderLLMGenerator()
    
    # 添加不同的LLM提供者
    # multi_gen.add_provider("openai", OpenAIProvider("your-openai-key"))
    # multi_gen.add_provider("claude", ClaudeProvider("your-claude-key"))
    # multi_gen.add_provider("gemini", GeminiProvider("your-gemini-key"))
    # multi_gen.add_provider("deepseek", DeepSeekProvider("your-deepseek-key"))
    
    # 示例：使用OpenAI生成函数
    try:
        # openai_gen = UniversalLLMFunctionGenerator(
        #     OpenAIProvider("your-api-key")
        # )
        
        # # 生成一个质数检测函数
        # is_prime = openai_gen.generate_function(
        #     "创建一个函数，检测一个数字是否为质数，包含错误处理",
        #     "is_prime"
        # )
        
        # print(f"17是质数吗？{is_prime(17)}")
        # print(f"函数源码：\n{inspect.getsource(is_prime)}")
        
        print("请按照注释中的示例配置你的API密钥后运行")
        
    except Exception as e:
        print(f"示例执行失败: {e}")

# 简化的配置辅助函数
def quick_setup(provider_type: str, api_key: str, **kwargs) -> UniversalLLMFunctionGenerator:
    """快速设置生成器"""
    providers = {
        'openai': lambda: OpenAIProvider(api_key, kwargs.get('model', 'gpt-3.5-turbo')),
        'claude': lambda: ClaudeProvider(api_key, kwargs.get('model', 'claude-3-sonnet-20240229')),
        'gemini': lambda: GeminiProvider(api_key, kwargs.get('model', 'gemini-pro')),
        'deepseek': lambda: DeepSeekProvider(api_key, kwargs.get('base_url', 'https://api.deepseek.com/v1'))
    }
    
    if provider_type not in providers:
        raise ValueError(f"不支持的提供者类型: {provider_type}")
    
    provider = providers[provider_type]()
    return UniversalLLMFunctionGenerator(provider)

if __name__ == "__main__":
    main()