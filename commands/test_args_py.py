import sys
with open('args_output.txt', 'w') as f:
    f.write('Arguments:\n')
    for i, arg in enumerate(sys.argv[1:], 1):
        f.write(f'Arg {i}: {arg}\n')
    f.write('Done.\n') 
    
## sys.argv[1:] --> this will have username, password etc. 

## connect to health check url with username, passowrd authentication 

### Validate the result 

### send notifcation like email if required

## End 