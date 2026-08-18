from .conformance import ConformanceBenchmark
from .iri_review import IriReviewBenchmark
from .rule_extraction import RuleExtractionBenchmark

BENCHMARKS = {
    "conformance": ConformanceBenchmark,
    "iri_review": IriReviewBenchmark,
    "rule_extraction": RuleExtractionBenchmark,
}
