import csv
import json
import os
from os.path import join
import sys

def main(args):
    if len(args) < 2:
        sys.stderr.write('Required argument(s): <input directory> <output directory>\n')
        sys.exit(-1)

    in_dir = args[0]
    out_dir = args[1]
    if not out_dir[0] == '/':
        sys.stderr.write('Output directory argument must be an absolute path! (must begin with /)\n')
        sys.exit(-1)

    for fn in os.listdir(in_dir):
        if not fn.endswith('.csv'):
            continue

        full_path = join(in_dir, fn)
        with open(full_path) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                text = row.pop('OBSERVATION_BLOB')
                pt_num = row['PATIENT_NUM']
                enc_num = row['ENCOUNTER_NUM']
                inst_num = row['INSTANCE_NUM']

                out_key = '%s-%s-%s' % (pt_num, enc_num, inst_num)
                out_text_fn = out_key + '.txt'
                out_text_json = out_key + '.json'

                # create file with note text        
                with open(join(out_dir, out_text_fn), 'wt') as of:
                    of.write(text)

                # create file with note metadata
                with open(join(out_dir, out_text_json), 'wt') as of:
                    of.write(json.dumps(row))
                    
                # write note paths to 
                print(join(out_dir, out_text_fn))

if __name__ == '__main__':
    main(sys.argv[1:])

