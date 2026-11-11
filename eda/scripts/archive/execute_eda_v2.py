"""Execute notebook cells with IPython and save actual outputs, without a kernel server."""
from pathlib import Path
import os
import time
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

eda = Path(__file__).resolve().parents[2]
os.chdir(eda)
notebook_path = eda / 'eda_v2_87%.ipynb'
nb = nbf.read(notebook_path, as_version=4)
shell = InteractiveShell.instance()
count = 0
for i, cell in enumerate(nb.cells):
    if cell.cell_type != 'code':
        continue
    count += 1
    started = time.monotonic()
    print(f'Executing cell {i} ({count})', flush=True)
    with capture_output() as captured:
        result = shell.run_cell(cell.source, store_history=True)
    cell.execution_count = count
    cell.outputs = []
    if captured.stdout:
        cell.outputs.append(nbf.v4.new_output('stream', name='stdout', text=captured.stdout))
    if captured.stderr:
        cell.outputs.append(nbf.v4.new_output('stream', name='stderr', text=captured.stderr))
    for output in captured.outputs:
        cell.outputs.append(nbf.v4.new_output('display_data', data=output.data, metadata=output.metadata))
    error = result.error_before_exec or result.error_in_exec
    if error:
        cell.outputs.append(nbf.v4.new_output('error', ename=type(error).__name__, evalue=str(error), traceback=[str(error)]))
        nbf.write(nb, notebook_path)
        raise RuntimeError(f'Cell {i} failed: {error}') from error
    nbf.validate(nb)
    nbf.write(nb, notebook_path)
    print(f'Completed cell {i}: {time.monotonic()-started:.1f}s, {len(cell.outputs)} outputs', flush=True)
print(f'All {count} code cells executed; saved {notebook_path}', flush=True)
