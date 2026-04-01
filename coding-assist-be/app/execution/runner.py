import base64
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.problems.models import ExecutionResult

JUDGE0_API_BASE_URL = "https://ce.judge0.com"
JUDGE0_LANGUAGE_ID_PYTHON = 71
JUDGE0_POLL_INTERVAL_MS = 400
JUDGE0_MAX_POLL_ATTEMPTS = 20


@dataclass
class RunnerInput:
    code: str
    stdin_payload: str


def _wrap_code(code: str) -> str:
    return (
        f"{code}\n\n"
        "if __name__ == '__main__':\n"
        "    if 'solve' in globals() and callable(globals()['solve']):\n"
        "        solve()\n"
    )


def run_python_code_local(code: str, stdin_payload: str) -> ExecutionResult:
    settings = get_settings()
    job = RunnerInput(code=code, stdin_payload=stdin_payload)
    with tempfile.TemporaryDirectory(prefix="learn-assist-") as temp_dir:
        script_path = Path(temp_dir) / "submission.py"
        script_path.write_text(_wrap_code(job.code), encoding="utf-8")
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                ["python", str(script_path)],
                input=job.stdin_payload,
                text=True,
                capture_output=True,
                timeout=settings.execution_timeout_seconds,
                check=False,
            )
            runtime_ms = int((time.perf_counter() - started) * 1000)
            return ExecutionResult(
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
                timed_out=False,
                runtime_ms=runtime_ms,
            )
        except subprocess.TimeoutExpired as exc:
            runtime_ms = int((time.perf_counter() - started) * 1000)
            return ExecutionResult(
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                exit_code=124,
                timed_out=True,
                runtime_ms=runtime_ms,
            )


def run_python_code_docker(code: str, stdin_payload: str) -> ExecutionResult:
    settings = get_settings()
    job = RunnerInput(code=code, stdin_payload=stdin_payload)

    with tempfile.TemporaryDirectory(prefix="learn-assist-docker-") as temp_dir:
        temp_path = Path(temp_dir)
        script_path = temp_path / "submission.py"
        script_path.write_text(_wrap_code(job.code), encoding="utf-8")

        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            settings.docker_disabled_network,
            "--cpus",
            "0.5",
            "--memory",
            f"{settings.execution_memory_mb}m",
            "-v",
            f"{temp_path}:/workspace:ro",
            settings.judge_image,
            "python",
            "/workspace/submission.py",
        ]

        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                input=job.stdin_payload,
                text=True,
                capture_output=True,
                timeout=settings.execution_timeout_seconds + 1,
                check=False,
            )
            runtime_ms = int((time.perf_counter() - started) * 1000)
            return ExecutionResult(
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
                timed_out=False,
                runtime_ms=runtime_ms,
            )
        except subprocess.TimeoutExpired as exc:
            runtime_ms = int((time.perf_counter() - started) * 1000)
            return ExecutionResult(
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                exit_code=124,
                timed_out=True,
                runtime_ms=runtime_ms,
            )
        except FileNotFoundError:
            return ExecutionResult(
                stdout="",
                stderr="Docker not found. Please install Docker Desktop.",
                exit_code=127,
                timed_out=False,
                runtime_ms=0,
            )


def _encode_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def _decode_base64(text: str | None) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text).decode("utf-8")
    except Exception:
        return ""


def _judge0_headers() -> dict[str, str]:
    return {"Content-Type": "application/json"}


def run_python_code_judge0(code: str, stdin_payload: str) -> ExecutionResult:
    settings = get_settings()
    job = RunnerInput(code=code, stdin_payload=stdin_payload)
    wrapped_code = _wrap_code(job.code)

    payload = {
        "language_id": JUDGE0_LANGUAGE_ID_PYTHON,
        "source_code": _encode_base64(wrapped_code),
        "stdin": _encode_base64(job.stdin_payload),
    }
    headers = _judge0_headers()
    started = time.perf_counter()
    timeout = settings.execution_timeout_seconds + 5
    base_url = JUDGE0_API_BASE_URL.rstrip("/")

    try:
        with httpx.Client(timeout=timeout) as client:
            submit_response = client.post(
                f"{base_url}/submissions?base64_encoded=true&wait=false&fields=*",
                json=payload,
                headers=headers,
            )
            submit_response.raise_for_status()
            token = submit_response.json().get("token")
            if not token:
                return ExecutionResult(
                    stdout="",
                    stderr="Judge0 did not return a token.",
                    exit_code=1,
                    timed_out=False,
                    runtime_ms=0,
                )

            result_payload: dict | None = None
            for _ in range(JUDGE0_MAX_POLL_ATTEMPTS):
                poll_response = client.get(
                    f"{base_url}/submissions/{token}?base64_encoded=true&fields=*",
                    headers=headers,
                )
                poll_response.raise_for_status()
                result_payload = poll_response.json()
                status_id = (result_payload.get("status") or {}).get("id")
                if status_id not in (1, 2):
                    break
                time.sleep(JUDGE0_POLL_INTERVAL_MS / 1000.0)

            runtime_ms = int((time.perf_counter() - started) * 1000)
            if not result_payload:
                return ExecutionResult(
                    stdout="",
                    stderr="Judge0 polling failed with empty response.",
                    exit_code=1,
                    timed_out=False,
                    runtime_ms=runtime_ms,
                )

            status = result_payload.get("status") or {}
            status_id = status.get("id", 0)
            status_description = status.get("description", "Unknown status")
            stdout = _decode_base64(result_payload.get("stdout"))
            stderr = _decode_base64(result_payload.get("stderr"))
            compile_output = _decode_base64(result_payload.get("compile_output"))
            message = _decode_base64(result_payload.get("message"))

            if status_id == 3:
                return ExecutionResult(
                    stdout=stdout,
                    stderr="",
                    exit_code=0,
                    timed_out=False,
                    runtime_ms=runtime_ms,
                )

            if status_id in (1, 2, 5):
                return ExecutionResult(
                    stdout=stdout,
                    stderr=stderr or status_description,
                    exit_code=124,
                    timed_out=True,
                    runtime_ms=runtime_ms,
                )

            combined_error = "\n".join(
                value for value in [stderr, compile_output, message, status_description] if value
            ).strip()
            return ExecutionResult(
                stdout=stdout,
                stderr=combined_error or "Execution failed",
                exit_code=1,
                timed_out=False,
                runtime_ms=runtime_ms,
            )
    except httpx.HTTPError as exc:
        runtime_ms = int((time.perf_counter() - started) * 1000)
        return ExecutionResult(
            stdout="",
            stderr=f"Judge0 HTTP error: {exc}",
            exit_code=1,
            timed_out=False,
            runtime_ms=runtime_ms,
        )


def run_python_code(code: str, stdin_payload: str) -> ExecutionResult:
    settings = get_settings()
    if settings.execution_backend == "local":
        return run_python_code_local(code, stdin_payload)
    if settings.execution_backend == "judge0":
        return run_python_code_judge0(code, stdin_payload)
    return run_python_code_docker(code, stdin_payload)
