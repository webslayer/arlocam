import multiprocessing
import time


def timeout(secs):
    def wrap(f):
        def wrapped_f(*args):
            p = multiprocessing.Process(target=f, args=(args))
            p.start()

            # Wait for 10 seconds or until process finishes
            p.join(secs)

            # If thread is still active
            if p.is_alive():
                print("running... let's kill it...")

                # Terminate
                p.terminate()
                p.join()

        return wrapped_f

    return wrap


@timeout(10)
def bar(r):
    for i in range(r):
        print("Tick")
        time.sleep(1)


if __name__ == "__main__":
    bar(100)
