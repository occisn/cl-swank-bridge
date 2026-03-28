# cl-swank-bridge

## What Is This?

This project lets Claude Code (or similar LLM with a CLI) **talk to a live Common Lisp image** in Emacs, through the Swank protocol. Claude Code can evaluate expressions, load ASDF systems, run tests, and see all output -- directly in your SLIME REPL inside Emacs.

**Why?** Claude Code runs in the terminal. Common Lisp development happens in Emacs + SLIME, centered on a live REPL. This bridge connects the two, so Claude Code can build, test, and interact with your running Lisp the same way you do -- through Swank.

**The bridge is a single file: [`swank-eval.py`](swank-eval.py).** Drop it into any Common Lisp project, inform the LLM, and you're set. The rest of this repo (the `.asd` files, `src/`, `tests/`) is a minimal demo project for illustration only.

## How It Works

```
 Claude Code (terminal)          SBCL                       Emacs + SLIME
 ─────────────────────          ────                       ────────────────
        |                            |                          |
        |--- TCP :4005 ------------->|                          |
        |   swank:eval-and-grab-output                          |
        |                            |                          |
        |                            |--- :write-string ------->|
        |                            |   (via REPL connection)  |
        |                            |                          |
        |<-- (:return (:ok ...)) ----|                          |
```

Claude Code connects to a dedicated Swank port (4005) for evaluation. To display results in the SLIME REPL, it routes `:write-string` events through the existing SLIME connection.

