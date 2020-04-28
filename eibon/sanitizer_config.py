import logging
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, Iterator, Optional


class SanitizerMapping(Mapping):

    def __init__(self, /, **kwargs: Any):
        self._data = kwargs

    def __getitem__(self, item: str) -> str:
        return self._data[item]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @property
    def options(self) -> str:
        return ':'.join(f'{key}={value}' for key, value in self._data.items())


class SanitizerEnvironment:

    def __init__(
            self,
            target_dir: str,
            custom_config: Optional[Dict[str, str]] = None,
    ):
        self._env = os.environ.copy()

        self._setup_base(custom_config or {})
        self._setup_address_sanitizer(target_dir)
        self._setup_leak_sanitizer()
        self._setup_thread_sanitizer()
        self._setup_ub_sanitizer()

    @property
    def environment(self) -> Dict[str, str]:
        return self._env

    def _setup_base(self, custom_config) -> None:
        for name, value in custom_config.items():
            if value is None and name in self._env:
                logging.debug('removing env var %s', name)
                self._env.pop(name)
                continue

            self._env[name] = value

    def _setup_address_sanitizer(self, target_dir: str) -> None:
        self._env['ASAN_OPTIONS'] = SanitizerMapping(
            **{
                **self._address_sanitizer_defaults(),
                **self._sanitizer_options_from_env('ASAN_OPTIONS'),
            }
        ).options

        if 'ASAN_SYMBOLIZER_PATH' not in self._env:
            symbolizer_bin = Path(target_dir) / 'llvm-symbolizer'

            if symbolizer_bin.is_file():
                self._env['ASAN_SYMBOLIZER_PATH'] = str(symbolizer_bin)

            return

        if not Path(self._env['ASAN_SYMBOLIZER_PATH']).is_file():
            logging.warning(
                'Invalid ASAN_SYMBOLIZER_PATH (%s)',
                self._env['ASAN_SYMBOLIZER_PATH'],
            )

    def _setup_leak_sanitizer(self) -> None:
        self._env['LSAN_OPTIONS'] = SanitizerMapping(
            **{
                **self._leak_sanitizer_defaults(),
                **self._sanitizer_options_from_env('LSAN_OPTIONS'),
            }
        ).options

    def _setup_thread_sanitizer(self) -> None:
        self._env['TSAN_OPTIONS'] = SanitizerMapping(
            **{
                **self._thread_sanitizer_defaults(),
                **self._sanitizer_options_from_env('TSAN_OPTIONS'),
            }
        ).options

    def _setup_ub_sanitizer(self) -> None:
        self._env['UBSAN_OPTIONS'] = SanitizerMapping(
            **{
                **self._ub_sanitizer_defaults(),
                **self._sanitizer_options_from_env('UBSAN_OPTIONS'),
            }
        ).options

    @staticmethod
    def _address_sanitizer_defaults() -> SanitizerMapping:
        return SanitizerMapping(
            abort_on_error='false',
            allocator_may_return_null='true',
            check_initialization_order='true',
            detect_invalid_pointer_pairs='1',
            detect_leaks='true',
            disable_coredump='true',
            handle_abort='true',
            handle_sigbus='true',
            handle_sigfpe='true',
            handle_sigill='true',
            malloc_context_size='20',
            sleep_before_dying='0',
            strict_init_order='true',
            strict_string_checks='true',
            symbolize='true',
            print_stacktrace='1',
            debug='true',
            print_stats='true',
            unmap_shadow_on_exit='true'
        )

    @staticmethod
    def _leak_sanitizer_defaults() -> SanitizerMapping:
        return SanitizerMapping(
            max_leaks='1',
            print_suppressions='false',
        )

    @staticmethod
    def _thread_sanitizer_defaults() -> SanitizerMapping:
        return SanitizerMapping(
            halt_on_error='1',
        )

    @staticmethod
    def _ub_sanitizer_defaults() -> SanitizerMapping:
        return SanitizerMapping(
            print_stacktrace='1',
        )

    def _sanitizer_options_from_env(self, key: str) -> Dict[str, str]:
        if key not in self._env:
            return {}

        delim = re.compile(r":(?![\\|/])")
        options = {}

        for option in delim.split(self._env[key]):
            try:
                opt_name, opt_value = option.split('=')

                if ':' in opt_value:
                    assert is_quoted(opt_value), (
                        '%s value must be quoted' % opt_name)

                if opt_name == 'suppressions':
                    sup_file = Path.home().joinpath(opt_value.strip('\'"'))

                    if not sup_file.is_file():
                        raise IOError(
                            'Suppression file %s does not exist' % str(sup_file)
                        )

                    opt_value = f'"{sup_file}"'

                options[opt_name] = opt_value
            except ValueError:
                logging.warning("Malformed option in %r", key)

        return options


def is_quoted(token: str) -> bool:
    return (
        token.startswith('\'') and token.endswith('\'')
        or
        token.startswith('"') and token.endswith('"')
    )
