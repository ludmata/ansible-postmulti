# ansible-postmulti
postmulti module for ansible

The postmulti module changes postfix multi instance configuration by invoking 'postmulti'. This is needed if you want to use the standart method of initialization and usage of postfix multi instance mode. The standard solutions (like using command module) lack idempotency or you need to run multiple ansible task which is cumbersome. The module does not support group asignment after creation, although its easy to make it work if needed.

### Options:
  - action:
    [init|create|destroy] a postfix multi instance. When creating new instance state is required.
  - state:
    [enabled|disabled] enable or disable a postfix instance. When creating specify the initial state.
  - name: Name of postfix instance. Required.
  - group: Group of postfix instance. 
  - path: Config path of the new instance. Default is /etc/instance-name.

### Examples:
Put it in your role library folder and create tasks similar to:
```
- name: postmulti init
  postmulti:
    action: init
  tags:
    - postmulti

- name: create postfix instances
  postmulti:
    name: postfix-input
    action: create
    path: /etc/my-custom-path
    group: mta
    state: enabled
```