from eibon.sanitizer_config import SanitizerEnvironment


def test_config_defaults(tmp_path):
    sane = SanitizerEnvironment('')

    assert 'ASAN_OPTIONS' in sane.environment
    assert 'LSAN_OPTIONS' in sane.environment
    assert 'UBSAN_OPTIONS' in sane.environment
