#!/usr/bin/env bash
# Standalone Earlgrey sim_verilator software build (no Bazel, no vendor writes).
set -euo pipefail
repo=$(cd "$(dirname "$0")/../../../../.." && pwd)
out="$repo/chip/top/dv/sim/sw_sim_verilator"
mkdir -p "$out"
exec > >(tee -a "$out/build.log") 2>&1
export PYTHONDONTWRITEBYTECODE=1
sw_python=${OT_SW_PYTHON:-/workspace/oss/venv/bin/python}
if ! command -v "$sw_python" >/dev/null 2>&1; then
  echo "SW build blocked: Python interpreter unavailable: $sw_python"
  exit 1
fi
for tool in riscv64-unknown-elf-gcc riscv64-unknown-elf-ar riscv64-unknown-elf-objcopy; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "SW build blocked: required tool unavailable: $tool"
    exit 1
  fi
done
"$sw_python" - "$repo" <<'PY'
import pathlib, sys, subprocess, os, time
import hjson
ROOT=pathlib.Path(sys.argv[1]).resolve()
OT=pathlib.Path(os.environ.get('OT_UPSTREAM_ROOT','/workspace/oss/opentitan')).resolve()
OUT=ROOT/'chip/top/dv/sim/sw_sim_verilator'
GEN=OUT/'generated'; OBJ=OUT/'obj'
for p in [GEN, OBJ, GEN/'hw/top/dt', GEN/'sw/device/lib/dif/autogen',GEN/'external']: p.mkdir(parents=True,exist_ok=True)
PY=sys.executable
os.environ['PYTHONPATH']=str(OT)+':'+str(OT/'util')
sys.path[:0]=[str(OT),str(OT/'util')]
import hashlib, shutil
revision=subprocess.check_output(['git','-C',str(OT),'rev-parse','HEAD'],text=True).strip()
expected='d63fbbcd5c2847e2483efc106a9f3a426251c7f1'
if revision != expected: raise SystemExit(f'Expected matching OpenTitan {expected}, found {revision}')
compiler=subprocess.check_output(['riscv64-unknown-elf-gcc','--version'],text=True)
recipe=ROOT/'chip/top/dv/tb/verilator/build_sw.sh'
key=hashlib.sha256(recipe.read_bytes()+str(OT).encode()+revision.encode()+compiler.encode()+PY.encode()).hexdigest()
keyfile=OUT/'build.key'
images=[OUT/n for n in ['test_rom_sim_verilator.39.scr.vmem','uart_smoketest_sim_verilator.64.scr.vmem','otp_sim_verilator.vmem']]
if keyfile.exists() and keyfile.read_text().strip()==key and all(p.is_file() for p in images):
 print('SW images cached: matching recipe, upstream revision and compiler.');sys.exit(0)
# Invalidate every generated header/object when the recipe changes, including
# changes to compiler defines and GCC compatibility overlays.
for p in [GEN,OBJ]:
 if p.exists(): shutil.rmtree(p)
for p in [GEN,OBJ,GEN/'hw/top/dt',GEN/'sw/device/lib/dif/autogen',GEN/'external']: p.mkdir(parents=True,exist_ok=True)
start=time.monotonic()
def run(args):
 print('+',' '.join(map(str,args)),flush=True)
 subprocess.run(list(map(str,args)),check=True,cwd=GEN,timeout=120)
