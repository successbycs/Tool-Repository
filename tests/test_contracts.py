from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_repository.contracts import Adapter, AdapterResult, Idempotency, OperationDefinition, SideEffect, validate_adapter_contract


class ExampleAdapter(Adapter):
    adapter_id = "example"

    def validate_config(self, config: dict[str, object]) -> list[str]:
        return [] if config.get("enabled") is True else ["enabled must be true"]

    def list_operations(self) -> list[OperationDefinition]:
        return [OperationDefinition("echo", "Return the supplied message.", {"type": "object"}, {"type": "object"}, SideEffect.READ_ONLY, Idempotency.IDEMPOTENT)]

    def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, object], *, config: dict[str, object]) -> AdapterResult:
        return AdapterResult(success=True, output={"message": arguments.get("message")})

    def health_check(self, *, config: dict[str, object]) -> AdapterResult:
        return AdapterResult(success=True, output={"ready": True}) if config.get("enabled") is True else AdapterResult.failure("invalid_config", "enabled must be true")


class ContractTests(unittest.TestCase):
    def test_example_adapter_satisfies_static_contract(self) -> None:
        self.assertEqual(validate_adapter_contract(ExampleAdapter()), [])

    def test_results_are_normalized(self) -> None:
        result = ExampleAdapter().invoke("echo", {"message": "hello"}, config={"enabled": True})
        self.assertEqual(result.to_dict(), {"success": True, "output": {"message": "hello"}, "error": None, "metadata": {}})

    def test_contradictory_results_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            AdapterResult(success=True, error={"code": "x", "message": "x", "retryable": False})
        with self.assertRaises(ValueError):
            AdapterResult(success=False, error={"code": "x", "message": "x", "retryable": False}, output={"unexpected": True})
        with self.assertRaises(ValueError):
            AdapterResult(success="yes")  # type: ignore[arg-type]

    def test_duplicate_operations_are_rejected(self) -> None:
        class DuplicateAdapter(ExampleAdapter):
            def list_operations(self) -> list[OperationDefinition]:
                operation = super().list_operations()[0]
                return [operation, operation]

        self.assertIn("duplicate operation name: echo", validate_adapter_contract(DuplicateAdapter()))

    def test_malformed_operation_metadata_is_rejected_without_crashing(self) -> None:
        class MalformedAdapter(ExampleAdapter):
            adapter_id = 123

            def list_operations(self) -> list[OperationDefinition]:
                return [OperationDefinition("destroy", "Destroy data.", {}, {}, "destructive", "unknown", "later")]  # type: ignore[arg-type]

        issues = validate_adapter_contract(MalformedAdapter())
        self.assertIn("adapter_id must be a non-empty string", issues)
        self.assertIn("destroy: side_effect must be a SideEffect", issues)
        self.assertIn("destroy: idempotency must be an Idempotency", issues)
        self.assertIn("destroy: timeout_seconds must be a finite positive number when provided", issues)

    def test_destructive_operation_requires_explicit_opt_in(self) -> None:
        class DestructiveAdapter(ExampleAdapter):
            def list_operations(self) -> list[OperationDefinition]:
                return [OperationDefinition("delete", "Delete test data.", {}, {}, SideEffect.DESTRUCTIVE, Idempotency.IDEMPOTENT)]

            def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, object], *, config: dict[str, object]) -> AdapterResult:
                return AdapterResult(success=True, output={"deleted": True})

        adapter = DestructiveAdapter()
        denied = adapter.invoke("delete", {}, config={"enabled": True})
        self.assertEqual(denied.error["code"], "destructive_opt_in_required")
        string_denied = adapter.invoke("delete", {}, config={"enabled": True}, allow_destructive="false")  # type: ignore[arg-type]
        self.assertEqual(string_denied.error["code"], "destructive_opt_in_required")
        self.assertTrue(adapter.invoke("delete", {}, config={"enabled": True}, allow_destructive=True).success)

    def test_malformed_operation_cannot_bypass_destructive_gate(self) -> None:
        class RawOperationAdapter(ExampleAdapter):
            def list_operations(self) -> list[OperationDefinition]:
                return [OperationDefinition("delete", "Delete test data.", {}, {}, "destructive", "unknown")]  # type: ignore[arg-type]

        result = RawOperationAdapter().invoke("delete", {}, config={"enabled": True}, allow_destructive=True)
        self.assertEqual(result.error["code"], "invalid_operation_definition")

    def test_invalid_operation_name_is_rejected_during_discovery(self) -> None:
        class InvalidNameAdapter(ExampleAdapter):
            def list_operations(self) -> list[OperationDefinition]:
                return [OperationDefinition([], "Invalid name.", {}, {}, SideEffect.READ_ONLY, Idempotency.IDEMPOTENT)]  # type: ignore[arg-type]

        result = InvalidNameAdapter().invoke("echo", {}, config={"enabled": True})
        self.assertEqual(result.error["code"], "invalid_operation_definition")

    def test_unclassified_execution_failure_is_not_marked_retryable(self) -> None:
        class FailingAdapter(ExampleAdapter):
            def _invoke_operation(self, operation: OperationDefinition, arguments: dict[str, object], *, config: dict[str, object]) -> AdapterResult:
                raise RuntimeError("provider unavailable")

        result = FailingAdapter().invoke("echo", {}, config={"enabled": True})
        self.assertEqual(result.error, {"code": "adapter_execution_failed", "message": "adapter operation failed", "retryable": False})

    def test_invalid_config_and_unknown_operation_return_normalized_failures(self) -> None:
        adapter = ExampleAdapter()
        self.assertEqual(adapter.invoke("echo", {}, config={}).error["code"], "invalid_config")
        self.assertEqual(adapter.invoke("missing", {}, config={"enabled": True}).error["code"], "operation_not_found")
