# TODO: This file is mostly gen ai yap so I need to revise and read through it to understand what it did... will take time...
import subprocess
import sys
import os
import threading
import queue
import time
import traceback
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLI_SCRIPT = os.path.join(SCRIPT_DIR, "Main.py")
LOG_FILE = os.path.join(SCRIPT_DIR, "cli_automation.log")

PROMPT_MARKER = "Enter your number here:"   # exact prompt to watch for
FINAL_WAIT_SECONDS = 30

def _reader_thread(stream, out_queue):
    """Read lines from 'stream' and put them (stripped) into out_queue.
       Do NOT close the stream here. Thread exits when EOF reached."""
    try:
        while True:
            line = stream.readline()
            if line == "":  # EOF
                break
            out_queue.put(line)
    except Exception:
        # if something goes wrong reading, put exception info into queue
        out_queue.put(f"[READER ERROR] {traceback.format_exc()}\n")
    # do not close stream

def run_headless_prompt_based():
    # open log in append mode and keep it open until the end
    log = open(LOG_FILE, "a", encoding="utf-8")
    try:
        log.write(f"\n[{datetime.now().isoformat()}] --- Starting automated CLI run ---\n")
        log.flush()

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", CLI_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )
        except Exception as e:
            log.write(f"[{datetime.now().isoformat()}] ERROR launching child: {e}\n")
            log.write(traceback.format_exc())
            log.flush()
            return

        # queues for lines read by threads
        stdout_q = queue.Queue()
        stderr_q = queue.Queue()

        t_out = threading.Thread(target=_reader_thread, args=(proc.stdout, stdout_q), daemon=True)
        t_err = threading.Thread(target=_reader_thread, args=(proc.stderr, stderr_q), daemon=True)
        t_out.start()
        t_err.start()

        def send_input(cmd: str):
            try:
                if proc.stdin:
                    proc.stdin.write(cmd + "\n")
                    proc.stdin.flush()
                    log.write(f"[{datetime.now().isoformat()}] [INPUT] {cmd}\n")
                    log.flush()
            except Exception as e:
                log.write(f"[{datetime.now().isoformat()}] ERROR sending input '{cmd}': {e}\n")
                log.write(traceback.format_exc())
                log.flush()

        prompt_count = 0
        sent_execute = False
        sent_quit = False
        child_error = False

        try:
            while True:
                got_something = False

                # drain stdout queue
                while True:
                    try:
                        line = stdout_q.get_nowait()
                    except queue.Empty:
                        break
                    got_something = True
                    # main thread writes to log only
                    log.write(line)
                    log.flush()

                    # detect prompt
                    if PROMPT_MARKER in line:
                        prompt_count += 1
                        if prompt_count == 1 and not sent_execute:
                            send_input("2")
                            sent_execute = True
                        elif prompt_count >= 2 and not sent_quit:
                            send_input("q")
                            sent_quit = True

                # drain stderr queue
                while True:
                    try:
                        el = stderr_q.get_nowait()
                    except queue.Empty:
                        break
                    got_something = True
                    log.write(f"[STDERR] {el}")
                    log.flush()
                    child_error = True

                # check if process exited
                rc = proc.poll()
                if rc is not None:
                    # process finished; drain any remaining items then break
                    while True:
                        try:
                            line = stdout_q.get_nowait()
                            log.write(line)
                            log.flush()
                        except queue.Empty:
                            break
                    while True:
                        try:
                            el = stderr_q.get_nowait()
                            log.write(f"[STDERR] {el}")
                            log.flush()
                            child_error = True
                        except queue.Empty:
                            break
                    break

                if not got_something:
                    time.sleep(0.1)
                    continue

            # close stdin to signal EOF
            try:
                if proc.stdin:
                    proc.stdin.close()
            except Exception:
                pass

            # wait for graceful exit
            try:
                proc.wait(timeout=FINAL_WAIT_SECONDS)
            except subprocess.TimeoutExpired:
                log.write(f"[{datetime.now().isoformat()}] Child did not exit in {FINAL_WAIT_SECONDS}s — killing.\n")
                log.flush()
                try:
                    proc.kill()
                except Exception:
                    pass

            # join threads to ensure they finished reading
            t_out.join(timeout=5)
            t_err.join(timeout=5)

            # final attempt to read any leftovers after threads joined
            while not stdout_q.empty():
                log.write(stdout_q.get())
            while not stderr_q.empty():
                log.write(f"[STDERR] {stderr_q.get()}")

            rc = proc.returncode
            if rc == 0 and not child_error:
                log.write(f"[{datetime.now().isoformat()}] --- CLI run finished successfully (exit code 0) ---\n")
            else:
                log.write(f"[{datetime.now().isoformat()}] --- CLI run finished with errors. exit_code={rc} ---\n")
            log.flush()

        except Exception as e:
            log.write(f"[{datetime.now().isoformat()}] Unexpected runner error: {e}\n")
            log.write(traceback.format_exc())
            log.flush()
            try:
                proc.kill()
            except Exception:
                pass

    finally:
        # ensure log is closed only after threads have finished and main thread wrote final messages
        try:
            log.write(f"[{datetime.now().isoformat()}] --- Runner exiting ---\n")
            log.flush()
        except Exception:
            pass
        try:
            log.close()
        except Exception:
            pass

if __name__ == "__main__":
    run_headless_prompt_based()
