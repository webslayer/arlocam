import multiprocessing

from .arlo_wrap import ArloWrap


def snap_timeout():
    arlo = ArloWrap()
    p = multiprocessing.Process(target=arlo.take_snapshot)
    p.start()

    # Wait for 10 seconds or until process finishes
    p.join(60)

    # If thread is still active
    if p.is_alive():
        print("running... let's kill it...")

        # Terminate
        p.terminate()
        p.join()
