import json
import os
import requests
import sys
from os.path import join
import tqdm

from multiprocessing import Process, Queue
from threading import Thread
STARTING_PORT_NUM = 8080

def worker(url, input_queue, output_queue):
    for task in iter(input_queue.get, 'STOP'):
        text, metadata, output_fn = task

        try:
            r = requests.post(url, data=text, params={'format':'full'})
            if r.status_code == 200:
                output = r.json()
                output['metadata'] = metadata
        except:
            sys.stderr.write("Error processing instance num %s\n" % (inst_num,) )
            output = None

        output_queue.put( (output, output_fn) )

def write_worker(num_jobs, done_queue):
    # num_jobs is our intended number of jobs but if the DB doens't have that many
    # rows then we'll never get there. Instead just wait for the signal.

    with tqdm.tqdm(total=num_jobs) as pbar:
        while True:
            output, output_fn = done_queue.get()

            if not output is None:
                # error during processing
                if output == 'STOP':
                    break

                with open(output_fn, 'wt') as of:
                    of.write(json.dumps(output))

            # update progress bar every time even if the output was bad
            pbar.update()


def main(args):
    if len(args) < 2:
        sys.stderr.write('Required arg(s): <input filenames file> <output directory> [num_processes=1]\n')
        sys.exit(-1)

    url = 'http://localhost:8080/ctakes-web-rest/service/analyze'

    task_queue = Queue()
    done_queue = Queue()

    num_processes = 1
    if len(args) == 3:
        num_processes = int(args[2])

    processes = []
    for i in range(num_processes):
        # assume that the port numbers are sequential from 8080 up
        port_num = STARTING_PORT_NUM + i % num_processes
        url = 'http://localhost:%d/ctakes-web-rest/service/analyze' % (port_num)
        sys.stderr.write("Process %d sending requests to %s\n" % (i, url))
        processes.append(Process(target=worker, args=(url, task_queue, done_queue)))
        processes[i].start()


    with open(args[0], 'rt') as f:
        filenames = f.readlines()

    num_jobs = len(filenames)
    write_thread = Process(target=write_worker, args=(num_jobs, done_queue,))
    write_thread.start()

    for fn in filenames:
        fn = fn.rstrip()
        basename = os.path.basename(fn)[:-4]
        output_file = join(args[1], basename + '.json')

        json_fn = fn.replace('.txt', '.json')
        with open(json_fn, 'rt') as json_f:
            metadata = json.loads(json_f.read())

        with open(fn, 'rt') as f:
            text = f.read()
            task_queue.put( (text, metadata, output_file) )

    sys.stderr.write("Finished creating %d jobs\n" % (num_jobs,) )

    for i in range(num_processes):
        task_queue.put('STOP')

    # wait for all processes to finish
    for i in range(num_processes):
        # sys.stderr.write('Waiting for process %d to finish' % (i,))
        # sys.stderr.flush()
        processes[i].join()

    # tell consumer to finish
    done_queue.put( ('STOP', 'STOP') )

    write_thread.join()

if __name__ == '__main__':
    main(sys.argv[1:])

