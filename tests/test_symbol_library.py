# -*- coding: utf-8 -*-
"""符号库完整性回归测试。"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "cazz-patent" / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


md_to_docx = _load("md_to_docx", SCRIPTS / "md_to_docx.py")


def test_relations_and_operators():
    expected = {
        "lesssim": "≲", "gtrsim": "≳", "triangleq": "≜",
        "therefore": "∴", "because": "∵", "nleq": "≰", "nsim": "≁",
        "uplus": "⊎", "sqsubseteq": "⊑", "boxplus": "⊞", "dagger": "†",
        "varkappa": "ϰ", "varpi": "ϖ", "checkmark": "✓", "backslash": "∖",
    }
    for key, value in expected.items():
        assert md_to_docx._SYMBOLS.get(key) == value, f"symbol {key} mismatch"


def test_arrows_and_integrals():
    expected = {
        "hookrightarrow": "↪", "rightleftharpoons": "⇌",
        "updownarrow": "↕", "nearrow": "↗", "multimap": "⊸",
        "iiint": "∭", "oint": "∮", "bigwedge": "⋀", "blacktriangle": "▲",
    }
    for key, value in expected.items():
        assert md_to_docx._SYMBOLS.get(key) == value, f"symbol {key} mismatch"


def test_function_names_and_accents_are_structural():
    structural = [
        "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "coth",
        "csc", "sec", "cot", "deg", "lg", "hom", "sgn", "diag", "tr",
        "trace", "rank", "span", "erf", "erfc", "adj", "liminf", "limsup",
        "injlim", "projlim", "varliminf", "varlimsup",
        "mathfrak", "mathsf", "mathtt", "mathscr", "bm",
        "widehat", "widetilde", "check", "breve", "acute", "grave", "mathring",
        "overline", "underline",
    ]
    for name in structural:
        assert name in md_to_docx._SKIP_COMMANDS, f"{name} should be structural"


def test_new_symbols_resolve_without_unknown():
    latex = r"$$\arg\min_x f(x) \lesssim y \triangleq z \Rightarrow w \hookrightarrow v \quad \iiint_\Omega \varphi \, dV \widehat{\theta} = \overline{\mu} \therefore$$"
    _sym_map, unknown = md_to_docx._build_symbol_map(latex)
    assert not unknown, f"unexpected unknown commands: {sorted(unknown)}"
