def wait_for_ray_output(ray_process, success_string = 'trace success', fail_string = '',verbose=True):
    """_summary_

    Args:
        ray_process (_type_): _description_
        success_string (str, optional): _description_. Defaults to 'trace success'.
        fail_string (str, optional): _description_. Defaults to ''.
        verbose (bool, optional): _description_. Defaults to True.
    """
    out = "dummy-start-value"
    while len(out) > 0 and out != success_string:
       out = ray_process.stdout.readline().decode('utf8').rstrip('\n')
       #print(len(out), "###", out)
       if verbose:
	       print(out)
       #time.sleep(0.05)



def single_job(ray_stuff, ray_process):
    ray_verbose, ray_loc, rml_loc, exp_obj, exp_data, exp_loc, prefix = ray_stuff
    #print("DEBUG::rml_loc",rml_loc)
    print ('Starting Single Job')
    #ray_verbose = True
    if ray_verbose == True:
        print ('################')
        print ('pid', ray_process.pid)
    env = dict(os.environ)
    load_command = bytes('load '+ rml_loc + '\n', "utf-8" )
    ray_process.stdin.write(load_command)
    if ray_verbose == True:
        print ("loading rml file", rml_loc)
    ray_process.stdin.flush()
    if ray_verbose == True:
        print(ray_process.stdout.readline())
    if ray_verbose == True:
        print ("start tracing")
    trace_command=bytes('trace'+'\n', encoding='utf-8')
    ray_process.stdin.write(trace_command)
    ray_process.stdin.flush()
    wait_for_ray_output(ray_process, success_string = 'trace success', verbose=False)
    
    if ray_verbose == True:
        print ("exporting")
    export_command=bytes("export "+exp_obj+" "+exp_data+" "+exp_loc+" "+str(prefix)+'_'+" \n", 'utf-8')
    print('export command', export_command)
    ray_process.stdin.write(export_command)
    ray_process.stdin.flush()
    print(ray_process.stdout.readline())
    print('exported')
    print('OUT',ray_process.stdout.readline())

