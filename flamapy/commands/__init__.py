#!/usr/bin/python
import argparse
from functools import wraps
import inspect
from flamapy.interfaces.python.FLAMAFeatureModel import FLAMAFeatureModel

def extract_commands(cls):
    commands = []
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        docstring = method.__doc__
        signature = inspect.signature(method)
        # Exclude 'self' from parameters
        parameters = list(signature.parameters.values())[1:]  # Skip 'self'
        commands.append((name, docstring, method, parameters))
    return commands

def flamapy_cli() -> None:
    parser = argparse.ArgumentParser(description='FLAMA Feature Model CLI')
    subparsers = parser.add_subparsers(dest='command')

    dynamic_commands = extract_commands(FLAMAFeatureModel)

    # Add dynamic commands
    for name, docstring, method, parameters in dynamic_commands:
        subparser = subparsers.add_parser(name, help=docstring)
        
        # Add model_path to each subparser
        subparser.add_argument('model_path', type=str, help='Path to the feature model file')
        
        # Check if configuration_path is needed
        if 'configuration_path' in [param.name for param in parameters]:
            subparser.add_argument('--configuration_path', type=str, help='Path to the configuration file', required=False)
        
        for param in parameters:
            arg_name = param.name
            if arg_name not in ['model_path', 'configuration_path']:  # Avoid duplicates
                if param.default == param.empty:  # Positional argument
                    subparser.add_argument(arg_name, type=param.annotation, help=param.annotation.__name__)
                else:  # Optional argument
                    subparser.add_argument(f'--{arg_name}', type=param.annotation, default=param.default, help=f'Optional {param.annotation.__name__}')
        subparser.set_defaults(func=method, method_name=name, parameters=parameters)

    args = parser.parse_args()

    if args.command:
        try:
            # Instantiate the class with the required parameters for each command
            cls_instance = FLAMAFeatureModel(args.model_path, getattr(args, 'configuration_path', None))
            method_parameters = [param.name for param in args.parameters]
            command_args = {k: v for k, v in vars(args).items() if k in method_parameters}
            method = getattr(cls_instance, args.method_name)
            result = method(**command_args)
            if result is not None:
                print(result)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Available commands:")
        for name, docstring, _, _ in dynamic_commands:
            print(f"  {name}: {docstring}")
        parser.print_help()