top=OT/'hw/top_earlgrey/data/autogen/top_earlgrey.gen.hjson'
cfg=hjson.loads(top.read_text()); types=sorted({m['type'] for m in cfg['module']})
from reggen.ip_block import IpBlock
from reggen.gen_cheader import gen_cdefines
if not (GEN/'generation.done').exists():
 for ip in types:
  candidates=[OT/f'hw/top_earlgrey/ip_autogen/{ip}/data/{ip}.hjson',OT/f'hw/ip/{ip}/data/{ip}.hjson',OT/f'hw/top_earlgrey/ip/{ip}/data/{ip}.hjson']
  path=next((p for p in candidates if p.exists()),None)
  if not path: continue
  with (GEN/'hw/top'/f'{ip}_regs.h').open('w') as f: gen_cdefines(IpBlock.from_path(str(path),[]),f,None,'Generated from matching upstream OpenTitan')
  run([PY,OT/'util/autogen_dif.py','-i',path,'-o',GEN/'sw/device/lib/dif/autogen'])
  args=[PY,OT/'util/dttool.py','-t',top,'-o',GEN/'hw/top/dt','--gen-ip','-i',path]
  if ip in ['clkmgr','pwrmgr','rstmgr']:
   args+=['--extension',OT/f'hw/top/dt/{ip}_binding.py','--ipconfig',OT/f'hw/top_earlgrey/ip_autogen/{ip}/data/top_earlgrey_{ip}.ipconfig.hjson']
  if ip=='otp_ctrl': args+=['--default-node','core','--extension',OT/'hw/top_earlgrey/ip_autogen/otp_ctrl/util/dt.py','--ipconfig',OT/'hw/top_earlgrey/ip_autogen/otp_ctrl/data/top_earlgrey_otp_ctrl.ipconfig.hjson']
  run(args)
 run([PY,OT/'util/dttool.py','-t',top,'-o',GEN/'hw/top/dt','--gen-top'])
 for p in (OT/'hw/top_earlgrey/sw/autogen').glob('*.h'): (GEN/'hw/top'/p.name).write_text(p.read_text())
 for alias,target in [('top.h','top_earlgrey.h'),('top_memory.h','top_earlgrey_memory.h')]: (GEN/'hw/top'/alias).write_text(f'#include "hw/top/{target}"\n')
 (GEN/'generation.done').touch()
freertos=GEN/'external/freertos'
if not freertos.exists(): freertos.symlink_to(OT/'sw/vendor/freertos_freertos_kernel',target_is_directory=True)
from build_info import generate_build_info_c_source
(GEN/'build_info.c').write_text(generate_build_info_c_source(int('d63fbbcd5c2847e2483efc106a9f3a426251c7f1',16)))
# GCC lacks Clang's BSS-section pragma. Adapt only the generated include overlay.
import re
macros=(OT/'sw/device/lib/base/macros.h').read_text()
macros=re.sub(r'#define OT_SET_BSS_SECTION\(name, \.\.\.\).*?#define OT_SET_BSS_SECTION_\(section\) _Pragma\(#section\)', '#define OT_SET_BSS_SECTION(name, ...) __attribute__((section(name))) __VA_ARGS__', macros, flags=re.S)
header=GEN/'sw/device/lib/base/macros.h';header.parent.mkdir(parents=True,exist_ok=True);header.write_text(macros)
flags=['-U__INT32_TYPE__','-D__INT32_TYPE__=int','-U__UINT32_TYPE__','-D__UINT32_TYPE__=unsigned int','-march=rv32imc_zicsr_zifencei','-mabi=ilp32','-mcmodel=medany','-Os','-g','-ffreestanding','-fno-builtin','-fno-common','-ffunction-sections','-fdata-sections','-Wno-attributes','-DOPENTITAN_IS_EARLGREY','-DHAS_FLASH_CTRL','-DHAS_OTP_CTRL','-DHAS_RETENTION_RAM','-DOPENTITAN_HAS_ALERT_HANDLER=1','-DOPENTITAN_HAS_FLASH_CTRL=1','-I'+str(GEN),'-I'+str(OT),'-I'+str(OT/'sw/device/lib/base/freestanding'),'-I'+str(freertos/'include'),'-I'+str(freertos/'portable/GCC/RISC-V'),'-I'+str(OT/'sw/device/lib/testing/test_framework')]
flags += ['-DOTTF_CONSOLE_HAS_UART','-DOTTF_CONSOLE_HAS_SPI_DEVICE']
flags += ['-DOPENTITAN_HAS_'+ip.upper()+'=1' for ip in types]
paths=[]
for d in ['sw/device/lib/base','sw/device/lib/runtime','sw/device/lib/dif','sw/device/lib/testing','sw/device/silicon_creator/lib','sw/device/silicon_creator/lib/drivers','sw/device/silicon_creator/lib/base','sw/device/lib/testing/test_framework']:
 for p in (OT/d).glob('*.c'):
  if any(s in p.name for s in ['unittest','mock','english_breakfast','darjeeling','functest','ujson','_host','crc32','hardened_memory','random_order','polyfills']): continue
  if p.parent.name == 'testing' and p.stem not in ['pinmux_testutils','flash_ctrl_testutils','rand_testutils','uart_testutils','rv_plic_testutils','entropy_testutils','alert_handler_testutils','spi_device_testutils']: continue
  if p.parent.name == 'dif' and p.stem.removeprefix('dif_') not in types: continue
  paths.append(p)
