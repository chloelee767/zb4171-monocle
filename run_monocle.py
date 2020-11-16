import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping
import pprint

class StringToBoolAction(argparse.Action):
    TRUE_STRINGS = ('t', 'true')
    FALSE_STRINGS = ('f', 'false')

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string = None):
        if type(values) != str:
            raise ValueError("value must be a string")
        values = values.lower()
        if values in StringToBoolAction.TRUE_STRINGS:
            setattr(namespace, self.dest, True)
        elif values in StringToBoolAction.FALSE_STRINGS:
            setattr(namespace, self.dest, False)
        else:
            raise ValueError("value must be one of: " +
                             ",".join(StringToBoolAction.TRUE_STRINGS + StringToBoolAction.FALSE_STRINGS))

class DisableAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string = None):
        raise ValueError("this parameter has been disabled")

def cli_prefix(*names: str) -> str:
    return '--' + '.'.join(names)

def add_as_nested(d: dict, names, value) -> None:
    current = d
    for i, k in enumerate(names):
        if i == len(names) - 1:
            current[k] = value
        if k not in current:
            current[k] = {}
        current = current[k]

def add_monocle_3_arg_convertor(config_dict: Mapping[str, Any]):
    make_flag_when_false = lambda name : lambda value: '' if value else '--no-' + name
    make_flag_when_true = lambda name: lambda value: '--' + name if value else ''
    make_value_flag = lambda name : lambda value: '--' + name + '=' + str(value)
    for name, d in config_dict.items():
        if M3_CLI_ARG in d:
            continue
        default_value = d[ARGPARSE_CONFIG][DEFAULT]
        if type(default_value) == bool:
            if default_value == True:
                fn = make_flag_when_false(name)
            else:
                fn = make_flag_when_true(name)
        else:
            fn = make_value_flag(name)
        # print(fn(default_value))
        d[M3_CLI_ARG] = fn
    return config_dict

def add_input_output(parser):
    parser.add_argument('--input', required = True)
    parser.add_argument('--output', required = True)

def generate_command(prefix, args_dict, config):
    input = args_dict['input']
    output = args_dict['output']
    io = f'"{input}" "{output}"'
    del args_dict['input']
    del args_dict['output']
    optionals = ' '.join(config[name][M3_CLI_ARG](value) for name, value in args_dict.items())
    return f'{prefix} {optionals} {io}'

# constants

ARGPARSE_CONFIG = 'parser-config'
M3_CLI_ARG = 'monocle3-cli-converter-function'

DEFAULT = 'default'
ACTION = 'action'
TYPE = 'type'

PREPROCESS = 'preprocess-cds'
REDUCE_DIM = 'reduce-dimension'
CLUSTER_CELLS = 'cluster-cells'
LEARN_GRAPH = 'learn-graph'
ORDER_CELLS = 'order-cells'

INPUT = 'input'
OUTPUT = 'output'

preprocess_config = add_monocle_3_arg_convertor({
    'method' : { ARGPARSE_CONFIG : { DEFAULT: 'PCA' } },
    'num-dim' : { ARGPARSE_CONFIG : { DEFAULT : 50, TYPE : int } },
    'norm-method' : { ARGPARSE_CONFIG : {DEFAULT : 'log'} },
    'pseudo-count' : { ARGPARSE_CONFIG : { DEFAULT : 1.0, TYPE : float } },
    'scaling' : { ARGPARSE_CONFIG : { DEFAULT : True, ACTION: StringToBoolAction } },
})

reduce_dim_config = add_monocle_3_arg_convertor({
    'max-components' : { ARGPARSE_CONFIG : { DEFAULT : 2, TYPE : int } },
    'reduction-method' : { ARGPARSE_CONFIG : { DEFAULT : 'UMAP' } },
    'preprocess-method' : { ARGPARSE_CONFIG : { DEFAULT : 'PCA' } },
    'umap.min-dist': { ARGPARSE_CONFIG : { DEFAULT : 0.1, TYPE : float } },
    'umap.n-neighbors' : { ARGPARSE_CONFIG : { DEFAULT : 15, TYPE : int } },
    'umap.nn-method' : { ARGPARSE_CONFIG : { DEFAULT : 'annoy' } },
})

