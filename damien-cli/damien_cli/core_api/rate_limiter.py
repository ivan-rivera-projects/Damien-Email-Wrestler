def with_rate_limiting(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper