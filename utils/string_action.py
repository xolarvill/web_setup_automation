import re
from typing import List, Tuple, Dict
from difflib import SequenceMatcher

class StringPatternTransformer:
    """
    字符串模式转换器类
    
    给定两个字符串A和B，学习它们之间的转换模式，
    然后能够将任意字符串C中符合A模式的部分转换为B的对应形式。
    """
    
    def __init__(self, string_a: str, string_b: str):
        """
        初始化转换器
        
        Args:
            string_a: 原始字符串A
            string_b: 目标字符串B（作为改进标准）
        """
        self.string_a = string_a
        self.string_b = string_b
        self.transformation_rules = []
        self._analyze_differences()
    
    def _analyze_differences(self):
        """分析A和B之间的差异，提取转换规则"""
        # 使用SequenceMatcher分析字符串差异
        matcher = SequenceMatcher(None, self.string_a, self.string_b)
        
        # 获取匹配块
        matching_blocks = matcher.get_matching_blocks()
        
        # 提取转换规则
        a_pos = 0
        b_pos = 0
        
        for match in matching_blocks:
            # 处理匹配块之前的差异部分
            if a_pos < match.a or b_pos < match.b:
                a_segment = self.string_a[a_pos:match.a]
                b_segment = self.string_b[b_pos:match.b]
                
                if a_segment or b_segment:  # 至少有一个不为空
                    self.transformation_rules.append({
                        'from': a_segment,
                        'to': b_segment,
                        'type': 'substitution' if a_segment and b_segment else 
                               'deletion' if a_segment else 'insertion'
                    })
            
            # 更新位置到匹配块结束
            a_pos = match.a + match.size
            b_pos = match.b + match.size
    
    def get_transformation_rules(self) -> List[Dict]:
        """获取所有转换规则"""
        return self.transformation_rules
    
    def transform(self, string_c: str) -> str:
        """
        将字符串C中符合A模式的部分转换为B的对应形式
        
        Args:
            string_c: 要转换的字符串
            
        Returns:
            转换后的字符串
        """
        result = string_c
        
        # 首先尝试直接替换整个字符串A为B
        if self.string_a in result:
            result = result.replace(self.string_a, self.string_b)
        else:
            # 应用具体的转换规则
            for rule in self.transformation_rules:
                if rule['type'] == 'substitution':
                    if rule['from'] in result:
                        result = result.replace(rule['from'], rule['to'])
                elif rule['type'] == 'deletion':
                    if rule['from'] in result:
                        result = result.replace(rule['from'], '')
                # insertion类型的规则较复杂，这里暂时跳过
        
        return result
    
    def transform_advanced(self, string_c: str, context_aware: bool = True) -> str:
        """
        高级转换功能，支持上下文感知的转换
        
        Args:
            string_c: 要转换的字符串
            context_aware: 是否启用上下文感知
            
        Returns:
            转换后的字符串
        """
        if not context_aware:
            return self.transform(string_c)
        
        result = string_c
        
        # 寻找最长公共子序列和模式
        matcher = SequenceMatcher(None, self.string_a, string_c)
        similarity = matcher.ratio()
        
        # 如果相似度较高，进行更精确的转换
        if similarity > 0.3:  # 阈值可调
            # 找到匹配的部分并进行转换
            matching_blocks = matcher.get_matching_blocks()
            
            # 构建转换后的字符串
            new_parts = []
            c_pos = 0
            
            for match in matching_blocks:
                # 添加不匹配的前缀部分（保持原样）
                if c_pos < match.b:
                    new_parts.append(string_c[c_pos:match.b])
                
                # 对匹配部分应用A->B的转换逻辑
                if match.size > 0:
                    matched_part = string_c[match.b:match.b + match.size]
                    # 这里可以应用更复杂的转换逻辑
                    new_parts.append(matched_part)
                
                c_pos = match.b + match.size
            
            # 添加剩余部分
            if c_pos < len(string_c):
                new_parts.append(string_c[c_pos:])
            
            candidate_result = ''.join(new_parts)
            
            # 如果高级转换产生了变化，使用它；否则回退到简单转换
            if candidate_result != string_c:
                result = candidate_result
        
        # 最后应用简单的替换规则作为补充
        final_result = self.transform(result)
        
        return final_result
    
    def show_analysis(self):
        """显示A和B之间的分析结果"""
        print(f"原始字符串A: '{self.string_a}'")
        print(f"目标字符串B: '{self.string_b}'")
        print(f"\n发现的转换规则:")
        
        for i, rule in enumerate(self.transformation_rules):
            print(f"  规则 {i+1}: {rule['type']}")
            print(f"    从: '{rule['from']}' -> 到: '{rule['to']}'")
        
        # 计算相似度
        similarity = SequenceMatcher(None, self.string_a, self.string_b).ratio()
        print(f"\n字符串相似度: {similarity:.2%}")


# 使用示例
if __name__ == "__main__":
    # 示例1: 简单的字符替换
    print("=== 示例1: 简单替换 ===")
    transformer1 = StringPatternTransformer("hello world", "hello universe")
    transformer1.show_analysis()
    
    test_string1 = "I say hello world to everyone"
    result1 = transformer1.transform(test_string1)
    print(f"\n转换测试:")
    print(f"输入: '{test_string1}'")
    print(f"输出: '{result1}'")
    
    print("\n" + "="*50 + "\n")
    
    # 示例2: 复杂的模式变化
    print("=== 示例2: 复杂模式 ===")
    transformer2 = StringPatternTransformer("快速的棕色狐狸", "敏捷的棕色狐狸")
    transformer2.show_analysis()
    
    test_string2 = "这只快速的棕色狐狸跳过了懒狗"
    result2 = transformer2.transform(test_string2)
    print(f"\n转换测试:")
    print(f"输入: '{test_string2}'")
    print(f"输出: '{result2}'")
    
    print("\n" + "="*50 + "\n")
    
    # 示例3: 高级转换
    print("=== 示例3: 高级转换 ===")
    transformer3 = StringPatternTransformer("old_function_name", "new_function_name")
    transformer3.show_analysis()
    
    test_string3 = "Please call old_function_name() in your code"
    result3 = transformer3.transform_advanced(test_string3)
    print(f"\n高级转换测试:")
    print(f"输入: '{test_string3}'")
    print(f"输出: '{result3}'")