paths += list((GEN/'sw/device/lib/dif/autogen').glob('*.c'))+list((GEN/'hw/top/dt').glob('*.c'))
paths += [OT/'sw/device/lib/arch/device_sim_verilator.c',OT/'sw/device/lib/arch/boot_stage_rom_ext.c',OT/'hw/top_earlgrey/sw/autogen/top_earlgrey.c',OT/'hw/top_earlgrey/sw/dt/sim_verilator.c',GEN/'build_info.c',OT/'sw/device/silicon_creator/rom/bootstrap.c',OT/'sw/device/lib/crt/crt.S']
paths += [freertos/p for p in ['list.c','queue.c','tasks.c']]+[freertos/'portable/MemMang/heap_1.c']
paths += [OT/'sw/device/lib/testing/test_framework/freertos_port.S']
def compile_source(p):
 o=OBJ/(str(p.relative_to(OT) if p.is_relative_to(OT) else p.relative_to(GEN)).replace('/','_')+'.o')
 if not o.exists() or o.stat().st_mtime < p.stat().st_mtime or p.name.startswith('static_critical_'): run(['riscv64-unknown-elf-gcc',*flags,'-c',p,'-o',o])
 return o
objects=[compile_source(p) for p in paths]
archive=OBJ/'libot.a'; run(['riscv64-unknown-elf-ar','rcs',archive,*objects])
# Mirror the upstream preprocessed linker scripts and static-critical section includes.
for p in [OT/'sw/device/lib/testing/test_framework/ottf_common.ld',OT/'sw/device/silicon_creator/lib/base/static_critical.ld']:
 q=GEN/p.relative_to(OT);q.parent.mkdir(parents=True,exist_ok=True)
 run(['riscv64-unknown-elf-gcc',*flags,'-E','-P','-x','c',p,'-o',q])
def link(name,srcs,ld):
 linker=GEN/(name+'.ld')
 run(['riscv64-unknown-elf-gcc',*flags,'-DOPENTITAN_TOP_MEMORY_LD='+str(OT/'hw/top_earlgrey/sw/autogen/top_earlgrey_memory.ld'),'-E','-P','-x','c',OT/ld,'-o',linker])
 elf=OUT/(name+'.elf')
 run(['riscv64-unknown-elf-gcc',*flags,'-nostdlib','-static','-Wl,--gc-sections','-Wl,--defsym=_chip_info_size=12','-Wl,-Map='+str(OUT/(name+'.map')),'-L'+str(GEN),'-L'+str(OT),'-T',linker,*[compile_source(OT/p) for p in srcs],*[compile_source(p) for p in (OT/'sw/device/silicon_creator/lib/base').glob('static_critical_*.c')],compile_source(GEN/'build_info.c'),'-Wl,--start-group',archive,'-lgcc','-Wl,--end-group','-o',elf])
 return elf
