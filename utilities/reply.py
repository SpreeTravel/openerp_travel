import os


def get_dict():
    res = {}
    with open('seed_es.po') as f:
        tmp = None
        for x in f.readlines():
            parts = x.split(' ', 1)
            if parts[0] == 'msgid':
                res[parts[1]] = None
                tmp = parts[1]
            elif parts[0] == 'msgstr':
                res[tmp] = parts[1]
    return res


if __name__ == '__main__':
    seed = get_dict()
    files = os.listdir('./')
    files = [f for f in files if '.po' in f and 'seed' not in f]
    print files
    for x in files:
        with open(x) as f:
            f2 = open('copy_' + x, 'w')
            for lines in f.readlines():
                parts = lines.split(' ', 1)
                if parts[0] == 'msgid':
                    tmp = parts[1]
                    f2.write(lines)
                elif parts[0] == 'msgstr':
                    try:
                        f2.write('msgstr ' + seed[tmp])
                    except KeyError:
                        f2.write(lines)
                else:
                    f2.write(lines)
