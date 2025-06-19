import sys
with open('args_output.txt', 'w') as f:
    f.write('Arguments:\n')
    for i, arg in enumerate(sys.argv[1:], 1):
        f.write(f'Arg {i}: {arg}\n')
    f.write('Done.\n') 