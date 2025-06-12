# DeepEval 是一个用于评估大型语言模型（LLM）应用的框架，特别适用于检索增强生成（RAG）等场景。
# 它提供了多种评估指标，帮助开发者量化和分析模型的性能。

from deepeval.metrics import ContextualPrecisionMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

# 定义一个测试案例（LLMTestCase），这是 DeepEval 进行评估的基本单元。
# 它封装了评估所需的全部信息。
test_case = LLMTestCase(
    # input: 用户的原始输入或问题。
    input="如果这双鞋不合脚怎么办？",
    # actual_output: 你的 RAG 系统或 LLM 应用针对该输入实际生成的答案。
    actual_output="我们提供30天无理由全额退款服务。",
    # expected_output: 预期的、理想的答案。这通常作为评估的"黄金标准"。
    expected_output="顾客可以在30天内退货并获得全额退款。",
    # retrieval_context: RAG 系统检索到的、用于生成答案的上下文信息。
    retrieval_context=["所有顾客都有资格享受30天无理由全额退款服务。"]
)

# 定义评估指标（Metrics）
# ContextualPrecisionMetric: 上下文精确度。
# 该指标评估检索到的上下文中有多少内容被实际用于生成答案。
# 一个低分可能表示检索到的上下文包含了大量与生成答案无关的信息。
contextual_precision = ContextualPrecisionMetric()

# AnswerRelevancyMetric: 答案相关性。
# 该指标评估生成的答案与原始输入问题的相关程度。
# 一个低分表示答案可能没有直接回应用户的问题。
answer_relevancy = AnswerRelevancyMetric()

# 使用定义的指标对测试案例进行评估。
# .measure() 方法会执行评估并计算得分。
contextual_precision.measure(test_case)
answer_relevancy.measure(test_case)

# 打印评估结果。
# 分数通常在 0 到 1 之间，1 表示最佳表现。
print("上下文精确度得分: ", contextual_precision.score)
print("答案相关性得分: ", answer_relevancy.score)
