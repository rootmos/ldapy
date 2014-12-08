#!/usr/bin/python

import sys
import syslog
if __name__ == "__main__":
    if len (sys.argv) < 3:
        sys.exit (-1)

    args = sys.argv
    args.pop (0)
    module_name = args.pop (0)
    __import__ (module_name)
    module = sys.modules[module_name]

    class_name = args.pop (0)
    cls = getattr (module, class_name)
    method = getattr (cls, args.pop (0))

    method (args)
    sys.exit (0)
