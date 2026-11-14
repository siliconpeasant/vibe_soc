"""IEEE 1685 component wire ports and the documented bus-interface subset.

Register maps deliberately remain with xml2yml/yml2reg. Only ElementTree is used;
no XML extension or external entity resolver is installed.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .common import IDENT, write_text
from .parse import VerilogModule

NAMESPACES = {year: f'http://www.accellera.org/XMLSchema/IPXACT/1685-{year}'
              for year in ('2014', '2022')}
PORT_NAME = re.compile(IDENT)
DIMENSION = re.compile(r'\[([^\[\]]+)\]')
BOUND_SEPARATOR = re.compile(r'(?<!:):(?!:)')
DIRECTIONS = {'in': 'input', 'out': 'output', 'inout': 'inout'}
MODES = ('master', 'slave', 'initiator', 'target')
MODE_NAMES = {'2014': {'initiator': 'master', 'target': 'slave'},
              '2022': {'master': 'initiator', 'slave': 'target'}}
VLNV_FIELDS = ('vendor', 'library', 'name', 'version')


def import_component(file):
    root = ET.parse(file).getroot()
    namespace = next((ns for ns in NAMESPACES.values() if root.tag == '{'+ns+'}component'), None)
    if namespace is None:
        raise ValueError(f'{file}: expected an IEEE 1685-2014/2022 ipxact:component')
    ns = {'i': namespace}

    def text(node, path, required=True):
        value = node.findtext(path, namespaces=ns)
        if value is None or not value.strip():
            if required:
                raise ValueError(f'{file}: missing IP-XACT {path}')
            return ''
        return value.strip()

    def identifier(value):
        if not PORT_NAME.fullmatch(value):
            raise ValueError(f'{file}: unsupported HDL identifier {value!r}')
        return value

    def vlnv(node):
        if node is None or any(not node.get(k) for k in VLNV_FIELDS):
            raise ValueError(f'{file}: incomplete IP-XACT VLNV reference')
        return {k: node.get(k) for k in VLNV_FIELDS}

    module = VerilogModule(identifier(text(root, 'i:name')))
    module.file = str(Path(file).resolve())
    module.vlnv = {k: text(root, 'i:'+k) for k in VLNV_FIELDS}
    for param in root.findall('i:parameters/i:parameter', ns):
        module.params.append((identifier(text(param, 'i:name')), text(param, 'i:value'), ''))
    for port in root.findall('i:model/i:ports/i:port', ns):
        name = identifier(text(port, 'i:name'))
        if name in module.details:
            raise ValueError(f'{file}: duplicate port {name}')
        wire = port.find('i:wire', ns)
        if wire is None:
            raise ValueError(f'{file}: unsupported IP-XACT non-wire port {name}')
        direction = text(wire, 'i:direction')
        if direction not in DIRECTIONS:
            raise ValueError(f'{file}: unsupported direction {direction} on {name}')
        width = ''.join('['+text(v, 'i:left')+':'+text(v, 'i:right')+']'
                        for v in wire.findall('i:vectors/i:vector', ns))
        module.ports.append((DIRECTIONS[direction], width, name))
        module.details[name] = dict(type=text(wire, 'i:wireTypeDefs/i:wireTypeDef/i:typeName', False),
                                    unpacked='', file=module.file, line=1)
        # Silently flattening slices/arrays changes the public interface.
        if port.find('i:arrays', ns) is not None:
            raise ValueError(f'{file}: unsupported IP-XACT unpacked array {name}')
    buses = []
    for bus in root.findall('i:busInterfaces/i:busInterface', ns):
        name = text(bus, 'i:name')
        modes = [mode for mode in MODES if bus.find('i:'+mode, ns) is not None]
        if len(modes) != 1:
            raise ValueError(f'{file}: bus {name} needs one supported master/slave/initiator/target mode')
        abstractions = []
        for abstraction in bus.findall('i:abstractionTypes/i:abstractionType', ns):
            maps = []
            for mapping in abstraction.findall('i:portMaps/i:portMap', ns):
                physical = text(mapping, 'i:physicalPort/i:name')
                if physical not in module.details:
                    raise ValueError(f'{file}: bus {name} references unknown physical port {physical}')
                if any(mapping.find(path, ns) is not None for path in (
                        'i:physicalPort/i:partSelect', 'i:logicalPort/i:range', 'i:logicalPort/i:vector')):
                    raise ValueError(f'{file}: bus {name}: sliced port maps are unsupported')
                maps.append(dict(logical_port=text(mapping, 'i:logicalPort/i:name'), physical_port=physical))
            abstractions.append(dict(abstraction_type=vlnv(abstraction.find('i:abstractionRef', ns)), port_maps=maps))
        buses.append(dict(name=name, bus_type=vlnv(bus.find('i:busType', ns)),
                          mode=modes[0], abstraction_types=abstractions))
    if len({b['name'] for b in buses}) != len(buses):
        raise ValueError(f'{file}: duplicate bus interface name')
    module.bus_interfaces = buses
    return module


def export_component(module, output=None, version='2014', bus_interfaces=None):
    if version not in NAMESPACES:
        raise ValueError('IP-XACT version must be 2014 or 2022')
    namespace = NAMESPACES[version]
    ET.register_namespace('ipxact', namespace)

    def element(parent, tag, value=None, **attributes):
        node = ET.SubElement(parent, '{'+namespace+'}'+tag, attributes)
        if value is not None:
            node.text = str(value)
        return node

    def reference(parent, tag, value):
        if not isinstance(value, dict) or any(not value.get(k) for k in VLNV_FIELDS):
            raise ValueError(f'incomplete {tag} VLNV reference')
        return element(parent, tag, **{k: str(value[k]) for k in VLNV_FIELDS})

    root = ET.Element('{'+namespace+'}component')
    identity = getattr(module, 'vlnv', dict(vendor='local', library='soc', name=module.name, version='1.0'))
    for key in VLNV_FIELDS:
        element(root, key, module.name if key == 'name' else identity[key])
    buses = getattr(module, 'bus_interfaces', []) if bus_interfaces is None else bus_interfaces
    if buses:
        group = element(root, 'busInterfaces')
        for bus in buses:
            item = element(group, 'busInterface')
            element(item, 'name', bus['name'])
            reference(item, 'busType', bus['bus_type'])
            if bus.get('abstraction_types'):
                abstractions = element(item, 'abstractionTypes')
                for abstraction in bus['abstraction_types']:
                    entry = element(abstractions, 'abstractionType')
                    reference(entry, 'abstractionRef', abstraction['abstraction_type'])
                    mappings = element(entry, 'portMaps') if abstraction['port_maps'] else None
                    for mapping in abstraction['port_maps']:
                        physical = mapping['physical_port']
                        if physical not in module.details:
                            raise ValueError(f'bus {bus["name"]}: unknown physical port {physical}')
                        pair = element(mappings, 'portMap')
                        element(element(pair, 'logicalPort'), 'name', mapping['logical_port'])
                        element(element(pair, 'physicalPort'), 'name', physical)
            if bus['mode'] not in MODES:
                raise ValueError(f'unsupported bus mode {bus["mode"]}')
            element(item, MODE_NAMES[version].get(bus['mode'], bus['mode']))
    model = element(root, 'model')
    ports = element(model, 'ports') if module.ports else None
    reverse = {v: k for k, v in DIRECTIONS.items()}
    for direction, width, name in module.ports:
        detail = module.details.get(name, {})
        if direction not in reverse or detail.get('unpacked'):
            raise ValueError(f'{name}: IP-XACT export supports scalar/packed wire ports only')
        port = element(ports, 'port')
        element(port, 'name', name)
        wire = element(port, 'wire')
        element(wire, 'direction', reverse[direction])
        if width:
            dimensions = DIMENSION.findall(width)
            if not dimensions or ''.join('['+d+']' for d in dimensions) != width:
                raise ValueError(f'{name}: unsupported packed dimensions {width}')
            vectors = element(wire, 'vectors')
            for dimension in dimensions:
                bounds = BOUND_SEPARATOR.split(dimension)
                if len(bounds) != 2:
                    raise ValueError(f'{name}: unsupported packed dimension {dimension}')
                vector = element(vectors, 'vector')
                element(vector, 'left', bounds[0])
                element(vector, 'right', bounds[1])
        if detail.get('type'):
            definition = element(element(wire, 'wireTypeDefs'), 'wireTypeDef')
            element(definition, 'typeName', detail['type'])
    if module.params:
        parameters = element(root, 'parameters')
        for name, value, _ in module.params:
            parameter = element(parameters, 'parameter', parameterId=name)
            element(parameter, 'name', name)
            element(parameter, 'value', value)
    ET.indent(root, space='  ')
    result = ET.tostring(root, encoding='unicode', xml_declaration=True) + '\n'
    if output:
        write_text(output, result)
    return result
