"""Generate a bounded Verilator wiring smoke harness (no functional signoff)."""
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from .common import bit_width, resolve_param_width, write_text
from .extract import select_module
from .filelist import generate_filelist
from .render import declaration

CLOCK = re.compile(r'(?:clk(?:_\w+)?|\w+_clk(?:_i|_o)?)')
RESET = re.compile(r'(?:^|_)(?:rst|reset)(?:_|n(?:_|$)|$)')
ACTIVE_LOW = re.compile(r'(?:_n(?:[io]|_[io])?|(?:rst|reset)n(?:_[io])?)$')


def smoke_text(module, cycles=10, reset_cycles=2, period=10):
    if cycles <= 0 or reset_cycles < 1 or reset_cycles >= cycles:
        raise ValueError('cycles must exceed reset_cycles >= 1')
    if period < 2 or period % 2:
        raise ValueError('period must be an even integer >= 2')
    name = module.name + '_smoke_tb'
    lines = [f'module {name};']
    connections, clocks, resets, outputs = [], [], [], []
    for direction, width, port in module.ports:
        detail = dict(module.details.get(port, {}))
        width = resolve_param_width(width, module.params + module.localparams)
        detail['unpacked'] = resolve_param_width(detail.get('unpacked', ''), module.params + module.localparams)
        if direction not in ('input', 'output'):
            raise ValueError(f'{port}: smoke harness requires input/output value ports; map inouts/interfaces explicitly in a reviewed testbench')
        clock = direction == 'input' and bool(CLOCK.fullmatch(port))
        reset = direction == 'input' and bool(RESET.search(port))
        if (clock or reset) and (bit_width(width, detail['unpacked']) != 1 or detail.get('type', '') not in ('', 'wire', 'reg', 'logic', 'bit')):
            raise ValueError(f'{port}: detected clock/reset must be a scalar bit')
        if direction == 'output' or clock or reset:
            signal = 'tb_' + port
            if direction == 'output':
                lines.append('    ' + declaration('', width, signal, detail) + ';')
                outputs.append(signal)
            else:
                asserted = '0' if clock or ACTIVE_LOW.search(port) else '1'
                lines.append(f"    logic {signal} = 1'b{asserted};")
                if clock:
                    clocks.append(signal)
                else:
                    resets.append((signal, "1'b1" if asserted == '0' else "1'b0"))
            connections.append(f'        .{port}({signal})')
        else:
            value = "'{default:'0}" if detail['unpacked'] else "'0"
            connections.append(f'        .{port}({value})')
    lines += [f'    {module.name} dut (', ',\n'.join(connections), '    );', '    initial begin']
    # Drive every detected clock together; the smoke test makes no CDC claim.
    def tick(count):
        return [f'        repeat ({count}) begin', f'            #{period // 2};'] + [
            f'            {signal} = ~{signal};' for signal in clocks] + ['        end']
    lines += tick(reset_cycles * 2)
    lines += [f'        {signal} = {value};' for signal, value in resets]
    lines += tick((cycles - reset_cycles) * 2)
    display = ' '.join('%p' for _ in outputs)
    arguments = ', ' + ', '.join(outputs) if outputs else ''
    lines += [f'        $display("PASS: {module.name} smoke ({cycles} cycles) {display}"{arguments});',
              '        $finish;', '    end', 'endmodule']
    return '\n'.join(lines) + '\n'


def generate_smoke_tb(top_file, output='', module_name=None, cycles=10, reset_cycles=2,
                       period=10, run=False, module_files=(), include_dirs=(), defines=(),
                       packages=(), library_dirs=()):
    if Path(top_file).suffix.lower() == '.xml':
        raise ValueError('smoke requires an HDL implementation, not an IP-XACT interface description')
    module = select_module(top_file, module_name, include_dirs=include_dirs, defines=defines, packages=packages)
    output = Path(output or Path(top_file).with_name(module.name + '_smoke_tb.sv')).resolve()
    text = smoke_text(module, cycles, reset_cycles, period)
    manifest = generate_filelist(top_file, str(output.with_suffix('.f')), module_files=module_files,
                                 include_dirs=include_dirs, defines=defines, packages=packages, library_dirs=library_dirs)
    write_text(output, text)
    name = module.name + '_smoke_tb'

    def command(directory):
        return ['verilator', '--binary', '--timing', '-Wall', '--top-module', name,
                '--Mdir', str(directory), '-f', str(manifest), str(output)]

    # The printed command uses a directory alongside the harness, never obj_dir.
    build_dir = output.parent / (name + '_build')
    recipe = shlex.join(command(build_dir)) + ' && ' + shlex.quote(str(build_dir / ('V' + name)))
    result = f'Smoke testbench written: {output}\nFilelist written: {manifest}\nBuild/run: {recipe}\n'
    if run:
        if not shutil.which('verilator'):
            raise ValueError('Verilator is required for --run')
        with tempfile.TemporaryDirectory(prefix='soc-integrate-smoke-') as directory:
            build = subprocess.run(command(directory), capture_output=True, text=True, timeout=120)
            if build.returncode:
                raise ValueError('Verilator smoke build failed:\n' + build.stdout + build.stderr)
            simulation = subprocess.run([str(Path(directory) / ('V'+name))], capture_output=True, text=True, timeout=30)
            if simulation.returncode or f'PASS: {module.name} smoke' not in simulation.stdout:
                raise ValueError('Verilator smoke run failed:\n' + simulation.stdout + simulation.stderr)
            result += simulation.stdout + simulation.stderr
    return result
