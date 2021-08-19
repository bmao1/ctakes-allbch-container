import csv
import json
import os
import requests
import sys
from os.path import join
import tqdm

from multiprocessing import Process, Queue
from threading import Thread
STARTING_PORT_NUM = 8080

def read_sem_types(fn):
    st_to_path = {}
    with open(fn, 'rt') as f:
        for line in f.readlines():
            line = line.rstrip()
            sem_type, path = line.split('\t')
            st_to_path[sem_type] = path

    return st_to_path

tui_to_path = read_sem_types('tui_sem_paths.txt')

def worker(url, input_queue, output_queue):
    for task in iter(input_queue.get, 'STOP'):
        text, metadata, output_fn = task

        try:
            r = requests.post(url, data=text, params={'format':'full'})
            if r.status_code == 200:
                output = r.json()['_views']['_InitialView']
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

                output_fn = output_fn.replace('.json', '.csv')
                with open(output_fn, 'wt') as of:
                    writer = csv.writer(of) 
                    metadata = output['metadata']
                    pt_num = metadata['PATIENT_NUM']
                    start_date = metadata['START_DATE']
                    for sem_type in output.keys():
                        for ent in output[sem_type]:
                            if 'ontologyConceptArr' in ent:
                                polarity = 'Asserted' if ent['polarity'] == 0 else 'Negated'
                                for concept in ent['ontologyConceptArr']:
                                    cui = concept['cui']
                                    pt = concept['preferredText']
                                    tui = concept['tui']
                                    sem_type_path = tui_to_path[tui]
                                    full_path = '/'.join([sem_type_path, '%s-%s' % (cui, pt)]).replace(' ', '_')
                                    
                                    writer.writerow([pt_num, full_path, '', polarity, start_date])

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