When everything runs on the same host (e.g., all in WSL, or all on native Linux), `localhost` just works. If Claude Code and Emacs/SBCL are on different hosts (e.g., Claude Code in WSL2, Emacs on Windows), see [WSL2 Networking](#wsl2-networking) below.

## Prerequisites

- SBCL with SLIME/Swank
- Emacs with SLIME
- Python 3 (for `swank-eval.py`)
- Claude Code

## Step-by-Step Setup

### 1. Copy `swank-eval.py` into your project

Only one file is needed. Download or copy [`swank-eval.py`](swank-eval.py) into your Common Lisp project directory.

### 2. Start your Common Lisp environment

Launch Emacs and start SLIME (`M-x slime`). You now have a live SBCL image connected to Emacs via Swank.

### 3. Open a second Swank port for Claude Code

In your SLIME REPL, run:

```lisp
(swank:create-server :port 4005 :dont-close t)
```

This opens a second Swank listener that Claude Code will connect to. `:dont-close t` keeps it open for repeated connections.

### 4. Tell the LLM about the bridge

The LLM needs to know the bridge exists. Add the following to your project's `CLAUDE.md` (or equivalent instructions file for your LLM):

```markdown
## Swank Bridge

A live Common Lisp image is available via Swank. Use `swank-eval.py` to evaluate expressions:

- Silent eval: `python3 swank-eval.py "(expression)"`
- Visible in SLIME REPL: `python3 swank-eval.py "(expression)" --repl`

Use `--repl` for build, test, and demo commands so the user sees output in their REPL.
Common workflows: `(asdf:load-system "system-name")`, `(asdf:test-system "system-name")`.
```

### 5. Use it

From a terminal in the project directory, start Claude Code (or your LLM CLI). It can now evaluate CL expressions, build systems, and run tests through `swank-eval.py`.

## Usage

### From Claude Code (natural language)

Once `swank-eval.py` is in your project and the Swank port is open, you can just ask Claude Code in plain English:

> "Build the system in the REPL"
>
> "Force reload and run the tests"
>
> "Call the main function"
>
> "Evaluate (mapcar #'1+ '(1 2 3)) and show it in the REPL"

Claude Code will use `swank-eval.py` behind the scenes.

### From the command line

You can also call `swank-eval.py` directly:

```bash
# Silent eval -- result returned to caller only
python3 swank-eval.py "(+ 1 2)"
# => 3

# Visible eval -- expression, output, and result shown in SLIME REPL
python3 swank-eval.py "(+ 1 2)" --repl

# Specify package
python3 swank-eval.py "(main)" --package MY-PACKAGE

# Connect to a remote host (e.g., Windows host from WSL2)
python3 swank-eval.py "(+ 1 2)" --host 192.168.96.1
```

### Typical Workflows

```bash
# Load a system
python3 swank-eval.py '(asdf:load-system "my-system")' --repl

# Force recompile everything
python3 swank-eval.py '(asdf:load-system "my-system" :force t)' --repl

# Run tests (Parachute output displayed in REPL)
python3 swank-eval.py '(asdf:test-system "my-system")' --repl

# Call functions
python3 swank-eval.py '(my-package:main)' --repl
```

### Two Modes

| Mode   | Flag        | Expression visible in REPL | Output visible in REPL | Result returned to caller |
|--------|-------------|----------------------------|------------------------|---------------------------|
| Silent | _(default)_ | No                         | No                     | Yes                       |
| REPL   | `--repl`    | Yes                        | Yes                    | Yes                       |

## How the REPL Bridge Works

The key challenge: Claude Code's Swank connection is separate from SLIME's. Output sent to Claude's connection doesn't appear in the REPL.

The solution uses Swank internals to forward output to the REPL connection:

```lisp
;; Bind to the REPL's connection (second in the list)
(let ((swank::*emacs-connection* (second swank::*connections*)))
  ;; :repl-result target inserts at the prompt position
  (swank::send-to-emacs (list :write-string "text" :repl-result)))
```

Output from the evaluated expression is captured via broadcast streams and forwarded:

```lisp
(let ((*standard-output* (make-broadcast-stream *standard-output* capture-stream)))
  (eval expr))
;; Then send captured output to REPL via :write-string
```

## Demo Project

This repo includes a minimal CL project (`cl-project`) to demonstrate the bridge:

```
cl-project.asd         -- ASDF system definition
cl-project-tests.asd   -- Test system definition
package.lisp           -- CL-PROJECT package definition
src/file1.lisp         -- factorial, collatz-steps
src/file2.lisp         -- double, triple, main
tests/file1-tests.lisp -- Parachute tests for file1
tests/file2-tests.lisp -- Parachute tests for file2
```

## WSL2 Networking

Claude Code always runs in WSL2. Depending on where Emacs/SBCL runs, networking differs:

### Emacs in WSL (recommended)

When Emacs and SBCL also run inside WSL, everything is in the same network namespace. **No extra configuration is needed** — the default `localhost` connection works out of the box. This is the simplest setup.

### Emacs on Windows

When Emacs and SBCL run on **Windows** but Claude Code runs in WSL2, they are in different network namespaces — `localhost` won't cross the boundary. Three extra steps are needed:

**1. Bind Swank to all interfaces**

By default, Swank listens on `127.0.0.1` (loopback only). To accept connections from WSL2, bind to `0.0.0.0` before creating the server:

```lisp
(setf swank::*loopback-interface* "0.0.0.0")
(swank:create-server :port 4005 :dont-close t)
```

**2. Allow the port through Windows Firewall**

In an elevated PowerShell:

```powershell
New-NetFirewallRule -DisplayName "Swank WSL" -Direction Inbound -LocalPort 4005 -Protocol TCP -Action Allow
```

**3. Use the Windows host IP**

From WSL2, the Windows host IP is typically the default gateway:

```bash
ip route show default | awk '{print $3}'
# e.g., 192.168.96.1
```

Then pass it with `--host`:

```bash
python3 swank-eval.py '(+ 1 2)' --repl --host 192.168.96.1
```

For `CLAUDE.md`, add `--host` to the Swank Bridge section so the LLM uses it automatically.

## Limitations

- Expressions sent via `--repl` appear visually in the REPL but are **not** in SLIME's input history (M-p/M-n)
- Each eval opens/closes a TCP connection, producing a harmless `swank:close-connection` message
- Requires `(swank:create-server :port 4005 :dont-close t)` to be run manually after SLIME starts

## License

MIT
