
import sys

def main(args):

    sem_types = {}
    path_to_tui = {}
    for line in sys.stdin.readlines():
        parts = line.split('|')
        if parts[0] == 'STY':
            tui = parts[1]
            sem_type = parts[2]
            tree_path = parts[3]
            sem_types[tui] = (sem_type, tree_path)
            path_to_tui[tree_path] = tui

    for tui in sem_types.keys():
        sem_type, path = sem_types[tui]
        path_elements = path.split('.')
        
        parents = []
        print("Building path for tui %s with path %s and elements %s" % (tui, path, str(path_elements)))
        for ind in range(1,len(path_elements)):
            subpath = '.'.join(path_elements[:ind])
            print("Subpath at ind %d is %s" % (ind, subpath))
            sub_type = sem_types[path_to_tui[subpath]][0]
            parents.append(sub_type)

        parents.append(sem_type)
        path = '/'.join(parents)

        print('%s\t/%s' % (tui, path))



     
if __name__ == '__main__':
    main(sys.argv[1:])

