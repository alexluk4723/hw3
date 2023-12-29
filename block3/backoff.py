import time

def backoff(tries, sleep):
    def backoff_decorator(fun):
        def backoff_wrapper(*args, **kwargs):
            iter_try = 0
            while iter_try < tries:
                try:
                    return fun(*args, **kwargs)
                except Exception as _:
                    iter_try += 1
                    print(f"Attempt {iter_try} of {tries} is failed; sleep {sleep} seconds...")
                    if iter_try < tries:
                        time.sleep(sleep)
            print("Failed. Try again later")
        return backoff_wrapper
    return backoff_decorator