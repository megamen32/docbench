"""docbench — Document Conformance Benchmark harness.

Two benchmarks:
  * conformance     — documents + canonical ruleset -> findings/evidence/disposition
  * rule_extraction — institution policy document -> machine-readable ruleset

Sidecars:
  * datasets — manifest-driven fetch of external benchmark datasets
  * errorgen — deterministic controlled corruption of valid packets
"""

__version__ = "0.1.0"