rom=link('test_rom_sim_verilator',['sw/device/lib/testing/test_rom/test_rom.c','sw/device/lib/testing/test_rom/test_rom_start.S'],'sw/device/lib/testing/test_rom/test_rom.ld')
flash=link('uart_smoketest_sim_verilator',['sw/device/tests/uart_smoketest.c','sw/device/silicon_creator/lib/manifest_def.c','sw/device/tests/closed_source/test_hooks_default.c','sw/device/lib/testing/test_framework/ottf_start.S','sw/device/lib/testing/test_framework/ottf_isrs.S'],'sw/device/lib/testing/test_framework/ottf_silicon_creator_a.ld')
run([PY,OT/'hw/ip/rom_ctrl/util/scramble_image.py',top,OT/'hw/top_earlgrey/data/autogen/top_earlgrey.secrets.testing.gen.hjson','base-rom',rom,OUT/'test_rom_sim_verilator.39.scr.vmem',OUT/'test_rom_sim_verilator.hash.c'])
# Upstream sim_verilator.bzl uses plain 64-bit flash VMEM; the C++ memory
# loader uses raw flash words; test ROM disables flash ECC and scrambling.
binary=OUT/'uart_smoketest_sim_verilator.bin';run(['riscv64-unknown-elf-objcopy','-O','binary',flash,binary])
# The test ROM reads the entry offset directly from the flash manifest.
# Linking manifest_def.c explicitly above keeps the linker-populated header;
# an omitted header makes the ROM interpret instructions as an entry address.
# Check the exported binary too, so a wrong objcopy load base fails before sim.
from elftools.elf.elffile import ELFFile
import struct
with flash.open('rb') as f:
 elf=ELFFile(f)
 symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
 manifest=elf.get_section_by_name('.manifest')
 if manifest is None or manifest['sh_size'] != 1024:
  raise SystemExit('Flash image must contain the upstream 1024-byte manifest')
 base=symbols['_ottf_start_address']
 header=manifest.data()
 data=binary.read_bytes()
 if manifest['sh_addr'] != base or data[:len(header)] != header:
  raise SystemExit('Flash binary does not start with its linked manifest')
 for offset,symbol in [(816,'_manifest_address_translation'),(892,'_manifest_code_start'),(896,'_manifest_code_end'),(900,'_manifest_entry_point')]:
  if struct.unpack_from('<I',header,offset)[0] != symbols[symbol]:
   raise SystemExit(f'Flash manifest field disagrees with linker symbol {symbol}')
 entry=base+symbols['_manifest_entry_point']
 if entry != elf['e_entry'] or not base+symbols['_manifest_code_start'] <= entry < base+symbols['_manifest_code_end']:
  raise SystemExit('Flash manifest entry must match ELF entry within executable code')
 print(f'FLASH_MANIFEST_OK base={base:#x} entry={entry:#x}',flush=True)
data=binary.read_bytes();data+=b'\xff'*((-len(data))%8)
with (OUT/'uart_smoketest_sim_verilator.64.scr.vmem').open('w') as f:
 for offset in range(0,len(data),8): f.write(f'@{offset//8:08x} {int.from_bytes(data[offset:offset+8],"little"):016x}\n')
