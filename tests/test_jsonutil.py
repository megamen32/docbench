from docbench.jsonutil import extract_json, strip_think


def test_strip_think_complete():
    assert strip_think("<think>internal</think>{\"a\": 1}") == '{"a": 1}'


def test_strip_think_truncated():
    assert strip_think("<think>the user just") == ""


def test_extract_plain_json():
    assert extract_json('{"a": {"b": 2}}') == {"a": {"b": 2}}


def test_extract_fenced_json():
    text = 'prose\n```json\n{"a": 1}\n```\nmore prose'
    assert extract_json(text) == {"a": 1}


def test_extract_with_braces_inside_strings():
    # raw text contains JSON-escaped quotes: {"cmd": "print(\"}\")", "x": 1}
    text = 'prefix {"cmd": "print(\\"}\\")", "x": 1} suffix'
    assert extract_json(text) == {"cmd": 'print("}")', "x": 1}


def test_extract_json_after_think_block():
    text = '<think>reasoning {"fake": 1}</think>\n{"real": 2}'
    assert extract_json(text) == {"real": 2}


def test_extract_none_on_garbage():
    assert extract_json("no json here at all") is None
