import os


def get_dict():
    res = {}
    with open('seed.dict', 'r') as f:
        for x in f.readlines():
            parts = x.split(':')
            res[parts[0]] = parts[1]
    return res


def write_dict(res):
    path = os.path.join(os.getcwd(), 'seed.dict')
    if os.path.exists(path):
        os.remove(path)
    with open('seed.dict', 'w') as f:
        for key, value in res.items():
            key = key.strip()
            f.write(str(key) + ':' + str(value))


if __name__ == '__main__':
    seed = get_dict()
    files = os.listdir('./')
    files = [f for f in files if '.po' in f]
    print files
    for x in files:
        with open(x) as f:
            f2 = open('copy_' + x, 'w')
            for lines in f.readlines():
                parts = lines.split(' ', 1)
                if parts[0] == 'msgid':
                    tmp = parts[1].strip()
                    f2.write(lines)
                elif parts[0] == 'msgstr':
                    try:
                        f2.write('msgstr ' + seed[tmp])
                    except KeyError:
                        f2.write(lines)
                        cmpa = parts[1].strip()
                        if tmp != cmpa:
                            seed[tmp] = parts[1]
                else:
                    f2.write(lines)

    write_dict(seed)
