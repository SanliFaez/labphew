from threading import Lock

_basler_lock = Lock()   # This lock prevents accessing the Basler buffer from two threads at the same time.
                        # Apparently Basler shares memory between cameras, and the process of reading from the grab
                        # result is not thread-safe. The error is very obscure (SIGSEGV on Linux).
