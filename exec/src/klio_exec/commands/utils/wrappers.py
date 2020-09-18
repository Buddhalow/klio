# Copyright 2020 Spotify AB

import functools
import inspect


def _get_transform_error_msg(txf=None, entity_id=None, err_msg=None):
    # This error message is printed instead of logged since user may not
    # run with logs turned on
    return (
        "WARN: Error caught while profiling {txf}.process for "
        "entity ID {entity_id}: {err_msg}".format(
            txf=txf, entity_id=entity_id, err_msg=err_msg
        )
    )


def _print_user_exceptions_generator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        transform_name = args[0].__class__.__name__
        entity_id = args[1]
        result = None
        try:
            result = yield from func(*args, **kwargs)

        except Exception as e:
            msg = _get_transform_error_msg(
                txf=transform_name, entity_id=entity_id, err_msg=e
            )
            print(msg)

        return result

    return wrapper


def _print_user_exceptions_func(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        transform_name = args[0].__class__.__name__
        entity_id = args[1]
        result = None
        try:
            result = func(*args, **kwargs)

        except Exception as e:
            msg = _get_transform_error_msg(
                txf=transform_name, entity_id=entity_id, err_msg=e
            )
            print(msg)

        return result

    return wrapper


def print_user_exceptions(profile_fn):
    # Don't crap out if the process method errors; just continue profiling
    if inspect.isgeneratorfunction(profile_fn):
        return _print_user_exceptions_generator(profile_fn)
    else:
        return _print_user_exceptions_func(profile_fn)


# adapted from line_profiler; memory_profiler doesn't handle generator
# functions for some reason.
class KLineProfilerMixin(object):
    """Mixin for CPU & Memory line profilers."""

    def __call__(self, func):
        # Overwrite to handle generators in the same fashion as funcs
        self.add_function(func)
        if inspect.isgeneratorfunction(func):
            return self.wrap_generator(func)
        return self.wrap_function(func)

    def wrap_function(self, func):
        """Wrap a function to profile it."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.enable_by_count()
            try:
                return func(*args, **kwargs)
            finally:
                self.disable_by_count()

        return wrapper

    def wrap_generator(self, func):
        """Wrap a generator to profile it."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.enable_by_count()
            try:
                yield from func(*args, **kwargs)
            finally:
                self.disable_by_count()

        return wrapper
