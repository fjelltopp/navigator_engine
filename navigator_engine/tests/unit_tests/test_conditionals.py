import navigator_engine.pluggable_logic.conditional_functions as conditionals
import pytest


@pytest.mark.parametrize("actions,expected,remove_skips", [
    ([1], True, []),
    ([2], False, [2]),
    ([1, 2, 3], False, [2, 3])
])
def test_check_not_skipped(mock_engine, actions, expected, remove_skips):
    mock_engine.progress.skipped = [2, 3, 4]
    result = conditionals.check_not_skipped(actions, mock_engine)
    assert result == expected
    assert mock_engine.remove_skips == remove_skips


def test_check_not_skipped_raises_error(mock_engine):
    with pytest.raises(TypeError, match="hello"):
        conditionals.check_not_skipped("hello", mock_engine)
