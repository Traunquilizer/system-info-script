import sys
import getopt
from subprocess import *


def main(argv):
    try:
        opts, args = getopt.getopt(
            argv, "t:s:i:h", ["help", "ifile=", "timer=", "service="])
    except getopt.GetoptError:
        print('info.py -i <inputfile> or info.py -t <systemd timer> or info.py -s <systemd service>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h --help':
            print('info.py -i <inputfile> or info.py -t <systemd timer> or info.py -s <systemd service>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            disk_devices(arg)
        elif opt in ("-t", "--timer"):
            systemd_timers(arg)
        elif opt in ("-s", "--service"):
            systemd_services(arg)


def disk_devices(arg):
    with open(arg) as target_f:
        target = target_f.readline().strip('\n')
    try:
        part1 = run(['lsblk', '-o', 'NAME,TYPE,SIZE,FSAVAIL,FSTYPE,MOUNTPOINT',
                     target], capture_output=True, text=True, check=True)
        part2 = run(['grep', '-w', target.split("/")[-1]], input=part1.stdout,
                    capture_output=True, text=True, check=True)
    except CalledProcessError as e:
        print(e)
        sys.exit(1)
    info = part2.stdout.split()
    info[0] = target
    print(' '.join(info))


def systemd_timers(arg):
    try:
        part1 = run(['systemctl', 'list-timers', arg],
                    capture_output=True, text=True, check=True)
        part2 = run(['grep', '-w', arg], input=part1.stdout,
                    capture_output=True, text=True)
        inactive1 = run(['systemctl', 'list-timers', '--state=inactive',
                         arg], capture_output=True, text=True, check=True)
        inactive2 = run(['grep', '-w', arg], input=inactive1.stdout,
                        capture_output=True, text=True)
    except CalledProcessError as e:
        print(part1.stdout, '\n', part2.stdout, '\n',
              inactive1.stdout, '\n', inactive2.stdout)
        print(e)
        sys.exit(1)
    out = part2.stdout.split()
    inct = inactive2.stdout.split()
    if inct:
        astr = 'inactive, last started '
        info = inct[2:6]
        info.insert(0, inct[-2])
    elif out:
        astr = 'active, last started '
        info = out[7:11]
        info.insert(0, out[-2])
    info.insert(1, astr)
    info = ' '.join(info)
    print(info)


def systemd_services(arg):
    try:
        part1 = run(['systemctl', 'show',
                     arg], capture_output=True, text=True, check=True)
        part2 = run(['grep', '-w', 'User\|FragmentPath\|Group'], input=part1.stdout,
                    capture_output=True, text=True)
        act1 = run(["systemctl", "status", arg],
                   capture_output=True, text=True)
        act2 = run(['grep', '-w', 'Active'], input=act1.stdout,
                   capture_output=True, text=True)
    except CalledProcessError as e:
        print(e)
        sys.exit(1)
    out = part2.stdout.split('\n')[:-1]
    res = {"name": None, "user": None, "group": None}
    for i in out:
        if i.split('=')[0] == "User":
            res["user"] = i.split('=')[1].strip('\n')
        elif i.split('=')[0] == "Group":
            res["group"] = i.split('=')[1].strip('\n')
        elif i.split('=')[0] == "FragmentPath":
            res["name"] = i.split('/')[-1].strip('\n')
    act = act2.stdout.split()
    indexes = [1, 4, 5, 6, 7]
    final = [act[i].strip(';') for i in indexes]
    final.insert(0, res["name"])
    final[1] = f'{final[1]},'
    final.insert(2, f"user {res['user']},")
    final.insert(3, f"group {res['group']},")
    final[4] = f'last started {final[4]}'
    print(" ".join(final))


if __name__ == '__main__':
    main(sys.argv[1:])