cluster_cells_config = add_monocle_3_arg_convertor({
    'reduction-method' : { ARGPARSE_CONFIG : { DEFAULT : 'UMAP' } },
    'knn' : { ARGPARSE_CONFIG : { DEFAULT : 20, TYPE : int } },
    'weight' : { ARGPARSE_CONFIG : { DEFAULT : False, ACTION : StringToBoolAction } },
    'louvain-iter' : { ARGPARSE_CONFIG : { DEFAULT : 1, TYPE : int } },
    'resolution' : { ARGPARSE_CONFIG : { DEFAULT : None, TYPE : float },
                     M3_CLI_ARG : lambda v : '' if v == None else f'--resolution={v}' },
    'partition-qval' : { ARGPARSE_CONFIG : { DEFAULT : 0.05, TYPE: float } },
})

learn_graph_config = add_monocle_3_arg_convertor({
    'use-partition' : { ARGPARSE_CONFIG : {  DEFAULT: True, ACTION: StringToBoolAction } },
    'close-loop': { ARGPARSE_CONFIG : { DEFAULT: True, ACTION: StringToBoolAction } },
    'euclidean-distance-ratio': { ARGPARSE_CONFIG : { DEFAULT: 1.0, TYPE: float } },
    'geodesic-distance-ratio': { ARGPARSE_CONFIG : { DEFAULT: 1.0, TYPE: float } },
    'prune-graph': { ARGPARSE_CONFIG : { DEFAULT: True, ACTION: StringToBoolAction } },
    'minimal-branch-len': { ARGPARSE_CONFIG : { DEFAULT: 1, TYPE: int } },
    'orthogonal-proj-tip': { ARGPARSE_CONFIG : { DEFAULT: False, ACTION: StringToBoolAction } },
})

def add_args(parser, config_dict, cli_prefix_fn = cli_prefix):
    for name, config in config_dict.items():
        parser.add_argument(cli_prefix_fn(name), **config[ARGPARSE_CONFIG])

def replace_underscores(d : dict) -> dict:
    return {
        k.replace('_','-'): replace_underscores(v) if isinstance(v, dict) else v \
            for k,v in d.items()
    }

# TODO: think of a better way to deal with underscore/dash problem in parser

def disable_argument(parser : argparse.ArgumentParser, arg, prefix = '--'):
    # TODO: check that parser contains arg
    default = parser.get_default(arg.replace('-','_'))
    parser.add_argument(prefix + arg, help = argparse.SUPPRESS, action = DisableAction, default = default)

preprocess_parser = argparse.ArgumentParser()
add_input_output(preprocess_parser)
add_args(preprocess_parser, preprocess_config)

reduce_dim_parser = argparse.ArgumentParser()
add_input_output(reduce_dim_parser)
add_args(reduce_dim_parser, reduce_dim_config)

cluster_cells_parser = argparse.ArgumentParser()
add_input_output(cluster_cells_parser)
add_args(cluster_cells_parser, cluster_cells_config)

learn_graph_parser = argparse.ArgumentParser()
add_input_output(learn_graph_parser)
add_args(learn_graph_parser, learn_graph_config)

monocle_parser = argparse.ArgumentParser(conflict_handler = 'resolve')
add_input_output(monocle_parser)
monocle_parser.add_argument('--temp-dir', default='')
monocle_parser.add_argument('--save-config-to', default=None)
add_args(monocle_parser, preprocess_config, lambda n: cli_prefix(PREPROCESS, n))
add_args(monocle_parser, reduce_dim_config, lambda n : cli_prefix(REDUCE_DIM, n))
add_args(monocle_parser, cluster_cells_config, lambda n : cli_prefix(CLUSTER_CELLS, n))
add_args(monocle_parser, learn_graph_config, cli_prefix_fn = lambda n : cli_prefix(LEARN_GRAPH, n))
for arg in (f'{REDUCE_DIM}.preprocess-method',
            f'{REDUCE_DIM}.reduction-method', # disable because learn graph only works with UMAP
            f'{CLUSTER_CELLS}.reduction-method'):
    disable_argument(monocle_parser, arg)
# print(monocle_parser.parse_args('--input x --output y'.split()))

def generate_preprocess_cds_command(args_dict):
    return generate_command('monocle3 preprocess', args_dict, preprocess_config)

def generate_reduce_dim_command(args_dict):
    return generate_command('monocle3 reduceDim', args_dict, reduce_dim_config)

