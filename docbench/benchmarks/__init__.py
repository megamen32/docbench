from .conformance import ConformanceBenchmark
from .rule_extraction import RuleExtractionBenchmark

BENCHMARKS = {
    "conformance": ConformanceBenchmark,
    "rule_extraction": RuleExtractionBenchmark,
}
