# AGKOS v0.1 — a simulated operating system written in AGK-Real

A real bare-metal OS can't be built with AGK-Real (it compiles to Python,
and Python needs an OS underneath it). So AGKOS is the honest version of
that dream: a **simulated OS** — a kernel with a priority scheduler, memory
manager, persistent virtual filesystem, message passing, a virtual network,
and an interactive shell, all written in AGK, all actually running.

## Run it

```sh
agk run boot.agk
```

You get a boot sequence and a shell prompt showing your directory (`/ $`).
Try:

```
help
ls
cat /readme.txt
run counter 5
run sleeper 3
top
tick 10
send 1 hello there
write /home/todo.txt buy milk
ping web1
fetch http://web1/index.html
shutdown
```

Or in a browser: open `web/terminal.html` (regenerate with
`python3 web/build_terminal.py` after changing the `.agk` sources) — it
boots the real OS in Pyodide with an interactive terminal.

## Architecture

| File | What it is |
|---|---|
| `boot.agk` | Boot sequence: probes memory, restores or seeds the filesystem, starts the shell |
| `kernel.agk` | The kernel. Owns memory, scheduler, filesystem, inboxes, and the virtual net; exposes the syscall layer (`sys_print`, `sys_uptime`, `sys_sleep`, `sys_send`, `sys_recv`, `sys_lookup`, `sys_ping`, `sys_fetch`, file syscalls, `spawn`) |
| `memory.agk` | `MemoryManager`: 256-block pool, first-fit allocation, free-list coalescing |
| `process.agk` | `Process` + `Scheduler`: priority-ordered cooperative scheduling with sleep states and per-process CPU accounting. Each cycle gives every READY, awake process one `tick()`; finished processes are reaped and their memory freed |
| `fs.agk` | `FileSystem`: in-memory tree with JSON persistence (`save`/`load`). Missing paths `raise`; the shell catches them like syscall errors |
| `pipes.agk` | `InboxTable`: per-process message inboxes for `sys_send`/`sys_recv` |
| `net.agk` | `NetSim`: virtual hosts, DNS table, and canned web pages for `ping`/`fetch` |
| `programs.agk` | User programs (`CounterProg`, `ClockProg`, `WriterProg`, `SleeperProg`, `EchoerProg`, `TalkerProg`, `NetProg`). They touch hardware only through kernel syscalls |
| `shell.agk` | Interactive shell (see below) |
| `web/` | Browser terminal: `template.html` + `build_terminal.py` → `terminal.html` |

## Shell commands

```
ps                 list processes
top                process table (pid/name/state/pri/cpu)
run <prog> [n] [prio]   counter | clock | writer | sleeper | netprobe
run echoer [prio]       message echoer (prints anything sent to it)
run talker [n] [name] [prio]  send n pings to process 'name'
send <pid> <msg>   send a message to a process inbox
kill <pid>         terminate a process
tick [n]           advance the scheduler n cycles
mem                show memory usage
pwd / cd [path]    working directory navigation (relative paths, ..)
ls [path]          list a directory (default: cwd)
cat / write / mkdir / rm / cp / mv   file operations
run_script <path>  execute commands from a file
save               persist filesystem to agkos-fs.json
ping <host>        ping a virtual network host
fetch <url>        fetch a page from the virtual web
hosts              list virtual network hosts
echo / uptime / help
shutdown           halt the system (persists filesystem)
```

The filesystem persists to `agkos-fs.json` in the launch directory —
`save` writes it explicitly and `shutdown` writes it automatically; the
next boot restores it.

## What it demonstrates

- Multi-module AGK programs with cross-module class references
- Exceptions as syscall errors (`raise`/`catch` across module boundaries)
- String interpolation, `for`/`while` loops, priority scheduling with sleep
- Inter-process messaging, virtual networking, JSON persistence
- The full pipeline: `boot.agk` compiles all 9 modules into one Python program

## Compiler fixes found while building this

1. **Cross-module references**: imported modules were analyzed standalone, so
   `kernel.agk` couldn't see `memory.agk`'s classes. `pipeline.py` now analyzes
   modules in dependency order with earlier modules visible.
2. **`raise` with interpolation**: `"...{x}..."` desugars to `"...".format(x)`,
   which was raised as a raw `str` (a `TypeError` in Python). `codegen.py` now
   wraps `.format()` calls in `Exception(...)` too.
