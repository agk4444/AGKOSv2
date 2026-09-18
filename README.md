# AGKOS v0.1 — a simulated operating system written in AGK-Real

A real bare-metal OS can't be built with AGK-Real (it compiles to Python,
and Python needs an OS underneath it). So AGKOS is the honest version of
that dream: a **simulated OS** — a kernel with a scheduler, memory manager,
virtual filesystem, and interactive shell, all written in AGK, all actually
running.

## Run it

```sh
agk run boot.agk
```

You get a boot sequence and a shell prompt (`agk>`). Try:

```
help
ls
cat /readme.txt
run counter 5
run clock 3
ps
tick 10
write /home/todo.txt buy milk
cat /home/todo.txt
shutdown
```

## Architecture

| File | What it is |
|---|---|
| `boot.agk` | Boot sequence: probes memory, mounts the filesystem seeds, starts the shell |
| `kernel.agk` | The kernel. Owns memory, scheduler, filesystem; exposes the syscall layer (`sys_print`, `sys_uptime`, `sys_write_file`, `sys_read_file`, `spawn`) |
| `memory.agk` | `MemoryManager`: 256-block pool, first-fit allocation, free-list coalescing |
| `process.agk` | `Process` + `Scheduler`: cooperative round-robin. Each cycle gives every READY process one `tick()`; finished processes are reaped and their memory freed |
| `fs.agk` | `FileSystem`: in-memory tree. Missing paths `raise`; the shell catches them like syscall errors |
| `programs.agk` | User programs (`CounterProg`, `ClockProg`, `WriterProg`). They touch hardware only through kernel syscalls |
| `shell.agk` | Interactive shell: `help ps run kill tick mem ls cat write mkdir echo uptime shutdown` |

## What it demonstrates

- Multi-module AGK programs with cross-module class references
- Exceptions as syscall errors (`raise`/`catch` across module boundaries)
- String interpolation, `for`/`while` loops, default-free cooperative scheduling
- The full pipeline: `boot.agk` compiles all 7 modules into one Python program

## Compiler fixes found while building this

1. **Cross-module references**: imported modules were analyzed standalone, so
   `kernel.agk` couldn't see `memory.agk`'s classes. `pipeline.py` now analyzes
   modules in dependency order with earlier modules visible.
2. **`raise` with interpolation**: `"...{x}..."` desugars to `"...".format(x)`,
   which was raised as a raw `str` (a `TypeError` in Python). `codegen.py` now
   wraps `.format()` calls in `Exception(...)` too.
