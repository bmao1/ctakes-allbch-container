import json
import requests
import sys

def main(args):
    if len(args) < 2:
        sys.stderr.write('Required arg(s): <input filenames file> <output directory>\n')

    url = 'http://localhost:8080/ctakes-web-rest/service/analyze'

    with open(args[0], 'rt') as f:
        filenames = f.read()

    for fn in filenames:
        basename = os.path.basename(fn)[:-4]

        json_fn = fn.replace('.txt', '.json')
        with open(json_fn, 'rt') as json_f:
            metadata = json.loads(json_f.read())

        with open(fn, 'rt') as f:
            text = f.read()
            r = requests.post(url, data=text, params={'format':'full'})
            if r.status_code == 200:
                output = r.json()
                output['metadata'] = metadata
                with open(join(args[1], basename + '.json'), 'wt') as of:
                    of.write(json.dumps(output))
            else:
                print(fn)

            
if __name__ == '__main__':
    main(sys.argv[1:])

