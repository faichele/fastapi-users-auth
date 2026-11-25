import warnings
from pathlib import Path


def test_web_auth_module_compiles_when_invalid_escapes_are_errors():
    module = Path(__file__).resolve().parents[1] / "dependencies" / "web_auth_deps.py"
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        warnings.simplefilter("error", SyntaxWarning)
        compile(module.read_bytes(), str(module), "exec")
