#!/usr/bin/env python3
"""Evaluate Common Lisp expressions via a Swank connection."""

import socket
import sys
import re
import time


def swank_send(sock, msg):
    encoded = f"{len(msg):06x}{msg}"
    sock.sendall(encoded.encode("utf-8"))


def swank_recv_return(sock, timeout=5):
    response = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if b":return" in response:
                text = response.decode("utf-8", errors="replace")
                if re.search(r'\(:return\s+\(:ok\s', text) or \
                   re.search(r'\(:return\s+\(:abort', text):
                    break
        except socket.timeout:
            break
    return response.decode("utf-8", errors="replace")


def swank_connect(host="127.0.0.1", port=4005):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.settimeout(5)
    try:
        sock.recv(4096)
    except socket.timeout:
        pass
    return sock


def swank_eval(expr, package="COMMON-LISP-USER", host="127.0.0.1", port=4005):
    """Evaluate EXPR silently and return the result."""
    sock = swank_connect(host, port)

    escaped = expr.replace("\\", "\\\\").replace('"', '\\"')
    msg = f'(:emacs-rex (swank:eval-and-grab-output "{escaped}") "{package}" t 1)'
    swank_send(sock, msg)

    text = swank_recv_return(sock)
    sock.close()

    ok_match = re.search(r'\(:return \(:ok \("((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\)\) \d+\)', text)
    if ok_match:
        output = ok_match.group(1).replace('\\"', '"').replace("\\\\", "\\")
        value = ok_match.group(2).replace('\\"', '"').replace("\\\\", "\\")
        result = ""
        if output:
            result += output
        result += value
        return result

    abort_match = re.search(r'\(:return \(:abort "((?:[^"\\]|\\.)*)"\)', text)
    if abort_match:
        return f"ABORT: {abort_match.group(1)}"

    return f"RAW: {text}"


def swank_eval_in_repl(expr, package="COMMON-LISP-USER", host="127.0.0.1", port=4005):
    """Evaluate EXPR visibly in the SLIME REPL (input + result shown)."""
    escaped_inner = expr.replace("\\", "\\\\").replace('"', '\\"')
    escaped_outer = escaped_inner.replace("\\", "\\\\").replace('"', '\\"')
    wrapper = f'''
(locally (declare (sb-ext:muffle-conditions style-warning))
  (let* ((conn (second swank::*connections*))
         (swank::*emacs-connection* conn)
         (nl (string #\\Newline))
         (output (make-string-output-stream))
         (values (let ((*standard-output* (make-broadcast-stream *standard-output* output))
                       (*error-output* (make-broadcast-stream *error-output* output))
                       (*trace-output* (make-broadcast-stream *trace-output* output)))
                   (multiple-value-list (eval (read-from-string "{escaped_inner}")))))
         (output-str (get-output-stream-string output))
         (result-str (format nil "~{{~S~^, ~}}" values)))
    (swank::send-to-emacs (list :write-string "{escaped_outer}" :repl-result))
    (swank::send-to-emacs (list :write-string nl :repl-result))
    (when (plusp (length output-str))
      (swank::send-to-emacs (list :write-string output-str :repl-result)))
    (swank::send-to-emacs (list :write-string result-str :repl-result))
    (swank::send-to-emacs (list :write-string nl :repl-result))
    result-str))
'''
    return swank_eval(wrapper, package=package, host=host, port=port)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: swank-eval.py <expression> [--repl] [--package PKG] [--port PORT]")
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("expr", help="Common Lisp expression to evaluate")
    parser.add_argument("--repl", action="store_true", help="Show result in SLIME REPL")
    parser.add_argument("--package", default="COMMON-LISP-USER")
    parser.add_argument("--port", type=int, default=4005)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    if args.repl:
        print(swank_eval_in_repl(args.expr, package=args.package, host=args.host, port=args.port))
    else:
        print(swank_eval(args.expr, package=args.package, host=args.host, port=args.port))
