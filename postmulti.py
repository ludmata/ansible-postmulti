#!/usr/bin/python
import subprocess


DOCUMENTATION = '''
---
module: postmulti
short_description: changes postfix multiinstance parameters
description:
  - The M(postmulti) module changes postfix multiinstance configuration by invoking 'postmulti'.
    This is needed if you want to use the standart method of initialization and usage
    of postfix multi instance mode. The standard solutions (like using command module) lack
    idempotency or you need to run multiple ansible task which is cumbersome. The module does not 
    support group asignment after creation, although its easy to make it work if needed.
options:
  action:
    description:
      - [init|create|destroy] a postfix multi instance. When creating new instance state is required.
    required: true
    default: null
  state:
    description:
      - [enabled|disabled] enable or disable a postfix instance. When creating specify the initial state.
    required: true
    default: null
  name:
    description:
      - Name of postfix instance 
    required: false
    default: null
  group:
    description:
      - Group of postfix instance 
    required: false
    default: null
  path:
    description:
      - Config path of the new instance.
    required: false
    default: '/etc/instance-name/'
author:
  - Ludmil Stamboliyski <me@ludmata.info>
'''

EXAMPLES = '''
- postmulti: action=init

- postmulti: action=create name=postfix-out group=mta state=enabled

- postmulti: state=disabled name=postfix-out group=mta

'''


def run(args, module):
    try:
        cmd = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = cmd.communicate()
        rc = cmd.returncode
    except (OSError, IOError) as e:
        module.fail_json(rc=e.errno, msg=str(e), cmd=args)
    if rc != 0:
        module.fail_json(rc=rc, msg=err, cmd=args)
    if err:
        module.warn(str(err))
    return out

def initialize(module):
    status = check_init(module)
    if status == 'yes':
        module.exit_json(
            msg=status,
            changed=False,
        )
    if not module.check_mode:
        run(['postmulti', '-e', 'init'], module)
    module.exit_json(
        msg="Postfix multi instance initialized",
        changed=True,
    )

def check_init(module):
    status = run(['postconf', '-h', 'multi_instance_enable'], module).decode("utf-8").strip()
    return status

def create(name, group, path, module):
    status = check_init(module)
    if status != 'yes':
        module.fail_json(msg="Multiinstance not enabled")
    exists = check_state(name,module)
    if not exists:
        args = ['postmulti', '-I', name, '-e', 'create']
        if group:
            args.extend(['-G', group])
        if path:
            args.append('config_directory='+path)
        run(args, module)
        changed = True
    else:
        changed = False
    return changed

def destroy(name, path, module):
    status = check_init(module)
    if not status == 'yes':
        module.fail_json(msg="Multiinstance not enabled")
    exists = check_state(name,module)
    if exists:
        args = ['postmulti', '-i', name, '-e', 'destroy']
        if not path:
            path = '/etc/' + name
        run(['postsuper', '-c', path, '-d', 'ALL'], module)
        disable(name, module)
        run(args, module)
        changed = True
    else:
        changed = False       
    return changed

def enable(name, module):
    status = check_init(module)
    state = check_state(name,module)
    if not status == 'yes':
        module.fail_json(msg="Multiinstance not enabled")
    if state == 'y':
        changed = False
    else:
        run(['postmulti', '-i', name, '-e', 'enable'], module)
        changed = True
    return changed

def disable(name, module):
    status = check_init(module)
    state = check_state(name,module)
    if not status == 'yes':
        module.fail_json(msg="Multiinstance not enabled")
    if state != 'y':
        changed = False
    else:
        run(['postmulti', '-i', name, '-e', 'disable'], module)
        changed = True
    return changed

# y,n or empty string
def check_state(name, module):
    l = run(['postmulti', '-l'], module)
    state = ''
    for line in l.decode('utf8').split('\n'):
        if not line.strip():
            continue
        if (line.split())[0] == name:
            state = (line.split())[2]
            break
    return state

def main():
    module = AnsibleModule(
        argument_spec = dict(
            action=dict(choices=['init', 'create', 'destroy'], required=False),
            state=dict(choices=['enabled', 'disabled'], required=False),
            path=dict(type="str", required=False),
            name=dict(required=False, type="str"),
            group=dict(required=False, type="str"),
        ),
        required_one_of=[['action','state']],
        required_if = [
            ["action", "create", ["name", "state"]],
            ["action", "destroy", ["name"]],
            ["state", "enabled", ["name"]],
            ["state", "disabled", ["name"]],
        ],
        supports_check_mode=True,
    )
    action = module.params['action']
    state = module.params['state']
    name = module.params['name']
    group = module.params['group']
    path = module.params['path']

    if action == 'init':
        initialize(module)
    elif action == 'create':
        Cchanged = create(name, group, path, module)
        if state == 'enabled':
            Schanged = enable(name, module)
        elif state == 'disabled':
            Schanged = disable(name, module)
        else:
            module.fail_json(msg="Unknown state: " + state)
        module.exit_json(
            msg="Instance "+name+" created and "+state+".",
            changed=(Cchanged or Schanged),
        )
            
    elif action == 'destroy':
        changed = destroy(name, path, module)
        module.exit_json(
            msg="Instance "+name+" destroyed.",
            changed=changed,
        )
        
    elif state:
        if state == 'enabled':
            s = enable(name, module)
        elif state == 'disabled':
            s = disable(name, module)
        else:
            module.fail_json(msg="Unknown state: " + state )

        if s == '':
            module.fail_json(msg="Instance " + name + " not found.")
        module.exit_json(
            msg="Instance " + name  + " " + state + ".",
            changed=s,
        )
        
from ansible.module_utils.basic import *  # noqa

if __name__ == '__main__':
    main()