# Reproduce the img_rma partitions from the BUILD declarations rather than
# silently using the older hand-maintained OTP HJSON defaults.
import ast, json, types
ns={'struct':lambda **kw:types.SimpleNamespace(**kw)}
consttree=ast.parse((OT/'rules/const.bzl').read_text())
for node in consttree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['CONST','EARLGREY_LOC_ALERTS'] for t in node.targets):
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<otp constants>','exec'),ns)
alerts=next(n.value for n in ast.parse((OT/'hw/top_earlgrey/data/autogen/defs.bzl').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EARLGREY_ALERTS' for t in n.targets))
ns['EARLGREY_ALERTS']=ast.literal_eval(alerts)
ns.update(otp_hex=lambda x:f'0x{x:08x}',otp_partition=lambda name,**kw:dict(name=name,**kw),TARGET_COMPATIBLE_WITH=[])
ns['otp_per_class_bytes']=lambda **kw:f'0x{sum(kw[k]<<(8*i) for i,k in enumerate("ABCD")):08x}'
ns['otp_per_class_ints']=lambda **kw:[f'0x{kw[k]:08x}' for k in 'ABCD']
ns['otp_per_class_lists']=lambda **kw:[f'0x{int(x.strip(),16):08x}' for k in 'ABCD' for x in kw[k].split(',')]
ns['otp_alert_classification']=lambda alert_list,default:[f'0x{sum(getattr(ns["CONST"].ALERT,"CLASS_"+c.strip())<<(8*i) for i,c in enumerate(default.split(","))):08x}' for _ in alert_list]
configs={}
for node in ast.parse((OT/'hw/top_earlgrey/data/otp/BUILD').read_text()).body:
 if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='otp_json':
  kw={k.arg:eval(compile(ast.Expression(k.value),'<otp BUILD field>','eval'),ns) for k in node.value.keywords if k.arg in ['name','partitions']}
  if 'partitions' not in kw: continue
  for partition in kw['partitions']:
   if 'items' in partition: partition['items']=[dict(name=k,value=v) for k,v in partition['items'].items()]
  configs[kw['name']]=dict(partitions=kw['partitions'])
otp_files=[]
for name in ['rma','creator_sw_cfg','owner_sw_cfg','hw_cfg0','hw_cfg1','secret0','secret1','secret2_unlocked']:
 p=GEN/('otp_'+name+'.json');p.write_text(json.dumps(configs['otp_json_'+name]));otp_files.append(p)
# Fake signing keys and their SHA256 block digest use upstream's own generator.
keycall=next(n.value for n in ast.parse((OT/'sw/device/silicon_creator/rom/keys/fake/otp/BUILD').read_text()).body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='otp_json_rot_keys')
keyparts=eval(compile(ast.Expression(next(k.value for k in keycall.keywords if k.arg=='partitions')),'<OTP fake keys>','eval'),ns)
for partition in keyparts: partition['items']=[dict(name=k,value=v) for k,v in partition['items'].items()]
keyinput=GEN/'otp_fake_keys_input.json';keyinput.write_text(json.dumps(dict(partitions=keyparts)))
keyoutput=GEN/'otp_fake_keys.json'
run([PY,OT/'util/design/gen-otp-rot-auth-json.py','--input',keyinput,'--output',keyoutput])
# Mirror opentitanlib/otp/alert_handler.rs and opentitantool otp alert-digest
# for the BUILD's all-X/disabled alert configuration; fail if that changes.
import zlib, struct
owner={i['name']:i['value'] for i in configs['otp_json_owner_sw_cfg']['partitions'][0]['items']}
assert int(owner['OWNER_SW_CFG_ROM_ALERT_CLASS_EN'],16)==0xa9a9a9a9
assert int(owner['OWNER_SW_CFG_ROM_ALERT_ESCALATION'],16)==0xd1d1d1d1
for item in ['OWNER_SW_CFG_ROM_ALERT_CLASSIFICATION','OWNER_SW_CFG_ROM_LOCAL_ALERT_CLASSIFICATION']:
 assert all(int(v,16)==0x94949494 for v in owner[item])
words=[]
for count in [len(ns['EARLGREY_ALERTS']),len(ns['EARLGREY_LOC_ALERTS'])]: words += [1]*count+[0]*count+[0]*count
phases=[int(v,16) for v in owner['OWNER_SW_CFG_ROM_ALERT_PHASE_CYCLES']]
for i in range(4): words += [1,0x3900,int(owner['OWNER_SW_CFG_ROM_ALERT_ACCUM_THRESH'][i],16),int(owner['OWNER_SW_CFG_ROM_ALERT_TIMEOUT_CYCLES'][i],16),*phases[i*4:i*4+4]]
crc=zlib.crc32(struct.pack('<'+'I'*len(words),*words))
assert crc==0xf9616122, f'upstream alert register defaults changed: {crc:#x}'
digests=[dict(name='OWNER_SW_CFG_ROM_ALERT_DIGEST_'+name,value=f'0x{crc^state^0x739:08x}') for name,state in [('PROD',0x65f2520f),('PROD_END',0x91b9b68a),('DEV',0x0b5a75e0),('RMA',0xcf8cfaab)]]
digestfile=GEN/'otp_alert_digest.json';digestfile.write_text(json.dumps(dict(partitions=[dict(name='OWNER_SW_CFG',items=digests)])))
otp_files.insert(1,keyoutput);otp_files.insert(4,digestfile)
run([PY,OT/'util/design/gen-otp-img.py','--quiet','--lc-state-def',OT/'hw/ip/lc_ctrl/data/lc_ctrl_state.hjson','--mmap-def',OT/'hw/top_earlgrey/data/otp/otp_ctrl_mmap.hjson','--top-secret-cfg',OT/'hw/top_earlgrey/data/autogen/top_earlgrey.secrets.testing.gen.hjson','--img-cfg',otp_files[0],'--add-cfg',*otp_files[1:],'--out',OUT/'otp_sim_verilator.BITWIDTH.vmem'])
(OUT/'otp_sim_verilator.vmem').write_bytes((OUT/'otp_sim_verilator.24.vmem').read_bytes())
elapsed=time.monotonic()-start
(OUT/'build_time.log').write_text(f'SW_BUILD_SECONDS={elapsed:.3f}\n')
keyfile.write_text(key+'\n')
print(f'SW_BUILD_SECONDS={elapsed:.3f}',flush=True)
PY