def generate_cluster_cells_command(args_dict):
    return generate_command('monocle3 partition', args_dict, cluster_cells_config)

def generate_learn_graph_command(args_dict):
    command = generate_command('monocle3 learnGraph', args_dict, learn_graph_config)
    return command

def generate_order_cells_command(args_dict):
    return generate_command('monocle3 orderCells', args_dict, {}) # no arguments except input and output

def generate_monocle3_commands(args_dict : dict):
    """
    Returns:
        list of [(command string, temp file to delete)...]
    """
    args_dict = args_dict.copy()

    args_dict[f'{REDUCE_DIM}.preprocess-method'] = args_dict[f'{PREPROCESS}.method']
    # args_dict[f'{CLUSTER_CELLS}.reduction-method'] = args_dict[f'{REDUCE_DIM}.reduction-method']

    temp_dir = Path(args_dict['temp-dir'])
    args_dict[f'{PREPROCESS}.{INPUT}'] = args_dict[INPUT]
    tmp1 = args_dict[f'{PREPROCESS}.{OUTPUT}'] = args_dict[f'{REDUCE_DIM}.{INPUT}'] = str(temp_dir / f'{PREPROCESS}-out.rds')
    tmp2 = args_dict[f'{REDUCE_DIM}.{OUTPUT}'] = args_dict[f'{CLUSTER_CELLS}.{INPUT}'] = str(temp_dir / f'{REDUCE_DIM}-out.rds')
    tmp3 = args_dict[f'{CLUSTER_CELLS}.{OUTPUT}'] = args_dict[f'{LEARN_GRAPH}.{INPUT}'] = str(temp_dir / f'{CLUSTER_CELLS}-out.rds')
    tmp4 = args_dict[f'{LEARN_GRAPH}.{OUTPUT}'] = args_dict[f'{ORDER_CELLS}.{INPUT}'] = str(temp_dir / f'{LEARN_GRAPH}-out.rds')
    args_dict[f'{ORDER_CELLS}.{OUTPUT}'] = args_dict[OUTPUT]

    commands = []
    for command_name, generate_fn, tmp_file in ((PREPROCESS, generate_preprocess_cds_command, None),
                                                (REDUCE_DIM, generate_reduce_dim_command, tmp1),
                                                (CLUSTER_CELLS, generate_cluster_cells_command, tmp2),
                                                (LEARN_GRAPH, generate_learn_graph_command, tmp3),
                                                (ORDER_CELLS, generate_order_cells_command, tmp4)):
        args = { k[len(command_name)+1:] : v for k, v in args_dict.items() if k.startswith(command_name)}
        cmd = generate_fn(args)
        commands.append((cmd, tmp_file))

    return commands

def clean_up_monocle_args_dict(args_dict : dict) -> dict:
    result = {
        # don't automate creation of inner dicts to ensure only functions we know about are added
        PREPROCESS : {},
        REDUCE_DIM : {},
        CLUSTER_CELLS : {},
        LEARN_GRAPH : {},
    }
    for k,v in args_dict.items():
        if '.' not in k:
            continue
        function_name, param = k.split(sep=".", maxsplit=1)
        result[function_name][param] = v

    # remove disabled params
    # TODO extract out
    del result[REDUCE_DIM]['preprocess-method']
    del result[CLUSTER_CELLS]['reduction-method']

    return result

# import pprint
# ad = replace_underscores(vars(monocle_parser.parse_args("--input x --output y --learn-graph.minimal-branch-len 12".split())))
# pprint.pp(ad)
# pprint.pp(generate_monocle3_commands(ad))

def monocle3_cli(*args_words):
    args_dict = replace_underscores(vars(monocle_parser.parse_args(*args_words)))
    if 'help' in args_dict:
        return

    if 'save-config-to' in args_dict:
        json.dump(clean_up_monocle_args_dict(args_dict), open(args_dict['save-config-to'], 'w'), indent = 2)
    commands = generate_monocle3_commands(args_dict)
    for c, tmp_file in commands:
        # raise error and don't execute further commands if there is a nonzero exit code
        print(c)
        subprocess.run(c, shell=True, check = True)
        if tmp_file:
            Path(tmp_file).unlink(missing_ok=True)

if __name__ == '__main__':
    monocle3_cli()
