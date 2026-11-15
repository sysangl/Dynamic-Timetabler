from multiprocessing import Process


def run_parallel(*fns):
    proc:list[Process] = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()